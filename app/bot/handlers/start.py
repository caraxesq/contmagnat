import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import main_menu_keyboard
from app.core.constants import BACK_TO_MAIN_MENU, MAIN_MENU_ABOUT

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    logger.info("Telegram /start received from user_id=%s", message.from_user.id if message.from_user else None)
    await message.answer(
        "Привет. Я помогу выбрать тематику, сгенерировать пост, отредактировать его и подготовить новый вариант.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == BACK_TO_MAIN_MENU)
async def back_to_main_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню.", reply_markup=main_menu_keyboard())


@router.message(F.text == MAIN_MENU_ABOUT)
async def handle_about(message: Message) -> None:
    await message.answer(
        "Бот помогает генерировать Telegram-посты по выбранной тематике и обучающим примерам. "
        "Админка позволяет добавлять и проверять посты для будущего обучения.",
        reply_markup=main_menu_keyboard(),
    )
