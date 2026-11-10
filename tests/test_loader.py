from pathlib import Path

import pytest

from tools.data_loader import load_source, validate_user_sql

FIXTURE = Path(__file__).parent / "fixtures" / "tiny.csv"


def test_load_csv():
    df = load_source(FIXTURE)
    assert df.shape[0] == 10
    assert "city" in df.columns


def test_load_with_duckdb_sql():
    df = load_source(FIXTURE, sql="SELECT city, COUNT(*) AS n FROM source GROUP BY city ORDER BY n DESC")
    assert "city" in df.columns
    assert "n" in df.columns
    assert df.shape[0] >= 3


def test_sql_allows_select_from_source():
    assert validate_user_sql("SELECT * FROM source WHERE status = 'delivered';").startswith("SELECT")


def test_sql_rejects_copy_and_read_csv():
    with pytest.raises(ValueError):
        validate_user_sql("COPY source TO 'out.csv'")
    with pytest.raises(ValueError):
        validate_user_sql("SELECT * FROM read_csv_auto('C:/secret.csv')")
    with pytest.raises(ValueError):
        validate_user_sql("SELECT * FROM 'other.csv'")
    with pytest.raises(ValueError):
        validate_user_sql("SELECT 1; SELECT 2")


def test_load_excel(tmp_path: Path):
    # Polars lê Excel via fastexcel; sem ele no requirements o upload .xlsx quebrava no deploy.
    import openpyxl

    wb = openpyxl.Workbook()
    wb.active.append(["city", "n"])
    wb.active.append(["Recife", 3])
    path = tmp_path / "t.xlsx"
    wb.save(path)
    df = load_source(path)
    assert df.columns == ["city", "n"]
    assert df.shape == (1, 2)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT content FROM read_text('README.md')",
        "SELECT * FROM read_csv('tests/fixtures/dirty.csv')",
        "SELECT * FROM 'tests/fixtures/dirty.csv'",
    ],
)
def test_sql_cannot_read_server_files(sql):
    # O app é público: o SQL do visitante não pode ler arquivos do servidor.
    with pytest.raises(Exception):
        load_source(FIXTURE, sql=sql)


def test_sql_cannot_read_files_even_if_regex_misses(monkeypatch):
    # Mesmo que o filtro por regex deixe passar, o DuckDB recusa o acesso.
    import tools.data_loader as dl

    monkeypatch.setattr(dl, "validate_user_sql", lambda s: s)
    with pytest.raises(Exception, match="(?i)external|disabled|permission"):
        load_source(FIXTURE, sql="SELECT content FROM read_text('README.md')")


def test_sql_on_excel(tmp_path: Path):
    import openpyxl

    wb = openpyxl.Workbook()
    wb.active.append(["city", "n"])
    wb.active.append(["Recife", 3])
    wb.active.append(["Natal", 5])
    path = tmp_path / "t.xlsx"
    wb.save(path)
    df = load_source(path, sql="SELECT city FROM source WHERE n > 4")
    assert df["city"].to_list() == ["Natal"]
