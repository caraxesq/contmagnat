import pytest

from app.core.config import Settings
from app.core.errors import GenerationNotConfiguredError
from app.services.text_generation import (
    AnthropicTextGenerator,
    MockTextGenerator,
    OpenRouterTextGenerator,
    create_text_generator,
)


def test_create_text_generator_defaults_to_mock() -> None:
    generator = create_text_generator(Settings(_env_file=None))

    assert isinstance(generator, MockTextGenerator)


def test_create_text_generator_uses_anthropic_provider_when_configured() -> None:
    generator = create_text_generator(
        Settings(
            _env_file=None,
            TEXT_GENERATION_PROVIDER="anthropic",
            ANTHROPIC_BASE_URL="https://api.gngn.my",
            ANTHROPIC_AUTH_TOKEN="key",
            ANTHROPIC_MODEL="claude-opus-4-7",
        )
    )

    assert isinstance(generator, AnthropicTextGenerator)


def test_create_text_generator_keeps_openrouter_provider_available() -> None:
    generator = create_text_generator(
        Settings(
            _env_file=None,
            TEXT_GENERATION_PROVIDER="openrouter",
            OPENROUTER_API_KEY="key",
            OPENROUTER_CHAT_MODEL="model",
        )
    )

    assert isinstance(generator, OpenRouterTextGenerator)


@pytest.mark.asyncio
async def test_anthropic_provider_without_config_returns_clear_generation_error() -> None:
    generator = create_text_generator(Settings(_env_file=None, TEXT_GENERATION_PROVIDER="anthropic"))

    with pytest.raises(GenerationNotConfiguredError, match="Anthropic"):
        await generator.generate("prompt")
