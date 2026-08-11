# ADR-005: Bias Inferred by LLM Per-Run

**Context:** Need bias annotation per news source. Options: hardcoded YAML, LLM inference, or hybrid.

**Decision:** LLM inference per-run.

**Rationale:**
- Zero maintenance burden.
- LLM can adapt to new sources without config updates.
- Consistency acceptable for casual briefing (not academic research).

**Consequences:**
- Bias labels may vary slightly run-to-run for the same source.
- Adds token cost to each LLM call (minimal, single sentence per source).
