from __future__ import annotations

from pathlib import Path

import streamlit as st

from tools.timing import DEFAULT_MANUAL_MINUTES, format_duration

SAMPLE = Path("data/raw/pedidos_ifood.csv")
UPLOADS = Path("data/processed/uploads")

st.set_page_config(page_title="Agente de Relatórios", page_icon="📊", layout="wide")
st.title("Agente de automação de relatórios")
st.caption("Ingestão → perfil factual → análises → Markdown + PDF. O diferencial é medir o tempo.")

with st.sidebar:
    st.subheader("Entrada")
    uploaded = st.file_uploader("CSV, Excel ou Parquet", type=["csv", "xlsx", "xls", "parquet"])
    use_sample = st.checkbox("Usar dataset de exemplo (pedidos)", value=not bool(uploaded), disabled=bool(uploaded))
    sql = st.text_area(
        "SQL DuckDB (opcional)",
        placeholder="SELECT * FROM source WHERE status = 'delivered'",
        help="A tabela `source` aponta para o arquivo carregado.",
    )
    st.subheader("Execução")
    use_llm = st.toggle("Usar LLM (se houver chave no ambiente)", value=False)
    manual_minutes = st.number_input(
        "Tempo manual estimado (min)",
        min_value=15.0,
        max_value=24 * 60.0,
        value=float(DEFAULT_MANUAL_MINUTES),
        step=15.0,
    )
    run = st.button("Gerar relatório", type="primary", use_container_width=True)

source_path: Path | None = None
if uploaded is not None:
    UPLOADS.mkdir(parents=True, exist_ok=True)
    source_path = UPLOADS / uploaded.name
    source_path.write_bytes(uploaded.getbuffer())
elif use_sample and SAMPLE.exists():
    source_path = SAMPLE

if source_path is None:
    st.info("Envie um arquivo ou gere o exemplo com `python cli.py sample`.")
    st.stop()

st.write(f"Arquivo: `{source_path}`")

if run:
    from graph.workflow import run_pipeline

    status = st.status("Rodando pipeline…", expanded=True)

    def _progress(msg: str) -> None:
        status.write(msg)

    with st.spinner("Analisando dados reais (sem inventar números)…"):
        result = run_pipeline(
            source_path,
            "outputs/reports",
            sql=sql.strip() or None,
            use_llm=use_llm,
            manual_minutes=float(manual_minutes),
            progress=_progress,
        )
    status.update(label="Concluído", state="complete")
    st.session_state["last_result"] = result

result = st.session_state.get("last_result")
if not result:
    st.stop()

eco = result["economy"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tempo do agente", format_duration(eco["agent_seconds"]))
c2.metric("Tempo manual est.", format_duration(eco["manual_seconds"]))
c3.metric("Redução", f"{eco['reduction_pct']:.2f}%")
c4.metric("LLM", "sim" if result.get("used_llm") else "não")

st.subheader("Tempos por etapa")
timings = {k: v for k, v in (result.get("timings") or {}).items() if k != "total"}
if timings:
    import plotly.express as px

    fig = px.bar(
        x=list(timings.keys()),
        y=list(timings.values()),
        labels={"x": "etapa", "y": "segundos"},
        color_discrete_sequence=["#1d3557"],
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280)
    st.plotly_chart(fig, use_container_width=True)

md_path = result.get("report_md_path")
pdf_path = result.get("report_pdf_path")
dl1, dl2 = st.columns(2)
if md_path and Path(md_path).exists():
    dl1.download_button("Baixar Markdown", Path(md_path).read_bytes(), file_name="report.md", mime="text/markdown")
if pdf_path and Path(pdf_path).exists():
    dl2.download_button("Baixar PDF", Path(pdf_path).read_bytes(), file_name="report.pdf", mime="application/pdf")

plots = result.get("analysis_results") or []
images = [a for r in plots for a in r.get("artifacts") or []]
if images:
    st.subheader("Gráficos")
    cols = st.columns(min(2, len(images)))
    for i, img in enumerate(images):
        if Path(img).exists():
            cols[i % 2].image(img, use_container_width=True)

st.subheader("Relatório")
st.markdown(result.get("report_md") or "")
