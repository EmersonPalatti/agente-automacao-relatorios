# Agente de automação de relatórios

Analistas de Operações gastam horas montando relatórios recorrentes: limpar a base, calcular os mesmos recortes, montar os gráficos e escrever o resumo para a gestão. Este agente faz esse trabalho em minutos. Ele recebe uma tabela (CSV, Excel, Parquet ou uma consulta SQL no DuckDB), limpa, analisa e devolve um relatório em Markdown e PDF com gráficos e insights, e **mede quanto tempo economizou** em relação ao processo manual.

**App publicado:** <https://agente-automacao-relatorios.streamlit.app/>

O LLM não inventa a análise. Limpeza e perfil dos dados são feitos por código. O modelo escolhe o que analisar, escreve o Python que roda num sandbox e redige o texto final a partir dos números que esse código calculou. O prompt proíbe números novos, e um avaliador mede quantos escapam (2,9% na última medição).

## Tempo manual estimado vs Tempo do agente

Dataset de exemplo `pedidos_ifood.csv` (800 linhas, 11 colunas), comparado a uma estimativa de 3h30 de trabalho manual (EDA, gráficos e texto). Como medir o tempo manual de verdade está em [`results.md`](results.md#como-cronometrar-o-tempo-manual).

| | Sem LLM | Com LLM |
|---|---|---|
| Tempo do agente | **0,8 s** | **2 min 7 s** |
| Redução de tempo | 99,99% | **98,99%** |
| Custo | $0 | **$0** (13 473 tokens, 8 chamadas, modelo gratuito) |
| Análises | templates prontos | 5 de 5 com código gerado pelo LLM |

O tempo é medido com `time.perf_counter()` em cada etapa e sai no próprio relatório.

### Qualidade dos prompts

Os prompts foram reescritos e medidos com [`scripts/eval_prompts.py`](scripts/eval_prompts.py), em 4 corridas por versão e dois domínios (pedidos e chamados de suporte):

| | v1 | v2 |
|---|---|---|
| Análises resolvidas por código gerado | 84% | **100%** |
| Código certo na 1ª tentativa | 58% | **95%** |
| Números no texto que não vieram dos dados | 6,1% | **2,9%** |
| Tempo médio por relatório | 3 min 43 s | **2 min 51 s** |

Detalhes, metodologia e limitações em [`results.md`](results.md). Alguns ajustes feitos depois da v2 ainda não passaram por essa medição.

## Demo

| Nulos por coluna | Pedidos por cidade | Série temporal |
|---|---|---|
| ![Nulos por coluna](docs/demo/missingness.png) | ![Pedidos por cidade](docs/demo/top_city.png) | ![Série temporal](docs/demo/timeseries.png) |

## Como funciona

```mermaid
flowchart TD
    IN[/"CSV · Excel · Parquet<br/>+ SQL DuckDB opcional"/] --> ING["<b>ingest</b><br/>Polars → Parquet"]
    ING --> CLN["<b>clean</b><br/>espaços, tokens de nulo,<br/>colunas vazias"]
    CLN --> PRF["<b>profile</b><br/>estatísticas calculadas"]
    PRF --> CHK{"tem linhas?"}
    CHK -- não --> WRT
    CHK -- sim --> PLN["<b>plan</b><br/>escolhe 3 a 5 análises"]
    PLN --> ANL

    subgraph ANL["<b>analyze</b>, para cada análise"]
        direction TB
        COD["coder escreve Python"] --> SBX["sandbox<br/>allowlist AST · 90 s · sem secrets"]
        SBX -- "erro ou sem métricas<br/>até 3 tentativas" --> COD
        SBX -- "falhou 3 vezes" --> TPL["template determinístico<br/>se existir para o tipo"]
    end

    ANL --> WRT["<b>write</b><br/>insights a partir das métricas"]
    WRT --> CMP[["<b>compile</b><br/>report.md · report.pdf · PNGs"]]

    classDef llm fill:#fde2e4,stroke:#c9184a,color:#590d22
    class PLN,COD,WRT llm
```

As etapas em rosa usam o LLM. Sem chave de API, ou com `--no-llm`, cada uma tem uma versão determinística: o plano sai do perfil, as análises usam templates e o texto é montado a partir das métricas.

| Etapa | O que faz | Código |
|---|---|---|
| ingest | Lê o arquivo, aplica o SQL opcional e salva em Parquet | [`tools/data_loader.py`](tools/data_loader.py) |
| clean | Limpeza leve e registrada, sem apagar linhas nem imputar nulos | [`tools/cleaner.py`](tools/cleaner.py) |
| profile | Tipos, nulos, cardinalidade, exemplos e resumo numérico | [`tools/profiler.py`](tools/profiler.py) |
| plan | O LLM escolhe as análises a partir do perfil | [`prompts/planner.md`](prompts/planner.md) |
| analyze | O LLM gera Python, que roda no sandbox e imprime as métricas | [`prompts/coder.md`](prompts/coder.md), [`tools/code_executor.py`](tools/code_executor.py) |
| write | O LLM escreve Insights, Recomendações e Limitações | [`prompts/writer.md`](prompts/writer.md) |
| compile | Monta o Markdown e o PDF com tempos, limpeza e tokens | [`tools/report_builder.py`](tools/report_builder.py) |

A orquestração é um grafo LangGraph com estado tipado ([`graph/state.py`](graph/state.py)) e uma aresta condicional para datasets sem linhas ([`graph/workflow.py`](graph/workflow.py)).

## Rodando localmente

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python cli.py sample                                    # gera data/raw/pedidos_ifood.csv
python cli.py run data/raw/pedidos_ifood.csv --no-llm   # sem LLM, em menos de 1 s
streamlit run app.py                                    # interface web
```

Cada execução cria `outputs/reports/<data>_<hora>_<id>/`, com `report.md`, `report.pdf` e os gráficos em `plots/`.

Outras opções da CLI (`python cli.py run --help`):

```bash
# Filtra com SQL antes de analisar (a tabela se chama source)
python cli.py run data/raw/pedidos_ifood.csv --sql "SELECT * FROM source WHERE status = 'delivered'"

# Usa o LLM para planejar e escrever, mas analisa com templates
python cli.py run data/raw/pedidos_ifood.csv --no-codegen

# Muda a estimativa de tempo manual usada na comparação (padrão: 210 min)
python cli.py run data/raw/pedidos_ifood.csv --manual-minutes 120

# Salva em outra pasta (padrão: outputs/reports)
python cli.py run data/raw/pedidos_ifood.csv --out relatorios/

# Consulta um banco DuckDB (o --sql é obrigatório nesse caso)
python cli.py run vendas.duckdb --sql "SELECT * FROM pedidos"
```

### Configurando o LLM

Copie `.env.example` para `.env` e preencha uma chave. As chamadas passam pelo [LiteLLM](https://docs.litellm.ai/docs/providers), então qualquer provedor suportado funciona. `LLM_MODEL` precisa ser do mesmo provedor da chave preenchida:

| Provedor | Variável | `LLM_MODEL` |
|---|---|---|
| OpenRouter (padrão, gratuito) | `OPENROUTER_API_KEY` | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` |
| OpenAI | `OPENAI_API_KEY` | `openai/<modelo>` |
| Google Gemini | `GEMINI_API_KEY` | `gemini/<modelo>` |
| Groq | `GROQ_API_KEY` | `groq/<modelo>` |
| Anthropic | `ANTHROPIC_API_KEY` | `anthropic/<modelo>` |

Se só houver `OPENROUTER_API_KEY` e `LLM_MODEL` vier sem prefixo de provedor, o código acrescenta `openrouter/`. Um `LLM_MODEL` de outro provedor sem a chave dele não avisa nada: as chamadas falham e o pipeline segue no modo determinístico.

O plano gratuito do OpenRouter tem um limite diário de chamadas. Quando ele estoura, o pipeline não para: cada etapa volta para a versão determinística e o log mostra o motivo.

## App no Streamlit Cloud

O app publicado roda o mesmo pipeline, com algumas diferenças pensadas para um link público:

- **Código gerado não roda no app.** Mesmo com o LLM ligado, ele só planeja e escreve, e as análises usam templates. O codegen no sandbox fica na CLI local.
- **SQL só aceita `SELECT` ou `WITH`** sobre a tabela `source`. Os dados são carregados na memória e, antes de rodar a consulta, o acesso do DuckDB a arquivos é desligado e travado, então funções como `read_text` não leem nada do servidor. Erro de SQL aparece como mensagem, não como traceback.
- **Upload de até 20 MB**, com nome sanitizado. Arquivos enviados e relatórios com mais de 6 horas são apagados a cada nova execução.
- Se o LLM for ligado sem chave configurada, o app avisa e segue no modo determinístico.

Para publicar o seu: em [share.streamlit.io](https://share.streamlit.io), crie um app apontando para este repositório, branch `main`, arquivo `app.py`. O `runtime.txt` pede Python 3.12.

Para usar o LLM no app, coloque a chave em **Settings → Secrets**, na raiz do TOML. O Streamlit exporta as chaves da raiz como variáveis de ambiente, que é de onde o código lê. Dentro de uma seção como `[openrouter]`, ela não é encontrada:

```toml
OPENROUTER_API_KEY = "sk-or-..."
```

Num app público, qualquer visitante pode ligar o LLM e consumir essa cota. Por isso a recomendação é deixar o app público sem chave.

## Segurança do sandbox

O código gerado pelo LLM só roda na CLI e passa por duas barreiras ([`tools/code_executor.py`](tools/code_executor.py)):

1. **Análise da AST** antes de rodar. O código é rejeitado se importar algo fora de pandas, numpy, matplotlib e alguns módulos da biblioteca padrão, se usar `open`, `eval`, `exec`, `getattr` ou similares, se citar `os`, `sys`, `subprocess`, `socket` e afins, se acessar atributos `__dunder__`, ou se chamar funções que leem ou gravam arquivos, como `pd.read_csv`, `df.to_csv` e `np.load`.
2. **Subprocesso separado**, com timeout de 90 s, diretório de trabalho na pasta de saída e um ambiente mínimo, sem nenhuma variável `*_API_KEY`.

Não é isolamento de sistema operacional, como um container. A checagem da AST é uma lista de bloqueio: reduz bastante o risco, mas não garante que nenhum caminho escape. Por isso o codegen fica desligado no app público.

## Avaliando os prompts

```bash
python scripts/eval_prompts.py --label minha_versao --runs 2 --compare outputs/eval/v2.json
```

O script roda o pipeline completo com LLM em dois datasets e mede:

- **Planner:** colunas inexistentes, colunas de ID e análises repetidas.
- **Coder:** sucesso, sucesso na 1ª tentativa e quedas para o template.
- **Writer:** números no texto que não aparecem nos dados que ele recebeu.

O resultado fica em `outputs/eval/<label>.json`.

## Estrutura

```
agente-automacao-relatorios/
├── app.py                # Interface Streamlit
├── cli.py                # CLI (Typer): sample e run
├── graph/                # LangGraph: estado, nós e o grafo
├── tools/                # Código determinístico: loader, cleaner, profiler,
│                         #   analyses (templates), code_executor (sandbox),
│                         #   report_builder (Markdown e PDF), models (Pydantic),
│                         #   llm, timing, uploads, sample_data
├── prompts/              # Prompts do planner, coder e writer
├── scripts/              # eval_prompts.py
├── experiments/          # Histórico das versões do pipeline
├── tests/                # pytest, incluindo testes do app com AppTest
├── data/raw/             # Dataset de exemplo
├── data/processed/       # Uploads do app (apagados após 6 h, fora do git)
├── docs/demo/            # Gráficos usados neste README
├── .streamlit/           # Configuração do app (limite de upload)
├── results.md            # Medições de tempo e de qualidade dos prompts
└── outputs/              # Relatórios e avaliações gerados (fora do git)
```

O histórico das versões do pipeline está em [`experiments/v1_basic`](experiments/v1_basic/README.md), o MVP com análises por template e codegen só para o tipo `custom`, e em [`experiments/v2_with_cleaning`](experiments/v2_with_cleaning/README.md), que trouxe a limpeza registrada, o codegen no sandbox e a aresta condicional.

## Testes

```bash
python -m pytest
```

Os testes cobrem loader (incluindo o bloqueio de leitura de arquivos via SQL), limpeza, perfil, sandbox, uploads, medição de tempo, o pipeline sem LLM e o app Streamlit rodando com `AppTest`. Nenhum deles chama o LLM. A qualidade das respostas do modelo é medida pelo `scripts/eval_prompts.py`.

## Limitações conhecidas

- As medições de qualidade usam 4 corridas por versão com um modelo gratuito de saída variável. Servem como sinal, não como benchmark.
- O writer ainda calcula uma razão por conta própria de vez em quando, como "7 vezes maior", apesar de o prompt proibir. O avaliador detecta isso, mas o pipeline ainda não marca esses números no relatório.
- O tempo manual de 3h30 ainda é uma estimativa, não uma medição cronometrada. O protocolo para cronometrar está em [`results.md`](results.md#como-cronometrar-o-tempo-manual).
