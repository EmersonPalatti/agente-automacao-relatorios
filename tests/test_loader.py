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
