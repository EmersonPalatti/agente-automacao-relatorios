# AGENTS.md — Agente de Automação de Relatórios / ETL Leve

Este arquivo define as regras, stack, estrutura e convenções para o projeto **agente-automacao-relatorios** (ou `data-agent-pipeline`).

O objetivo é construir um agente (ou sistema multi-agente) que recebe dados tabulares (CSV, Excel ou query DuckDB), realiza limpeza/transformação leve, gera insights e produz um relatório (Markdown + PDF) ou dashboard. O diferencial principal para o portfólio do estágio iFood é **documentar e medir a economia de tempo** em relação ao processo manual.

## Contexto e Diferencial

Projetos similares existentes (referência de pesquisa):

| Projeto | Stack principal | O que faz bem | O que falta (oportunidade) |
|---------|------------------|---------------|----------------------------|
| Maggydata/ai-data-analyst-langgraph | LangGraph + Streamlit + pandas/Plotly | Multi-agente (Explorer → Planner → Coder → Writer), self-correction, sandbox | Relatório PDF final, métricas de tempo, DuckDB |
| udaybhookya/agentic-ai-data-analyst | LangGraph + PDF | Pipeline completo até PDF, self-correction | Interface Streamlit, documentação de tempo |
| dhrumilrana25/Agentic-Cleanse | LangGraph + Streamlit | ETL com HITL, security critic, self-healing | Foco em limpeza, não em insights/relatório |
| archanags001/AI-Report-Generator | LangGraph + Streamlit + PDF | Multi-agente + PDF + Streamlit | Menos ênfase em ETL e medição de tempo |
| Vários NL2SQL + DuckDB | Streamlit + DuckDB + LLM | Consultas naturais rápidas | Pouca orquestração multi-etapa e relatório completo |

**Nosso diferencial para o portfólio:**
- Medição explícita de tempo (antes vs depois) documentada no README e no próprio relatório gerado.
- Suporte a CSV/Excel **e** DuckDB (ETL leve).
- Pipeline claro: Ingestão → Limpeza/Transformação → Insights → Relatório.
- Deploy como Streamlit **e** CLI.
- Estrutura de experimentos versionados (inspirada no Prompt Lab).

## Stack Recomendada

| Camada | Tecnologia | Motivo |
|--------|------------|--------|
| Linguagem | Python 3.11+ | Padrão para dados + agentes |
| Orquestração | **LangGraph** (preferencial) | Controle explícito de estado, loops de correção, HITL fácil |
| Alternativa leve | Tool calling simples (LangChain ou PydanticAI) | Se o fluxo for mais linear |
| Dados | **Polars** + **DuckDB** | Rápido, eficiente, SQL nativo no DuckDB |
| Fallback | pandas | Compatibilidade e exemplos |
| Validação | **Pydantic** v2 | Structured outputs entre agentes |
| LLM | **LiteLLM** | Multi-provider (OpenAI, Groq, Gemini, etc.) |
| Visualização | Plotly | Interativo no Streamlit |
| Relatório | Markdown + **WeasyPrint** ou ReportLab | PDF profissional |
| Interface | **Streamlit** | Upload, progresso, download |
| CLI | Typer ou argparse | Automação e scripts |
| Observabilidade | LangSmith (opcional) ou logs estruturados | Debug de agentes |
| Testes | pytest + exemplos de datasets | Garantir que o pipeline funciona |

**Não usar por padrão:** CrewAI (mais pesado e menos controle fino para este caso), AutoGen (arquivado), PandasAI puro (menos orquestração multi-agente).

## Estrutura de Pastas Sugerida

```
agente-automacao-relatorios/
├── AGENTS.md                  # Este arquivo
├── README.md                  # Overview + resultados de tempo + demo
├── requirements.txt
├── .env.example
├── app.py                     # Streamlit (entrada principal)
├── cli.py                     # Interface CLI
├── graph/                     # LangGraph
│   ├── __init__.py
│   ├── state.py               # TypedDict / Pydantic state
│   ├── nodes.py               # Funções dos nós (profiler, cleaner, analyzer, writer)
│   └── workflow.py            # Construção do grafo + conditional edges
├── agents/                    # Lógica dos agentes (se quiser separar)
│   ├── profiler.py
│   ├── transformer.py
│   ├── insight_writer.py
│   └── report_compiler.py
├── tools/                     # Ferramentas determinísticas
│   ├── data_loader.py         # CSV, Excel, DuckDB
│   ├── code_executor.py       # Sandbox com timeout
│   └── report_builder.py      # Markdown → PDF
├── prompts/                   # Prompts versionados
│   ├── profiler.md
│   ├── analyzer.md
│   └── writer.md
├── experiments/               # Versões de pipeline / prompts
│   ├── v1_basic/
│   └── v2_with_cleaning/
├── data/
│   ├── raw/                   # Datasets de exemplo
│   └── processed/
├── outputs/                   # Relatórios gerados (gitignored)
│   ├── reports/
│   └── plots/
├── notebooks/                 # Exploração e validação
└── tests/
    └── test_pipeline.py
```

## Convenções e Regras para Agentes

### O que os agentes devem fazer
1. **Profiler (determinístico primeiro)**: Usar Polars/pandas para estatísticas reais (shape, nulls, dtypes, unique). LLM só interpreta e sugere.
2. **Self-correction**: Qualquer geração de código deve ter loop de retry (máx. 3 tentativas) com o erro retornado.
3. **Structured output**: Usar Pydantic entre nós sempre que um agente alimenta o próximo.
4. **Sandbox**: Execução de código gerado em subprocess com timeout e ambiente limpo.
5. **Medição de tempo**: Registrar tempo de cada etapa e tempo total. Incluir no relatório final e no README.
6. **Documentar economia**: No README e no próprio relatório, sempre incluir seção “Tempo manual estimado vs Tempo do agente”.
7. **Saídas**: Sempre gerar Markdown legível + PDF. Streamlit deve permitir download.
8. **Logs claros**: Cada nó deve logar o que fez (para debug e para o usuário ver progresso).

### O que os agentes NÃO devem fazer
- Inventar estatísticas ou números que não vieram do código executado.
- Rodar código sem sandbox/timeout.
- Depender de nomes de colunas hardcoded (deve ser data-agnostic).
- Gerar relatório sem antes ter executado as análises reais.
- Ignorar erros de execução e continuar.

## Métricas que devem ser documentadas

No README e em um `results.md` ou seção do relatório:

| Métrica | Como medir | Exemplo |
|---------|------------|---------|
| Tempo manual | Estimativa realista (ou cronometrada) | 3–4 horas de EDA + relatório |
| Tempo do agente | `time.perf_counter()` no pipeline | 2–4 minutos |
| Economia | Diferença + % | ~98% de redução |
| Custo LLM | Tokens / LiteLLM | ~$0.05–0.20 por relatório |
| Qualidade | Revisão humana ou checklist | Insights corretos / plots úteis |

## Fluxo Mínimo Viável (MVP)

1. Upload CSV ou seleção de arquivo local.
2. Profiler gera resumo factual.
3. Agente planeja 3–5 análises relevantes.
4. Código é gerado, executado (com retry) e plots salvos.
5. Writer gera narrativa + insights.
6. Compilador gera Markdown + PDF.
7. Streamlit mostra progresso + permite download.
8. README documenta o antes/depois de tempo.

## Próximos Passos Sugeridos

1. Criar estrutura de pastas e `requirements.txt`.
2. Implementar o grafo básico (Profiler → Planner → Coder → Writer).
3. Adicionar medição de tempo desde o início.
4. Fazer um dataset de exemplo (ex.: vendas ou pedidos) e documentar tempo manual.
5. Deploy Streamlit Cloud + README com GIF/demo e números.

---

**Última atualização:** Pesquisa realizada em 2026-10-27. Foco em diferencial de portfólio (economia de tempo documentada + ETL leve + multi-formato).
