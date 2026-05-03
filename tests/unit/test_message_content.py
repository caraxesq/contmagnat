from types import SimpleNamespace

from app.bot.message_content import extract_training_message


def test_extract_training_message_uses_text() -> None:
    message = SimpleNamespace(text="Текст поста", caption=None, forward_origin=None)

    result = extract_training_message(message)

    assert result.text == "Текст поста"
    assert result.source_type == "manual"


def test_extract_training_message_uses_caption_when_text_is_missing() -> None:
    message = SimpleNamespace(text=None, caption="Подпись поста", forward_origin=None)

    result = extract_training_message(message)

    assert result.text == "Подпись поста"


def test_extract_training_message_marks_forwarded_channel_source() -> None:
    chat = SimpleNamespace(id=-100, title="Канал еды", username="food")
    origin = SimpleNamespace(chat=chat, type="channel")
    message = SimpleNamespace(text="Форвард", caption=None, forward_origin=origin)

    result = extract_training_message(message)

    assert result.source_type == "forward"
    assert result.source_title == "Канал еды"
    assert result.forward_metadata == {"chat_id": -100, "chat_title": "Канал еды", "chat_username": "food"}


def test_extract_training_message_returns_none_for_media_without_text() -> None:
    message = SimpleNamespace(text=None, caption=None, forward_origin=None)

    result = extract_training_message(message)

    assert result.text is None
