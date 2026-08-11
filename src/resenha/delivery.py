"""Discord delivery scaffold for Resenha."""

import asyncio
import logging
from typing import cast

import discord

logger = logging.getLogger(__name__)


class ResenhaBot(discord.Client):
    """Lightweight discord.py client for delivering briefings."""

    def __init__(self, token: str) -> None:
        self.token = token
        super().__init__(intents=discord.Intents.default())

    async def on_ready(self) -> None:
        logger.info(f"Logged in as {self.user}")

    async def send_briefing(
        self,
        channel_id: int,
        embeds: list[discord.Embed],
    ) -> list[int]:
        channel = self.get_channel(channel_id)
        if channel is None:
            logger.warning(f"Channel {channel_id} not found")
            return []
        message_ids: list[int] = []
        for embed in embeds:
            last_exception = None
            for attempt in range(3):
                try:
                    msg = await cast(discord.abc.Messageable, channel).send(embed=embed)
                    message_ids.append(msg.id)
                    break
                except discord.HTTPException as e:
                    last_exception = e
                    if attempt < 2:  # Not the last attempt
                        delay = 2 ** (attempt + 1)  # 2, 4
                        logger.warning(
                            f"Retry {attempt + 1}/3 after {delay}s: {e}"
                        )
                        await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All retries exhausted sending embed: {last_exception}"
                )
                raise cast(Exception, last_exception)
        return message_ids

    async def close(self) -> None:
        await super().close()


async def run_bot(token: str, channel_id: int, embeds: list) -> list[int]:
    """Create bot, connect, send briefing, and disconnect. Returns sent message IDs."""
    bot = ResenhaBot(token=token)

    _original_on_ready = bot.on_ready
    message_ids: list[int] = []

    async def on_ready() -> None:
        await _original_on_ready()
        ids = await bot.send_briefing(channel_id, embeds)
        message_ids.extend(ids)
        await bot.close()

    setattr(bot, "on_ready", on_ready)
    await bot.start(token)
    return message_ids
