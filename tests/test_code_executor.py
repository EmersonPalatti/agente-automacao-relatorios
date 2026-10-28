from pathlib import Path

import polars as pl

from tools.code_executor import child_env, execute_code, looks_unsafe
from tools.data_loader import save_parquet


def test_blocks_unsafe_code():
    assert looks_unsafe("import subprocess\nsubprocess.call('ls')")
    assert looks_unsafe("import os\nprint(os.environ)")
    assert looks_unsafe("from pathlib import Path\nPath.home()")
    assert looks_unsafe("open('x.txt')")
    assert looks_unsafe("eval('1')")


def test_allows_word_requests_in_comments():
    assert looks_unsafe("# this requests a histogram\nax.plot([1, 2])") is None


def test_allows_pandas_and_json_imports():
    assert looks_unsafe("import json\nprint(json.dumps({'a': 1}))") is None
    assert looks_unsafe("import pandas as pd\nprint(len(pd.Series([1])))") is None


def test_child_env_has_no_secrets(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "should-not-leak")
    monkeypatch.setenv("OPENAI_API_KEY", "should-not-leak")
    env = child_env(tmp_path)
    assert "OPENROUTER_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert env.get("MPLBACKEND") == "Agg"


def test_executes_and_saves_plot(tmp_path: Path):
    df_path = tmp_path / "df.parquet"
    save_parquet(pl.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}), df_path)
    code = """
print('RESULTS_JSON: {"n": %s}' % len(df))
fig, ax = plt.subplots()
ax.plot(df["x"], df["y"])
fig.savefig(f"{OUT_DIR}/line.png")
plt.close(fig)
"""
    result = execute_code(code, df_path, tmp_path / "plots")
    assert result.ok, result.stderr
    assert result.metrics.get("n") == 3
    assert any(p.endswith("line.png") for p in result.artifacts)


def test_generated_child_does_not_see_api_key(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "should-not-leak")
    df_path = tmp_path / "df.parquet"
    save_parquet(pl.DataFrame({"x": [1]}), df_path)
    # import os is blocked before the process starts
    blocked = execute_code("import os\nprint(os.environ)", df_path, tmp_path / "plots")
    assert not blocked.ok
    assert "bloqueado" in (blocked.stderr or "")
