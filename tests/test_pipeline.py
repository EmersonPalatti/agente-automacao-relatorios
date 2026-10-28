from pathlib import Path

from graph.workflow import run_pipeline
from tools.analyses import plan_from_profile
from tools.data_loader import load_source
from tools.profiler import profile_dataframe

FIXTURE = Path(__file__).parent / "fixtures" / "tiny.csv"


def test_fallback_plan_is_data_agnostic():
    profile = profile_dataframe(load_source(FIXTURE))
    specs = plan_from_profile(profile)
    assert 3 <= len(specs) <= 5
    types = {s.analysis_type for s in specs}
    assert "missingness" in types
    for spec in specs:
        for col in spec.columns_hint:
            assert col in [c.name for c in profile.columns]


def test_full_pipeline_without_llm(tmp_path: Path):
    result = run_pipeline(
        FIXTURE,
        tmp_path / "out",
        use_llm=False,
        manual_minutes=210,
        run_id="test",
    )
    assert Path(result["report_md_path"]).exists()
    assert Path(result["report_pdf_path"]).exists()
    md = result["report_md"]
    assert "Tempo manual estimado vs tempo do agente" in md
    assert "**10**" in md or "10" in md
    assert "São Paulo" in md or "city" in md
    assert result["economy"]["reduction_pct"] > 90
    assert "total" in result["timings"]
    for step in ("ingest", "profile", "plan", "analyze", "write", "compile"):
        assert step in result["timings"]
    successes = [r for r in result["analysis_results"] if r["success"]]
    assert successes, "pelo menos uma análise precisa ter rodado"
    assert any(r.get("artifacts") for r in successes)
