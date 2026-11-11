# Resultados de tempo

Comparação usada no relatório (processo manual de EDA + gráficos + texto):

| Cenário | Tempo manual estimado |
|---|---|
| Dataset de pedidos (800 linhas, 11 colunas) | 3h 30min (210 min) |

Esse valor é uma estimativa. Quando houver uma medição cronometrada, ela entra na tabela abaixo e passa a ser o número usado no README e no relatório, com `--manual-minutes`.

### Como cronometrar o tempo manual

Uma medição vale mais que a estimativa, desde que siga as mesmas regras do agente:

1. **Mesma entrada:** `data/raw/pedidos_ifood.csv`, sem olhar o relatório do agente antes.
2. **Mesma entrega:** um documento com qualidade dos dados (nulos por coluna), concentração por cidade, comparação de uma métrica entre grupos, evolução no tempo, de 4 a 7 insights com números e de 2 a 4 recomendações. Com gráficos.
3. **Ferramentas livres:** Excel, pandas ou o que a pessoa usaria no dia a dia. Sem LLM, porque o ponto é comparar com o processo manual.
4. **Cronômetro corrido:** começa ao abrir o arquivo e para quando o documento está pronto para enviar. Pausas longas ficam de fora; consultas a documentação ficam dentro.
5. **Registre por etapa**, para comparar com o tempo por etapa do agente.

| Data | Quem | Ferramenta | Limpeza e perfil | Análises e gráficos | Texto | Total |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | _a medir_ |

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

## Avaliação dos prompts (v1 → v2)

Medido com `scripts/eval_prompts.py`, que roda o pipeline com LLM e codegen em dois datasets de domínios diferentes, `pedidos_ifood.csv` e um de chamados de suporte gerado pelo script, com 2 corridas em cada. Modelo: `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`. Data: 2026-11-09.

| Métrica | v1 | v2 |
|---|---|---|
| Análises resolvidas por código gerado | 84% | **100%** |
| Código certo na 1ª tentativa | 58% | **95%** |
| Análises que caíram no template | 3 | **0** |
| Números do writer que não estão no payload | 6,1% (8 de 132) | **2,9%** (4 de 139) |
| Tempo médio por relatório | 3min 43s | **2min 51s** |
| Tokens por relatório | 17 879 | 20 771 (+16%) |

O planner já era bom na v1, sem colunas inventadas, colunas de ID ou análises repetidas, e continuou assim na v2.

O que mudou:

- **Coder:** passou a receber nulos, número de valores distintos e exemplos de cada coluna, além do número de linhas. No retry, recebe também o código que falhou, não só o erro. O prompt agora descreve o que o sandbox rejeita, como tratar datas em texto e o formato exato do `RESULTS_JSON`, com tipos numpy convertidos. Código que roda mas não imprime métricas passa a contar como falha e entra no retry.
- **Planner:** ganhou uma tabela com a ordem de `columns_hint` por tipo de análise, a regra de só usar `missingness` quando há nulos e a orientação de escrever `goal` como pergunta de negócio.
- **Writer:** passou a receber o `goal` de cada análise. O prompt proíbe calcular números novos, como diferenças, razões ou "X vezes", proíbe inventar unidade e pede as seções Insights, Recomendações e Limitações. A saída é limpa de `<think>`, de blocos de código e de bullets com `*`.
- **`prompts/profiler.md`:** removido, porque nenhum código o usava.

Limitações da medição:

- São 4 corridas por versão, com um modelo gratuito de saída variável. É um sinal forte, não um benchmark.
- Entre a v1 e a v2 também foi corrigido um bug de encoding no sandbox: no Windows, a saída do código gerado era lida como cp1252. Parte do ganho no codegen pode vir daí.
- O verificador de grounding ignorava números seguidos de unidade, como `21,0h`, nas duas versões. Ele foi corrigido depois da medição, então as taxas acima estão subestimadas do mesmo jeito para v1 e v2.
- Os últimos ajustes, como o aviso de nomes reservados no coder, o retry sem métricas e a limpeza do writer, foram feitos depois da v2 e só têm testes unitários. A corrida de confirmação bateu no limite diário do plano gratuito do OpenRouter.

```bash
python scripts/eval_prompts.py --label minha_versao --runs 2 --compare outputs/eval/v2.json
```
