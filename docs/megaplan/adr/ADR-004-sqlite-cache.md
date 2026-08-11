# ADR-004: SQLite for Data Caching

**Context:** Need to cache fetched data (prices, news, macro) for deduplication and feedback loop analysis.

**Decision:** SQLite via `sqlite3` stdlib.

**Rationale:**
- Zero external dependency for database.
- Structured, queryable, portable.
- Single-file `.db` — easy to inspect, backup, delete.

**Consequences:**
- Schema migrations manual (no ORM).
- Concurrent writes unlikely (single cron job), so no locking concerns.
