from pathlib import Path

from tools.cleaner import clean_dataframe
from tools.data_loader import load_source

DIRTY = Path(__file__).parent / "fixtures" / "dirty.csv"


def test_clean_strips_null_tokens_and_drops_empty_column():
    df = load_source(DIRTY)
    cleaned, log = clean_dataframe(df)
    assert "empty_col" not in cleaned.columns
    assert log.n_rows_out == log.n_rows_in == 5
    assert log.n_cols_out == log.n_cols_in - 1
    cities = cleaned["city"].to_list()
    assert "São Paulo" in cities
    assert None in cities
    assert "NA" not in [c for c in cities if c]
    assert "Rio de Janeiro" in cities
    statuses = cleaned["status"].to_list()
    assert None in statuses
    assert all(s is None or s == s.strip() for s in statuses)
    assert any(a.action == "drop_empty_columns" for a in log.actions)
    assert any(a.action == "null_fill" and a.column == "city" for a in log.actions)
