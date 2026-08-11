# Resenha — Product Vision

**Goal:** A Python-based, LLM-powered daily news briefing bot that reads the user's Brazilian investment portfolio from Google Sheets, fetches financial news and macro data, summarizes it via Gemini Flash (free tier), and delivers structured Discord embeds with bias annotation and a relaxed Brazilian-Portuguese voice.

## Roadmap

### Cycle 0: Scaffolding
- B-001: Project scaffold — `pyproject.toml`, package structure, pytest, `.env`, `.gitignore`
- B-002: Config loader — Pydantic settings, env vars, sheet ID, Discord token, asset list cache
- B-003: Portfolio reader — Google Sheets client, parse "Consolidado" tab into typed dataclasses
- B-004: Discord bot scaffold — `discord.py` client, channel verification, embed sender

### Cycle 1: Fetch Pipeline
- B-005: Price fetcher — `yfinance` integration, cache to SQLite
- B-006: Macro fetcher — BCB SGS API (SELIC, IPCA, Dólar)
- B-007: News fetcher — RSS aggregation (InfoMoney, Suno, Seu Dinheiro, Exame)
- B-008: Raw data assembler — combine price + macro + news into prompt context

### Cycle 2: Summarizer
- B-009: Gemini client — Google AI Studio integration, prompt builder
- B-010: Bias inferrer — LLM-based source bias annotation per article
- B-011: Summary generator — asset-grouped briefings with voice/tone

### Cycle 3: Delivery
- B-012: Discord embed formatter — structured embeds per asset/topic
- B-013: Cron scheduler — 7am BRT pre-market, 7pm BRT EOD, Saturday long-form
- B-014: End-to-end smoke test — full pipeline run

### Cycle 4: Feedback Loop
- B-015: Reaction tracker — SQLite schema, Discord reaction event listener
- B-016: Feedback weighting — per-source and per-asset ranking algorithm
- B-017: Adaptive briefing — adjust depth/tone based on feedback scores

### Cycle 5: Context & Daily Awareness
- B-022: Remove Suno RSS source
- B-023: Briefing memory — include previous briefing in prompt to avoid repetition
- B-024: Email and calendar daily agenda — aggregate week events and relevant unread emails
- B-025: Fix mypy type errors — get `mypy src/` clean and add a type-check gate