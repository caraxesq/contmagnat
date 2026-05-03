import pytest

from app.core.errors import GenerationNotConfiguredError
from app.services.generation import GenerationService


class FakeGenerationLogsRepository:
    def __init__(self) -> None:
        self.saved: list[dict[str, str | None]] = []

    async def add_log(
        self,
        *,
        topic: str,
        user_request: str,
        generated_text: str | None,
        status: str,
        custom_topic: str | None = None,
        prompt: str | None = None,
    ) -> object:
        self.saved.append(
            {
                "topic": topic,
                "custom_topic": custom_topic,
                "user_request": user_request,
                "generated_text": generated_text,
                "status": status,
                "prompt": prompt,
            }
        )
        return object()


@pytest.mark.asyncio
async def test_generation_returns_mock_response_and_logs_request() -> None:
    repository = FakeGenerationLogsRepository()
    service = GenerationService(generation_logs_repository=repository)

    result = await service.generate_post(
        topic="отношения",
        user_request="Пост про доверие",
    )

    assert result.status == "ok"
    assert "локальный mock-ответ" in result.generated_text
    assert repository.saved == [
        {
            "topic": "отношения",
            "custom_topic": None,
            "user_request": "Пост про доверие",
            "generated_text": result.generated_text,
            "status": "ok",
            "prompt": repository.saved[0]["prompt"],
        }
    ]
    assert "Пост про доверие" in str(repository.saved[0]["prompt"])


class NotConfiguredTextGenerator:
    async def generate(self, prompt: str) -> str:
        raise GenerationNotConfiguredError("Anthropic generation is not configured")


@pytest.mark.asyncio
async def test_generation_returns_clear_message_when_provider_is_not_configured() -> None:
    service = GenerationService(text_generator=NotConfiguredTextGenerator())

    result = await service.generate_post(
        topic="дом",
        user_request="Пост про уют",
    )

    assert result.status == "error"
    assert "Anthropic generation is not configured" in result.generated_text
