from __future__ import annotations

from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    source_path: str
    source_name: str
    sql: str | None
    output_dir: str
    run_dir: str
    plots_dir: str
    df_path: str
    use_llm: bool
    manual_minutes: float
    profile: dict[str, Any]
    cleaning_log: dict[str, Any]
    plan: dict[str, Any]
    analysis_results: list[dict[str, Any]]
    insights_md: str
    report_md: str
    report_md_path: str
    report_pdf_path: str
    timings: dict[str, float]
    logs: list[str]
    errors: list[str]
    token_usage: list[dict[str, Any]]
    used_llm: bool
