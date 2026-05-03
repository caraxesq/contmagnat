import logging
from typing import Protocol

from app.clients.anthropic import AnthropicClient
from app.clients.openrouter import OpenRouterClient
from app.core.config import Settings

logger = logging.getLogger(__name__)


class TextGenerator(Protocol):
    async def generate(self, prompt: str) -> str:
        pass


class MockTextGenerator:
    async def generate(self, prompt: str) -> str:
        logger.info("Using mock text generator")
        return (
            "Сгенерированный тестовый пост:\n\n"
            "Вот черновик поста по вашему запросу. OpenRouter пока не настроен, "
            "поэтому это локальный mock-ответ для проверки e2e сценария."
        )


class OpenRouterTextGenerator:
    def __init__(self, client: OpenRouterClient) -> None:
        self.client = client

    async def generate(self, prompt: str) -> str:
        return await self.client.create_chat_completion(prompt)


class AnthropicTextGenerator:
    def __init__(self, client: AnthropicClient) -> None:
        self.client = client

    async def generate(self, prompt: str) -> str:
        return await self.client.create_message(prompt)


def create_text_generator(settings: Settings) -> TextGenerator:
    provider = settings.text_generation_provider.strip().lower()
    if provider == "anthropic":
        logger.info("Using Anthropic text generator")
        return AnthropicTextGenerator(AnthropicClient(settings))
    if provider == "openrouter" or (
        provider != "mock" and settings.openrouter_api_key and settings.openrouter_chat_model
    ):
        logger.info("Using OpenRouter text generator")
        return OpenRouterTextGenerator(OpenRouterClient(settings))
    return MockTextGenerator()
