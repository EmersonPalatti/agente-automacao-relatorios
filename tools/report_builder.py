from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from tools.llm import summarize_usage
from tools.models import AnalysisPlan, AnalysisResult, CleaningLog, DataProfile
from tools.timing import TimeEconomy, format_duration


def build_markdown(
    *,
    source_name: str,
    profile: DataProfile,
    plan: AnalysisPlan,
    results: list[AnalysisResult],
    timings: dict[str, float],
    economy: TimeEconomy,
    used_llm: bool,
    insights_md: str,
    cleaning_log: CleaningLog | None = None,
    token_usage: list[dict] | None = None,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        f"# Relatório de análise — {source_name}",
        "",
        f"Gerado em {now}. Números abaixo vêm de código executado, não de chute do modelo.",
        "",
        "## Tempo manual estimado vs tempo do agente",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Tempo manual estimado | {format_duration(economy.manual_seconds)} |",
        f"| Tempo do agente | {format_duration(economy.agent_seconds)} |",
        f"| Tempo economizado | {format_duration(economy.saved_seconds)} |",
        f"| Redução | {economy.reduction_pct:.2f}% |",
        f"| LLM | {'sim' if used_llm else 'não (plano e narrativa determinísticos)'} |",
        "",
        "O tempo manual assume EDA + gráficos + relatório escrito por uma pessoa "
        "(valor padrão: 3h30). Ajuste se o seu processo for diferente.",
        "",
    ]
    usage = summarize_usage(token_usage or [])
    if used_llm and usage["calls"]:
        cost = usage["cost_usd"]
        cost_txt = "gratuito / $0" if cost == 0 else f"${cost:.4f}"
        lines += [
            "## Custo e tokens (LLM)",
            "",
            f"- Modelo: `{usage['model']}`",
            f"- Chamadas: **{usage['calls']}**",
            f"- Tokens: **{usage['total_tokens']}** (prompt {usage['prompt_tokens']}, completion {usage['completion_tokens']})",
            f"- Custo estimado: **{cost_txt}**",
            "",
        ]
    if cleaning_log is not None:
        lines += [
            "## Limpeza aplicada",
            "",
            f"- Shape: {cleaning_log.n_rows_in}x{cleaning_log.n_cols_in} → "
            f"{cleaning_log.n_rows_out}x{cleaning_log.n_cols_out}",
            f"- Linhas removidas: **0** (o cleaner não apaga linhas nem imputa valores)",
            "",
        ]
        if cleaning_log.actions:
            for act in cleaning_log.actions:
                col = f" `{act.column}`" if act.column else ""
                lines.append(f"- `{act.action}`{col}: {act.detail} (n={act.count})")
            lines.append("")
        else:
            lines += ["- Nenhuma transformação necessária.", ""]
    lines += [
        "## Perfil dos dados",
        "",
        f"- Linhas: **{profile.n_rows}**",
        f"- Colunas: **{profile.n_cols}**",
        "",
        "| Coluna | Tipo | Nulos | Únicos | Papel |",
        "|---|---|---:|---:|---|",
    ]
    for col in profile.columns:
        role = []
        if col.is_likely_id:
            role.append("id")
        if col.is_numeric:
            role.append("numérica")
        if col.is_datetime:
            role.append("data")
        if col.is_categorical:
            role.append("categórica")
        lines.append(
            f"| {col.name} | `{col.dtype}` | {col.null_pct:.1f}% | {col.n_unique} | {', '.join(role) or '—'} |"
        )
    if profile.numeric_summary:
        lines += ["", "### Resumo numérico", ""]
        for name, stats in profile.numeric_summary.items():
            mean = stats.get("mean")
            median = stats.get("median")
            lines.append(
                f"- **{name}**: média { _fmt(mean) }, mediana { _fmt(median) }, "
                f"min { _fmt(stats.get('min')) }, max { _fmt(stats.get('max')) }"
            )
    if profile.notes:
        lines += ["", "### Notas do profiler", ""]
        lines.extend(f"- {n}" for n in profile.notes)

    if plan.narrative_focus:
        lines += ["", f"**Foco do relatório:** {plan.narrative_focus}", ""]

    insights = insights_md.strip() or "_Sem insights gerados._"
    if not insights.startswith("##"):
        insights = "## Insights\n\n" + insights
    lines += ["", insights, "", "## Análises executadas", ""]

    for i, result in enumerate(results, start=1):
        status = "ok" if result.success else "falhou"
        how = ", codigo gerado" if result.used_llm_code else ""
        lines += [f"### {i}. {result.title} ({status}{how})", ""]
        if result.error:
            lines += [f"> Erro: {result.error}", ""]
        if result.metrics:
            lines += ["```json", json.dumps(result.metrics, ensure_ascii=False, indent=2), "```", ""]
        for art in result.artifacts:
            p = Path(art)
            lines += [f"![{p.stem}]({p.as_posix()})", ""]

    lines += [
        "## Tempos por etapa",
        "",
        "| Etapa | Tempo |",
        "|---|---|",
    ]
    for name, seconds in timings.items():
        if name == "total":
            continue
        lines.append(f"| {name} | {format_duration(seconds)} |")
    if "total" in timings:
        lines.append(f"| **total** | **{format_duration(timings['total'])}** |")

    lines += [
        "",
        "## Método",
        "",
        "- Limpeza leve (strip, tokens nulos, colunas 100% vazias) é determinística e registrada acima.",
        "- Profiler (Polars) calcula shape, nulos, tipos e únicos depois da limpeza.",
        "- Com LLM, cada análise gera Python e roda no sandbox (até 3 tentativas); se falhar, usa template versionado.",
        "- Sem LLM, só os templates. O texto do modelo só interpreta números já calculados.",
        "",
    ]
    return "\n".join(lines)


def write_markdown(text: str, dest: str | Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return dest


def write_pdf(markdown_text: str, dest: str | Path, image_base: str | Path | None = None) -> Path:
    """PDF simples a partir do Markdown gerado (títulos, tabelas, imagens, parágrafos)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image,
        ListFlowable,
        ListItem,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    font_name, font_bold = _register_fonts()
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "H1pt",
            parent=styles["Heading1"],
            fontName=font_bold,
            fontSize=16,
            spaceAfter=10,
            textColor=colors.HexColor("#1d3557"),
        )
    )
    styles.add(
        ParagraphStyle(
            "H2pt",
            parent=styles["Heading2"],
            fontName=font_bold,
            fontSize=13,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#1d3557"),
        )
    )
    styles.add(
        ParagraphStyle(
            "H3pt",
            parent=styles["Heading3"],
            fontName=font_bold,
            fontSize=11,
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle("Bodypt", parent=styles["Normal"], fontName=font_name, fontSize=9.5, leading=13)
    )
    styles.add(
        ParagraphStyle(
            "Codept",
            parent=styles["Code"],
            fontName=font_name,
            fontSize=7.5,
            leading=10,
            backColor=colors.HexColor("#f4f1de"),
        )
    )

    story: list = []
    in_code = False
    code_lines: list[str] = []
    table_rows: list[list[str]] | None = None
    base = Path(image_base) if image_base else dest.parent

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            table_rows = None
            return
        data = [[Paragraph(_esc(c), styles["Bodypt"]) for c in row] for row in table_rows]
        tbl = Table(data, colWidths=None)
        tbl.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), font_bold),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d3557")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 1), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c9c9c9")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                ]
            )
        )
        story.append(tbl)
        story.append(Spacer(1, 8))
        table_rows = None

    for raw in markdown_text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines) or " ", styles["Codept"]))
                story.append(Spacer(1, 6))
                code_lines = []
                in_code = False
            else:
                flush_table()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.startswith("|") and "|" in line[1:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") and c for c in cells):
                continue
            if table_rows is None:
                table_rows = []
            table_rows.append(cells)
            continue
        else:
            flush_table()

        if not line:
            story.append(Spacer(1, 4))
            continue
        if line.startswith("# "):
            story.append(Paragraph(_esc(line[2:]), styles["H1pt"]))
            continue
        if line.startswith("## "):
            story.append(Paragraph(_esc(line[3:]), styles["H2pt"]))
            continue
        if line.startswith("### "):
            story.append(Paragraph(_esc(line[4:]), styles["H3pt"]))
            continue
        if line.startswith("!["):
            path = _image_path(line, base)
            if path and path.exists():
                img = Image(str(path))
                img._restrictSize(16 * cm, 8.5 * cm)
                story.append(img)
                story.append(Spacer(1, 8))
            continue
        if line.startswith("- "):
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(_inline(line[2:]), styles["Bodypt"]))],
                    bulletType="bullet",
                    leftIndent=12,
                )
            )
            continue
        if line.startswith("> "):
            story.append(Paragraph(f"<i>{_inline(line[2:])}</i>", styles["Bodypt"]))
            continue
        story.append(Paragraph(_inline(line), styles["Bodypt"]))

    flush_table()
    if in_code and code_lines:
        story.append(Preformatted("\n".join(code_lines), styles["Codept"]))

    doc = SimpleDocTemplate(
        str(dest),
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title=dest.stem,
    )
    doc.build(story)
    return dest


def _register_fonts() -> tuple[str, str]:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = []
    try:
        from matplotlib import font_manager

        candidates.append(Path(font_manager.findfont("DejaVu Sans")))
        for font in font_manager.fontManager.ttflist:
            fname = Path(font.fname)
            if "DejaVuSans-Bold" in fname.name:
                candidates.append(fname)
                break
    except Exception:
        pass
    candidates += [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    regular = next((p for p in candidates if p and p.exists() and "bold" not in p.name.lower() and "bd" not in p.stem.lower()), None)
    bold = next((p for p in candidates if p and p.exists() and ("bold" in p.name.lower() or p.stem.lower().endswith("bd"))), None)
    if regular:
        pdfmetrics.registerFont(TTFont("ReportSans", str(regular)))
        if bold:
            pdfmetrics.registerFont(TTFont("ReportSans-Bold", str(bold)))
            return "ReportSans", "ReportSans-Bold"
        return "ReportSans", "ReportSans"
    return "Helvetica", "Helvetica-Bold"


def _image_path(line: str, base: Path) -> Path | None:
    start = line.find("(")
    end = line.rfind(")")
    if start == -1 or end == -1:
        return None
    rel = line[start + 1 : end]
    p = Path(rel)
    if p.exists():
        return p
    alt = base / rel
    return alt if alt.exists() else p


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _inline(text: str) -> str:
    import re

    text = _esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font face='Courier' size='8'>\1</font>", text)
    return text


def _fmt(v: float | None) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1000:
        return f"{v:,.2f}"
    return f"{v:.2f}"
