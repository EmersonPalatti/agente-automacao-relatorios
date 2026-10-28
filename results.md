# Resultados de tempo

Comparação usada no relatório (processo manual de EDA + gráficos + texto):

| Cenário | Tempo manual estimado |
|---|---|
| Dataset de pedidos (800 linhas, 11 colunas) | 3h 30min (210 min) |

## Corridas do agente

| Data | Dataset | LLM | Modelo | Tempo agente | Tokens | Custo | Redução |
|---|---|---|---|---|---|---|---|
| 2026-10-27 | `pedidos_ifood.csv` | não | — | **0.9s** | 0 | $0 | 99.99% |
| 2026-10-27 | `pedidos_ifood.csv` | sim | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | **3min 43s** | 20 904 (14 chamadas) | **$0** (free) | **98.23%** |

Na corrida com LLM: planner e writer usaram o Nemotron; cada análise tentou gerar Python no sandbox (3 retries) e, quando o código falhou, o template versionado fechou o gráfico. Insights do relatório citam só números já calculados.

Etapas (com LLM): ingest+clean+profile ~0.1s, plan ~19s, analyze ~186s, write ~18s, compile ~0.2s.

### Como medir de novo

```bash
python cli.py run data/raw/pedidos_ifood.csv --no-llm
python cli.py run data/raw/pedidos_ifood.csv
```

O `report.md` gerado inclui economia de tempo, limpeza aplicada e, se houver LLM, tokens/custo.
