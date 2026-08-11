"""Tests for resenha.news."""

from datetime import datetime
from unittest.mock import patch

import pytest

from resenha.cache import Cache
from resenha.news import NewsItem, fetch_news, fetch_general_news


def _make_feed(entries):
    """Build a fake feedparser result."""

    class FakeFeed:
        def __init__(self, entries):
            self.entries = entries
            self.bozo = False

    return FakeFeed(entries)


def _make_entry(title, link, summary, published_parsed=None):
    class FakeEntry:
        def __init__(self, title, link, summary, published_parsed):
            self.title = title
            self.link = link
            self.summary = summary
            self.published_parsed = published_parsed

    return FakeEntry(title, link, summary, published_parsed)


@patch("resenha.news.feedparser.parse")
def test_fetch_news_filters_by_tickers(mock_parse, tmp_path):
    cache = Cache(db_path=tmp_path / "test_cache.db")

    entries = [
        _make_entry(
            "PETR4 sobe 2%",
            "http://example.com/1",
            "Resumo PETR4",
            (2024, 1, 1, 10, 0, 0),
        ),
        _make_entry(
            "Ibovespa fecha estável",
            "http://example.com/2",
            "Resumo mercado",
            (2024, 1, 1, 9, 0, 0),
        ),
    ]
    mock_parse.return_value = _make_feed(entries)

    result = fetch_news(["PETR4"], cache=cache)

    assert len(result) == 1
    assert result[0].title == "PETR4 sobe 2%"
    assert result[0].tickers_mentioned == ["PETR4"]


@patch("resenha.news.feedparser.parse")
def test_fetch_news_deduplicates_by_url(mock_parse, tmp_path):
    cache = Cache(db_path=tmp_path / "test_cache.db")

    entries1 = [
        _make_entry(
            "PETR4 sobe", "http://example.com/1", "Resumo", (2024, 1, 1, 10, 0, 0)
        ),
    ]
    entries2 = [
        _make_entry(
            "PETR4 sobe copy",
            "http://example.com/1",
            "Resumo2",
            (2024, 1, 1, 11, 0, 0),
        ),
    ]

    mock_parse.side_effect = [
        _make_feed(entries1),
        _make_feed(entries2),
    ]

    result = fetch_news(["PETR4"], cache=cache)

    assert len(result) == 1


@patch("resenha.news.feedparser.parse")
def test_fetch_news_cache_hit(mock_parse, tmp_path):
    cache = Cache(db_path=tmp_path / "test_cache.db")

    entries = [
        _make_entry(
            "VALE3 cai",
            "http://example.com/3",
            "Resumo VALE3",
            (2024, 1, 2, 10, 0, 0),
        ),
    ]
    mock_parse.return_value = _make_feed(entries)

    result1 = fetch_news(["VALE3"], cache=cache)
    assert len(result1) == 1
    assert mock_parse.call_count == 2  # 2 sources fetched

    mock_parse.reset_mock()
    result2 = fetch_news(["VALE3"], cache=cache)
    assert len(result2) == 1
    assert mock_parse.call_count == 0  # all sources served from cache


@patch("resenha.news.feedparser.parse")
def test_fetch_news_graceful_failure(mock_parse, tmp_path):
    cache = Cache(db_path=tmp_path / "test_cache.db")

    mock_parse.side_effect = [
        Exception("Connection error"),
        _make_feed(
            [
                _make_entry(
                    "ITUB4 sobe",
                    "http://example.com/4",
                    "Resumo ITUB4",
                    (2024, 1, 3, 10, 0, 0),
                ),
            ]
        ),
    ]

    result = fetch_news(["ITUB4"], cache=cache)

    assert len(result) == 1
    assert result[0].title == "ITUB4 sobe"


@patch("resenha.news.feedparser.parse")
def test_fetch_news_sorted_by_published(mock_parse, tmp_path):
    cache = Cache(db_path=tmp_path / "test_cache.db")

    entries = [
        _make_entry(
            "BBB antigo", "http://example.com/5", "Resumo BBB", (2024, 1, 1, 10, 0, 0)
        ),
        _make_entry(
            "BBB recente",
            "http://example.com/6",
            "Resumo BBB",
            (2024, 1, 3, 10, 0, 0),
        ),
        _make_entry(
            "BBB médio", "http://example.com/7", "Resumo BBB", (2024, 1, 2, 10, 0, 0)
        ),
    ]
    mock_parse.return_value = _make_feed(entries)

    result = fetch_news(["BBB"], cache=cache)

    assert len(result) == 3
    assert result[0].title == "BBB recente"
    assert result[1].title == "BBB médio"
    assert result[2].title == "BBB antigo"


@patch("resenha.news.feedparser.parse")
def test_fetch_general_news_includes_all_items(mock_parse, tmp_path):
    cache = Cache(db_path=tmp_path / "test_cache.db")

    entries = [
        _make_entry(
            f"Título {i}",
            f"http://example.com/gen{i}",
            f"Resumo {i}",
            (2024, 1, i + 1, 10, 0, 0),
        )
        for i in range(3)
    ]
    mock_parse.return_value = _make_feed(entries)

    result = fetch_general_news(cache=cache)

    assert len(result) == 3
    for item in result:
        assert item.tickers_mentioned == []


@patch.dict(
    "resenha.news.GENERAL_RSS_SOURCES",
    {
        "SourceA": "http://a.example.com/rss",
        "SourceB": "http://b.example.com/rss",
    },
    clear=True,
)
@patch("resenha.news.feedparser.parse")
def test_fetch_general_news_deduplicates(mock_parse, tmp_path):
    cache = Cache(db_path=tmp_path / "test_cache.db")

    entries1 = [
        _make_entry(
            "Notícia duplicada",
            "http://example.com/same-url",
            "Resumo 1",
            (2024, 1, 1, 10, 0, 0),
        ),
    ]
    entries2 = [
        _make_entry(
            "Notícia duplicada copy",
            "http://example.com/same-url",
            "Resumo 2",
            (2024, 1, 1, 11, 0, 0),
        ),
    ]

    # 2 sources, first two share the same URL — expect dedup
    mock_parse.side_effect = [
        _make_feed(entries1),
        _make_feed(entries2),
    ]

    result = fetch_general_news(cache=cache)

    assert len(result) == 1


@patch.dict(
    "resenha.news.GENERAL_RSS_SOURCES",
    {
        "SourceA": "http://a.example.com/rss",
        "SourceB": "http://b.example.com/rss",
    },
    clear=True,
)
@patch("resenha.news.feedparser.parse")
def test_fetch_general_news_per_source_limit(mock_parse, tmp_path):
    """Each general source contributes at most 5 items (B-019)."""
    cache = Cache(db_path=tmp_path / "test_cache.db")

    entries_a = [
        _make_entry(
            f"A-{i}",
            f"http://a.example.com/{i}",
            f"Summary A-{i}",
            (2024, 1, i + 1, 10, 0, 0),
        )
        for i in range(8)
    ]
    entries_b = [
        _make_entry(
            f"B-{i}",
            f"http://b.example.com/{i}",
            f"Summary B-{i}",
            (2024, 1, i + 1, 10, 0, 0),
        )
        for i in range(8)
    ]
    mock_parse.side_effect = [
        _make_feed(entries_a),
        _make_feed(entries_b),
    ]

    result = fetch_general_news(cache=cache)

    # 5 per source × 2 sources = 10 max (all URLs unique, no dedup expected)
    assert len(result) <= 10
    assert len(result) == 10
