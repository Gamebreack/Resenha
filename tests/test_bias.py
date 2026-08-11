"""Tests for resenha.bias."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from resenha.bias import annotate_news, infer_source_bias
from resenha.gemini import GeminiClient
from resenha.news import NewsItem


def test_infer_source_bias_calls_gemini():
    gemini = MagicMock(spec=GeminiClient)
    gemini.generate.return_value = "center-right business bias"

    result = infer_source_bias("InfoMoney", gemini)

    gemini.generate.assert_called_once()
    call_args = gemini.generate.call_args
    prompt = call_args[0][0] if call_args[0] else call_args[1]["prompt"]
    assert "InfoMoney" in prompt
    assert result == "center-right business bias"


def test_infer_source_bias_uses_cache():
    gemini = MagicMock(spec=GeminiClient)
    gemini.generate.return_value = "center-right business bias"

    cache = MagicMock()
    cache.get.return_value = None

    result1 = infer_source_bias("InfoMoney", gemini, cache=cache)
    assert result1 == "center-right business bias"
    assert gemini.generate.call_count == 1

    # Second call: cache returns the stored value
    cache.get.return_value = {"bias": "center-right business bias"}
    result2 = infer_source_bias("InfoMoney", gemini, cache=cache)
    assert result2 == "center-right business bias"
    assert gemini.generate.call_count == 1


def test_annotate_news_queries_unique_sources():
    gemini = MagicMock(spec=GeminiClient)
    gemini.generate.return_value = "some bias"

    news = [
        NewsItem(
            title="T1", url="http://a", source="InfoMoney",
            published=datetime.now(), summary="", tickers_mentioned=[],
        ),
        NewsItem(
            title="T2", url="http://b", source="Seu Dinheiro",
            published=datetime.now(), summary="", tickers_mentioned=[],
        ),
        NewsItem(
            title="T3", url="http://c", source="InfoMoney",
            published=datetime.now(), summary="", tickers_mentioned=[],
        ),
    ]

    result = annotate_news(news, gemini)

    assert gemini.generate.call_count == 2
    assert set(result.keys()) == {"InfoMoney", "Seu Dinheiro"}


def test_infer_source_bias_returns_unknown_on_failure():
    gemini = MagicMock(spec=GeminiClient)
    gemini.generate.side_effect = Exception("API error")

    result = infer_source_bias("InfoMoney", gemini)

    assert result == "unknown"
