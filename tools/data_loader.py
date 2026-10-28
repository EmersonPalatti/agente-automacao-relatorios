from __future__ import annotations

import re
from pathlib import Path

import polars as pl

TABLE_NAME = "source"

_FORBIDDEN_SQL = re.compile(
    r"\b(attach|copy|install|unload|load|export|pragma|create|drop|insert|update|delete|"
    r"alter|grant|vacuum|checkpoint|call|execute|reset|"
    r"read_csv(?:_auto)?|read_parquet|read_json(?:_auto)?|read_xlsx|read_blob|"
    r"glob|getenv|which|system|shell|cmd|httpfs|sqlite_scan|postgres_scan)\b",
    re.IGNORECASE,
)


def validate_user_sql(sql: str) -> str:
    """SELECT/WITH de uma instrução, sem funções de arquivo nem DDL/DML."""
    text = sql.strip()
    if not text:
        raise ValueError("SQL vazio")
    core = text.rstrip().rstrip(";")
    if ";" in core:
        raise ValueError("apenas uma instrucao SQL")
    head = core.split(None, 1)[0].upper()
    if head not in {"SELECT", "WITH"}:
        raise ValueError("apenas SELECT ou WITH")
    if _FORBIDDEN_SQL.search(core):
        raise ValueError("SQL contem operacao ou funcao nao permitida")
    if re.search(r"from\s+['\"]", core, re.IGNORECASE):
        raise ValueError("FROM so pode usar a tabela source")
    return core


def load_source(path: str | Path, sql: str | None = None) -> pl.DataFrame:
    """Carrega CSV, Excel, Parquet ou DuckDB. SQL opcional usa a tabela `source`."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")

    suffix = p.suffix.lower()
    if sql and sql.strip():
        return _load_with_sql(p, validate_user_sql(sql), suffix)

    if suffix == ".csv":
        return pl.read_csv(p, try_parse_dates=True, infer_schema_length=5000)
    if suffix in {".xlsx", ".xls"}:
        return pl.read_excel(p)
    if suffix == ".parquet":
        return pl.read_parquet(p)
    if suffix in {".duckdb", ".db"}:
        raise ValueError("Arquivo DuckDB exige uma query SQL (tabelas do arquivo).")
    raise ValueError(f"Formato não suportado: {suffix or '(sem extensão)'}")


def save_parquet(df: pl.DataFrame, dest: str | Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(dest)
    return dest


def _posix(p: Path) -> str:
    return p.resolve().as_posix().replace("'", "''")


def _load_with_sql(path: Path, sql: str, suffix: str) -> pl.DataFrame:
    import duckdb

    if suffix in {".duckdb", ".db"}:
        con = duckdb.connect(str(path), read_only=True)
        try:
            return _query_polars(con, sql)
        finally:
            con.close()

    con = duckdb.connect()
    try:
        file_sql = _posix(path)
        if suffix == ".csv":
            con.execute(
                f"CREATE VIEW {TABLE_NAME} AS SELECT * FROM read_csv_auto('{file_sql}')"
            )
        elif suffix == ".parquet":
            con.execute(
                f"CREATE VIEW {TABLE_NAME} AS SELECT * FROM read_parquet('{file_sql}')"
            )
        elif suffix in {".xlsx", ".xls"}:
            pdf = pl.read_excel(path)
            con.register(TABLE_NAME, pdf.to_pandas())
        else:
            raise ValueError(f"SQL sobre {suffix} não é suportado")
        return _query_polars(con, sql)
    finally:
        con.close()


def _query_polars(con, sql: str) -> pl.DataFrame:
    rel = con.sql(sql)
    if hasattr(rel, "pl"):
        return rel.pl()
    return pl.from_arrow(rel.arrow())
