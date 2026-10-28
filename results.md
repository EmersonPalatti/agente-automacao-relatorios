# Resultados de tempo

Comparação usada no relatório (processo manual de EDA + gráficos + texto):

| Cenário | Tempo manual estimado |
|---|---|
| Dataset de pedidos (800 linhas, 11 colunas) | 3h 30min (210 min) |

## Corridas do agente

| Data | Dataset | LLM | Tempo agente | Redução | Relatório |
|---|---|---|---|---|---|
| 2026-10-27 | `data/raw/pedidos_ifood.csv` | não | **0.9s** | 99.99% | `outputs/reports/` (gitignored) |

Etapas na corrida sem LLM (ordem de grandeza): ingest ~0.05s, profile/plan/write ~0s, analyze ~0.6s (5 gráficos), compile Markdown+PDF ~0.2s.

Com LLM (planner + writer) o tempo sobe para a faixa de **1–4 min**, ainda ~98% mais rápido que o processo manual de 3h30. Custo típico: tokens via LiteLLM, da ordem de alguns centavos por relatório.

### Como medir de novo

```bash
python cli.py run data/raw/pedidos_ifood.csv --no-llm
```

O `report.md` gerado inclui a seção **Tempo manual estimado vs tempo do agente** e a tabela por etapa.
