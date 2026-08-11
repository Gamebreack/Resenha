# ADR-006: Graceful Degradation on Source Failures

**Context:** RSS feeds go down, APIs rate-limit, scrapers break.

**Decision:** Skip failed sources/assets, deliver what worked, log errors.

**Rationale:**
- Partial briefing > no briefing.
- User expects daily delivery; outages should not abort the run.
- Error logs enable debugging without user-facing failure.

**Consequences:**
- Briefing completeness varies day-to-day.
- Need clear indicator in Discord when data is missing ("No news for ITUB4 today").
