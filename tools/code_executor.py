from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

_UNSAFE = [
    r"(?m)^\s*import\s+subprocess\b",
    r"(?m)^\s*from\s+subprocess\b",
    r"\bos\.system\s*\(",
    r"\bos\.popen\s*\(",
    r"\bshutil\.rmtree\s*\(",
    r"(?m)^\s*import\s+socket\b",
    r"(?m)^\s*from\s+socket\b",
    r"(?m)^\s*import\s+requests\b",
    r"(?m)^\s*from\s+requests\b",
    r"(?m)^\s*import\s+http\.client\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__\s*\(",
]

WRAPPER = """\
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

df = pd.read_parquet(r"__DATA_PATH__")
OUT_DIR = Path(r"__OUT_DIR__")
OUT_DIR.mkdir(parents=True, exist_ok=True)

__CODE__
"""


@dataclass
class ExecutionResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    artifacts: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


def looks_unsafe(code: str) -> str | None:
    for pat in _UNSAFE:
        if re.search(pat, code):
            return f"codigo bloqueado: {pat}"
    return None


def extract_metrics(stdout: str) -> dict:
    for line in stdout.splitlines():
        if line.startswith("RESULTS_JSON:"):
            raw = line[len("RESULTS_JSON:") :].strip()
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {"value": parsed}
    return {}


def list_pngs(out_dir: Path) -> list[str]:
    if not out_dir.exists():
        return []
    return sorted(str(p) for p in out_dir.glob("*.png"))


def execute_code(
    code: str,
    data_path: str | Path,
    out_dir: str | Path,
    timeout: int = 90,
) -> ExecutionResult:
    unsafe = looks_unsafe(code)
    if unsafe:
        return ExecutionResult(ok=False, stderr=unsafe)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    before = set(list_pngs(out_dir))
    script_path = out_dir / "_run.py"
    script = (
        WRAPPER.replace("__DATA_PATH__", str(Path(data_path).resolve()))
        .replace("__OUT_DIR__", str(out_dir.resolve()))
        .replace("__CODE__", textwrap.dedent(code).strip())
    )
    script_path.write_text(script, encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"}
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(out_dir),
            env=env,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(ok=False, stderr=f"timeout após {timeout}s")

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    after = set(list_pngs(out_dir))
    artifacts = sorted(after - before)
    ok = proc.returncode == 0
    return ExecutionResult(
        ok=ok,
        stdout=stdout,
        stderr=stderr if not ok else "",
        artifacts=artifacts,
        metrics=extract_metrics(stdout) if ok else {},
    )
