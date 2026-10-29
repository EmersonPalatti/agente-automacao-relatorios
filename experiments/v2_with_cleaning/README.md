# v2_with_cleaning

Evolução do `v1_basic`, adicionando etapa determinística de limpeza, geração de código em sandbox isolado para todas as análises com LLM e endurecimento de segurança.

```
ingest → clean → profile ─(n_rows > 0)─→ plan → analyze → write → compile
                    └─────(n_rows == 0)──────────────────↗
```

## O que mudou em relação ao `v1_basic`

1. **Nó `clean` (`tools/cleaner.py`):**
   - Faz `strip` em colunas de texto, converte tokens vazios/nulos (`""`, `"NA"`, `"n/a"`, `"-"`, `"null"`, `"?"`) em `null` real e remove colunas 100% vazias.
   - Registra cada transformação em `CleaningLog` sem apagar linhas nem imputar valores inventados.
2. **Correção do Profiler para `Datetime` (`tools/profiler.py`):**
   - No `v1`, timestamps únicos (`order_datetime`) eram classificados como `is_likely_id=True` por terem `n_unique == n_rows`.
   - No `v2`, colunas `Date`/`Datetime`/`Time` nunca recebem `is_likely_id`, liberando séries temporais limpas.
3. **Codegen no Sandbox + Fallback (`tools/code_executor.py` e `graph/nodes.py`):**
   - Com LLM habilitado e `allow_codegen=True`, cada análise tenta gerar Python (até 3 tentativas com erro real devolvido ao prompt).
   - Se o código falhar após 3 tentativas, o nó cai automaticamente para o template determinístico (`tools/analyses.py`).
   - Detecção de artefatos `.png` por `mtime_ns` + prefixo por `spec.id`, evitando perda de gráficos quando dois scripts usam nomes parecidos.
4. **Segurança e Performance:**
   - Subprocesso do sandbox roda com ambiente mínimo (`child_env`), sem expor `OPENROUTER_API_KEY` ou `OPENAI_API_KEY`, mais validação AST (`looks_unsafe`).
   - SQL DuckDB restrito a uma única instrução `SELECT`/`WITH` sobre `source` (`validate_user_sql`).
   - Upload sanitizado contra *path traversal* e limitado a 20 MB (`safe_upload_path`).
   - Renderização única do PDF em `compile_report`.

