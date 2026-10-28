from __future__ import annotations

from datetime import date, datetime

import polars as pl

from tools.models import ColumnProfile, DataProfile

_NUMERIC = [
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.UInt8,
    pl.UInt16,
    pl.UInt32,
    pl.UInt64,
    pl.Float32,
    pl.Float64,
]
if hasattr(pl, "Decimal"):
    _NUMERIC.append(pl.Decimal)
_NUMERIC = tuple(_NUMERIC)
_DATETIME = (pl.Date, pl.Datetime, pl.Time)


def profile_dataframe(df: pl.DataFrame) -> DataProfile:
    n_rows, n_cols = df.shape
    columns: list[ColumnProfile] = []
    numeric_summary: dict[str, dict[str, float | None]] = {}
    notes: list[str] = []

    for name in df.columns:
        s = df[name]
        dtype_name = _dtype_label(s.dtype)
        null_count = int(s.null_count())
        null_pct = (null_count / n_rows * 100.0) if n_rows else 0.0
        n_unique = int(s.n_unique())
        n_unique_pct = (n_unique / n_rows * 100.0) if n_rows else 0.0
        is_numeric = s.dtype in _NUMERIC
        is_datetime = s.dtype in _DATETIME
        is_likely_id = (not is_datetime) and _is_likely_id(name, n_unique, n_rows)
        is_categorical = (
            not is_numeric
            and not is_datetime
            and not is_likely_id
            and 1 < n_unique <= 50
            and n_unique < n_rows
        )
        columns.append(
            ColumnProfile(
                name=name,
                dtype=dtype_name,
                null_count=null_count,
                null_pct=round(null_pct, 2),
                n_unique=n_unique,
                n_unique_pct=round(n_unique_pct, 2),
                sample_values=_samples(s),
                is_likely_id=is_likely_id,
                is_numeric=is_numeric,
                is_datetime=is_datetime,
                is_categorical=is_categorical,
            )
        )
        if is_numeric:
            numeric_summary[name] = _numeric_stats(s)
        if null_pct >= 20:
            notes.append(f"{name}: {null_pct:.1f}% nulos")
        if is_likely_id:
            notes.append(f"{name}: parece identificador (não usar em agregações)")

    if n_rows == 0:
        notes.append("DataFrame vazio")

    return DataProfile(
        n_rows=n_rows,
        n_cols=n_cols,
        columns=columns,
        numeric_summary=numeric_summary,
        notes=notes,
    )


def _dtype_label(dtype) -> str:
    text = str(dtype)
    if text.startswith("Datetime"):
        return "Datetime"
    return text


def _is_likely_id(name: str, n_unique: int, n_rows: int) -> bool:
    lowered = name.lower()
    if lowered in {"id", "uuid", "pk"} or lowered.endswith("_id"):
        return True
    if n_rows >= 10 and n_unique == n_rows:
        return True
    return False


def _samples(s: pl.Series, n: int = 5) -> list[str]:
    values = s.drop_nulls().head(n).to_list()
    out: list[str] = []
    for v in values:
        if isinstance(v, datetime):
            out.append(v.isoformat(sep=" ", timespec="seconds"))
        elif isinstance(v, date):
            out.append(v.isoformat())
        else:
            out.append(str(v))
    return out


def _numeric_stats(s: pl.Series) -> dict[str, float | None]:
    def _f(v) -> float | None:
        return None if v is None else float(v)

    return {
        "min": _f(s.min()),
        "max": _f(s.max()),
        "mean": _f(s.mean()),
        "median": _f(s.median()),
        "std": _f(s.std()),
    }
