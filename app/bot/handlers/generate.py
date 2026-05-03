import logging
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from app.bot.command_parsing import parse_generate_command
from app.bot.keyboards import generated_post_keyboard, main_menu_keyboard, topics_keyboard
from app.bot.states import UserFlowStates
from app.core.config import get_settings
from app.core.constants import (
    BACK_TO_MAIN_MENU,
    CUSTOM_TOPIC,
    MAIN_MENU_EDIT,
    MAIN_MENU_GENERATE,
    MAIN_MENU_REGENERATE,
    MAIN_MENU_SELECT_TOPIC,
    PROFILE_BUTTON_PREFIX,
)
from app.services.generation import GenerationService
from app.services.storage import repository_bundle
from app.services.text_generation import create_text_generator
from app.services.topic_registry import TopicRegistry

router = Router()
logger = logging.getLogger(__name__)


def training_data_dir() -> str:
    return get_settings().training_data_dir


def topic_registry() -> TopicRegistry:
    return TopicRegistry(training_data_dir())


@router.message(Command("generate"))
async def generate_from_command(message: Message, state: FSMContext | None = None) -> None:
    user_request = parse_generate_command(message.text or "")
    if not user_request:
        await message.answer(
            "Напишите запрос после команды: /generate пост про завтрак",
            reply_markup=main_menu_keyboard(),
        )
        return

    logger.info("Telegram /generate request received: %s", user_request)
    generated_text = await _generate_text_with_examples(
        topic=CUSTOM_TOPIC,
        custom_topic="быстрый запрос",
        style_scope="topic",
        user_request=user_request,
    )
    if state is not None:
        await state.update_data(
            selected_topic=CUSTOM_TOPIC,
            custom_topic="быстрый запрос",
            last_user_request=user_request,
            last_generated_text=generated_text,
        )
    await message.answer(generated_text, reply_markup=generated_post_keyboard())


@router.message(F.text == MAIN_MENU_SELECT_TOPIC)
async def start_topic_selection(message: Message, state: FSMContext) -> None:
    await state.set_state(UserFlowStates.choosing_topic)
    await message.answer("Выберите тематику.", reply_markup=_topics_keyboard())


@router.message(UserFlowStates.choosing_topic)
async def choose_user_topic(message: Message, state: FSMContext) -> None:
    await _save_topic_from_message(
        message=message,
        state=state,
        custom_state=UserFlowStates.entering_custom_topic,
        next_state=None,
        success_prefix="Выбрана тематика",
    )


@router.message(UserFlowStates.entering_custom_topic)
async def enter_user_custom_topic(message: Message, state: FSMContext) -> None:
    custom_topic = (message.text or "").strip()
    if not custom_topic:
        await message.answer("Название тематики не должно быть пустым.", reply_markup=_topics_keyboard())
        return

    await state.update_data(selected_topic=CUSTOM_TOPIC, custom_topic=custom_topic, style_scope="topic")
    await state.set_state(None)
    await message.answer(f"Выбрана тематика: {custom_topic}", reply_markup=main_menu_keyboard())


@router.message(F.text == MAIN_MENU_GENERATE)
async def start_generation(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("selected_topic"):
        await state.set_state(UserFlowStates.choosing_topic_for_generation)
        await message.answer("Выберите тематику для будущего поста.", reply_markup=_topics_keyboard())
        return

    await state.set_state(UserFlowStates.waiting_request)
    await message.answer(
        "Опишите тему, тезис или черновик поста.",
        reply_markup=_back_keyboard(),
    )


@router.message(UserFlowStates.choosing_topic_for_generation)
async def choose_generation_topic(message: Message, state: FSMContext) -> None:
    await _save_topic_from_message(
        message=message,
        state=state,
        custom_state=UserFlowStates.entering_custom_topic_for_generation,
        next_state=UserFlowStates.waiting_request,
        success_prefix="Выбрана тематика",
    )
    if await state.get_state() == UserFlowStates.waiting_request.state:
        await message.answer("Опишите тему, тезис или черновик поста.", reply_markup=_back_keyboard())


@router.message(UserFlowStates.entering_custom_topic_for_generation)
async def enter_generation_custom_topic(message: Message, state: FSMContext) -> None:
    custom_topic = (message.text or "").strip()
    if not custom_topic:
        await message.answer("Название тематики не должно быть пустым.", reply_markup=_topics_keyboard())
        return

    await state.update_data(selected_topic=CUSTOM_TOPIC, custom_topic=custom_topic, style_scope="topic")
    await state.set_state(UserFlowStates.waiting_request)
    await message.answer("Опишите тему, тезис или черновик поста.", reply_markup=_back_keyboard())


@router.message(UserFlowStates.waiting_request)
async def generate_post(message: Message, state: FSMContext) -> None:
    user_request = (message.text or "").strip()
    if not user_request:
        await message.answer("Запрос не должен быть пустым.", reply_markup=_back_keyboard())
        return

    data = await state.get_data()
    topic = str(data["selected_topic"])
    custom_topic = _optional_str(data.get("custom_topic"))
    logger.info("Telegram generation request received: %s", user_request)

    generated_text = await _generate_text_with_examples(
        topic=topic,
        custom_topic=custom_topic,
        style_scope=str(data.get("style_scope") or "topic"),
        user_request=user_request,
    )

    await state.update_data(last_user_request=user_request, last_generated_text=generated_text)
    await state.set_state(None)
    await message.answer(generated_text, reply_markup=generated_post_keyboard())


@router.message(F.text == MAIN_MENU_EDIT)
async def start_editing(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("last_generated_text"):
        await message.answer(
            "Сначала сгенерируйте пост, потом его можно будет отредактировать.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(UserFlowStates.editing_post)
    await message.answer("Отправьте обновленный текст поста.", reply_markup=_back_keyboard())


@router.message(UserFlowStates.editing_post)
async def save_edited_post(message: Message, state: FSMContext) -> None:
    edited_text = (message.text or "").strip()
    if not edited_text:
        await message.answer("Текст поста не должен быть пустым.", reply_markup=_back_keyboard())
        return

    await state.update_data(last_generated_text=edited_text)
    await state.set_state(None)
    await message.answer(edited_text, reply_markup=generated_post_keyboard())


@router.message(F.text == MAIN_MENU_REGENERATE)
async def regenerate_post(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    topic = _optional_str(data.get("selected_topic"))
    user_request = _optional_str(data.get("last_user_request"))
    if not topic or not user_request:
        await message.answer(
            "Сначала выберите тематику и сгенерируйте первый пост.",
            reply_markup=main_menu_keyboard(),
        )
        return

    generated_text = await _generate_text_with_examples(
        topic=topic,
        custom_topic=_optional_str(data.get("custom_topic")),
        style_scope=str(data.get("style_scope") or "topic"),
        user_request=user_request,
    )
    await state.update_data(last_generated_text=generated_text)
    await state.set_state(None)
    await message.answer(generated_text, reply_markup=generated_post_keyboard())


async def _save_topic_from_message(
    *,
    message: Message,
    state: FSMContext,
    custom_state: Any,
    next_state: Any,
    success_prefix: str,
) -> None:
    topic = message.text or ""
    if topic == BACK_TO_MAIN_MENU:
        await state.clear()
        await message.answer("Главное меню.", reply_markup=main_menu_keyboard())
        return

    if topic == CUSTOM_TOPIC:
        await state.set_state(custom_state)
        await message.answer("Введите название кастомной тематики.", reply_markup=_back_keyboard())
        return

    if topic.startswith(PROFILE_BUTTON_PREFIX):
        profile = topic.removeprefix(PROFILE_BUTTON_PREFIX).strip()
        if profile in topic_registry().list_profiles():
            await state.update_data(selected_topic=profile, custom_topic=None, style_scope="profile")
            if next_state is not None:
                await state.set_state(next_state)
            else:
                await state.set_state(None)
            await message.answer(f"{success_prefix}: {profile}", reply_markup=main_menu_keyboard())
            return

    if topic not in topic_registry().list_topics():
        await message.answer("Выберите тематику кнопкой ниже.", reply_markup=_topics_keyboard())
        return

    await state.update_data(selected_topic=topic, custom_topic=None, style_scope="topic")
    if next_state is not None:
        await state.set_state(next_state)
    else:
        await state.set_state(None)
    await message.answer(f"{success_prefix}: {topic}", reply_markup=main_menu_keyboard())


async def _generate_text_with_examples(
    *,
    topic: str,
    custom_topic: str | None,
    user_request: str,
    style_scope: str = "topic",
) -> str:
    settings = get_settings()
    async with repository_bundle() as repositories:
        try:
            style_posts = await repositories.posts.list_by_topic(
                topic=topic,
                custom_topic=custom_topic,
                limit=5,
                style_scope=style_scope,
            )
        except TypeError:
            style_posts = await repositories.posts.list_by_topic(
                topic=topic,
                custom_topic=custom_topic,
                limit=5,
            )
        service = GenerationService(
            generation_logs_repository=repositories.generation_logs,
            text_generator=create_text_generator(settings),
        )
        result = await service.generate_post(
            topic=topic,
            custom_topic=custom_topic,
            user_request=user_request,
            style_examples=[post.text for post in style_posts],
        )
        await repositories.commit()
        return result.generated_text


def _topics_keyboard() -> ReplyKeyboardMarkup:
    registry = topic_registry()
    return topics_keyboard(topics=registry.list_topics(), profiles=registry.list_profiles())


def _back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_TO_MAIN_MENU)]],
        resize_keyboard=True,
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
