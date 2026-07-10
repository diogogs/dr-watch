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

> **Estado:** charter v0 (2026-07-10). Spikes dia-1 feitos; build ainda NÃO começou —
> arranca depois da fase interview-proof do energia-forecast (drift a solo + estudo).

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

4-5 temas: **habitação, saúde, economia** (confirmados) + 1-2 a decidir pelo autor
(candidatos: energia — sinergia com o outro projeto —, fiscalidade, justiça). Tudo o resto
classifica como "outros" e aparece sem resumo dedicado na v1.

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

**2026-07-10 — pré-arranque.** Feito: brainstorm + decisões (nome, temas, free-tier
estrito); spikes dia-1 TODOS verdes (RSS ✓, PDFs/pypdf ✓, backfill → forward-only ✓, legal
→ CDADC art. 8.º ✓); auditoria de capacidade das plataformas ✓ (incl. fix do keepalive/Neon
no energia); este charter.

### A seguir (quando o projeto arrancar)
- [ ] Autor: escolher os 1-2 temas finais + validar o nome do domínio público do site.
- [ ] Repo GitHub + scaffold (uv, ruff, mypy, pytest, CI) + migração inicial.
- [ ] Ingestão RSS + PDFs com testes sobre fixtures reais (guardar os XMLs/PDFs de dias
      reais como fixtures, incluindo um dia sem publicação — domingos!).
- [ ] **Golden set**: autor etiqueta ~100 diplomas (usar o arquivo RSS acumulado entretanto).
- [ ] Pipeline LLM + evals + digest + site.

### Pré-arranque: acumular dados desde já (decisão pendente)
O arquivo é forward-only ⇒ cada dia sem ingestão é um dia perdido para sempre. Opção barata
a considerar ANTES do build: um mini-workflow (20 linhas) que guarda o XML do RSS diário num
repo/storage desde já, para o golden set e o arquivo nascerem com semanas de dados. Custo:
~zero. Decidir com o autor.
