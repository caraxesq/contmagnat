from types import SimpleNamespace

import pytest

from app.bot.handlers import admin
from app.bot.handlers.admin import (
    add_admin_profile,
    add_admin_topic,
    check_admin_password,
    choose_admin_topic,
    choose_profile,
    delete_admin_post,
    save_admin_posts,
    save_and_train,
    show_admin_posts,
    show_profile_posts,
    start_admin,
    start_admin_topic_creation,
    start_admin_profile_creation,
    start_admin_profile_posts_upload,
    start_admin_profile_selection,
    start_admin_topic_selection,
)
from app.bot.states import AdminFlowStates
from app.db.memory import posts_repository


@pytest.fixture(autouse=True)
def reset_admin_flow_state(monkeypatch, tmp_path) -> None:
    admin.authorized_admin_user_ids.clear()
    posts_repository.posts.clear()
    posts_repository._next_id = 1
    monkeypatch.setattr(admin, "training_data_dir", lambda: tmp_path)


class FakeMessage:
    def __init__(self, text: str = "", user_id: int = 123, caption: str | None = None) -> None:
        self.text = text
        self.caption = caption
        self.forward_origin = None
        self.from_user = SimpleNamespace(id=user_id)
        self.answers: list[tuple[str, dict[str, object]]] = []

    async def answer(self, text: str, **kwargs: object) -> None:
        self.answers.append((text, kwargs))


class FakeCallback:
    def __init__(self, data: str, user_id: int = 123) -> None:
        self.data = data
        self.from_user = SimpleNamespace(id=user_id)
        self.message = FakeMessage(user_id=user_id)
        self.alerts: list[tuple[str, dict[str, object]]] = []

    async def answer(self, text: str = "", **kwargs: object) -> None:
        self.alerts.append((text, kwargs))


class FakeState:
    def __init__(self, data: dict[str, object] | None = None) -> None:
        self.data = data or {}
        self.state = None

    async def set_state(self, state) -> None:
        self.state = state

    async def update_data(self, **kwargs: object) -> None:
        self.data.update(kwargs)

    async def get_data(self) -> dict[str, object]:
        return dict(self.data)


@pytest.mark.asyncio
async def test_wrong_admin_password_keeps_admin_closed(monkeypatch) -> None:
    monkeypatch.setattr(admin, "get_admin_password", lambda: "secret")
    message = FakeMessage("bad")
    state = FakeState()

    await check_admin_password(message, state)

    assert 123 not in admin.authorized_admin_user_ids
    assert state.state == AdminFlowStates.entering_password
    assert "Неверный пароль" in message.answers[0][0]


@pytest.mark.asyncio
async def test_correct_admin_password_opens_admin_menu(monkeypatch) -> None:
    monkeypatch.setattr(admin, "get_admin_password", lambda: "secret")
    message = FakeMessage("secret")
    state = FakeState()

    await start_admin(FakeMessage(user_id=123), state)
    await check_admin_password(message, state)

    assert 123 in admin.authorized_admin_user_ids
    assert state.state == AdminFlowStates.menu
    assert "Админка" in message.answers[0][0]


@pytest.mark.asyncio
async def test_admin_topic_selection_saves_topic() -> None:
    admin.authorized_admin_user_ids.add(123)
    state = FakeState()
    message = FakeMessage("кулинария")

    await start_admin_topic_selection(FakeMessage(), state)
    await choose_admin_topic(message, state)

    assert state.data["admin_selected_topic"] == "кулинария"
    assert state.state == AdminFlowStates.menu
    assert message.answers[0][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_admin_add_topic_creates_topic(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(admin, "training_data_dir", lambda: tmp_path)
    admin.authorized_admin_user_ids.add(123)
    state = FakeState()
    message = FakeMessage("маркетинг")

    await start_admin_topic_creation(FakeMessage(), state)
    await add_admin_topic(message, state)

    assert "маркетинг" in message.answers[0][0]
    from app.services.topic_registry import TopicRegistry

    assert "маркетинг" in TopicRegistry(tmp_path).list_topics()


@pytest.mark.asyncio
async def test_admin_upload_saves_posts_for_selected_topic() -> None:
    state = FakeState({"admin_selected_topic": "дом", "admin_custom_topic": None})
    message = FakeMessage("Пост один\n\nПост два")

    await save_admin_posts(message, state)

    assert "Сохранено постов: 2" in message.answers[0][0]
    assert state.state == AdminFlowStates.waiting_posts


@pytest.mark.asyncio
async def test_admin_upload_saves_caption_when_forward_has_no_text() -> None:
    state = FakeState({"admin_selected_topic": "дом", "admin_custom_topic": None})
    message = FakeMessage("", caption="Подпись из канала")

    await save_admin_posts(message, state)

    assert "Сохранено постов: 1" in message.answers[0][0]


@pytest.mark.asyncio
async def test_admin_profile_flow_saves_profile_posts(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(admin, "training_data_dir", lambda: tmp_path)
    admin.authorized_admin_user_ids.add(123)
    state = FakeState()

    await start_admin_profile_creation(FakeMessage(), state)
    await add_admin_profile(FakeMessage("Канал красоты"), state)
    await start_admin_profile_selection(FakeMessage(), state)
    await choose_profile(FakeMessage("Канал красоты"), state)
    await start_admin_profile_posts_upload(FakeMessage(), state)
    await save_admin_posts(FakeMessage("Профильный пост"), state)

    message = FakeMessage()
    await show_profile_posts(message, state)

    assert state.data["admin_selected_profile"] == "Канал красоты"
    assert "Профильный пост" in message.answers[0][0]


@pytest.mark.asyncio
async def test_admin_check_data_shows_uploaded_posts() -> None:
    admin.authorized_admin_user_ids.add(123)
    state = FakeState({"admin_selected_topic": "дом", "admin_custom_topic": None})

    await save_admin_posts(FakeMessage("Пост для проверки"), state)
    message = FakeMessage()
    await show_admin_posts(message, state)

    assert "Пост для проверки" in message.answers[0][0]


@pytest.mark.asyncio
async def test_admin_delete_removes_post_by_callback_id() -> None:
    admin.authorized_admin_user_ids.add(123)
    state = FakeState({"admin_selected_topic": "дом", "admin_custom_topic": None})
    await save_admin_posts(FakeMessage("Пост для удаления"), state)

    show_message = FakeMessage()
    await show_admin_posts(show_message, state)
    post_id = int(show_message.answers[0][0].split("#", maxsplit=1)[1].split()[0])

    callback = FakeCallback(f"admin_delete_post:{post_id}")
    await delete_admin_post(callback)

    message = FakeMessage()
    await show_admin_posts(message, state)
    assert "Постов пока нет" in message.answers[0][0]


@pytest.mark.asyncio
async def test_admin_delete_callback_requires_authorized_admin() -> None:
    state = FakeState({"admin_selected_topic": "дом", "admin_custom_topic": None})
    await save_admin_posts(FakeMessage("Пост остается"), state)
    callback = FakeCallback("admin_delete_post:1", user_id=999)

    await delete_admin_post(callback)

    admin.authorized_admin_user_ids.add(123)
    message = FakeMessage()
    await show_admin_posts(message, state)
    assert "Пост остается" in message.answers[0][0]
    assert "Сначала войдите" in callback.alerts[0][0]


@pytest.mark.asyncio
async def test_admin_save_and_train_returns_confirmation_without_real_api() -> None:
    admin.authorized_admin_user_ids.add(123)
    message = FakeMessage()

    await save_and_train(message)

    assert "Индексация пропущена" in message.answers[0][0]
