from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.core.config import Settings
from app.services.access_control import is_user_allowed


class AccessControlMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if (
            user is None
            or not self.settings.allowed_telegram_user_ids
            or is_user_allowed(user.id, self.settings.allowed_telegram_user_ids)
        ):
            return await handler(event, data)

        if isinstance(event, Message):
            await event.answer("У вас нет доступа к этому боту.")
        elif isinstance(event, CallbackQuery):
            await event.answer("У вас нет доступа к этому боту.", show_alert=True)
        return None
