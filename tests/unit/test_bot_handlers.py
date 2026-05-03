from types import SimpleNamespace

import pytest

from app.bot.handlers.generate import generate_from_command
from app.bot.handlers.start import handle_start


class FakeMessage:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.from_user = SimpleNamespace(id=123)
        self.answers: list[str] = []

    async def answer(self, text: str, **_: object) -> None:
        self.answers.append(text)


@pytest.mark.asyncio
async def test_start_handler_answers_with_intro() -> None:
    message = FakeMessage()

    await handle_start(message)

    assert "Привет" in message.answers[0]


@pytest.mark.asyncio
async def test_generate_command_answers_with_generated_text(monkeypatch) -> None:
    async def fake_generate_text_with_examples(**_: object) -> str:
        return "Сгенерированный тестовый пост"

    monkeypatch.setattr(
        "app.bot.handlers.generate._generate_text_with_examples",
        fake_generate_text_with_examples,
    )
    message = FakeMessage("/generate пост про завтрак")

    await generate_from_command(message)

    assert "Сгенерированный тестовый пост" in message.answers[0]
