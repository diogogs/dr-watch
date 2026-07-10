# dr-watch

What did the Portuguese state decide today? A daily, autonomous LLM system over the
Diário da República (Série I): every morning it ingests the official gazette, classifies
each act by theme, summarizes it in plain language with mandatory citations to the official
PDF, and publishes a daily digest and a searchable archive. Its accuracy is measured
continuously and published — citation validity, coverage, classification against a
hand-labelled golden set.

Status: pre-launch. The daily RSS collector is running (the archive is forward-only, so
collection started before the build); the pipeline, evals and site come next. Design and
decisions live in [CLAUDE.md](CLAUDE.md) and `docs/decisions/`.

By the author of [energia-forecast](https://github.com/diogogs/energia-forecast) — the same
design DNA: real data daily, zero-cost infrastructure, immutable outputs, honest public
evaluation.
