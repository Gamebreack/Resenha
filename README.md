# Resenha

AI-powered financial briefing pipeline using Gemini, market data, RSS, Google Workspace and Discord.

> Bot diário de briefings financeiros para Discord, com análise em português brasileiro via Gemini.
> (Daily financial briefing bot for Discord, with analysis in Brazilian Portuguese via Gemini.)

Resenha reads an investment portfolio from Google Sheets, collects prices, macro data, RSS news and a Google Workspace agenda (Calendar + Gmail), generates a pt-BR briefing via Gemini, and delivers it as Discord embeds.

## What it does

- Pre-market, end-of-day, and weekly long-form briefings (`--once pre-market|eod|long-form`).
- Asset- and topic-grouped summaries in Brazilian Portuguese.
- Portfolio-aware prompts with previous-briefing memory to avoid repetition.
- Reaction-based feedback weighting that adjusts briefing depth/tone.
- Graceful degradation: each pipeline step fails independently and falls back to defaults.

## Architecture

```
Sheets/Gmail/Calendar ─┐
yfinance prices ───────┼─→ assembler (BriefingContext) → Gemini → Discord embeds
BCB macro + RSS news ──┘         ↑ SQLite cache + briefing memory + reactions
```

- `src/resenha/pipeline.py`: orchestrates fetch → assemble → generate → deliver; `_try_step` isolates failures; `FALLBACK_TICKERS` used when the portfolio read fails.
- `src/resenha/__main__.py`: `--once <style>` for single runs, `--schedule` for the built-in asyncio scheduler.
- `data/`: local SQLite cache, briefing memory, and reaction registry (git-ignored).

## AI / LLM

- `src/resenha/gemini.py` uses the `google-genai` SDK with model `gemini-flash-lite-latest`.
- Retry with backoff on HTTP 429 (3 attempts); other errors propagate to the pipeline's graceful-degradation path.
- Prompt assembly in `src/resenha/summary.py` + `prompts.py`, including portfolio, macro, news, agenda, adaptive feedback, and previous briefing.
- Note: `src/resenha/bias.py` provides source-bias helpers, but they are not wired into the current pipeline.

## Integrations

| Area | Implementation |
| --- | --- |
| Portfolio | Google Sheets API (`portfolio.py`), `Consolidado` tab |
| Market data | `yfinance` per-ticker, cached in SQLite (`prices.py`, `cache.py`) |
| Macro | Banco Central do Brasil SGS API — SELIC, IPCA, USD/BRL (`macro.py`) |
| News | `feedparser` RSS aggregation, per-asset + general feeds (`news.py`) |
| Agenda | Calendar (next 7 days) + unread Gmail (last 24h) (`agenda.py`) |
| Memory | SQLite `past_briefings` table (`memory.py`) |
| Feedback | Discord reaction tracking + scoring (`reactions.py`, `feedback.py`, `adaptive.py`) |
| Delivery | `discord.py` embeds with retry (`delivery.py`, `summary.py`) |

Google auth uses an OAuth authorized-user token file configured via `GOOGLE_TOKEN_PATH`.

## Requirements

- Python 3.11+
- Discord bot token + channel ID.
- Gemini API key (Google AI Studio).
- Google OAuth token with Sheets/Calendar/Gmail read scopes.
- Google Sheet ID for the portfolio.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env  # fill in tokens and IDs
```

See `docs/configuration.md` for environment variables and Google OAuth setup.

## Run

```bash
python -m resenha --once pre-market
python -m resenha --once eod
python -m resenha --once long-form
python -m resenha --schedule
```

Recurring execution uses the built-in scheduler (`--schedule`) or an external cron/service; see `docs/operations.md`.

## Tests

```bash
python -m pytest tests/ -q
python -m mypy src/
```

Both should pass before a commit.

## Docs

- [Architecture](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [Operations](docs/operations.md)
- [Roadmap](docs/megaplan/megaplan.md)
- [Backlog](docs/megaplan/backlog.md)

## Notes

- Briefings are generated in Brazilian Portuguese.
- Developed with AI-assisted tooling.
- Reaction listener (`listener.py`) exists but is not attached to the delivery client in this revision.

## License

Not yet defined.
