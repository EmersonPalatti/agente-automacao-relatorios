# Agente de automação de relatórios

Pipeline de **ETL leve + insights + relatório (Markdown/PDF)** para dados tabulares (CSV, Excel ou SQL DuckDB). O diferencial de portfólio — pensado para o estágio iFood — é **medir e documentar a economia de tempo** frente ao processo manual.

Não é um chatbot que “chuta” EDA. Limpeza e profiler são determinísticos; análises geram (ou reutilizam) código executado de verdade. O LLM só planeja, tenta gerar Python e narra números já calculados.

## Diferencial

| Métrica | Como medir | Sem LLM | Com LLM (OpenRouter Nemotron 3 Ultra free) |
|---|---|---|---|
| Tempo manual estimado | EDA + gráficos + relatório escrito | 3h 30min | 3h 30min |
| Tempo do agente | `time.perf_counter()` | **0.9s** | **3min 43s** |
| Redução | diferença % | 99.99% | **98.23%** |
| Custo LLM | LiteLLM | $0 | **$0** (20 904 tokens, 14 chamadas) |
| Qualidade | números batem com o código | templates + profiler | planner/writer + sandbox (3 retries) |

Detalhe: [`results.md`](results.md). Relatório gerado inclui as mesmas métricas.

## Demo

![Nulos](docs/demo/missingness.png)

![Pedidos por cidade](docs/demo/top_city.png)

![Série temporal](docs/demo/timeseries.png)

## Pipeline

```
CSV / Excel / DuckDB
        ↓
   ingestão (Polars + Parquet)
        ↓
   limpeza leve (strip, tokens nulos, colunas vazias)
        ↓
   profiler factual
        ↓
   router condicional ──(n_rows == 0)──────────────────┐
        ↓ (n_rows > 0)                                 │
   planner (3–5 análises)                              │
        ↓                                              │
   codegen no sandbox (3 retries) → fallback template  │
        ↓                                              │
   writer (insights narrativos) ◀──────────────────────┘
        ↓
   Markdown + PDF compilados (+ tempos, limpeza, tokens)
```

Orquestração: **LangGraph** com estado tipado ([`PipelineState`](graph/state.py)) e aresta condicional para datasets vazios.

## Stack

Python 3.11+ · LangGraph · Polars · DuckDB · Pydantic v2 · LiteLLM · Matplotlib/Plotly · ReportLab · Streamlit · Typer · pytest

PDF via ReportLab (funciona nativamente no Windows sem dependências C/GTK).

## Estrutura do Projeto

```
agente-automacao-relatorios/
├── graph/             # Orquestração LangGraph (state, nodes, workflow com edges condicionais)
├── tools/             # Ferramentas determinísticas (cleaner, profiler, code_executor, loader, pdf)
├── prompts/           # Prompts versionados de sistema (planner, coder, writer)
├── experiments/       # Versões e histórico de evolução do pipeline (v1 vs v2)
├── app.py             # Interface visual Streamlit (upload, métricas, gráficos e download PDF)
├── cli.py             # Interface CLI (Typer) com execução em sandbox
├── tests/             # Suíte de testes automatizados (pytest)
├── docs/demo/         # Gráficos de demonstração gerados pelo agente
└── data/              # Datasets de exemplo (pedidos_ifood.csv)
```

## Experimentos Versionados

O projeto mantém experimentos documentados na pasta `experiments/`:
- [`experiments/v1_basic`](experiments/v1_basic/README.md): MVP inicial com perfil básico e análises em templates determinísticos.
- [`experiments/v2_with_cleaning`](experiments/v2_with_cleaning/README.md): pipeline atual com limpeza registrada (`CleaningLog`), correção de tipos temporais, geração de código no sandbox com fallback e arestas condicionais no LangGraph.

## Quickstart

```bash
python -m venv .venv
# Windows (cmd/PowerShell): .venv\Scripts\activate  (ou .venv\Scripts\Activate.ps1)
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python cli.py sample
python cli.py run data/raw/pedidos_ifood.csv --no-llm
streamlit run app.py
```

Os relatórios gerados são salvos em `outputs/reports/<timestamp>/` (`report.md`, `report.pdf` e gráficos PNG).

### Configuração de LLM (Multi-Provider via LiteLLM)

Copie `.env.example` → `.env`. O projeto aceita múltiplos provedores configurando a variável correspondente:
- **OpenRouter (padrão gratuito):** `OPENROUTER_API_KEY` com modelo `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`
- **OpenAI:** `OPENAI_API_KEY` (ex.: `LLM_MODEL=gpt-4o-mini`)
- **Google Gemini:** `GEMINI_API_KEY` (ex.: `LLM_MODEL=gemini/gemini-1.5-flash`)
- **Groq:** `GROQ_API_KEY` (ex.: `LLM_MODEL=groq/llama-3.3-70b-versatile`)

```bash
python cli.py run data/raw/pedidos_ifood.csv
```

SQL opcional (tabela `source`):

```bash
python cli.py run data/raw/pedidos_ifood.csv --sql "SELECT * FROM source WHERE status = 'delivered'"
```

Sem chave de API configurada, planner, writer e análises caem automaticamente no modo determinístico.

Codegen (Python no sandbox) é habilitado na **CLI**. No Streamlit o LLM, se ligado, só planeja e escreve; análises usam templates.

## Streamlit Community Cloud

`runtime.txt` pede **Python 3.12**. Em [share.streamlit.io](https://share.streamlit.io): New app → este repo → `app.py`.

Não coloque chave de LLM em app público. A UI não executa código gerado (`allow_codegen=False`), SQL é só `SELECT`/`WITH` em `source`, e upload é limitado a 20 MB com nome sanitizado. Codegen com sandbox (env sem secrets + allowlist AST) fica na CLI local.

## O que o agente faz / não faz

Faz: limpeza registrada, perfil real, plano data-agnostic, gráficos a partir dos dados, sandbox com timeout e ambiente mínimo, seção de economia de tempo.

Não faz: inventar estatística, imputar nulos, apagar linhas, hardcodar nomes de coluna, seguir depois de erro silencioso, copiar `API_KEY` para o processo do código gerado.

## Testes

```bash
pytest
# ou garantindo o interpretador do ambiente virtual:
python -m pytest -v
```
