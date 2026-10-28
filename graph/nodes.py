from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pandas as pd

from tools.analyses import REGISTRY, plan_from_profile
from tools.cleaner import clean_dataframe
from tools.code_executor import execute_code
from tools.data_loader import load_source, save_parquet
from tools.llm import complete, llm_configured, load_prompt, parse_json_object
from tools.models import AnalysisPlan, AnalysisResult, AnalysisSpec, CleaningLog, DataProfile
from tools.profiler import profile_dataframe
from tools.progress import emit
from tools.report_builder import build_markdown, write_markdown, write_pdf
from tools.timing import compute_economy

MAX_CODE_RETRIES = 3


def _log(state: dict, msg: str) -> list[str]:
    emit(msg)
    return list(state.get("logs") or []) + [msg]


def _timed_update(state: dict, step: str, started: float, **extra) -> dict:
    elapsed = time.perf_counter() - started
    timings = dict(state.get("timings") or {})
    timings[step] = elapsed
    extra["timings"] = timings
    extra.setdefault("logs", _log(state, f"{step} concluído em {elapsed:.2f}s"))
    return extra


def ingest(state: dict) -> dict:
    t0 = time.perf_counter()
    source = Path(state["source_path"])
    run_dir = Path(state["output_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = run_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    emit(f"Ingerindo {source.name}...")
    df = load_source(source, sql=state.get("sql"))
    df_path = save_parquet(df, run_dir / "processed.parquet")
    return _timed_update(
        state,
        "ingest",
        t0,
        run_dir=str(run_dir),
        plots_dir=str(plots_dir),
        df_path=str(df_path),
        source_name=source.name,
        logs=_log(state, f"ingest: {df.shape[0]} linhas x {df.shape[1]} colunas"),
    )


def clean(state: dict) -> dict:
    t0 = time.perf_counter()
    emit("Limpando dados...")
    import polars as pl

    df = pl.read_parquet(state["df_path"])
    cleaned, log = clean_dataframe(df)
    save_parquet(cleaned, state["df_path"])
    dropped = log.n_cols_in - log.n_cols_out
    return _timed_update(
        state,
        "clean",
        t0,
        cleaning_log=log.model_dump(),
        logs=_log(
            state,
            f"clean: {log.n_rows_out} linhas, {log.n_cols_out} colunas "
            f"({dropped} coluna(s) vazia(s) removida(s))",
        ),
    )


def profile(state: dict) -> dict:
    t0 = time.perf_counter()
    emit("Calculando perfil factual...")
    import polars as pl

    df = pl.read_parquet(state["df_path"])
    prof = profile_dataframe(df)
    return _timed_update(state, "profile", t0, profile=prof.model_dump())


def plan(state: dict) -> dict:
    t0 = time.perf_counter()
    emit("Planejando analises...")
    prof = DataProfile.model_validate(state["profile"])
    usage_acc = list(state.get("token_usage") or [])
    used_llm = False
    planned: AnalysisPlan | None = None

    if state.get("use_llm") and llm_configured():
        try:
            text, usage = complete(
                load_prompt("planner.md"),
                prof.model_dump_json(),
                json_mode=True,
            )
            usage_acc.append(usage)
            planned = AnalysisPlan.model_validate(parse_json_object(text))
            used_llm = True
        except Exception as exc:
            emit(f"Planner LLM falhou ({exc}); usando plano determinístico")

    if planned is None or not planned.analyses:
        specs = plan_from_profile(prof)
        planned = AnalysisPlan(
            analyses=specs,
            narrative_focus="Qualidade dos dados, concentração e métrica principal",
        )

    return _timed_update(
        state,
        "plan",
        t0,
        plan=planned.model_dump(),
        used_llm=bool(state.get("used_llm")) or used_llm,
        token_usage=usage_acc,
        logs=_log(state, f"plan: {len(planned.analyses)} análises"),
    )


def analyze(state: dict) -> dict:
    t0 = time.perf_counter()
    emit("Executando analises...")
    prof = DataProfile.model_validate(state["profile"])
    planned = AnalysisPlan.model_validate(state["plan"])
    df = pd.read_parquet(state["df_path"])
    plots_dir = Path(state["plots_dir"])
    usage_acc = list(state.get("token_usage") or [])
    used_llm = bool(state.get("used_llm"))
    results: list[AnalysisResult] = []

    for spec in planned.analyses:
        emit(f"  -> {spec.title}")
        result = None
        if state.get("use_llm") and state.get("allow_codegen", True) and llm_configured():
            result, usage, llm_used = _run_generated(spec, state["df_path"], plots_dir, prof)
            usage_acc.extend(usage)
            used_llm = used_llm or llm_used
            if not result.success:
                emit(f"     codegen falhou: {(result.error or '')[:240]}")
                fallback = _run_registry(df, spec, plots_dir, prof)
                if fallback is not None and fallback.success:
                    emit(f"     fallback template: {spec.analysis_type}")
                    result = fallback
        if result is None:
            result = _run_registry(df, spec, plots_dir, prof)
            if result is None:
                result = AnalysisResult(
                    spec_id=spec.id,
                    title=spec.title,
                    analysis_type=spec.analysis_type,
                    success=False,
                    error="sem template e sem LLM para gerar codigo",
                )
        results.append(result)

    return _timed_update(
        state,
        "analyze",
        t0,
        analysis_results=[r.model_dump() for r in results],
        used_llm=used_llm,
        token_usage=usage_acc,
        logs=_log(state, f"analyze: {sum(1 for r in results if r.success)}/{len(results)} ok"),
    )


def _run_registry(df, spec: AnalysisSpec, plots_dir: Path, prof: DataProfile) -> AnalysisResult | None:
    fn = REGISTRY.get(spec.analysis_type)
    if fn is None:
        return None
    try:
        return fn(df, spec, plots_dir, prof)
    except Exception as exc:
        return AnalysisResult(
            spec_id=spec.id,
            title=spec.title,
            analysis_type=spec.analysis_type,
            success=False,
            error=str(exc),
        )


def _run_generated(
    spec: AnalysisSpec,
    df_path: str,
    plots_dir: Path,
    prof: DataProfile,
) -> tuple[AnalysisResult, list[dict], bool]:
    last_error = ""
    usage_acc: list[dict] = []
    system = load_prompt("coder.md")
    cols = [{"name": c.name, "dtype": c.dtype} for c in prof.columns]
    for attempt in range(1, MAX_CODE_RETRIES + 1):
        user = (
            f"Titulo: {spec.title}\nObjetivo: {spec.goal}\n"
            f"analysis_type: {spec.analysis_type}\n"
            f"columns_hint: {spec.columns_hint}\n"
            f"Colunas disponiveis: {json.dumps(cols, ensure_ascii=False)}\n"
            f"Salve PNGs em OUT_DIR.\n"
        )
        if last_error:
            user += f"\nA tentativa anterior falhou:\n{last_error}\nCorrija o codigo.\n"
        try:
            code, usage = complete(system, user, temperature=0.1)
            usage_acc.append(usage)
        except Exception as exc:
            last_error = str(exc)
            continue
        code = _strip_fences(code)
        if not code.strip():
            last_error = "modelo devolveu codigo vazio"
            continue
        exec_result = execute_code(code, df_path, plots_dir)
        if exec_result.ok:
            return (
                AnalysisResult(
                    spec_id=spec.id,
                    title=spec.title,
                    analysis_type=spec.analysis_type,
                    success=True,
                    attempts=attempt,
                    stdout=exec_result.stdout,
                    artifacts=exec_result.artifacts,
                    metrics=exec_result.metrics,
                    used_llm_code=True,
                ),
                usage_acc,
                True,
            )
        last_error = exec_result.stderr or "erro desconhecido"
    return (
        AnalysisResult(
            spec_id=spec.id,
            title=spec.title,
            analysis_type=spec.analysis_type,
            success=False,
            attempts=MAX_CODE_RETRIES,
            error=last_error,
            used_llm_code=True,
        ),
        usage_acc,
        True,
    )


def _strip_fences(code: str) -> str:
    code = re.sub(r"<think>.*?</think>", "", code, flags=re.S | re.I).strip()
    if "```" not in code:
        return code
    chunks = code.split("```")
    picked = ""
    for i, chunk in enumerate(chunks):
        if i % 2 == 0:
            continue
        body = chunk
        if body.startswith("python"):
            body = body.split("\n", 1)[-1] if "\n" in body else ""
        elif body.startswith("py"):
            body = body.split("\n", 1)[-1] if "\n" in body else ""
        picked = body.strip()
        if picked.startswith("python"):
            continue
        if "plt" in picked or "df" in picked:
            return picked
    return picked or code


def write(state: dict) -> dict:
    t0 = time.perf_counter()
    emit("Escrevendo insights...")
    prof = DataProfile.model_validate(state["profile"])
    planned = AnalysisPlan.model_validate(state["plan"])
    results = [AnalysisResult.model_validate(r) for r in state.get("analysis_results") or []]
    usage_acc = list(state.get("token_usage") or [])
    used_llm = bool(state.get("used_llm"))
    insights = _fallback_insights(prof, planned, results)

    if state.get("use_llm") and llm_configured():
        payload = {
            "profile": {
                "n_rows": prof.n_rows,
                "n_cols": prof.n_cols,
                "notes": prof.notes,
                "numeric_summary": prof.numeric_summary,
            },
            "focus": planned.narrative_focus,
            "results": [
                {
                    "title": r.title,
                    "success": r.success,
                    "metrics": r.metrics,
                    "error": r.error,
                }
                for r in results
            ],
        }
        try:
            text, usage = complete(
                load_prompt("writer.md"),
                json.dumps(payload, ensure_ascii=False),
            )
            usage_acc.append(usage)
            insights = text.strip()
            used_llm = True
        except Exception as exc:
            emit(f"Writer LLM falhou ({exc}); usando narrativa determinística")

    return _timed_update(
        state,
        "write",
        t0,
        insights_md=insights,
        used_llm=used_llm,
        token_usage=usage_acc,
    )


def compile_report(state: dict) -> dict:
    t0 = time.perf_counter()
    emit("Compilando Markdown e PDF...")
    prof = DataProfile.model_validate(state["profile"])
    planned = AnalysisPlan.model_validate(state["plan"])
    results = [AnalysisResult.model_validate(r) for r in state.get("analysis_results") or []]
    timings = dict(state.get("timings") or {})
    # total parcial antes desta etapa; o workflow acrescenta o total final
    agent_so_far = sum(v for k, v in timings.items() if k != "total")
    economy = compute_economy(state.get("manual_minutes") or 210.0, agent_so_far)
    cleaning = None
    if state.get("cleaning_log"):
        cleaning = CleaningLog.model_validate(state["cleaning_log"])
    md = build_markdown(
        source_name=state.get("source_name") or Path(state["source_path"]).name,
        profile=prof,
        plan=planned,
        results=results,
        timings=timings,
        economy=economy,
        used_llm=bool(state.get("used_llm")),
        insights_md=state.get("insights_md") or "",
        cleaning_log=cleaning,
        token_usage=list(state.get("token_usage") or []),
    )
    run_dir = Path(state["run_dir"])
    md_path = write_markdown(md, run_dir / "report.md")
    pdf_path = write_pdf(md, run_dir / "report.pdf", image_base=run_dir)
    return _timed_update(
        state,
        "compile",
        t0,
        report_md=md,
        report_md_path=str(md_path),
        report_pdf_path=str(pdf_path),
    )


def _fallback_insights(profile: DataProfile, plan: AnalysisPlan, results: list[AnalysisResult]) -> str:
    bullets: list[str] = []
    bullets.append(
        f"O dataset tem **{profile.n_rows}** linhas e **{profile.n_cols}** colunas, "
        f"perfiladas por código (sem números inventados)."
    )
    high_null = [c for c in profile.columns if c.null_pct >= 10]
    if high_null:
        desc = ", ".join(f"{c.name} ({c.null_pct:.1f}%)" for c in high_null)
        bullets.append(f"Colunas com ≥10% de nulos: {desc}.")
    for result in results:
        if not result.success or not result.metrics:
            continue
        m = result.metrics
        if result.analysis_type == "categorical_top" and "top1_share_pct" in m:
            top_name = next(iter(m.get("top", {})), "?")
            bullets.append(
                f"Em **{m.get('column')}**, a categoria mais frequente é **{top_name}** "
                f"({m['top1_share_pct']}% das linhas)."
            )
        elif result.analysis_type == "numeric_distribution":
            bullets.append(
                f"**{m.get('column')}**: média {m.get('mean')}, mediana {m.get('median')}, "
                f"P90 {m.get('p90')} (n={m.get('n')})."
            )
        elif result.analysis_type == "timeseries":
            bullets.append(
                f"Série de **{m.get('value_col')}**: pico em {m.get('peak_day')} "
                f"(valor {m.get('peak_value')}); média diária {m.get('mean_per_day')}."
            )
        elif result.analysis_type == "numeric_by_category":
            groups = m.get("groups") or {}
            if groups:
                top = next(iter(groups))
                info = groups[top]
                bullets.append(
                    f"Maior soma de **{m.get('numeric')}** em **{top}** "
                    f"(n={info.get('count')}, soma={info.get('sum')})."
                )
        elif result.analysis_type == "correlation":
            pairs = m.get("top_pairs") or []
            if pairs:
                p = pairs[0]
                bullets.append(f"Maior |correlação|: {p['a']} vs {p['b']} (r={p['r']}).")
        elif result.analysis_type == "missingness":
            bullets.append(
                f"{m.get('cols_with_nulls')} coluna(s) têm algum nulo."
            )
    failed = [r.title for r in results if not r.success]
    if failed:
        bullets.append("Análises que não rodaram: " + "; ".join(failed) + ".")
    recs = [
        "Priorize limpeza nas colunas com mais nulos antes de modelagem.",
        "Use os recortes por categoria para decidir onde investigar outliers.",
    ]
    lines = ["## Insights", ""] + [f"- {b}" for b in bullets]
    lines += ["", "## Recomendações", ""] + [f"- {r}" for r in recs]
    if plan.narrative_focus:
        lines += ["", f"_Foco: {plan.narrative_focus}_"]
    return "\n".join(lines)
