from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    discord_token: str = Field(alias="DISCORD_TOKEN")
    database_url: str = Field(default="sqlite+aiosqlite:///./lunar_bot.db", alias="DATABASE_URL")
    guild_id: int | None = Field(default=None, alias="GUILD_ID")


settings = Settings()
