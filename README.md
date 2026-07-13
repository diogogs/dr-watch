# dr-watch

What did the Portuguese state decide today? A daily, autonomous LLM system over the
Diário da República (Série I): every morning it ingests the official gazette, classifies
each act by theme, rewrites it as a plain-language headline and summary with mandatory
citations to the official PDF, and publishes a daily digest and a searchable archive. Its accuracy is measured
continuously and published — citation validity, coverage, classification against a
hand-labelled golden set.

Live at https://dr-watch-omega.vercel.app — the daily digest, the forward-only archive,
and a public accuracy page where every pipeline run's self-measured quality is published
unedited. Design and
decisions live in [CLAUDE.md](CLAUDE.md) and `docs/decisions/`.

By the author of [energia-forecast](https://github.com/diogogs/energia-forecast) — the same
design DNA: real data daily, zero-cost infrastructure, immutable outputs, honest public
evaluation.
