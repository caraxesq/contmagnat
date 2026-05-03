import asyncio
import logging

from aiogram import Bot

from app.bot.dispatcher import create_dispatcher
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging()
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured. Create .env from .env.example "
            "and set TELEGRAM_BOT_TOKEN."
        )

    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = create_dispatcher(settings)
    logger.info("Starting Telegram bot polling")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
