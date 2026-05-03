from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TrainingMessage:
    text: str | None
    source_type: str
    source_title: str | None = None
    forward_metadata: dict[str, Any] | None = None


def extract_training_message(message: Any) -> TrainingMessage:
    text = _clean(getattr(message, "text", None) or getattr(message, "caption", None))
    forward_origin = getattr(message, "forward_origin", None)
    if forward_origin is None:
        return TrainingMessage(text=text, source_type="manual")

    chat = getattr(forward_origin, "chat", None)
    if chat is None:
        return TrainingMessage(text=text, source_type="forward")

    title = getattr(chat, "title", None)
    username = getattr(chat, "username", None)
    chat_id = getattr(chat, "id", None)
    metadata = {
        "chat_id": chat_id,
        "chat_title": title,
        "chat_username": username,
    }
    return TrainingMessage(
        text=text,
        source_type="forward",
        source_title=title,
        forward_metadata=metadata,
    )


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None
