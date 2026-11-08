# Resultados de tempo

Comparação usada no relatório (processo manual de EDA + gráficos + texto):

| Cenário | Tempo manual estimado |
|---|---|
| Dataset de pedidos (800 linhas, 11 colunas) | 3h 30min (210 min) |

## Corridas do agente

| Data | Dataset | LLM | Modelo | Codegen ok | Tempo agente | Tokens | Custo | Redução |
|---|---|---|---|---|---|---|---|---|
| 2026-11-08 | `pedidos_ifood.csv` | não | — | — (templates) | **0.8s** | 0 | $0 | 99.99% |
| 2026-11-08 | `pedidos_ifood.csv` | sim | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | **5/5** | **2min 7s** | 13 473 (8 chamadas) | **$0** (free) | **98.99%** |

Na corrida com LLM: planner e writer usaram o Nemotron, e as 5 análises rodaram o Python gerado no sandbox sem precisar do template de fallback. Insights do relatório citam só números já calculados.

Etapas (com LLM): ingest+clean+profile ~0.1s, plan ~19s, analyze ~93s, write ~14s, compile ~0.3s.

### Histórico

A corrida de 2026-10-27 (3min 43s, 20 904 tokens, 14 chamadas, 98.23%) foi feita com um bug no sandbox: o script era chamado por caminho relativo com `cwd` na própria pasta de saída, então nenhum código gerado chegava a rodar e todas as análises caíram no template depois de 3 tentativas. Corrigido em `tools/code_executor.py` (`out_dir.resolve()`), junto com `numpy as np` exposto no wrapper do sandbox.

### Como medir de novo

```bash
python cli.py run data/raw/pedidos_ifood.csv --no-llm
python cli.py run data/raw/pedidos_ifood.csv
```

O `report.md` gerado inclui economia de tempo, limpeza aplicada e, se houver LLM, tokens/custo.
