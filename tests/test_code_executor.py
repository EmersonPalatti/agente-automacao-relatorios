from pathlib import Path

import polars as pl

from tools.code_executor import execute_code, looks_unsafe
from tools.data_loader import save_parquet


def test_blocks_unsafe_code():
    assert looks_unsafe("import subprocess\nsubprocess.call('ls')")


def test_executes_and_saves_plot(tmp_path: Path):
    df_path = tmp_path / "df.parquet"
    save_parquet(pl.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}), df_path)
    code = """
print('RESULTS_JSON: {"n": %s}' % len(df))
fig, ax = plt.subplots()
ax.plot(df["x"], df["y"])
fig.savefig(OUT_DIR / "line.png")
plt.close(fig)
"""
    result = execute_code(code, df_path, tmp_path / "plots")
    assert result.ok, result.stderr
    assert result.metrics.get("n") == 3
    assert any(p.endswith("line.png") for p in result.artifacts)
