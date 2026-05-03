import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup

from app.bot.keyboards import (
    admin_menu_keyboard,
    admin_profiles_keyboard,
    admin_topics_keyboard,
    delete_post_keyboard,
)
from app.bot.message_content import extract_training_message
from app.bot.states import AdminFlowStates
from app.core.config import get_settings
from app.core.constants import (
    ADMIN_MENU_ADD_POSTS,
    ADMIN_MENU_ADD_PROFILE,
    ADMIN_MENU_ADD_PROFILE_POSTS,
    ADMIN_MENU_ADD_TOPIC,
    ADMIN_MENU_CHECK_DATA,
    ADMIN_MENU_CHECK_PROFILE,
    ADMIN_MENU_SAVE_AND_TRAIN,
    ADMIN_MENU_SELECT_PROFILE,
    ADMIN_MENU_SELECT_TOPIC,
    BACK_TO_ADMIN_MENU,
    CUSTOM_TOPIC,
    MAIN_MENU_ADMIN,
)
from app.db.file_storage import FilePostsRepository
from app.services.post_ingestion import PostIngestionService
from app.services.topic_registry import TopicRegistry
from app.services.training import TrainingService

router = Router()
logger = logging.getLogger(__name__)

authorized_admin_user_ids: set[int] = set()


def get_admin_password() -> str:
    return get_settings().admin_password


def training_data_dir() -> str:
    return get_settings().training_data_dir


def topic_registry() -> TopicRegistry:
    return TopicRegistry(training_data_dir())


def posts_repository() -> FilePostsRepository:
    return FilePostsRepository(training_data_dir())


@router.message(F.text == MAIN_MENU_ADMIN)
async def start_admin(message: Message, state: FSMContext) -> None:
    user_id = _message_user_id(message)
    if user_id in authorized_admin_user_ids:
        await state.set_state(AdminFlowStates.menu)
        await message.answer("Админка.", reply_markup=admin_menu_keyboard())
        return

    await state.set_state(AdminFlowStates.entering_password)
    await message.answer("Введите пароль админки.", reply_markup=_admin_back_keyboard())


@router.message(AdminFlowStates.entering_password)
async def check_admin_password(message: Message, state: FSMContext) -> None:
    password = get_admin_password()
    user_id = _message_user_id(message)
    if not password:
        await state.set_state(AdminFlowStates.entering_password)
        await message.answer("ADMIN_PASSWORD не настроен.", reply_markup=_admin_back_keyboard())
        return

    if (message.text or "") != password:
        await state.set_state(AdminFlowStates.entering_password)
        await message.answer("Неверный пароль.", reply_markup=_admin_back_keyboard())
        return

    authorized_admin_user_ids.add(user_id)
    await state.set_state(AdminFlowStates.menu)
    await message.answer("Админка открыта.", reply_markup=admin_menu_keyboard())


@router.message(F.text == BACK_TO_ADMIN_MENU)
async def back_to_admin_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminFlowStates.menu)
    await message.answer("Админка.", reply_markup=admin_menu_keyboard())


@router.message(AdminFlowStates.menu, F.text == ADMIN_MENU_SELECT_TOPIC)
async def start_admin_topic_selection(message: Message, state: FSMContext) -> None:
    if not await _ensure_admin(message):
        return
    await state.set_state(AdminFlowStates.choosing_topic)
    await message.answer(
        "Выберите тематику для админских действий.",
        reply_markup=admin_topics_keyboard(topic_registry().list_topics()),
    )


@router.message(AdminFlowStates.menu, F.text == ADMIN_MENU_ADD_TOPIC)
async def start_admin_topic_creation(message: Message, state: FSMContext) -> None:
    if not await _ensure_admin(message):
        return
    await state.set_state(AdminFlowStates.adding_topic)
    await message.answer("Введите название новой тематики.", reply_markup=_admin_back_keyboard())


@router.message(AdminFlowStates.adding_topic)
async def add_admin_topic(message: Message, state: FSMContext) -> None:
    topic = (message.text or "").strip()
    if not topic:
        await message.answer("Название тематики не должно быть пустым.", reply_markup=_admin_back_keyboard())
        return

    created = topic_registry().add_topic(topic)
    await state.update_data(admin_selected_topic=topic, admin_custom_topic=None)
    await state.set_state(AdminFlowStates.menu)
    suffix = "добавлена" if created else "уже есть"
    await message.answer(f"Тематика {topic} {suffix}.", reply_markup=admin_menu_keyboard())


@router.message(AdminFlowStates.choosing_topic)
async def choose_admin_topic(message: Message, state: FSMContext) -> None:
    topic = message.text or ""
    if topic == BACK_TO_ADMIN_MENU:
        await state.set_state(AdminFlowStates.menu)
        await message.answer("Админка.", reply_markup=admin_menu_keyboard())
        return

    if topic == CUSTOM_TOPIC:
        await state.set_state(AdminFlowStates.entering_custom_topic)
        await message.answer("Введите название кастомной тематики.", reply_markup=_admin_back_keyboard())
        return

    if topic not in topic_registry().list_topics():
        await message.answer(
            "Выберите тематику кнопкой ниже.",
            reply_markup=admin_topics_keyboard(topic_registry().list_topics()),
        )
        return

    await state.update_data(admin_selected_topic=topic, admin_custom_topic=None)
    await state.set_state(AdminFlowStates.menu)
    await message.answer(f"Выбрана тематика: {topic}", reply_markup=admin_menu_keyboard())


@router.message(AdminFlowStates.entering_custom_topic)
async def enter_admin_custom_topic(message: Message, state: FSMContext) -> None:
    custom_topic = (message.text or "").strip()
    if not custom_topic:
        await message.answer("Название тематики не должно быть пустым.", reply_markup=_admin_back_keyboard())
        return

    await state.update_data(admin_selected_topic=CUSTOM_TOPIC, admin_custom_topic=custom_topic)
    await state.set_state(AdminFlowStates.menu)
    await message.answer(f"Выбрана тематика: {custom_topic}", reply_markup=admin_menu_keyboard())


@router.message(AdminFlowStates.menu, F.text == ADMIN_MENU_ADD_PROFILE)
async def start_admin_profile_creation(message: Message, state: FSMContext) -> None:
    if not await _ensure_admin(message):
        return
    await state.set_state(AdminFlowStates.adding_profile)
    await message.answer("Введите название профиля канала.", reply_markup=_admin_back_keyboard())


@router.message(AdminFlowStates.adding_profile)
async def add_admin_profile(message: Message, state: FSMContext) -> None:
    profile = (message.text or "").strip()
    if not profile:
        await message.answer("Название профиля не должно быть пустым.", reply_markup=_admin_back_keyboard())
        return

    created = topic_registry().add_profile(profile)
    await state.update_data(admin_selected_profile=profile)
    await state.set_state(AdminFlowStates.menu)
    suffix = "добавлен" if created else "уже есть"
    await message.answer(f"Профиль канала {profile} {suffix}.", reply_markup=admin_menu_keyboard())


@router.message(AdminFlowStates.menu, F.text == ADMIN_MENU_SELECT_PROFILE)
async def start_admin_profile_selection(message: Message, state: FSMContext) -> None:
    if not await _ensure_admin(message):
        return
    await state.set_state(AdminFlowStates.choosing_profile)
    await message.answer(
        "Выберите профиль канала.",
        reply_markup=admin_profiles_keyboard(topic_registry().list_profiles()),
    )


@router.message(AdminFlowStates.choosing_profile)
async def choose_profile(message: Message, state: FSMContext) -> None:
    profile = message.text or ""
    if profile == BACK_TO_ADMIN_MENU:
        await state.set_state(AdminFlowStates.menu)
        await message.answer("Админка.", reply_markup=admin_menu_keyboard())
        return

    if profile not in topic_registry().list_profiles():
        await message.answer(
            "Выберите профиль кнопкой ниже.",
            reply_markup=admin_profiles_keyboard(topic_registry().list_profiles()),
        )
        return

    await state.update_data(admin_selected_profile=profile)
    await state.set_state(AdminFlowStates.menu)
    await message.answer(f"Выбран профиль: {profile}", reply_markup=admin_menu_keyboard())


@router.message(AdminFlowStates.menu, F.text == ADMIN_MENU_ADD_POSTS)
async def start_admin_posts_upload(message: Message, state: FSMContext) -> None:
    if not await _ensure_admin(message):
        return
    data = await state.get_data()
    if not data.get("admin_selected_topic"):
        await state.set_state(AdminFlowStates.choosing_topic)
        await message.answer("Сначала выберите тематику.", reply_markup=admin_topics_keyboard())
        return

    await state.update_data(admin_upload_scope="topic")
    await state.set_state(AdminFlowStates.waiting_posts)
    await message.answer(
        "Отправьте один или несколько постов. Разделяйте посты пустой строкой.",
        reply_markup=_admin_back_keyboard(),
    )


@router.message(AdminFlowStates.menu, F.text == ADMIN_MENU_ADD_PROFILE_POSTS)
async def start_admin_profile_posts_upload(message: Message, state: FSMContext) -> None:
    if not await _ensure_admin(message):
        return
    data = await state.get_data()
    if not data.get("admin_selected_profile"):
        await state.set_state(AdminFlowStates.choosing_profile)
        await message.answer(
            "Сначала выберите профиль канала.",
            reply_markup=admin_profiles_keyboard(topic_registry().list_profiles()),
        )
        return

    await state.update_data(admin_upload_scope="profile")
    await state.set_state(AdminFlowStates.waiting_posts)
    await message.answer(
        "Перешлите или отправьте посты для выбранного профиля. Можно несколько сообщений подряд.",
        reply_markup=_admin_back_keyboard(),
    )


@router.message(AdminFlowStates.waiting_posts)
async def save_admin_posts(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    training_message = extract_training_message(message)
    if not training_message.text:
        await message.answer("Пост без текста или подписи пропущен.", reply_markup=_admin_back_keyboard())
        return

    upload_scope = str(data.get("admin_upload_scope") or "topic")
    if upload_scope == "profile":
        topic = str(data["admin_selected_profile"])
        custom_topic = None
        style_scope = "profile"
    else:
        topic = str(data["admin_selected_topic"])
        custom_topic = _optional_str(data.get("admin_custom_topic"))
        style_scope = "topic"

    service = PostIngestionService(posts_repository())
    result = await service.ingest_text(
        topic=topic,
        custom_topic=custom_topic,
        raw_text=training_message.text,
        source_type=training_message.source_type,
        source_title=training_message.source_title,
        forward_metadata=training_message.forward_metadata,
        style_scope=style_scope,
    )

    await message.answer(
        f"Сохранено постов: {result.created_count}. Пропущено: {result.skipped_count}.",
        reply_markup=_admin_back_keyboard(),
    )
    await state.set_state(AdminFlowStates.waiting_posts)


@router.message(AdminFlowStates.menu, F.text == ADMIN_MENU_CHECK_DATA)
async def show_admin_posts(message: Message, state: FSMContext) -> None:
    if not await _ensure_admin(message):
        return
    data = await state.get_data()
    topic = _optional_str(data.get("admin_selected_topic"))
    if not topic:
        await message.answer("Сначала выберите тематику.", reply_markup=admin_topics_keyboard())
        return

    posts = await posts_repository().list_by_topic(
        topic=topic,
        custom_topic=_optional_str(data.get("admin_custom_topic")),
        limit=20,
    )

    if not posts:
        await message.answer("Постов пока нет.", reply_markup=admin_menu_keyboard())
        return

    for post in posts:
        preview = _preview(post.text)
        await message.answer(
            f"#{post.id} {preview}",
            reply_markup=delete_post_keyboard(post_id=post.id),
        )
    await message.answer("Данные показаны.", reply_markup=admin_menu_keyboard())


@router.message(AdminFlowStates.menu, F.text == ADMIN_MENU_CHECK_PROFILE)
async def show_profile_posts(message: Message, state: FSMContext) -> None:
    if not await _ensure_admin(message):
        return
    data = await state.get_data()
    profile = _optional_str(data.get("admin_selected_profile"))
    if not profile:
        await message.answer(
            "Сначала выберите профиль канала.",
            reply_markup=admin_profiles_keyboard(topic_registry().list_profiles()),
        )
        return

    posts = await posts_repository().list_by_topic(
        topic=profile,
        limit=20,
        style_scope="profile",
    )

    if not posts:
        await message.answer("Постов профиля пока нет.", reply_markup=admin_menu_keyboard())
        return

    for post in posts:
        await message.answer(
            f"#{post.id} {_preview(post.text)}",
            reply_markup=delete_post_keyboard(post_id=post.id),
        )
    await message.answer("Профиль показан.", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data.startswith("admin_delete_post:"))
async def delete_admin_post(callback: CallbackQuery) -> None:
    if (callback.from_user.id if callback.from_user else 0) not in authorized_admin_user_ids:
        await callback.answer("Сначала войдите в админку по паролю.", show_alert=True)
        return

    post_id = int(str(callback.data).split(":", maxsplit=1)[1])
    deleted = await posts_repository().delete_by_id(post_id)

    if callback.message is not None:
        text = "Пост удален." if deleted else "Пост не найден."
        await callback.message.answer(text, reply_markup=admin_menu_keyboard())
    await callback.answer()


@router.message(AdminFlowStates.menu, F.text == ADMIN_MENU_SAVE_AND_TRAIN)
async def save_and_train(message: Message) -> None:
    if not await _ensure_admin(message):
        return
    result = await TrainingService().save_and_train()
    logger.info("Training requested", extra={"status": result.status})
    await message.answer(result.message, reply_markup=admin_menu_keyboard())


async def _ensure_admin(message: Message) -> bool:
    if _message_user_id(message) in authorized_admin_user_ids:
        return True
    await message.answer("Сначала войдите в админку по паролю.", reply_markup=_admin_back_keyboard())
    return False


def _message_user_id(message: Message) -> int:
    return message.from_user.id if message.from_user else 0


def _admin_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_TO_ADMIN_MENU)]],
        resize_keyboard=True,
    )


def _preview(text: str, limit: int = 120) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1]}..."


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
