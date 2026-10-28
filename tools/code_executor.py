from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

ALLOWED_IMPORT_ROOTS = {
    "json",
    "math",
    "datetime",
    "collections",
    "statistics",
    "decimal",
    "re",
    "numpy",
    "pandas",
    "matplotlib",
}

FORBIDDEN_NAMES = {
    "eval",
    "exec",
    "open",
    "compile",
    "__import__",
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "vars",
    "breakpoint",
    "input",
    "exit",
    "quit",
    "memoryview",
    "classmethod",
    "staticmethod",
}

FORBIDDEN_ATTRS = {"parent", "parents", "home", "cwd", "root", "absolute", "resolve"}

FORBIDDEN_NAME_ROOTS = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "requests",
    "httpx",
    "urllib",
    "http",
    "shutil",
    "importlib",
    "ctypes",
    "pickle",
    "marshal",
    "pathlib",
    "builtins",
    "posix",
    "nt",
    "winreg",
    "mmap",
    "multiprocessing",
    "threading",
    "signal",
    "inspect",
    "code",
    "codeop",
    "pty",
    "webbrowser",
}

WRAPPER = """\
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import json
from pathlib import Path as _Path

df = pd.read_parquet(r"__DATA_PATH__")
_out = _Path(r"__OUT_DIR__")
_out.mkdir(parents=True, exist_ok=True)
OUT_DIR = str(_out)

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
    try:
        tree = ast.parse(textwrap.dedent(code))
    except SyntaxError as exc:
        return f"codigo invalido: {exc.msg}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root not in ALLOWED_IMPORT_ROOTS:
                    return f"import bloqueado: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".", 1)[0]
            if mod not in ALLOWED_IMPORT_ROOTS:
                return f"import bloqueado: {node.module}"
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return f"nome bloqueado: {node.id}"
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAME_ROOTS:
            return f"nome bloqueado: {node.id}"
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
            return f"atributo bloqueado: .{node.attr}"
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return f"atributo bloqueado: .{node.attr}"
    return None


def child_env(out_dir: Path) -> dict[str, str]:
    """Ambiente minimo para o Python filho — sem chaves, tokens ou perfil do usuario."""
    env: dict[str, str] = {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "MPLBACKEND": "Agg",
        "MPLCONFIGDIR": str(out_dir),
        "TMP": str(out_dir),
        "TEMP": str(out_dir),
        "TMPDIR": str(out_dir),
    }
    python_dir = Path(sys.executable).resolve().parent
    path_bits = [str(python_dir), str(python_dir / "Scripts"), str(python_dir / "DLLs")]
    base = Path(getattr(sys, "base_prefix", sys.prefix))
    path_bits += [str(base), str(base / "Scripts"), str(base / "DLLs")]
    if os.name == "nt":
        systemroot = os.environ.get("SYSTEMROOT", r"C:\Windows")
        env["SYSTEMROOT"] = systemroot
        env["WINDIR"] = os.environ.get("WINDIR", systemroot)
        env["PATHEXT"] = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")
        path_bits += [str(Path(systemroot) / "System32"), systemroot]
    else:
        path_bits += ["/usr/bin", "/bin"]
    env["PATH"] = os.pathsep.join(path_bits)
    return env


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
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(out_dir),
            env=child_env(out_dir),
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
