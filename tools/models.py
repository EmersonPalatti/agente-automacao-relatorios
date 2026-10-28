from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AnalysisType = Literal[
    "missingness",
    "categorical_top",
    "numeric_distribution",
    "timeseries",
    "numeric_by_category",
    "correlation",
    "custom",
]


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_count: int
    null_pct: float
    n_unique: int
    n_unique_pct: float
    sample_values: list[str] = Field(default_factory=list)
    is_likely_id: bool = False
    is_numeric: bool = False
    is_datetime: bool = False
    is_categorical: bool = False


class DataProfile(BaseModel):
    n_rows: int
    n_cols: int
    columns: list[ColumnProfile]
    numeric_summary: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class AnalysisSpec(BaseModel):
    id: str
    title: str
    goal: str
    analysis_type: AnalysisType = "custom"
    columns_hint: list[str] = Field(default_factory=list)


class AnalysisPlan(BaseModel):
    analyses: list[AnalysisSpec]
    narrative_focus: str = ""


class AnalysisResult(BaseModel):
    spec_id: str
    title: str
    analysis_type: str
    success: bool
    attempts: int = 1
    stdout: str = ""
    error: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    used_llm_code: bool = False
