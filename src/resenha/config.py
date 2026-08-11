"""Application settings loaded from environment variables and .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Resenha configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    discord_bot_token: str
    discord_channel_id: int
    gemini_api_key: str
    google_sheet_id: str
    google_sheet_tab: str = "Consolidado"
    cache_db_path: Path = Path("data/resenha.db")
    premarket_hour: int = 7
    eod_hour: int = 19
