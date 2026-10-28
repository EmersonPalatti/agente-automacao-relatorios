from pathlib import Path

from tools.data_loader import load_source

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
