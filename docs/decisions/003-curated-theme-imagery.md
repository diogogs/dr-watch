# ADR-003: Curated free-licensed theme imagery on an asymmetric front page

**Date:** 2026-07-13 · **Status:** accepted (supersedes the no-photos stance of ADR-002)

## Context

ADR-002 shipped a typographic front page and deliberately rejected photos. Reviewing it
live, the author found it too text-heavy and asked for imagery and an Observador-like
asymmetric front: cards of different sizes, only some with images. The original objections
remain real (no photojournalism of the acts exists; random stock decorates without
informing) — the decision is how to add imagery without those costs.

## Decision

**Curated theme illustrations, not per-story stock.** A hand-picked pool of free-licensed
photographs from Wikimedia Commons (Portuguese context where possible: Lisbon/Porto
facades for habitação, Santa Maria urgência for saúde, Baixa/Sines/euros for economia,
São Bento for outros), reviewed image by image before inclusion, resized into the repo
(`web/public/img/temas/`), and unified by a navy tint + desaturation overlay. The manifest
(`web/lib/images.ts`) is the single source of truth and drives both rendering and the
public `/creditos` attribution page; the footer states plainly that images are thematic
illustrations, not depictions of the acts.

Front page becomes a three-tier asymmetric grid (the reference the author pointed to):
hero with large image; middle column with one pictured secondary story plus a compact
list (small thumbnail, kicker + headline, `<details>` expands the full summary in place);
right column text-only with summaries. Tiers are assigned deterministically from the
normative-weight order. Image assignment cycles each theme's pool in display order, so
same-theme cards differ within a day.

## Why

- The honesty problem with stock photos was *implied specificity* — a photo pretending to
  depict the story. A small curated pool, reused daily and openly credited as thematic
  illustration, makes no such claim, and the tint treatment reads as design, not reportage.
- `<details>` on compact items keeps the front page scannable without deleting content —
  every act's summary and citation remain one tap away, on the page itself.
- Licensing is auditable: every file has author, license and source link on /creditos;
  CC0/PD preferred, CC BY/BY-SA accepted with attribution.

## Consequences

- The pools are small (3–4 per theme); heavy days repeat images within a theme. Enlarging
  a pool is an additive manifest + file change.
- Repo grows ~2 MB. Vercel serves the files statically; no external image host, no CSP or
  hotlinking concerns.
- If a photo ever misleads (e.g., a specific hospital pictured next to a story about a
  different hospital), the fix is pool-level: swap toward more generic imagery.
