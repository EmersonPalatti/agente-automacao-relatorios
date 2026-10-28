from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from tools.models import AnalysisResult, AnalysisSpec, DataProfile

plt.rcParams.update(
    {
        "figure.figsize": (9, 4.8),
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "font.size": 10,
    }
)


def _save(fig, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", dpi=130)
    plt.close(fig)
    return str(path)


def _col(df: pd.DataFrame, hint: list[str], candidates: list[str]) -> str | None:
    for name in hint:
        if name in df.columns:
            return name
    return candidates[0] if candidates else None


def _cats(profile: DataProfile) -> list[str]:
    return [c.name for c in profile.columns if c.is_categorical]


def _nums(profile: DataProfile) -> list[str]:
    return [c.name for c in profile.columns if c.is_numeric and not c.is_likely_id]


def _dates(profile: DataProfile) -> list[str]:
    dated = [c.name for c in profile.columns if c.is_datetime]
    if dated:
        return dated
    return [
        c.name
        for c in profile.columns
        if any(k in c.name.lower() for k in ("date", "time", "dt", "datetime"))
    ]


def run_missingness(df: pd.DataFrame, spec: AnalysisSpec, out_dir: Path, profile: DataProfile) -> AnalysisResult:
    pct = (df.isna().mean() * 100).sort_values(ascending=True)
    fig, ax = plt.subplots()
    pct.tail(min(15, len(pct))).plot.barh(ax=ax, color="#e85d04")
    ax.set_xlabel("% de nulos")
    ax.set_title(spec.title)
    artifact = _save(fig, out_dir / "missingness.png")
    metrics = {
        "null_pct_by_col": {k: round(float(v), 2) for k, v in pct.to_dict().items()},
        "cols_with_nulls": int((pct > 0).sum()),
    }
    return AnalysisResult(
        spec_id=spec.id,
        title=spec.title,
        analysis_type=spec.analysis_type,
        success=True,
        artifacts=[artifact],
        metrics=metrics,
        stdout=json.dumps(metrics, ensure_ascii=False),
    )


def run_categorical_top(df: pd.DataFrame, spec: AnalysisSpec, out_dir: Path, profile: DataProfile) -> AnalysisResult:
    col = _col(df, spec.columns_hint, _cats(profile))
    if not col:
        return _fail(spec, "Nenhuma coluna categórica disponível")
    counts = df[col].fillna("(nulo)").value_counts().head(12)
    fig, ax = plt.subplots()
    counts.sort_values().plot.barh(ax=ax, color="#0f4c5c")
    ax.set_xlabel("frequência")
    ax.set_title(spec.title)
    artifact = _save(fig, out_dir / f"top_{col}.png")
    total = int(counts.sum())
    metrics = {
        "column": col,
        "top": {str(k): int(v) for k, v in counts.to_dict().items()},
        "top1_share_pct": round(float(counts.iloc[0]) / max(len(df), 1) * 100, 2),
        "n_shown": int(len(counts)),
        "covered_rows": total,
    }
    return AnalysisResult(
        spec_id=spec.id,
        title=spec.title,
        analysis_type=spec.analysis_type,
        success=True,
        artifacts=[artifact],
        metrics=metrics,
        stdout=json.dumps(metrics, ensure_ascii=False),
    )


def run_numeric_distribution(df: pd.DataFrame, spec: AnalysisSpec, out_dir: Path, profile: DataProfile) -> AnalysisResult:
    col = _col(df, spec.columns_hint, _nums(profile))
    if not col:
        return _fail(spec, "Nenhuma coluna numérica disponível")
    series = pd.to_numeric(df[col], errors="coerce").dropna()
    fig, ax = plt.subplots()
    ax.hist(series, bins=30, color="#2a9d8f", edgecolor="white")
    ax.set_xlabel(col)
    ax.set_ylabel("frequência")
    ax.set_title(spec.title)
    artifact = _save(fig, out_dir / f"dist_{col}.png")
    metrics = {
        "column": col,
        "n": int(series.shape[0]),
        "mean": round(float(series.mean()), 4),
        "median": round(float(series.median()), 4),
        "p10": round(float(series.quantile(0.10)), 4),
        "p90": round(float(series.quantile(0.90)), 4),
        "min": round(float(series.min()), 4),
        "max": round(float(series.max()), 4),
    }
    return AnalysisResult(
        spec_id=spec.id,
        title=spec.title,
        analysis_type=spec.analysis_type,
        success=True,
        artifacts=[artifact],
        metrics=metrics,
        stdout=json.dumps(metrics, ensure_ascii=False),
    )


def run_timeseries(df: pd.DataFrame, spec: AnalysisSpec, out_dir: Path, profile: DataProfile) -> AnalysisResult:
    date_col = _col(df, spec.columns_hint, _dates(profile))
    num_candidates = [c for c in spec.columns_hint if c in df.columns and c != date_col]
    num_col = num_candidates[0] if num_candidates else (_nums(profile)[0] if _nums(profile) else None)
    if not date_col:
        return _fail(spec, "Nenhuma coluna de data/hora disponível")
    work = df.copy()
    work["_dt"] = pd.to_datetime(work[date_col], errors="coerce")
    work = work.dropna(subset=["_dt"])
    if work.empty:
        return _fail(spec, f"Não foi possível parsear datas em {date_col}")
    if num_col:
        work["_val"] = pd.to_numeric(work[num_col], errors="coerce")
        daily = work.groupby(work["_dt"].dt.date)["_val"].sum()
        ylabel = f"soma de {num_col}"
    else:
        daily = work.groupby(work["_dt"].dt.date).size()
        ylabel = "contagem"
        num_col = "count"
    fig, ax = plt.subplots()
    ax.plot(pd.to_datetime(daily.index), daily.values, color="#264653")
    ax.set_ylabel(ylabel)
    ax.set_title(spec.title)
    fig.autofmt_xdate()
    artifact = _save(fig, out_dir / "timeseries.png")
    metrics = {
        "date_col": date_col,
        "value_col": num_col,
        "n_days": int(daily.shape[0]),
        "min_day": str(daily.index.min()),
        "max_day": str(daily.index.max()),
        "peak_day": str(daily.idxmax()),
        "peak_value": round(float(daily.max()), 4),
        "mean_per_day": round(float(daily.mean()), 4),
    }
    return AnalysisResult(
        spec_id=spec.id,
        title=spec.title,
        analysis_type=spec.analysis_type,
        success=True,
        artifacts=[artifact],
        metrics=metrics,
        stdout=json.dumps(metrics, ensure_ascii=False),
    )


def run_numeric_by_category(df: pd.DataFrame, spec: AnalysisSpec, out_dir: Path, profile: DataProfile) -> AnalysisResult:
    nums = _nums(profile)
    cats = _cats(profile)
    num_col = None
    cat_col = None
    for name in spec.columns_hint:
        if name in df.columns and name in nums and num_col is None:
            num_col = name
        elif name in df.columns and name in cats and cat_col is None:
            cat_col = name
    num_col = num_col or (nums[0] if nums else None)
    cat_col = cat_col or (cats[0] if cats else None)
    if not num_col or not cat_col:
        return _fail(spec, "É preciso uma coluna numérica e uma categórica")
    work = df[[cat_col, num_col]].copy()
    work[num_col] = pd.to_numeric(work[num_col], errors="coerce")
    grouped = work.groupby(cat_col)[num_col].agg(["count", "mean", "median", "sum"]).sort_values("sum", ascending=False)
    top = grouped.head(12)
    fig, ax = plt.subplots()
    top["sum"].sort_values().plot.barh(ax=ax, color="#c1121f")
    ax.set_xlabel(f"soma de {num_col}")
    ax.set_title(spec.title)
    artifact = _save(fig, out_dir / f"{num_col}_by_{cat_col}.png")
    records = {
        str(idx): {
            "count": int(row["count"]),
            "mean": round(float(row["mean"]), 4),
            "median": round(float(row["median"]), 4),
            "sum": round(float(row["sum"]), 4),
        }
        for idx, row in top.iterrows()
    }
    metrics = {"numeric": num_col, "category": cat_col, "groups": records}
    return AnalysisResult(
        spec_id=spec.id,
        title=spec.title,
        analysis_type=spec.analysis_type,
        success=True,
        artifacts=[artifact],
        metrics=metrics,
        stdout=json.dumps(metrics, ensure_ascii=False),
    )


def run_correlation(df: pd.DataFrame, spec: AnalysisSpec, out_dir: Path, profile: DataProfile) -> AnalysisResult:
    hinted = [c for c in spec.columns_hint if c in df.columns]
    cols = hinted or _nums(profile)
    cols = [c for c in cols if c in df.columns]
    if len(cols) < 2:
        return _fail(spec, "É preciso pelo menos 2 colunas numéricas")
    work = df[cols].apply(pd.to_numeric, errors="coerce")
    corr = work.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr.index)), corr.index)
    fig.colorbar(im, ax=ax, fraction=0.046)
    ax.set_title(spec.title)
    artifact = _save(fig, out_dir / "correlation.png")
    pairs: list[dict[str, Any]] = []
    for i, a in enumerate(corr.columns):
        for j, b in enumerate(corr.columns):
            if i < j:
                val = corr.iloc[i, j]
                if pd.notna(val):
                    pairs.append({"a": str(a), "b": str(b), "r": round(float(val), 4)})
    pairs.sort(key=lambda x: abs(x["r"]), reverse=True)
    metrics = {"columns": cols, "top_pairs": pairs[:8]}
    return AnalysisResult(
        spec_id=spec.id,
        title=spec.title,
        analysis_type=spec.analysis_type,
        success=True,
        artifacts=[artifact],
        metrics=metrics,
        stdout=json.dumps(metrics, ensure_ascii=False),
    )


def _fail(spec: AnalysisSpec, error: str) -> AnalysisResult:
    return AnalysisResult(
        spec_id=spec.id,
        title=spec.title,
        analysis_type=spec.analysis_type,
        success=False,
        error=error,
    )


REGISTRY: dict[str, Callable[..., AnalysisResult]] = {
    "missingness": run_missingness,
    "categorical_top": run_categorical_top,
    "numeric_distribution": run_numeric_distribution,
    "timeseries": run_timeseries,
    "numeric_by_category": run_numeric_by_category,
    "correlation": run_correlation,
}


def plan_from_profile(profile: DataProfile) -> list[AnalysisSpec]:
    """Plano determinístico, data-agnostic, no máximo 5 análises."""
    cats = _cats(profile)
    nums = _nums(profile)
    dates = _dates(profile)
    specs: list[AnalysisSpec] = [
        AnalysisSpec(
            id="a1",
            title="Qualidade: valores ausentes",
            goal="Medir nulos por coluna para priorizar limpeza",
            analysis_type="missingness",
        )
    ]
    if cats:
        specs.append(
            AnalysisSpec(
                id=f"a{len(specs)+1}",
                title=f"Concentração em {cats[0]}",
                goal="Ver categorias dominantes",
                analysis_type="categorical_top",
                columns_hint=[cats[0]],
            )
        )
    if nums:
        specs.append(
            AnalysisSpec(
                id=f"a{len(specs)+1}",
                title=f"Distribuição de {nums[0]}",
                goal="Entender forma, centro e cauda da métrica principal",
                analysis_type="numeric_distribution",
                columns_hint=[nums[0]],
            )
        )
    if dates and nums:
        specs.append(
            AnalysisSpec(
                id=f"a{len(specs)+1}",
                title=f"{nums[0]} ao longo do tempo",
                goal="Detectar tendência e pico temporal",
                analysis_type="timeseries",
                columns_hint=[dates[0], nums[0]],
            )
        )
    if cats and nums:
        specs.append(
            AnalysisSpec(
                id=f"a{len(specs)+1}",
                title=f"{nums[0]} por {cats[0]}",
                goal="Comparar volume/valor entre grupos",
                analysis_type="numeric_by_category",
                columns_hint=[nums[0], cats[0]],
            )
        )
    elif len(nums) >= 2 and len(specs) < 5:
        specs.append(
            AnalysisSpec(
                id=f"a{len(specs)+1}",
                title="Correlação entre numéricas",
                goal="Encontrar pares linearmente associados",
                analysis_type="correlation",
                columns_hint=nums[:6],
            )
        )
    return specs[:5]
