"""Tests for resenha.listener.ReactionListener."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest


class TestEmojiMapping:
    """Tests for emoji-to-reaction-label mapping."""

    def test_emoji_mapping_known_emojis(self):
        """Known emojis map to correct labels."""
        from resenha.listener import EMOJI_MAP

        assert EMOJI_MAP["\U0001f44d"] == "up"       # 👍
        assert EMOJI_MAP["\U0001f44e"] == "down"     # 👎
        assert EMOJI_MAP["\u2764\ufe0f"] == "love"   # ❤️
        assert EMOJI_MAP["\U0001f525"] == "fire"     # 🔥

    def test_emoji_mapping_unknown_returns_none(self):
        """Unknown emoji is not in the mapping."""
        from resenha.listener import EMOJI_MAP

        assert "\U0001f921" not in EMOJI_MAP  # 🤡


class TestReactionListener:
    """Tests for ReactionListener.on_reaction_add."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock ReactionTracker."""
        from unittest.mock import MagicMock
        tracker = MagicMock()
        tracker.track = MagicMock()
        return tracker

    @pytest.fixture
    def mock_registry(self):
        """Mock a briefing registry dict."""
        return {
            "100": {"asset_ticker": "ITUB4", "embed_index": 0},
            "101": {"asset_ticker": "BBDC4", "embed_index": 1},
        }

    @pytest.fixture
    def listener(self, mock_tracker, mock_registry, tmp_path):
        """Create ReactionListener with mock tracker."""
        from resenha.listener import ReactionListener

        # Write registry to temp file
        import json
        registry_path = tmp_path / "briefing_registry.json"
        registry_path.write_text(json.dumps(mock_registry))

        listener = ReactionListener(tracker=mock_tracker, registry_path=registry_path)
        return listener

    @pytest.mark.asyncio
    async def test_on_reaction_add_calls_track(self, listener, mock_tracker):
        """on_reaction_add calls tracker.track() with correct args."""
        # Mock reaction
        reaction = MagicMock()
        reaction.message.id = 100
        reaction.emoji = "\U0001f44d"  # 👍

        # Mock user
        user = MagicMock()
        type(user).bot = PropertyMock(return_value=False)
        user.id = 789

        await listener.on_reaction_add(reaction, user)

        mock_tracker.track.assert_called_once_with(
            briefing_run_id="",
            message_id=100,
            embed_index=0,
            asset_ticker="ITUB4",
            reaction="up",
            user_id=789,
        )

    @pytest.mark.asyncio
    async def test_on_reaction_add_skips_unknown_emoji(self, listener, mock_tracker):
        """on_reaction_add skips unknown emoji and does not call track()."""
        reaction = MagicMock()
        reaction.message.id = 100
        reaction.emoji = "\U0001f921"  # 🤡 (clown)

        user = MagicMock()
        type(user).bot = PropertyMock(return_value=False)
        user.id = 789

        await listener.on_reaction_add(reaction, user)

        mock_tracker.track.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_reaction_add_skips_bot_user(self, listener, mock_tracker):
        """on_reaction_add skips reactions from bot users."""
        reaction = MagicMock()
        reaction.message.id = 100
        reaction.emoji = "\U0001f44d"  # 👍

        user = MagicMock()
        type(user).bot = PropertyMock(return_value=True)

        await listener.on_reaction_add(reaction, user)

        mock_tracker.track.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_reaction_add_unknown_message_id(self, mock_tracker, tmp_path):
        """If message_id not in registry, still tracks with empty asset_ticker."""
        import json
        from resenha.listener import ReactionListener

        registry_path = tmp_path / "briefing_registry.json"
        registry_path.write_text(json.dumps({}))

        listener = ReactionListener(tracker=mock_tracker, registry_path=registry_path)

        reaction = MagicMock()
        reaction.message.id = 999  # not in registry
        reaction.emoji = "\U0001f44d"  # 👍

        user = MagicMock()
        type(user).bot = PropertyMock(return_value=False)
        user.id = 789

        await listener.on_reaction_add(reaction, user)

        mock_tracker.track.assert_called_once_with(
            briefing_run_id="",
            message_id=999,
            embed_index=0,
            asset_ticker="",
            reaction="up",
            user_id=789,
        )

    @pytest.mark.asyncio
    async def test_on_reaction_add_love_emoji(self, listener, mock_tracker):
        """❤️ emoji maps to 'love'."""
        reaction = MagicMock()
        reaction.message.id = 100
        reaction.emoji = "\u2764\ufe0f"  # ❤️

        user = MagicMock()
        type(user).bot = PropertyMock(return_value=False)
        user.id = 123

        await listener.on_reaction_add(reaction, user)

        mock_tracker.track.assert_called_once()
        call_args = mock_tracker.track.call_args[1]
        assert call_args["reaction"] == "love"

    @pytest.mark.asyncio
    async def test_on_reaction_add_fire_emoji(self, listener, mock_tracker):
        """🔥 emoji maps to 'fire'."""
        reaction = MagicMock()
        reaction.message.id = 100
        reaction.emoji = "\U0001f525"  # 🔥

        user = MagicMock()
        type(user).bot = PropertyMock(return_value=False)
        user.id = 123

        await listener.on_reaction_add(reaction, user)

        call_args = mock_tracker.track.call_args[1]
        assert call_args["reaction"] == "fire"
