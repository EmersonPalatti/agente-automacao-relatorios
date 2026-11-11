from tools.llm import resolve_model


def test_model_without_provider_goes_through_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("LLM_MODEL", "nvidia/nemotron")
    assert resolve_model() == "openrouter/nvidia/nemotron"


def test_anthropic_model_keeps_its_provider(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "y")
    monkeypatch.setenv("LLM_MODEL", "anthropic/claude-haiku-5-5")
    assert resolve_model() == "anthropic/claude-haiku-5-5"


def test_no_openrouter_key_leaves_model_alone(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("LLM_MODEL", "nvidia/nemotron")
    assert resolve_model() == "nvidia/nemotron"
