"""Tests for resenha.delivery.ResenhaBot."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest


async def test_send_briefing() -> None:
    """send_briefing fetches channel and sends embeds."""
    with patch("resenha.delivery.discord.Embed") as mock_embed_cls:
        from resenha.delivery import ResenhaBot

        bot = ResenhaBot(token="mock-token")

        mock_channel = AsyncMock()
        bot.get_channel = MagicMock(return_value=mock_channel)

        mock_embed = MagicMock()
        await bot.send_briefing(channel_id=12345, embeds=[mock_embed])

        bot.get_channel.assert_called_once_with(12345)
        mock_channel.send.assert_awaited_once_with(embed=mock_embed)


async def test_on_ready_logs(caplog: pytest.LogCaptureFixture) -> None:
    """on_ready logs the bot user name."""
    from resenha.delivery import ResenhaBot

    with patch.object(ResenhaBot, "user", new_callable=PropertyMock) as mock_user:
        mock_user.return_value = "TestBot#1234"
        bot = ResenhaBot(token="mock-token")

        with caplog.at_level("INFO", logger="resenha.delivery"):
            await bot.on_ready()

    assert "Logged in as TestBot#1234" in caplog.text


async def test_send_briefing_retries_on_failure():
    """send_briefing retries up to 3 times with exponential backoff."""
    import asyncio

    from resenha.delivery import ResenhaBot

    import discord

    bot = ResenhaBot(token="mock-token")

    mock_channel = AsyncMock()
    # channel.send fails twice then succeeds
    mock_msg = MagicMock()
    mock_msg.id = 42
    mock_channel.send = AsyncMock(
        side_effect=[discord.HTTPException(MagicMock(), "fail1"),
                      discord.HTTPException(MagicMock(), "fail2"),
                      mock_msg]
    )
    bot.get_channel = MagicMock(return_value=mock_channel)

    mock_embed = MagicMock()

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await bot.send_briefing(channel_id=12345, embeds=[mock_embed])

    # Send should have been called 3 times
    assert mock_channel.send.await_count == 3
    # sleep should have been called twice (2s, 4s)
    assert mock_sleep.await_count == 2


async def test_send_briefing_exhausts_retries():
    """send_briefing raises after exhausting all retries."""
    import asyncio

    from resenha.delivery import ResenhaBot

    import discord

    bot = ResenhaBot(token="mock-token")

    mock_channel = AsyncMock()
    # channel.send always fails
    mock_channel.send = AsyncMock(
        side_effect=discord.HTTPException(MagicMock(), "always fail")
    )
    bot.get_channel = MagicMock(return_value=mock_channel)

    mock_embed = MagicMock()

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(discord.HTTPException):
            await bot.send_briefing(channel_id=12345, embeds=[mock_embed])

    # Send should have been called 3 times
    assert mock_channel.send.await_count == 3
    # sleep should have been called twice (2s, 4s)
    assert mock_sleep.await_count == 2
