from aiogram.types import InlineKeyboardMarkup

from app.bot.keyboards import (
    admin_menu_keyboard,
    generated_post_keyboard,
    main_menu_keyboard,
    profile_keyboard,
    topics_keyboard,
)
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
    BACK_TO_MAIN_MENU,
    MAIN_MENU_ABOUT,
    MAIN_MENU_ADMIN,
    MAIN_MENU_EDIT,
    MAIN_MENU_GENERATE,
    MAIN_MENU_REGENERATE,
    MAIN_MENU_SELECT_TOPIC,
)


def _reply_texts(markup) -> list[str]:
    return [button.text for row in markup.keyboard for button in row]


def test_main_menu_contains_full_user_route_and_admin_entry() -> None:
    texts = _reply_texts(main_menu_keyboard())

    assert texts == [
        MAIN_MENU_SELECT_TOPIC,
        MAIN_MENU_GENERATE,
        MAIN_MENU_ABOUT,
        MAIN_MENU_ADMIN,
    ]


def test_topics_keyboard_always_has_back_to_main_menu() -> None:
    texts = _reply_texts(topics_keyboard())

    assert BACK_TO_MAIN_MENU in texts


def test_topics_keyboard_accepts_dynamic_topics() -> None:
    texts = _reply_texts(topics_keyboard(topics=["маркетинг"]))

    assert texts[:1] == ["маркетинг"]


def test_topics_keyboard_lists_profiles_with_prefix() -> None:
    texts = _reply_texts(topics_keyboard(topics=["дом"], profiles=["Канал красоты"]))

    assert "Профиль: Канал красоты" in texts


def test_profile_keyboard_lists_profiles_and_back_to_main_menu() -> None:
    texts = _reply_texts(profile_keyboard(profiles=["Канал красоты"]))

    assert texts == ["Канал красоты", BACK_TO_MAIN_MENU]


def test_generated_post_keyboard_exposes_edit_regenerate_and_back_actions() -> None:
    texts = _reply_texts(generated_post_keyboard())

    assert texts == [MAIN_MENU_EDIT, MAIN_MENU_REGENERATE, BACK_TO_MAIN_MENU]


def test_admin_menu_contains_admin_actions_and_back_to_main_menu() -> None:
    texts = _reply_texts(admin_menu_keyboard())

    assert texts == [
        ADMIN_MENU_ADD_TOPIC,
        ADMIN_MENU_SELECT_TOPIC,
        ADMIN_MENU_ADD_POSTS,
        ADMIN_MENU_CHECK_DATA,
        ADMIN_MENU_ADD_PROFILE,
        ADMIN_MENU_SELECT_PROFILE,
        ADMIN_MENU_ADD_PROFILE_POSTS,
        ADMIN_MENU_CHECK_PROFILE,
        ADMIN_MENU_SAVE_AND_TRAIN,
        BACK_TO_MAIN_MENU,
    ]


def test_delete_post_keyboard_uses_inline_callback_with_post_id() -> None:
    from app.bot.keyboards import delete_post_keyboard

    markup = delete_post_keyboard(post_id=42)

    assert isinstance(markup, InlineKeyboardMarkup)
    assert markup.inline_keyboard[0][0].callback_data == "admin_delete_post:42"
    assert markup.inline_keyboard[0][0].text
