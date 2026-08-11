"""Tests for resenha.summary module."""

from unittest.mock import MagicMock, patch

import discord
import pytest

from resenha.assembler import BriefingContext
from resenha.gemini import GeminiClient
from resenha.summary import generate_briefing, generate_embeds


@patch("resenha.summary.build_briefing_prompt")
def test_generate_briefing_calls_gemini_and_prompts(mock_build_prompt):
    mock_build_prompt.return_value = "mocked prompt"

    ctx = MagicMock(spec=BriefingContext)
    gemini = MagicMock(spec=GeminiClient)
    gemini.generate.return_value = "mocked briefing text"

    result = generate_briefing(ctx, gemini, "pre-market")

    mock_build_prompt.assert_called_once_with(ctx, "pre-market", previous_briefing=None)
    gemini.generate.assert_called_once_with("mocked prompt", max_tokens=4000)
    assert result == "mocked briefing text"


@patch("resenha.summary.build_briefing_prompt")
def test_generate_briefing_passes_previous_briefing(mock_build_prompt):
    mock_build_prompt.return_value = "mocked prompt with previous"

    ctx = MagicMock(spec=BriefingContext)
    gemini = MagicMock(spec=GeminiClient)
    gemini.generate.return_value = "mocked briefing text"

    result = generate_briefing(ctx, gemini, "eod", previous_briefing="previous text")

    mock_build_prompt.assert_called_once_with(ctx, "eod", previous_briefing="previous text")
    gemini.generate.assert_called_once_with("mocked prompt with previous", max_tokens=4000)
    assert result == "mocked briefing text"


def test_generate_embeds_splits_text():
    text = (
        "## ITUB4\nSome news about ITUB4.\nMore lines.\n"
        "## BBDC4\nSome news about BBDC4.\n"
        "## PETR4\nSome news about PETR4.\n"
    )

    embeds = generate_embeds(text)

    assert isinstance(embeds, list)
    assert len(embeds) == 3
    for embed in embeds:
        assert isinstance(embed, discord.Embed)
        assert embed.title is not None
        assert embed.description is not None
        assert len(embed.description) <= 4096


def test_generate_embeds_limits_to_ten():
    lines = []
    for i in range(15):
        lines.append(f"## TICKER{i}")
        lines.append(f"Content for ticker {i}")
    text = "\n".join(lines)

    embeds = generate_embeds(text)

    assert len(embeds) == 10


def test_generate_embeds_macro_gets_green_color():
    """Section with SELIC header gets macro green color."""
    text = "## SELIC\nMacro economic content."

    embeds = generate_embeds(text)

    assert len(embeds) == 1
    assert embeds[0].color == discord.Color(0x2ECC71)


def test_generate_embeds_portfolio_gets_blue_color():
    """Section with IBOV header gets portfolio blue color."""
    text = "## IBOV\nPortfolio content."

    embeds = generate_embeds(text)

    assert len(embeds) == 1
    assert embeds[0].color == discord.Color(0x3498DB)


def test_generate_embeds_news_gets_orange_color():
    """Random section header gets news orange color."""
    text = "## XYZ\nSome random news."

    embeds = generate_embeds(text)

    assert len(embeds) == 1
    assert embeds[0].color == discord.Color(0xE67E22)


def test_generate_embeds_has_timestamp_and_footer():
    """Generated embeds have timestamp and footer."""
    text = "## Section\nContent."

    embeds = generate_embeds(text)

    assert len(embeds) == 1
    embed = embeds[0]
    assert embed.timestamp is not None
    assert embed.footer.text == "Resenha · Seu briefing diário"


def test_generate_embeds_has_author():
    """Generated embeds have author set to Resenha."""
    text = "## Section\nContent."

    embeds = generate_embeds(text)

    assert len(embeds) == 1
    embed = embeds[0]
    assert embed.author.name == "Resenha"
