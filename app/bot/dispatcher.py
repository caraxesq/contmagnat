from aiogram import Dispatcher

from app.bot.handlers import admin, generate, start, upload
from app.bot.middlewares import AccessControlMiddleware
from app.core.config import Settings


def create_dispatcher(settings: Settings) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.message.middleware(AccessControlMiddleware(settings))
    dispatcher.callback_query.middleware(AccessControlMiddleware(settings))
    dispatcher.include_router(start.router)
    dispatcher.include_router(admin.router)
    dispatcher.include_router(upload.router)
    dispatcher.include_router(generate.router)
    return dispatcher
