"""News fetching from Brazilian financial RSS feeds."""

import logging
from dataclasses import dataclass
from datetime import datetime

import feedparser  # type: ignore[import-untyped]

from resenha.cache import Cache

logger = logging.getLogger(__name__)

RSS_SOURCES = {
    "InfoMoney": "https://www.infomoney.com.br/feed/",
    "Seu Dinheiro": "https://www.seudinheiro.com/feed/",
}

GENERAL_RSS_SOURCES = {
    # Centro / geral
    "G1": "https://g1.globo.com/rss/g1/",
    "Folha": "https://www1.folha.uol.com.br/folha/emcimadahora/rss.xml",
    "Poder360": "https://www.poder360.com.br/feed/",
    # Direita
    "Crusoé": "https://crusoe.com.br/feed/",
    "Revista Oeste": "https://revistaoeste.com/feed/",
    # Esquerda
    "Piauí": "https://piaui.folha.uol.com.br/feed/",
    # Internacional
    "BBC Brasil": "https://www.bbc.com/portuguese/index.xml",
    # Tech / Ciência
    "TecMundo": "https://rss.tecmundo.com.br/feed",
    "Olhar Digital": "https://olhardigital.com.br/feed/",
    "Superinteressante": "https://super.abril.com.br/feed/",
    "Nautilus": "https://nautil.us/feed/",
    # Tech
    "Rest of World": "https://restofworld.org/feed/latest/",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Ars Technica": "https://arstechnica.com/information-technology/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    # Finance
    "The Guardian Business": "https://www.theguardian.com/business/rss",
    "CNBC Finance": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "NPR Economy": "https://feeds.npr.org/1017/rss.xml",
    "Fortune": "https://fortune.com/feed",
    # Politics
    "BBC News World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "The Guardian World": "https://www.theguardian.com/world/rss",
    "Al Jazeera English": "https://www.aljazeera.com/xml/rss/all.xml",
    "The American Conservative": "https://www.theamericanconservative.com/feed/",
    # Culture
    "G1 Pop & Arte": "https://g1.globo.com/rss/g1/pop-arte/",
    "Cinema com Rapadura": "https://cinemacomrapadura.com.br/feed/",
    "TMDQA!": "https://www.tenhomaisdiscosqueamigos.com/feed/",
    "Catraca Livre Gira": "https://catracalivre.com.br/gira/feed/",
    # Games / Cultura
    "IGN Brasil": "https://br.ign.com/feed.xml",
    "Nintendo Blast": "https://www.nintendoblast.com.br/feeds/posts/default",
    "GameVicio": "https://www.gamevicio.com/feed/",
}


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published: datetime
    summary: str
    tickers_mentioned: list[str]


def _parse_published(entry) -> datetime:
    """Extract published datetime from a feedparser entry."""
    if hasattr(entry, "published_parsed") and entry.published_parsed is not None:
        return datetime(*entry.published_parsed[:6])
    if hasattr(entry, "published") and entry.published:
        try:
            return datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed is not None:
        return datetime(*entry.updated_parsed[:6])
    if hasattr(entry, "updated") and entry.updated:
        try:
            return datetime.strptime(entry.updated, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            pass
    return datetime.min


def _entry_matches_tickers(entry, tickers: list[str]) -> list[str]:
    """Return list of tickers found in entry title or summary (case-insensitive)."""
    text = ""
    for attr in ("title", "summary", "description"):
        val = getattr(entry, attr, None)
        if val:
            text += " " + val
    text_lower = text.lower()
    return [ticker for ticker in tickers if ticker.lower() in text_lower]


def _normalize_entry(entry, source_name: str) -> NewsItem | None:
    """Convert a feedparser entry to a NewsItem."""
    url = getattr(entry, "link", getattr(entry, "url", ""))
    if not url:
        return None
    title = getattr(entry, "title", "")
    summary = getattr(entry, "summary", getattr(entry, "description", ""))
    published = _parse_published(entry)
    return NewsItem(
        title=title,
        url=url,
        source=source_name,
        published=published,
        summary=summary,
        tickers_mentioned=[],
    )


def _fetch_from_sources(
    sources: dict[str, str],
    cache: Cache | None = None,
    filter_tickers: list[str] | None = None,
    max_per_source: int | None = None,
) -> list[NewsItem]:
    """Fetch news from multiple RSS sources with optional ticker filtering.

    Args:
        sources: Mapping of source name to RSS URL.
        cache: Optional Cache instance for 30-minute per-source caching.
        filter_tickers: If provided, only include entries matching these tickers.
            If None, include all entries.
        max_per_source: If provided, limit each source to this many items
            (applied before deduplication). Use for general news feeds.

    Returns:
        List of NewsItem sorted by published date (most recent first).
    """
    all_items: list[NewsItem] = []
    seen_urls: set[str] = set()

    for source_name, url in sources.items():
        cache_key = f"news:{url}"
        source_items: list[NewsItem] = []
        cache_hit = False

        if cache is not None:
            cached_data = cache.get(cache_key, ttl_seconds=1800)
            if cached_data is not None:
                cache_hit = True
                for item_dict in cached_data.get("items", []):
                    item = NewsItem(
                        title=item_dict["title"],
                        url=item_dict["url"],
                        source=item_dict["source"],
                        published=datetime.fromisoformat(item_dict["published"]),
                        summary=item_dict["summary"],
                        tickers_mentioned=item_dict.get("tickers_mentioned", []),
                    )
                    # When loading from cache, only include items that match tickers
                    # if filtering is active (re-filter in case tickers changed).
                    if filter_tickers is not None:
                        if not item.tickers_mentioned:
                            continue
                        # Keep only tickers that are still in the requested set
                        matching = [t for t in item.tickers_mentioned if t in filter_tickers]
                        if not matching:
                            continue
                        item.tickers_mentioned = matching
                    source_items.append(item)

        if not cache_hit:
            try:
                feed = feedparser.parse(url)
            except Exception:
                logger.warning(
                    "Failed to fetch RSS from %s", source_name, exc_info=True
                )
                continue

            if hasattr(feed, "bozo") and feed.bozo:
                if not feed.entries and hasattr(feed, "bozo_exception"):
                    logger.warning(
                        "Malformed RSS from %s: %s",
                        source_name,
                        feed.bozo_exception,
                    )
                    continue

            for entry in feed.entries:
                normalized_item: NewsItem | None = _normalize_entry(entry, source_name)
                if normalized_item is None:
                    continue
                if filter_tickers is not None:
                    found_tickers = _entry_matches_tickers(entry, filter_tickers)
                    if found_tickers:
                        normalized_item.tickers_mentioned = found_tickers
                        source_items.append(normalized_item)
                else:
                    source_items.append(normalized_item)

            if cache is not None and source_items:
                cache.set(
                    cache_key,
                    {
                        "items": [
                            {
                                "title": item.title,
                                "url": item.url,
                                "source": item.source,
                                "published": item.published.isoformat(),
                                "summary": item.summary,
                                "tickers_mentioned": item.tickers_mentioned,
                            }
                            for item in source_items
                        ]
                    },
                )

        # Apply per-source item limit (e.g., 5 for general news)
        if max_per_source is not None:
            source_items = source_items[:max_per_source]

        for item in source_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                all_items.append(item)

    all_items.sort(key=lambda x: x.published, reverse=True)
    return all_items


def fetch_news(tickers: list[str], cache: Cache | None = None) -> list[NewsItem]:
    """Fetch financial news from RSS feeds and filter by tickers.

    Args:
        tickers: List of stock tickers to search for.
        cache: Optional Cache instance for 30-minute per-source caching.

    Returns:
        List of NewsItem sorted by published date (most recent first).
    """
    return _fetch_from_sources(RSS_SOURCES, cache, filter_tickers=tickers)


def fetch_general_news(cache: Cache | None = None) -> list[NewsItem]:
    """Fetch general-interest news from non-financial RSS feeds.

    Args:
        cache: Optional Cache instance for 30-minute per-source caching.

    Returns:
        List of up to 70 NewsItem sorted by published date (most recent first),
        with at most 5 items per source.
    """
    items = _fetch_from_sources(
        GENERAL_RSS_SOURCES, cache, filter_tickers=None, max_per_source=5
    )
    return items[:70]
