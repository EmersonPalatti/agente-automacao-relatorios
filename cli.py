from __future__ import annotations

import sys
from pathlib import Path

import typer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from tools.timing import DEFAULT_MANUAL_MINUTES, format_duration

app = typer.Typer(no_args_is_help=True, help="Agente de automação de relatórios / ETL leve.")


@app.command()
def run(
    source: Path = typer.Argument(..., exists=True, readable=True, help="CSV, Excel, Parquet ou DuckDB"),
    out: Path = typer.Option(Path("outputs/reports"), help="Diretório de saída"),
    sql: str | None = typer.Option(None, help="Query DuckDB (tabela registrada: source)"),
    no_llm: bool = typer.Option(False, help="Força plano e narrativa determinísticos"),
    manual_minutes: float = typer.Option(DEFAULT_MANUAL_MINUTES, help="Tempo manual estimado, em minutos"),
) -> None:
    from graph.workflow import run_pipeline

    def _progress(msg: str) -> None:
        typer.echo(f"- {msg}")

    result = run_pipeline(
        source,
        out,
        sql=sql,
        use_llm=not no_llm,
        manual_minutes=manual_minutes,
        progress=_progress,
    )
    eco = result["economy"]
    typer.echo("")
    typer.echo(f"Markdown: {result.get('report_md_path')}")
    typer.echo(f"PDF:      {result.get('report_pdf_path')}")
    typer.echo(
        f"Tempo do agente: {format_duration(eco['agent_seconds'])} | "
        f"redução {eco['reduction_pct']:.2f}% vs {format_duration(eco['manual_seconds'])} manuais"
    )


@app.command()
def sample(
    dest: Path = typer.Option(Path("data/raw/pedidos_ifood.csv")),
    n: int = typer.Option(800, min=10),
    seed: int = typer.Option(42),
) -> None:
    from tools.sample_data import write_sample_csv

    path = write_sample_csv(dest, n=n, seed=seed)
    typer.echo(f"dataset de exemplo: {path}")


if __name__ == "__main__":
    app()
