"""Raw data assembler: merges portfolio, prices, macro, news and agenda into a briefing context."""

from dataclasses import dataclass
from datetime import datetime

from resenha.agenda import CalendarEvent, EmailSummary
from resenha.macro import MacroData
from resenha.news import NewsItem
from resenha.portfolio import Asset


@dataclass
class AssetPosition:
    """An asset merged with its current price data."""

    asset: Asset
    price: dict | None


@dataclass
class AgendaData:
    """Aggregated calendar events and relevant unread emails."""

    events: list[CalendarEvent]
    emails: list[EmailSummary]


@dataclass
class BriefingContext:
    """Aggregated data ready for briefing generation."""

    portfolio: list[AssetPosition]
    macro: MacroData | None
    news_by_asset: dict[str, list[NewsItem]]
    general_news: list[NewsItem]
    agenda: AgendaData | None = None
    timestamp: datetime | None = None


def assemble_briefing_data(
    assets: list[Asset],
    prices: dict[str, dict],
    macro: MacroData | None,
    news: list[NewsItem],
    agenda: AgendaData | None = None,
) -> BriefingContext:
    """Merge assets with prices and group news by ticker.

    Args:
        assets: Portfolio assets.
        prices: Mapping from ticker to price dict.
        macro: Latest macroeconomic data.
        news: List of news items.
        agenda: Optional calendar/email agenda data.

    Returns:
        BriefingContext with all data assembled.
    """
    portfolio = [AssetPosition(asset=asset, price=prices.get(asset.ticker)) for asset in assets]

    news_by_asset: dict[str, list[NewsItem]] = {}
    general_news: list[NewsItem] = []

    for item in news:
        if item.tickers_mentioned:
            for ticker in item.tickers_mentioned:
                news_by_asset.setdefault(ticker, []).append(item)
        else:
            general_news.append(item)

    return BriefingContext(
        portfolio=portfolio,
        macro=macro,
        news_by_asset=news_by_asset,
        general_news=general_news,
        agenda=agenda,
        timestamp=datetime.now(),
    )
