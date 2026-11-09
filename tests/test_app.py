from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.chdir(ROOT)
    for var in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.run()
    return at


def test_report_images_are_rendered_not_linked(app):
    app.button[0].click().run()
    assert not app.exception
    # Nenhum ![..](caminho-do-servidor) deve chegar ao st.markdown.
    assert not any("](outputs/" in m.value for m in app.markdown)
    assert len(app.get("image")) == 5


def test_sql_error_shows_message_not_traceback(app):
    app.text_area[0].input("SELECT coluna_inexistente FROM source")
    app.button[0].click().run()
    assert not app.exception
    assert any("Erro no SQL" in e.value for e in app.error)


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("![top_city](outputs/r/plots/top_city.png)", ("top_city", "outputs/r/plots/top_city.png")),
        ("![dist_Valor (R$)](outputs/r/plots/dist_Valor (R$).png)", ("dist_Valor (R$)", "outputs/r/plots/dist_Valor (R$).png")),
        ("  ![a b](C:/x y/a b.png)  ", ("a b", "C:/x y/a b.png")),
        ("texto com ![inline](x.png) no meio", None),
        ("## Título", None),
    ],
)
def test_parse_image_line(line, expected):
    from tools.report_builder import parse_image_line

    assert parse_image_line(line) == expected
