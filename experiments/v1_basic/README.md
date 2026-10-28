# v1_basic

Primeira versão do pipeline, alinhada ao MVP do `AGENTS.md`.

```
ingest → profile → plan → analyze → write → compile
```

- **Profiler:** só Polars (shape, nulos, dtypes, únicos, resumo numérico).
- **Planner:** LLM com JSON estruturado se houver chave; senão `plan_from_profile`.
- **Coder:** funções determinísticas em `tools/analyses.py` para os tipos conhecidos; `custom` gera Python no sandbox (3 tentativas).
- **Writer:** LLM só interpreta métricas já calculadas; fallback monta bullets com os JSON das análises.
- **Tempo:** `time.perf_counter()` em cada nó + total no relatório.

Prompts desta versão: `prompts/planner.md`, `prompts/coder.md`, `prompts/writer.md`, `prompts/profiler.md`.
