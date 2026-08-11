# ADR-002: Gemini Flash (Free Tier)

**Context:** Need an LLM for summarization. Free tier preferred.

**Decision:** Gemini Flash latest via Google AI Studio free tier.

**Rationale:**
- 15 RPM / 1M TPM sufficient for 2–3 briefings/day.
- Strong multilingual support (Portuguese).
- Free tier has no internet access — raw data must be fetched and injected into prompt.

**Consequences:**
- Pipeline must fetch all content before LLM call.
- No live browsing. RSS + API + scraping only.
- Fallback: DeepSeek v4-pro if rate-limited.
