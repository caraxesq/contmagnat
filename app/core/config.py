from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    storage_backend: str = Field(default="memory", alias="STORAGE_BACKEND")
    training_data_dir: str = Field(default="data/training", alias="TRAINING_DATA_DIR")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=False, alias="API_RELOAD")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/contmagnat",
        alias="DATABASE_URL",
    )
    allowed_telegram_user_ids_raw: str = Field(
        default="",
        alias="ALLOWED_TELEGRAM_USER_IDS",
    )
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")

    text_generation_provider: str = Field(default="mock", alias="TEXT_GENERATION_PROVIDER")
    anthropic_base_url: str = Field(default="https://api.anthropic.com", alias="ANTHROPIC_BASE_URL")
    anthropic_auth_token: str = Field(default="", alias="ANTHROPIC_AUTH_TOKEN")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="", alias="ANTHROPIC_MODEL")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_chat_model: str = Field(default="", alias="OPENROUTER_CHAT_MODEL")
    openrouter_embedding_model: str = Field(default="", alias="OPENROUTER_EMBEDDING_MODEL")
    openrouter_embedding_dimensions: int = Field(
        default=1536,
        alias="OPENROUTER_EMBEDDING_DIMENSIONS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def allowed_telegram_user_ids(self) -> tuple[int, ...]:
        if not self.allowed_telegram_user_ids_raw:
            return ()
        return tuple(
            int(item.strip())
            for item in self.allowed_telegram_user_ids_raw.split(",")
            if item.strip()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
