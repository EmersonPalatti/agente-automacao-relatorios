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
    for step in ("ingest", "clean", "profile", "plan", "analyze", "write", "compile"):
        assert step in result["timings"]
    assert "Limpeza aplicada" in md
    successes = [r for r in result["analysis_results"] if r["success"]]
    assert successes, "pelo menos uma análise precisa ter rodado"
    assert any(r.get("artifacts") for r in successes)


def test_pipeline_marks_generated_code(tmp_path: Path, monkeypatch):
    good_code = """
print('RESULTS_JSON: {"n": %s}' % len(df))
fig, ax = plt.subplots()
ax.plot([1, 2, 3])
fig.savefig(f"{OUT_DIR}/gen.png")
plt.close(fig)
"""
    usage = {
        "prompt_tokens": 1,
        "completion_tokens": 1,
        "total_tokens": 2,
        "cost_usd": 0.0,
        "model": "mock",
    }

    def fake_complete(system, user, json_mode=False, temperature=0.2):
        if json_mode or "analysis_type" in system:
            return (
                '{"narrative_focus": "teste", "analyses": [{"id": "a1", "title": "plot gerado",'
                ' "goal": "n", "analysis_type": "custom", "columns_hint": []}]}',
                usage,
            )
        if "OUT_DIR" in system:
            return good_code, usage
        return "## Insights\n\n- mock com numero 10", usage

    monkeypatch.setattr("graph.nodes.complete", fake_complete)
    monkeypatch.setattr("graph.nodes.llm_configured", lambda: True)

    result = run_pipeline(
        FIXTURE,
        tmp_path / "out",
        use_llm=True,
        allow_codegen=True,
        manual_minutes=210,
        run_id="gen",
    )
    generated = [r for r in result["analysis_results"] if r.get("used_llm_code")]
    assert generated, result["analysis_results"]
    assert generated[0]["success"]
    assert any(str(p).endswith("gen.png") for p in generated[0]["artifacts"])
    assert "codigo gerado" in result["report_md"]


def test_empty_dataset_routes_directly_to_write(tmp_path: Path):
    result = run_pipeline(
        FIXTURE,
        tmp_path / "out",
        sql="SELECT * FROM source WHERE 1 = 0",
        use_llm=False,
        run_id="empty",
    )
    assert result["profile"]["n_rows"] == 0
    assert "plan" not in result["timings"]
    assert "analyze" not in result["timings"]
    assert "write" in result["timings"]
    assert "compile" in result["timings"]
    assert Path(result["report_md_path"]).exists()
    assert Path(result["report_pdf_path"]).exists()
