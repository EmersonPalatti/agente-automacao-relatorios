from __future__ import annotations

from pathlib import Path

import duckdb
import streamlit as st

from tools.llm import llm_configured
from tools.report_builder import parse_image_line
from tools.timing import DEFAULT_MANUAL_MINUTES, format_duration
from tools.uploads import MAX_UPLOAD_BYTES, prune_older_than, safe_upload_path

SAMPLE = Path("data/raw/pedidos_delivery.csv")
UPLOADS = Path("data/processed/uploads")
REPORTS = Path("outputs/reports")
RETENTION_SECONDS = 6 * 3600


def render_report(md: str) -> None:
    """Renderiza o Markdown do relatório trocando ![..](caminho) por st.image.

    O caminho dos gráficos é do disco do servidor; o navegador não consegue
    buscá-lo, então st.markdown mostraria a imagem quebrada.
    """
    buffer: list[str] = []
    for line in md.splitlines():
        image = parse_image_line(line)
        if image is None:
            buffer.append(line)
            continue
        if buffer:
            st.markdown("\n".join(buffer))
            buffer = []
        alt, raw_path = image
        path = Path(raw_path)
        if path.exists():
            st.image(str(path), caption=alt or None, width="stretch")
        else:
            st.caption(f"Gráfico indisponível: {alt or path.name}")
    if buffer:
        st.markdown("\n".join(buffer))


st.set_page_config(page_title="Agente de Relatórios", page_icon="📊", layout="wide")
st.title("Agente de automação de relatórios")
st.caption("Ingestão → limpeza → perfil → análises → Markdown + PDF. O diferencial é medir o tempo.")

with st.sidebar:
    st.subheader("Entrada")
    uploaded = st.file_uploader("CSV, Excel ou Parquet", type=["csv", "xlsx", "xls", "parquet"])
    use_sample = st.checkbox("Usar dataset de exemplo (pedidos)", value=not bool(uploaded), disabled=bool(uploaded))
    sql = st.text_area(
        "SQL DuckDB (opcional, só SELECT/WITH em `source`)",
        placeholder="SELECT * FROM source WHERE status = 'delivered'",
        help="Uma instrução SELECT ou WITH. Sem COPY/ATTACH/read_csv.",
    )
    st.subheader("Execução")
    st.caption(
        "Nesta UI o LLM, se ligado, só planeja e escreve. "
        "Código gerado no sandbox fica na CLI (`python cli.py run`)."
    )
    use_llm = st.toggle("Usar LLM para plano e insights (exige chave)", value=False)
    manual_minutes = st.number_input(
        "Tempo manual estimado (min)",
        min_value=15.0,
        max_value=24 * 60.0,
        value=float(DEFAULT_MANUAL_MINUTES),
        step=15.0,
    )
    run = st.button("Gerar relatório", type="primary", width="stretch")

if run:
    # O disco do app público é compartilhado e não se limpa sozinho.
    for folder in (REPORTS, UPLOADS):
        prune_older_than(folder, RETENTION_SECONDS)

source_path: Path | None = None
if uploaded is not None:
    # O Streamlit reexecuta o script a cada interação: grava o upload uma vez por arquivo.
    cached = st.session_state.get("upload")
    if cached and cached["id"] == uploaded.file_id and Path(cached["path"]).exists():
        source_path = Path(cached["path"])
    else:
        try:
            data = uploaded.getvalue()
            source_path = safe_upload_path(UPLOADS, uploaded.name, len(data))
            source_path.write_bytes(data)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        st.session_state["upload"] = {"id": uploaded.file_id, "path": str(source_path)}
elif use_sample and SAMPLE.exists():
    source_path = SAMPLE

if source_path is None:
    st.info("Envie um arquivo (até "
            f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB) ou gere o exemplo com `python cli.py sample`.")
    st.stop()

st.write(f"Arquivo: `{source_path.name}`")

if run:
    from graph.workflow import run_pipeline

    if use_llm and not llm_configured():
        st.warning("Nenhuma chave de LLM configurada: plano e insights vão usar o modo determinístico.")

    status = st.status("Rodando pipeline…", expanded=True)

    def _progress(msg: str) -> None:
        status.write(msg)

    try:
        with st.spinner("Analisando dados reais (sem inventar números)…"):
            result = run_pipeline(
                source_path,
                REPORTS,
                sql=sql.strip() or None,
                use_llm=use_llm,
                allow_codegen=False,
                manual_minutes=float(manual_minutes),
                progress=_progress,
            )
    except ValueError as exc:
        status.update(label="Falhou", state="error")
        st.error(str(exc))
        st.stop()
    except duckdb.Error as exc:
        # SQL válido para o filtro, mas que o DuckDB rejeita (coluna inexistente, sintaxe).
        status.update(label="Falhou", state="error")
        st.error(f"Erro no SQL: {str(exc).splitlines()[0]}")
        st.stop()
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
    st.plotly_chart(fig, width="stretch")

md_path = result.get("report_md_path")
pdf_path = result.get("report_pdf_path")
dl1, dl2 = st.columns(2)
if md_path and Path(md_path).exists():
    dl1.download_button("Baixar Markdown", Path(md_path).read_bytes(), file_name="report.md", mime="text/markdown")
if pdf_path and Path(pdf_path).exists():
    dl2.download_button("Baixar PDF", Path(pdf_path).read_bytes(), file_name="report.pdf", mime="application/pdf")

st.subheader("Relatório")
render_report(result.get("report_md") or "")
