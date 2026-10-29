from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from graph.nodes import analyze, clean, compile_report, ingest, plan, profile, write
from graph.state import PipelineState
from tools.progress import reset_progress, set_progress
from tools.timing import DEFAULT_MANUAL_MINUTES, compute_economy

log = logging.getLogger("data_agent")


def _route_after_profile(state: PipelineState) -> str:
    prof = state.get("profile") or {}
    if int(prof.get("n_rows") or 0) == 0:
        return "write"
    return "plan"


def build_graph():
    g = StateGraph(PipelineState)
    g.add_node("ingest", ingest)
    g.add_node("clean", clean)
    g.add_node("profile", profile)
    g.add_node("plan", plan)
    g.add_node("analyze", analyze)
    g.add_node("write", write)
    g.add_node("compile", compile_report)
    g.add_edge(START, "ingest")
    g.add_edge("ingest", "clean")
    g.add_edge("clean", "profile")
    g.add_conditional_edges(
        "profile",
        _route_after_profile,
        {"plan": "plan", "write": "write"},
    )
    g.add_edge("plan", "analyze")
    g.add_edge("analyze", "write")
    g.add_edge("write", "compile")
    g.add_edge("compile", END)
    return g.compile()


_APP = None


def get_app():
    global _APP
    if _APP is None:
        _APP = build_graph()
    return _APP


def run_pipeline(
    source_path: str | Path,
    output_dir: str | Path = "outputs/reports",
    *,
    sql: str | None = None,
    use_llm: bool = True,
    allow_codegen: bool = True,
    manual_minutes: float = DEFAULT_MANUAL_MINUTES,
    progress: Callable[[str], None] | None = None,
    run_id: str | None = None,
) -> dict:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    token = set_progress(progress)
    t0 = time.perf_counter()
    run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(output_dir) / run_id
    initial: PipelineState = {
        "source_path": str(Path(source_path)),
        "sql": sql,
        "output_dir": str(run_dir),
        "use_llm": use_llm,
        "allow_codegen": allow_codegen,
        "manual_minutes": manual_minutes,
        "timings": {},
        "started_at": t0,
        "logs": [],
        "errors": [],
        "token_usage": [],
        "used_llm": False,
    }
    try:
        final = get_app().invoke(initial)
    finally:
        reset_progress(token)

    timings = dict(final.get("timings") or {})
    if "total" not in timings:
        timings["total"] = time.perf_counter() - t0
    final["timings"] = timings
    if "economy" not in final:
        final["economy"] = compute_economy(manual_minutes, timings["total"]).as_dict()
    return dict(final)
