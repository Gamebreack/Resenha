"""Price fetching with caching via yfinance."""

import yfinance as yf  # type: ignore[import-untyped]

from resenha.cache import Cache


def fetch_price(ticker: str, cache: Cache | None = None) -> dict:
    """Fetch price data for a B3 ticker, appending .SA for yfinance."""
    ticker_sa = f"{ticker}.SA"

    if cache is not None:
        cached = cache.get(ticker_sa, ttl_seconds=3600)
        if cached is not None:
            return cached

    try:
        info = yf.Ticker(ticker_sa).info
        result = {
            "price": info.get("regularMarketPrice"),
            "change_pct": info.get("regularMarketChangePercent"),
            "volume": info.get("regularMarketVolume"),
            "high_52w": info.get("fiftyTwoWeekHigh"),
            "low_52w": info.get("fiftyTwoWeekLow"),
        }
    except Exception:
        if cache is not None:
            stale = cache._conn.execute(
                "SELECT value FROM cache WHERE key = ?", (ticker_sa,)
            ).fetchone()
            if stale is not None:
                import json

                return json.loads(stale[0])  # type: ignore[no-any-return]
        raise

    if cache is not None:
        cache.set(ticker_sa, result)

    return result
