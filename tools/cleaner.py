from __future__ import annotations

import polars as pl

from tools.models import CleaningAction, CleaningLog

NULL_TOKENS = ("", "na", "n/a", "null", "none", "-", "nan", "nat", "?")


def clean_dataframe(df: pl.DataFrame) -> tuple[pl.DataFrame, CleaningLog]:
    """Limpeza leve e data-agnostic. Não imputa e não apaga linhas."""
    n_rows_in, n_cols_in = df.shape
    actions: list[CleaningAction] = []
    if df.is_empty():
        return df, CleaningLog(
            n_rows_in=n_rows_in,
            n_cols_in=n_cols_in,
            n_rows_out=n_rows_in,
            n_cols_out=n_cols_in,
        )

    str_cols = [c for c in df.columns if _is_string(df[c].dtype)]
    if str_cols:
        null_before = {c: int(df[c].null_count()) for c in str_cols}
        exprs = [_clean_string_expr(c) for c in str_cols]
        df = df.with_columns(exprs)
        actions.append(
            CleaningAction(
                action="strip_and_null_tokens",
                detail="strip em texto; vazios e tokens tipo NA/n/a/- viram nulo",
                count=len(str_cols),
            )
        )
        for col in str_cols:
            extra = int(df[col].null_count()) - null_before[col]
            if extra > 0:
                actions.append(
                    CleaningAction(
                        action="null_fill",
                        column=col,
                        detail=f"{extra} valor(es) viraram nulo",
                        count=extra,
                    )
                )

    drop = [c for c in df.columns if df.height and df[c].null_count() == df.height]
    if drop and len(drop) < len(df.columns):
        df = df.drop(drop)
        actions.append(
            CleaningAction(
                action="drop_empty_columns",
                detail=", ".join(drop),
                count=len(drop),
            )
        )

    return df, CleaningLog(
        n_rows_in=n_rows_in,
        n_cols_in=n_cols_in,
        n_rows_out=df.height,
        n_cols_out=df.width,
        actions=actions,
    )


def _is_string(dtype) -> bool:
    return dtype == pl.String or str(dtype) in {"String", "Utf8"}


def _clean_string_expr(col: str) -> pl.Expr:
    stripped = pl.col(col).str.strip_chars()
    is_token = stripped.str.to_lowercase().is_in(list(NULL_TOKENS))
    return (
        pl.when(stripped.is_null() | (stripped == "") | is_token)
        .then(None)
        .otherwise(stripped)
        .alias(col)
    )
