from tools.timing import compute_economy, format_duration


def test_economy_example():
    eco = compute_economy(manual_minutes=210, agent_seconds=12.5)
    assert eco.manual_seconds == 210 * 60
    assert eco.saved_seconds == eco.manual_seconds - 12.5
    assert 99.0 < eco.reduction_pct < 100.0


def test_format_duration():
    assert format_duration(12.5).endswith("s")
    assert "min" in format_duration(125)
