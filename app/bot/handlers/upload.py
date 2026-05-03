import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import main_menu_keyboard, topics_keyboard
from app.bot.states import UploadStates
from app.core.constants import CUSTOM_TOPIC, MAIN_MENU_UPLOAD, is_standard_topic
from app.services.post_ingestion import PostIngestionService
from app.services.storage import repository_bundle

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == MAIN_MENU_UPLOAD)
async def start_upload(message: Message, state: FSMContext) -> None:
    await state.set_state(UploadStates.choosing_topic)
    await message.answer("Выберите тематику для dataset'а стиля.", reply_markup=topics_keyboard())


@router.message(UploadStates.choosing_topic)
async def choose_upload_topic(message: Message, state: FSMContext) -> None:
    topic = message.text or ""
    if topic == CUSTOM_TOPIC:
        await state.set_state(UploadStates.entering_custom_topic)
        await message.answer("Введите название кастомной тематики.")
        return

    if not is_standard_topic(topic):
        await message.answer("Выберите тематику кнопкой ниже.", reply_markup=topics_keyboard())
        return

    await state.update_data(topic=topic, custom_topic=None)
    await state.set_state(UploadStates.waiting_posts)
    await message.answer("Отправьте один или несколько постов. Разделяйте посты пустой строкой.")


@router.message(UploadStates.entering_custom_topic)
async def enter_upload_custom_topic(message: Message, state: FSMContext) -> None:
    custom_topic = (message.text or "").strip()
    if not custom_topic:
        await message.answer("Название тематики не должно быть пустым.")
        return

    await state.update_data(topic=CUSTOM_TOPIC, custom_topic=custom_topic)
    await state.set_state(UploadStates.waiting_posts)
    await message.answer("Отправьте один или несколько постов. Разделяйте посты пустой строкой.")


@router.message(UploadStates.waiting_posts)
async def save_posts(message: Message, state: FSMContext) -> None:
    raw_text = message.text or ""
    data = await state.get_data()
    logger.info("Telegram posts upload received", extra={"topic": data["topic"]})

    async with repository_bundle() as repositories:
        service = PostIngestionService(repositories.posts)
        result = await service.ingest_text(
            topic=data["topic"],
            custom_topic=data.get("custom_topic"),
            raw_text=raw_text,
        )
        await repositories.commit()

    await state.clear()
    await message.answer(
        f"Сохранено постов: {result.created_count}. Пропущено: {result.skipped_count}.",
        reply_markup=main_menu_keyboard(),
    )
