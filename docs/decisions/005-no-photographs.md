# ADR-005: No photographs — the front page is typographic

**Date:** 2026-07-13 · **Status:** accepted (closes the imagery arc of ADR-003/004)

## Context

ADR-004 made images scarce and importance-bound. The first live page settled the question:
the hero "Governo adapta o sistema de avaliação de desempenho à carreira diplomática" was
illustrated by shipping containers at Sines, because the story's *theme* is economia. The
mismatch is structural, not curatorial: a theme photo attached to one specific story claims
false specificity, and themes broad enough to be useful (economia, outros) are exactly the
ones no single photo can represent. Scarcity made it worse — one large wrong image at the
top instead of several small ones.

## Decision

Remove photographs entirely: manifest, `/creditos`, assets and footer note deleted. The
front keeps everything that worked: the two-column hierarchy by normative weight, the
plain-language headlines, theme colors, and the act-type stamps (DL, PORT, RAR, RET…) in
the side list — the one visual element that informs rather than decorates, because it
encodes what the act IS. The typographic OG share image (next/og) stays.

## Why

- An image that can be wrong about the story next to it costs credibility exactly where
  this product earns it: precision.
- Three iterations (all-cards imagery → scarce imagery → none) each failed on the same
  root cause; the honest conclusion is that gazette acts have no photographable referent.
- Removal was cheap by design — ADR-004 kept everything presentation-level.

## Consequences

- If imagery ever returns, it must be *derived from the act itself* (e.g., generated
  typographic art from the designation, or entity seals), never theme metaphors.
- The stamps may later extend to the main-column secondaries if visual anchoring is
  missed; hero stays pure typography.
