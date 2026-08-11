# ADR-001: Python Stack

**Context:** Need a language with strong ecosystem for financial data (yfinance), RSS (feedparser), Google APIs, and Discord (discord.py).

**Decision:** Python 3.11+.

**Rationale:**
- `yfinance`, `feedparser`, `google-genai`, `discord.py` are all Python-first.
- Cron-friendly: single-file scripts, easy venv activation.
- User's preference confirmed.

**Consequences:** Performance is not a concern for a cron job. Type safety via Pydantic + mypy.
