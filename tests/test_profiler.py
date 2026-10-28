from datetime import datetime
from pathlib import Path

import polars as pl

from tools.data_loader import load_source
from tools.profiler import profile_dataframe

FIXTURE = Path(__file__).parent / "fixtures" / "tiny.csv"


def test_profile_is_factual():
    df = load_source(FIXTURE)
    profile = profile_dataframe(df)
    assert profile.n_rows == 10
    assert profile.n_cols == 6
    names = [c.name for c in profile.columns]
    assert names == list(df.columns)
    rating = next(c for c in profile.columns if c.name == "rating")
    assert rating.null_count == 3
    city = next(c for c in profile.columns if c.name == "city")
    assert city.is_categorical
    oid = next(c for c in profile.columns if c.name == "order_id")
    assert oid.is_likely_id
    assert "order_value" in profile.numeric_summary
    mean = profile.numeric_summary["order_value"]["mean"]
    assert mean is not None
    assert abs(mean - float(df["order_value"].mean())) < 1e-6


def test_unique_datetime_is_not_id():
    df = pl.DataFrame(
        {
            "event_at": [datetime(2026, 1, 1, i) for i in range(10)],
            "value": list(range(10)),
        }
    )
    profile = profile_dataframe(df)
    ts = next(c for c in profile.columns if c.name == "event_at")
    assert ts.is_datetime
    assert not ts.is_likely_id
    assert ts.dtype == "Datetime"
