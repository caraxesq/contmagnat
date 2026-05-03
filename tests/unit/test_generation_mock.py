import pytest

from app.services.generation import GenerationService


class FakeTextGenerator:
    async def generate(self, prompt: str) -> str:
        return f"generated from: {prompt[:20]}"


@pytest.mark.asyncio
async def test_generation_uses_text_generator_when_available() -> None:
    service = GenerationService(text_generator=FakeTextGenerator())

    result = await service.generate_post(
        topic="кулинария",
        user_request="Пост про завтрак",
    )

    assert result.status == "ok"
    assert result.generated_text.startswith("generated from:")
