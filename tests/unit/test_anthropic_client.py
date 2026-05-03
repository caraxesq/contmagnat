import pytest

from app.clients.anthropic import AnthropicClient
from app.core.config import Settings
from app.core.errors import GenerationNotConfiguredError


def test_settings_can_ignore_local_env_for_unit_tests() -> None:
    settings = Settings(_env_file=None)

    assert settings.text_generation_provider == "mock"


def test_anthropic_client_builds_messages_url_from_base_url() -> None:
    client = AnthropicClient(
        Settings(
            _env_file=None,
            ANTHROPIC_BASE_URL="https://api.gngn.my",
            ANTHROPIC_AUTH_TOKEN="token",
            ANTHROPIC_MODEL="claude-opus-4-7",
        )
    )

    assert client.base_url == "https://api.gngn.my"
    assert client.messages_path == "/v1/messages"


def test_anthropic_client_prefers_auth_token_over_api_key() -> None:
    client = AnthropicClient(
        Settings(
            _env_file=None,
            ANTHROPIC_BASE_URL="https://api.gngn.my",
            ANTHROPIC_AUTH_TOKEN="auth-token",
            ANTHROPIC_API_KEY="api-key",
            ANTHROPIC_MODEL="claude-opus-4-7",
        )
    )

    headers = client.headers()

    assert headers["x-api-key"] == "auth-token"
    assert headers["Authorization"] == "Bearer auth-token"


def test_anthropic_client_falls_back_to_api_key() -> None:
    client = AnthropicClient(
        Settings(
            _env_file=None,
            ANTHROPIC_BASE_URL="https://api.gngn.my",
            ANTHROPIC_API_KEY="api-key",
            ANTHROPIC_MODEL="claude-opus-4-7",
        )
    )

    headers = client.headers()

    assert headers["x-api-key"] == "api-key"
    assert headers["Authorization"] == "Bearer api-key"


@pytest.mark.asyncio
async def test_anthropic_client_requires_base_url_token_and_model() -> None:
    client = AnthropicClient(Settings(_env_file=None, ANTHROPIC_BASE_URL="", ANTHROPIC_MODEL=""))

    with pytest.raises(GenerationNotConfiguredError, match="base URL, token and model"):
        await client.create_message("hello")
