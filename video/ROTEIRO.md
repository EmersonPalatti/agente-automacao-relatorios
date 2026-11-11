# Motion video — especificação

Fonte única de verdade para quem trabalha no vídeo. Não mude números, cores ou tempos sem combinar.

## Formato

- Remotion (React + TypeScript), projeto em `video/`.
- 1080 × 1350 (4:5), 30 fps, **1200 frames (40 s)**. Composição principal: id `LinkedInVideo`.
- Feito para o feed do LinkedIn, que toca **sem som**: todo o conteúdo está no texto da tela. Sem áudio.
- Margem de segurança: 80 px nas laterais, 120 px em cima e embaixo. Texto mínimo de 36 px (é lido no celular).
- Idioma: português do Brasil.
- **Nunca** mencionar iFood nem usar logo, cor ou nome de empresa. O dataset é "pedidos de delivery", sintético.

## Identidade visual

Minimalista. Muito espaço em branco, um elemento de foco por vez.

| Token | Hex | Uso |
|---|---|---|
| `bg` | `#FAFAF9` | fundo de todas as cenas |
| `ink` | `#111111` | títulos, números grandes, nós do LLM (preenchidos) |
| `gray` | `#737373` | texto secundário, legendas |
| `line` | `#E7E5E4` | linhas, bordas, nós determinísticos (contorno) |
| `greenBg` / `greenInk` | `#CDEBD5` / `#1F5133` | positivo: métricas, ✓ |
| `redBg` / `redInk` | `#F5D0CE` / `#7F1D1D` | negativo: tempo manual, erro |

Regras:
- Pastel só como **fundo** (chips, cards, marca-texto). Texto colorido usa a versão `Ink`.
- Verde/vermelho sempre acompanhados de sinal (✓ ↑ / ✗ ou número riscado), nunca só cor.
- Fontes: **Inter** (texto; 400, 600, 800) e **JetBrains Mono** (números, código, nomes das etapas; 500, 700), via `@remotion/google-fonts`.
- Movimento: entradas com `spring` (damping ~200, sem quique exagerado) ou `interpolate` com easing `Easing.bezier(0.16, 1, 0.3, 1)`. Entradas 12–18 frames, saídas 8–10 frames. Stagger 4–6 frames. Nada de rotação 3D, partículas ou glow.
- Transição entre cenas: corte seco ou fade de 8 frames. Sem wipes chamativos.

## Números permitidos (não invente outros)

- Tempo manual estimado: **~1h45** (faixa 1h30–2h, estimativa do autor).
- Tempo do agente: **~2 min** (corrida de 2 min 07 s).
- **Mais de 97% menos tempo.**
- **$0** de custo (modelo gratuito via OpenRouter).
- **5 de 5** análises resolvidas com código gerado pelo LLM.
- Pipeline: ingest → clean → profile → plan → analyze → write → compile. LLM em plan, analyze e write.
- Sandbox: até 3 tentativas, timeout de 90 s.

## Cenas (frames a 30 fps)

| # | Frames | Arquivo | Conteúdo |
|---|---|---|---|
| 1 | 0–90 | `src/scenes/S1Hook.tsx` | "~1h45" gigante em mono, com fundo `redBg`; uma linha o risca. "~2 min" entra por baixo em `greenBg` com spring. Legenda pequena em `gray`: "relatório de operações". Rodapé minúsculo: "tempo manual estimado". |
| 2 | 90–240 | `src/scenes/S2Pain.tsx` | Título: "Toda semana, o mesmo ritual:". Checklist em 4 itens que se marcam um a um (stagger): "Limpar a base", "Calcular os mesmos recortes", "Montar os gráficos", "Escrever o resumo". Relógio minimalista (círculo + ponteiro girando) em `redInk` no canto. |
| 3 | 240–330 | `src/scenes/S3Question.tsx` | "E se um agente fizesse isso?" centralizado. Depois um ícone de arquivo CSV (retângulo com cantinho dobrado + 4 linhas de tabela, label "pedidos.csv" em mono) cai no centro com spring. |
| 4 | 330–660 | `src/scenes/S4Pipeline.tsx` | Pipeline vertical com 7 nós (pílulas com nome em mono). Nós acendem em sequência (~40 frames cada). Determinísticos: contorno `line`, ao acender viram borda `ink`. LLM (plan, analyze, write): preenchidos `ink` com texto `bg`, tag pequena "LLM". Contador de tempo no topo direito em mono subindo de 0:00 até 2:07 no fim da cena. Durante "analyze", um mini-loop ao lado: "código gerado" → "sandbox" → chip `redBg` "✗ erro" → "retry" → chip `greenBg` "✓ métricas". |
| 5 | 660–810 | `src/scenes/S5Report.tsx` | "Saída: relatório em Markdown + PDF". 3 folhas (cards brancos com sombra suave) se abrem em leque, cada uma com um gráfico real de `public/plots/` (`missingness.png`, `top_city.png`, `timeseries.png`). |
| 6 | 810–1020 | `src/scenes/S6Metrics.tsx` | 3 cards `greenBg`/`greenInk` entram um por vez (stagger ~50 frames), número grande contando de 0 (odômetro/interpolate): "↑ 97%+ menos tempo", "$0 de custo", "5/5 análises com código gerado". |
| 7 | 1020–1110 | `src/scenes/S7Trust.tsx` | Uma frase só, centralizada: "Os números saem de código executado." e, abaixo em `gray`, "O LLM planeja e escreve. Não inventa." |
| 8 | 1110–1200 | `src/scenes/S8Outro.tsx` | Chips da stack em stagger: Python · LangGraph · Polars · DuckDB · Streamlit. Título "Agente de automação de relatórios". CTA: "Teste o app → link nos comentários". |

## Estrutura de arquivos (contrato)

```
video/
├── ROTEIRO.md
├── package.json            # remotion, @remotion/cli, @remotion/google-fonts, react, react-dom, typescript
├── remotion.config.ts
├── tsconfig.json
├── public/plots/           # missingness.png, top_city.png, timeseries.png (cópias de docs/demo/)
├── src/
│   ├── index.ts            # registerRoot
│   ├── Root.tsx            # <Composition id="LinkedInVideo" ...>
│   ├── Video.tsx           # <Series> ou <Sequence> com as 8 cenas nos frames acima
│   ├── theme.ts            # tokens de cor, fontes, easing, SAFE (margens)
│   ├── fonts.ts            # carrega Inter e JetBrains Mono
│   ├── components/         # Chip, Card, SceneFrame (fundo + margens), FadeIn, Counter
│   └── scenes/S1Hook.tsx … S8Outro.tsx
└── out/                    # renders (gitignored)
```

Cada cena exporta um componente nomeado (`export const S1Hook: React.FC = () => ...`), usa `useCurrentFrame()` com frame **local** (0 = início da cena, porque o `Video.tsx` envolve cada uma numa `<Sequence from=...>`), e importa cores só de `theme.ts`.

## Comandos

- `npm run dev` → Remotion Studio.
- `npm run render` → `npx remotion render LinkedInVideo out/video.mp4 --codec h264`.
- `npm run still -- --frame=N` → frame isolado para conferir.
- `npx tsc --noEmit` precisa passar.
