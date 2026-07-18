# CLAUDE.md — dr-watch (Diário da República, em linguagem humana)

## Contexto do projeto

Segundo projeto de portfólio de Diogo Guimarães Silva (o primeiro: energia-forecast). Um
sistema LLM autónomo que responde todas as manhãs à pergunta *"o que é que o Estado
português decidiu hoje?"*: ingere a Série I do Diário da República, classifica cada diploma
por tema, resume-o em linguagem clara com citações obrigatórias, publica um digest diário +
arquivo pesquisável, e **avalia a sua própria qualidade em público**.

Objetivo de carreira: preencher os dois gaps do portfólio que o energia-forecast não cobre —
**engenharia de LLMs** (RAG-adjacente, evals, guardrails, budget de tokens) e um **frontend
React/Next a sério** (a metade full-stack do posicionamento). Prioridade: sistema honesto e
em produção > demo vistosa. Part-time, ~2-3 semanas, AI-assisted assumido.

> **Contexto multi-projeto:** ver `C:\dev\CLAUDE.md` (mapa-mestre do portfólio). O projeto
> irmão energia-forecast vive em `C:\dev\energia-forecast` — os padrões de lá (ingestão
> idempotente, `first_seen_at`, insert-only, ADR-013 sobre triggers) são a referência.

## Princípios (herdados do energia-forecast, adaptados)

1. **Sistema, não notebook.** Dados reais diários, cadência de produção, custo zero estrito.
2. **Evals antes de prompts.** O golden set (curado à mão) existe antes de se afinar um
   único prompt — a versão LLM de "baselines antes do modelo".
3. **Baseline honesta:** o RSS já traz o sumário oficial de cada diploma. O output só se
   publica se acrescentar valor sobre esse sumário (clareza + classificação + agregação).
   Se não acrescentar, publica-se o sumário oficial, rotulado.
4. **Citações obrigatórias e verificáveis.** Cada afirmação liga ao documento oficial;
   citation validity é medida automaticamente, todos os dias, em público.
5. **Outputs insert-only.** Um digest publicado nunca é reescrito (correções = nova versão
   visível, nunca edição silenciosa).
6. **Falha honesta.** Budget guard de tokens: se o free tier esgotar, digest parcial com
   aviso ("N diplomas adiados") — nunca omissão silenciosa. Tudo logado (dq_log-like).
7. **Registar decisões** em ADRs curtos (`docs/decisions/`). Registo sóbrio em todas as
   superfícies públicas (sem emojis, sem taglines — ver memória do autor).

## Fontes (verificadas ao vivo em 2026-07-10)

| O quê | Como | Verificado |
|---|---|---|
| Diários do dia, Série I | RSS 2.0: `https://files.diariodarepublica.pt/rss/serie1.xml` — título, entidade emissora, **sumário oficial**, link direto ao PDF | ✅ 200, ~7-30 items/dia |
| Texto integral | PDFs em `files.diariodarepublica.pt/1s/YYYY/MM/{issue}/{pages}.pdf`, sem auth | ✅ download direto; **pypdf extrai texto embebido limpo** (testado em 2 PDFs reais; hifenização de quebra de linha a normalizar) |
| Série II | `rss/serie2.xml` existe | ✅ mas **fora da v1** (volume rebentaria o free tier LLM) |
| Backfill histórico | Sem API oficial documentada; a app é OutSystems (API interna frágil) | Decisão v1: **arquivo forward-only** — constrói-se a partir do lançamento. Backfill = spike futuro opcional |

**Legal:** textos oficiais (leis, decretos) estão excluídos de proteção autoral (CDADC,
art. 8.º); o © INCM no feed cobre a compilação/site. Resumir + citar + linkar é legítimo.
Verificação final dos termos do site antes do lançamento público (a página legal é JS-only,
não foi lida no spike).

## Temas v1 (âmbito deliberadamente pequeno)

**DECIDIDO (2026-07-10): habitação, saúde, economia.** Tudo o resto classifica como
"outros" e aparece sem resumo dedicado na v1. Expandir temas é backlog pós-v1.

## Pipeline diário (alvo)

```
~07:30 UTC  cron-job.org → workflow dispatch (lição ADR-013 do energia: NUNCA GH schedule
            no caminho crítico; schedules ficam como fallback — ingestão idempotente)
   ↓
Ingest: RSS Série I → raw (insert-only, first_seen_at) → download PDFs → texto normalizado
   ↓
LLM (free tier + budget guard, provider abstraído):
   1. classify   → tema(s) + tipo + entidade (output estruturado, schema forçado)
   2. summarize  → 2-3 frases de linguagem clara, com citação (página/excerto)
   3. verify     → suporte de cada afirmação no texto; validade das citações
   ↓
Digest do dia (insert-only) + arquivo
   ↓
Evals diários → log durável → página pública "How accurate is this?"
```

## Evals (a identidade do projeto)

| Métrica | Medição | Automática |
|---|---|---|
| Citation validity | link resolve + excerto citado existe no documento | ✅ 100% |
| Coverage | % dos diplomas do dia processados e publicados | ✅ 100% |
| Classification accuracy | vs golden set (~100 diplomas etiquetados à mão pelo autor, ANTES do prompt-tuning) | ✅ |
| Faithfulness | cada frase do resumo suportada pelo texto (LLM-as-judge + amostra manual semanal) | parcial |
| Valor vs sumário oficial | julgamento amostral: "mais claro/útil que o sumário do RSS?" | manual |

## Stack e budget free-tier (auditado 2026-07-10)

- **LLM:** Gemini Flash free tier (1.500 req/dia — precisamos ~20-100) com fallback Groq
  (1.000 req/dia); abstração de provider desde o dia 1; budget guard diário.
- **BD:** projeto Neon **próprio** (free = 100 projetos × 0.5 GB × 100 CU-h/mês cada).
  Lição do energia: nada de keepalives que toquem na BD; compute deve dormir.
- **Serving:** Next.js/React no **Vercel Hobby** — site + API como route handlers
  (serverless). **Sem segundo serviço Render** (o free são 750 instance-h/mês por workspace
  e a API do energia consome ~720).
- **Compute batch:** GitHub Actions (repo público, ilimitado), disparado por cron-job.org
  (free: jobs ilimitados, timeout 30s — chega para um dispatch).
- **Python 3.12 via uv** para o pipeline; TypeScript/Next para o site. ruff/mypy/pytest;
  testes de evals são gate de merge (o equivalente ao marker `leakage` do energia).

## Estrutura alvo do repositório

```
dr-watch/
├── CLAUDE.md / README.md / pyproject.toml
├── .github/workflows/        # ci, digest diário (dispatch), evals
├── src/
│   ├── ingestion/            # rss.py, pdf_text.py (idempotente, first_seen_at)
│   ├── pipeline/             # classify.py, summarize.py, verify.py, budget.py, providers/
│   ├── evals/                # golden set, citation checks, runners
│   └── db/                   # modelos, migrações alembic, repositórios
├── web/                      # Next.js (site + API route handlers)
├── tests/
└── docs/decisions/           # ADRs
```

## Convenções para o Claude Code

- Código e comentários em inglês; comunicação com o autor em português; superfícies
  públicas em inglês, registo sóbrio.
- Commits pequenos, convencionais, em inglês.
- Segredos só via env vars / GitHub Secrets (repo será público). `GEMINI_API_KEY`,
  `GROQ_API_KEY`, `DATABASE_URL`.
- Antes de mexer em `src/pipeline/` ou `src/evals/`: reler os princípios 2-6.
- Em dúvida entre "mais completo" e "mais simples mas em produção": a segunda.

## Estado atual

**Última atualização:** 2026-07-18. **LIVE: https://dr-watch-omega.vercel.app** — digest
diário, arquivo forward-only, `/precisao` (qualidade auto-medida, publicada sem edição).
**1º dia 100% autónomo em 07-13: 12 diplomas** ingeridos, analisados e publicados sem
intervenção (2 curados pelo run seguinte após 429s — a fila idempotente a pagar-se).
**Prompt v1 (ADR-001):** cada card é uma "capa de jornal" — headline LLM em linguagem
corrente (grounding de números cobre headline+resumo), designação oficial despromovida a
kicker, ordenação por peso normativo (lei → regras → recomendações → retificações).
Arquivo re-analisado sob v1 (20/20, 0 flagged, citações 20/20); site pinado em v1.
**Front page tipográfica em 2 colunas (ADR-002…005):** manchete + até 3 secundárias
completas na coluna principal, lateral «Mais nesta edição» com selos tipográficos do
tipo de ato (DL/PORT/RAR/RET, cor do tema, `<details>` expande resumo); agrupamento por
assunto (1 request/dia, `digest.day_grouping` append-only, validação determinística,
fallback = ungrouped); navegação: /tema/[tema], edição anterior/seguinte, OG `next/og`.
**Fotografias: testadas e removidas (ADR-005)** — foto de tema colada a história
específica = especificidade falsa (caso Sines×diplomatas); se voltarem, só derivadas
do próprio ato, nunca metáforas de tema.

**Incidente 07-16→18 (resolvido 07-18):** a INCM passou a emitir itens com link-imagem
no feed da Série I (34 anexos duplicados de uma portaria + o DL 146/2026 cujo único link
é um JPG); o parser estrito abortava a ingestão inteira → 3 dias sem digest. Fix: itens
não-PDF em quarentena com warning (nunca fatais) + `--feed-file` no runner para repor a
partir dos snapshots do repo (a razão de eles existirem). Backfill 17/17, 0 flagged,
citações 17/17. ⚠️ DL 146/2026 fica fora até a INCM corrigir o link (o feed acumula dias
→ entra sozinho se corrigirem).

### Histórico (condensado — detalhe no `git log`)

- Dia 1 (07-10): spikes verdes (RSS ✓, PDFs AES→`pypdf[crypto]` ✓, backfill→forward-only,
  legal→CDADC art. 8.º) → repo + CI → coletor RSS 2×/dia (last-wins: o feed acresce; em dias
  sem edição serve a ANTERIOR) → parser (variante Suplemento) → extração PDFs → Neon próprio
  (mig 0001) → runner diário idempotente validado no runner GH.
- Pipeline LLM: FallbackChain (Gemini pinado `gemini-3.1-flash-lite` — o 2.5 está fechado a
  contas novas — + Groq opcional), budget gasto ANTES da chamada, contrato pydantic nosso;
  classify + summarize + verify determinístico de números (custo zero); `digest.act_analysis`
  insert-only versionado por `prompt_version` (mig 0002).
- Evals: `evals.pipeline_run` append-only (cobertura, flags, citation check HEAD, mig 0003);
  digest é DERIVADO (query de composição partilhada com o site em `show_digest`).
- Workflow `Daily pipeline` = ingest→analyse (secrets DATABASE_URL + GEMINI_API_KEY; a chave
  Gemini viaja SEMPRE em header, nunca em URL). Resiliência 429: retry backoff 15/30/60s +
  pacing 6s/diploma (free tiers limitam por MINUTO — visto ao vivo em 07-13).
- Site Next.js (`web/`, UI em PT — produto para leitores portugueses): digest temático,
  arquivo, precisão; acesso via role Postgres `web_ro` (só leitura por GRANT); datas
  validadas (9999-99-99 dava 500). Vercel Hobby, root `web`; subdomínio limpo estava tomado.
- 25+ ficheiros de código, 26 testes (unit + integração com Postgres no CI), migrações
  0001-0004, tudo validado sobre artefactos reais.
- Prompt v1 (07-13, ADR-001): headline em linguagem corrente no mesmo request do resumo
  (budget inalterado); regra nova no resumo (abrir pela substância, não pela designação);
  `act_rank` (Python) / `actRank` (TS) — manter em sync — ordena por peso normativo;
  backfill do arquivo via bump de PROMPT_VERSION (insert-only: linhas v0 intactas).
- Front page + grouping (07-13, ADR-002, mig 0005): `group_related.py` agrupa por assunto
  com validação determinística (id inválido/duplicado ⇒ dia fica ungrouped — nunca parte o
  digest); dias re-agrupados em linhas novas quando chegam atos tardios; site compõe story
  cards em `digest.tsx` (`compose()`); 1º dia real: 188+189 (Defesa) e 190+191 (Igualdade)
  agrupados corretamente, dia 07-10 corretamente sem grupos.

### A seguir (retomar aqui)
- [ ] **Golden set (autor):** etiquetar ~100 diplomas com a CLI cega
      `uv run --env-file .env python -m src.evals.label` (ADR-006; letras h/s/e/o,
      1ª = tema principal; t = excerto, k = saltar, q = sair; retomável). /precisao
      publica a exatidão automaticamente a partir de 10 etiquetas. Só depois se afinam
      prompts (princípio 2).
- [ ] **Dispatch via cron-job.org** (opcional por agora — o schedule atrasado do GH serve
      enquanto o digest não tiver hora de publicação prometida).
- [ ] **Verificação final dos termos do site do DR** antes de divulgar publicamente.
- [ ] **Write-up** ("Building an LLM system that grades itself") quando houver ~1-2 semanas
      de digests + evals acumulados.
- [ ] Backlog: faithfulness LLM-as-judge amostral, Série II, backfill histórico, domínio.
