"""Discord reaction event listener for Resenha.

Ties ReactionTracker to discord.py's on_reaction_add event.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import discord

from resenha.reactions import ReactionTracker

logger = logging.getLogger(__name__)

EMOJI_MAP: dict[str, str] = {
    "\U0001f44d": "up",       # 👍
    "\U0001f44e": "down",     # 👎
    "\u2764\ufe0f": "love",   # ❤️
    "\U0001f525": "fire",     # 🔥
}


class ReactionListener:
    """Listens for Discord reaction events and tracks them via ReactionTracker."""

    def __init__(
        self,
        tracker: ReactionTracker,
        registry_path: str | Path = "data/briefing_registry.json",
    ) -> None:
        self._tracker = tracker
        self._registry_path = Path(registry_path)
        self._registry: dict[str, dict] = self.load_registry(self._registry_path)

    @staticmethod
    def load_registry(path: Path) -> dict[str, dict]:
        """Load the briefing registry from a JSON file."""
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return json.load(f)  # type: ignore[no-any-return]

    async def on_reaction_add(self, reaction: "discord.Reaction", user: "discord.User") -> None:
        """Handle a reaction add event from Discord.

        Skips bot users and unknown emojis. Looks up the message in the
        briefing registry to determine the asset ticker and embed index.
        """
        if user.bot:
            return

        emoji_str = str(reaction.emoji)
        label = EMOJI_MAP.get(emoji_str)
        if label is None:
            return

        message_id = reaction.message.id
        message_id_str = str(message_id)

        entry = self._registry.get(message_id_str, {})
        asset_ticker = entry.get("asset_ticker", "")
        embed_index = entry.get("embed_index", 0)
        briefing_run_id = entry.get("briefing_run_id", "")

        self._tracker.track(
            briefing_run_id=briefing_run_id,
            message_id=message_id,
            embed_index=embed_index,
            asset_ticker=asset_ticker,
            reaction=label,
            user_id=user.id,
        )

        logger.debug(
            "Tracked reaction: %s on msg %d ticker=%s",
            label,
            message_id,
            asset_ticker,
        )
