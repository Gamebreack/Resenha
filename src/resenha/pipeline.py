"""Pipeline orchestrator: runs the full briefing flow end-to-end."""

import json
import logging
import uuid
from pathlib import Path

from resenha.adaptive import build_adaptive_context
from resenha.assembler import AgendaData, assemble_briefing_data
from resenha.cache import Cache
from resenha.config import Settings
from resenha.delivery import run_bot
from resenha.gemini import GeminiClient
from resenha.macro import fetch_macro
from resenha.memory import BriefingMemory
from resenha.news import fetch_general_news, fetch_news
from resenha.portfolio import read_portfolio
from resenha.prices import fetch_price
from resenha.reactions import ReactionTracker
from resenha.summary import generate_briefing, generate_embeds
from resenha.agenda import fetch_calendar_events, fetch_relevant_emails

logger = logging.getLogger(__name__)

FALLBACK_TICKERS = [
    "ITUB4", "BBDC4", "EGIE3", "CPFE3", "TAEE11",
    "SBSP3", "VIVT3", "PSSA3", "RURA11", "BRCO11", "KNCR11",
]


async def run_pipeline(settings: Settings, style: str) -> str:
    """Run the full briefing pipeline and return the generated text."""

    cache_db = Cache(Path(settings.cache_db_path))

    # 1. Read portfolio (with fallback)
    assets = _try_step(
        lambda: read_portfolio(settings.google_sheet_id, settings.google_sheet_tab),
        "portfolio read",
        [],
    )
    tickers = [a.ticker for a in assets] if assets else FALLBACK_TICKERS

    # 2. Fetch prices
    prices = {}
    for ticker in tickers:
        result = _try_step(
            lambda t=ticker: fetch_price(t, cache_db),
            f"price fetch for {ticker}",
            None,
        )
        if result is not None:
            prices[ticker] = result

    # 3. Fetch macro
    macro = _try_step(
        lambda: fetch_macro(cache_db),
        "macro fetch",
        None,
    )

    # 3.5. Fetch agenda (calendar + relevant emails)
    token_path = Path.home() / ".hermes" / "google_token.json"
    events = _try_step(
        lambda: fetch_calendar_events(token_path),
        "calendar fetch",
        [],
    )
    emails = _try_step(
        lambda: fetch_relevant_emails(token_path),
        "email fetch",
        [],
    )
    agenda = AgendaData(events=events, emails=emails)

    # 4. Fetch financial news
    news = _try_step(
        lambda: fetch_news(tickers, cache_db),
        "news fetch",
        [],
    )

    # 4.5. Fetch general news
    general_news = _try_step(
        lambda: fetch_general_news(cache_db),
        "general news fetch",
        [],
    )

    # 5. Combine and assemble context
    all_news = news + general_news
    ctx = assemble_briefing_data(assets, prices, macro, all_news, agenda=agenda)

    # 5.5. Build adaptive feedback context from recent reactions
    tracker = ReactionTracker(db_path=settings.cache_db_path)
    feedback_text = build_adaptive_context(tracker, days=7)

    # 5.6. Fetch previous briefing memory for this style
    memory = BriefingMemory(db_path=settings.cache_db_path)
    previous_briefing = memory.get_last(style)

    # 6. Generate briefing via Gemini
    gemini = GeminiClient(api_key=settings.gemini_api_key)
    briefing_text = generate_briefing(ctx, gemini, style, feedback_text=feedback_text, previous_briefing=previous_briefing)

    # 6.5. Persist generated briefing memory
    memory.save(style, briefing_text)
    memory.prune(style, keep=1)

    # 7. Generate embeds
    embeds = generate_embeds(briefing_text)

    # 8. Deliver to Discord
    message_ids = await run_bot(settings.discord_bot_token, settings.discord_channel_id, embeds)

    # 9. Populate briefing registry for reaction tracking
    if message_ids:
        _save_briefing_registry(message_ids, embeds)

    return briefing_text


def _try_step(fn, label: str, default):
    """Run a pipeline step, logging and returning default on failure."""
    try:
        return fn()
    except Exception:
        logger.warning("Pipeline step failed: %s", label, exc_info=True)
        return default


REGISTRY_PATH = Path("data/briefing_registry.json")


def _save_briefing_registry(message_ids: list[int], embeds: list) -> None:
    """Save a mapping of message_id -> {asset_ticker, embed_index} for reaction tracking.

    Uses the embed title as the asset_ticker if available.
    """
    import discord

    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load existing registry
    registry: dict[str, dict] = {}
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r") as f:
            try:
                registry = json.load(f)
            except json.JSONDecodeError:
                registry = {}

    # Generate a new briefing run ID
    briefing_run_id = uuid.uuid4().hex[:12]

    for i, msg_id in enumerate(message_ids):
        if i < len(embeds):
            embed = embeds[i]
            title = getattr(embed, "title", "") if isinstance(embed, discord.Embed) else ""
        else:
            title = ""

        registry[str(msg_id)] = {
            "briefing_run_id": briefing_run_id,
            "asset_ticker": title,
            "embed_index": i,
        }

    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)

    logger.info(
        "Saved briefing registry: run=%s messages=%d",
        briefing_run_id,
        len(message_ids),
    )
