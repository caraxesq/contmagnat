from types import SimpleNamespace

import pytest

from app.bot.handlers.generate import (
    choose_user_topic,
    generate_post,
    regenerate_post,
    save_edited_post,
    start_editing,
    start_generation,
    start_topic_selection,
)
from app.bot.handlers.start import back_to_main_menu, handle_about, handle_start
from app.bot.states import UserFlowStates
from app.core.constants import BACK_TO_MAIN_MENU, MAIN_MENU_GENERATE


class FakeMessage:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.from_user = SimpleNamespace(id=123)
        self.answers: list[tuple[str, dict[str, object]]] = []

    async def answer(self, text: str, **kwargs: object) -> None:
        self.answers.append((text, kwargs))


class FakeState:
    def __init__(self, data: dict[str, object] | None = None) -> None:
        self.data = data or {}
        self.state = None
        self.cleared = False

    async def set_state(self, state) -> None:
        self.state = state

    async def update_data(self, **kwargs: object) -> None:
        self.data.update(kwargs)

    async def get_data(self) -> dict[str, object]:
        return dict(self.data)

    async def clear(self) -> None:
        self.cleared = True
        self.data = {}
        self.state = None


@pytest.mark.asyncio
async def test_start_handler_answers_with_full_main_menu() -> None:
    message = FakeMessage()

    await handle_start(message)

    assert "Привет" in message.answers[0][0]
    assert message.answers[0][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_back_to_main_menu_clears_state_and_shows_menu() -> None:
    message = FakeMessage(BACK_TO_MAIN_MENU)
    state = FakeState({"selected_topic": "дом"})

    await back_to_main_menu(message, state)

    assert state.cleared is True
    assert "Главное меню" in message.answers[0][0]


@pytest.mark.asyncio
async def test_about_handler_describes_bot() -> None:
    message = FakeMessage()

    await handle_about(message)

    assert "генерировать" in message.answers[0][0].lower()


@pytest.mark.asyncio
async def test_topic_selection_saves_topic_in_user_state() -> None:
    message = FakeMessage("дом")
    state = FakeState()

    await start_topic_selection(FakeMessage(), state)
    await choose_user_topic(message, state)

    assert state.data["selected_topic"] == "дом"
    assert state.data["custom_topic"] is None
    assert state.state is None
    assert "дом" in message.answers[0][0]


@pytest.mark.asyncio
async def test_topic_selection_saves_profile_scope(monkeypatch, tmp_path) -> None:
    from app.services.topic_registry import TopicRegistry
    from app.bot.handlers import generate

    TopicRegistry(tmp_path).add_profile("Канал красоты")
    monkeypatch.setattr(generate, "training_data_dir", lambda: tmp_path)
    message = FakeMessage("Профиль: Канал красоты")
    state = FakeState()

    await choose_user_topic(message, state)

    assert state.data["selected_topic"] == "Канал красоты"
    assert state.data["style_scope"] == "profile"


@pytest.mark.asyncio
async def test_generation_without_topic_routes_to_topic_selection() -> None:
    message = FakeMessage(MAIN_MENU_GENERATE)
    state = FakeState()

    await start_generation(message, state)

    assert state.state == UserFlowStates.choosing_topic_for_generation
    assert "Выберите тематику" in message.answers[0][0]


@pytest.mark.asyncio
async def test_generation_saves_last_request_and_generated_text(monkeypatch) -> None:
    async def fake_generate_text_with_examples(**_: object) -> str:
        return "Готовый пост"

    monkeypatch.setattr(
        "app.bot.handlers.generate._generate_text_with_examples",
        fake_generate_text_with_examples,
    )
    message = FakeMessage("Пост про уют")
    state = FakeState({"selected_topic": "дом", "custom_topic": None})

    await generate_post(message, state)

    assert state.data["last_user_request"] == "Пост про уют"
    assert state.data["last_generated_text"] == "Готовый пост"
    assert state.state is None
    assert "Готовый пост" in message.answers[0][0]


@pytest.mark.asyncio
async def test_editing_updates_last_generated_text() -> None:
    state = FakeState({"last_generated_text": "Старый текст"})

    await start_editing(FakeMessage(), state)
    await save_edited_post(FakeMessage("Новый текст"), state)

    assert state.data["last_generated_text"] == "Новый текст"
    assert state.state is None


@pytest.mark.asyncio
async def test_regenerate_uses_previous_topic_and_request(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    async def fake_generate_text_with_examples(**kwargs: object) -> str:
        calls.append(kwargs)
        return "Новый вариант"

    monkeypatch.setattr(
        "app.bot.handlers.generate._generate_text_with_examples",
        fake_generate_text_with_examples,
    )
    message = FakeMessage()
    state = FakeState(
        {
            "selected_topic": "красота",
            "custom_topic": None,
            "last_user_request": "Пост про уход",
        }
    )

    await regenerate_post(message, state)

    assert calls[0]["topic"] == "красота"
    assert calls[0]["user_request"] == "Пост про уход"
    assert calls[0]["style_scope"] == "topic"
    assert state.data["last_generated_text"] == "Новый вариант"


@pytest.mark.asyncio
async def test_generation_passes_profile_scope_to_generator(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    async def fake_generate_text_with_examples(**kwargs: object) -> str:
        calls.append(kwargs)
        return "Профильный текст"

    monkeypatch.setattr(
        "app.bot.handlers.generate._generate_text_with_examples",
        fake_generate_text_with_examples,
    )
    state = FakeState(
        {"selected_topic": "Канал красоты", "custom_topic": None, "style_scope": "profile"}
    )

    await generate_post(FakeMessage("Пост"), state)

    assert calls[0]["style_scope"] == "profile"


@pytest.mark.asyncio
async def test_generate_text_uses_rag_examples(monkeypatch, tmp_path) -> None:
    from app.bot.handlers import generate
    from app.db.file_storage import FilePostsRepository, FileGenerationLogsRepository

    class Bundle:
        def __init__(self) -> None:
            self.posts = FilePostsRepository(tmp_path)
            self.generation_logs = FileGenerationLogsRepository(tmp_path)

        async def commit(self) -> None:
            return None

    class BundleContext:
        async def __aenter__(self):
            return Bundle()

        async def __aexit__(self, *_):
            return None

    captured: dict[str, object] = {}

    class FakeGenerationService:
        def __init__(self, **_: object) -> None:
            pass

        async def generate_post(self, **kwargs: object):
            captured.update(kwargs)
            return type("Result", (), {"generated_text": "ok"})()

    repository = FilePostsRepository(tmp_path)
    await repository.add_post(topic="дом", text="Пост про уютный завтрак дома")
    monkeypatch.setattr(generate, "training_data_dir", lambda: tmp_path)
    monkeypatch.setattr(generate, "repository_bundle", lambda: BundleContext())
    monkeypatch.setattr(generate, "GenerationService", FakeGenerationService)

    result = await generate._generate_text_with_examples(
        topic="дом",
        custom_topic=None,
        user_request="завтрак",
        style_scope="topic",
    )

    assert result == "ok"
    assert captured["style_examples"] == ["Пост про уютный завтрак дома"]
