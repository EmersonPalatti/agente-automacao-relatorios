# Agente de automação de relatórios

Pipeline de **ETL leve + insights + relatório (Markdown/PDF)** para dados tabulares (CSV, Excel ou SQL DuckDB). O diferencial de portfólio — pensado para o estágio iFood — é **medir e documentar a economia de tempo** frente ao processo manual.

Não é um chatbot que “chuta” EDA. O profiler e as análises correm em código; o LLM, quando existe, só planeja e narra números já calculados.

## Diferencial

| Métrica | Como medir | Resultado (dataset de pedidos, sem LLM) |
|---|---|---|
| Tempo manual estimado | EDA + gráficos + relatório escrito | 3h 30min |
| Tempo do agente | `time.perf_counter()` no pipeline | **0.9s** no dataset de pedidos, sem LLM |
| Economia | diferença e % | **99.99%** nessa corrida |
| Custo LLM | opcional (LiteLLM) | R$ 0 no modo `--no-llm` |
| Qualidade | checklist: números batem com o código | profiler determinístico + sandbox |

Detalhe das corridas: [`results.md`](results.md).

## Pipeline

```
CSV / Excel / DuckDB
        ↓
   ingestão (Polars + Parquet)
        ↓
   profiler factual
        ↓
   planner (3–5 análises)
        ↓
   análises + gráficos (retry em código gerado)
        ↓
   writer (insights)
        ↓
   Markdown + PDF  (+ tempos por etapa)
```

Orquestração: **LangGraph**. Estado tipado, um nó por etapa, logs e tempos em todos os nós.

## Stack

Python 3.11+ · LangGraph · Polars · DuckDB · Pydantic v2 · LiteLLM · Matplotlib/Plotly · ReportLab · Streamlit · Typer · pytest

## Quickstart

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -r requirements.txt

python cli.py sample
python cli.py run data/raw/pedidos_ifood.csv --no-llm
streamlit run app.py
```

SQL opcional (a tabela do arquivo se chama `source`):

```bash
python cli.py run data/raw/pedidos_ifood.csv --sql "SELECT * FROM source WHERE status = 'delivered'"
```

Copie `.env.example` para `.env` se quiser planner/writer com LLM (`LLM_MODEL` + chave do provedor). Sem chave, o pipeline continua determinístico.

## O que o agente faz / não faz

Faz: perfil real, plano data-agnostic, gráficos a partir dos dados, relatório com seção de economia de tempo, sandbox com timeout para código gerado.

Não faz: inventar estatística, hardcodar nomes de coluna, seguir depois de erro silencioso, executar código gerado sem timeout.

## Estrutura

Ver `AGENTS.md` para regras do projeto. Código principal:

- `graph/` — estado, nós, grafo LangGraph
- `tools/` — loader, profiler, análises, sandbox, PDF
- `prompts/` — prompts versionados
- `experiments/v1_basic/` — notas desta versão
- `data/raw/` — dataset de exemplo (pedidos estilo iFood)
- `tests/` — loader, profiler, pipeline sem LLM, sandbox

## Testes

```bash
pytest
```
