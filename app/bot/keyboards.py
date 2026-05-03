from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

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
    CUSTOM_TOPIC,
    MAIN_MENU_ABOUT,
    MAIN_MENU_ADMIN,
    MAIN_MENU_EDIT,
    MAIN_MENU_GENERATE,
    MAIN_MENU_REGENERATE,
    MAIN_MENU_SELECT_TOPIC,
    PROFILE_BUTTON_PREFIX,
    STANDARD_TOPICS,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MAIN_MENU_SELECT_TOPIC)],
            [KeyboardButton(text=MAIN_MENU_GENERATE)],
            [KeyboardButton(text=MAIN_MENU_ABOUT)],
            [KeyboardButton(text=MAIN_MENU_ADMIN)],
        ],
        resize_keyboard=True,
    )


def topics_keyboard(
    topics: list[str] | tuple[str, ...] | None = None,
    profiles: list[str] | tuple[str, ...] | None = None,
) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=topic)] for topic in (topics or STANDARD_TOPICS)]
    rows.extend([[KeyboardButton(text=f"{PROFILE_BUTTON_PREFIX}{profile}")] for profile in (profiles or [])])
    rows.append([KeyboardButton(text=CUSTOM_TOPIC)])
    rows.append([KeyboardButton(text=BACK_TO_MAIN_MENU)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def profile_keyboard(profiles: list[str] | tuple[str, ...]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=profile)] for profile in profiles]
    rows.append([KeyboardButton(text=BACK_TO_MAIN_MENU)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def generated_post_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MAIN_MENU_EDIT)],
            [KeyboardButton(text=MAIN_MENU_REGENERATE)],
            [KeyboardButton(text=BACK_TO_MAIN_MENU)],
        ],
        resize_keyboard=True,
    )


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_MENU_ADD_TOPIC)],
            [KeyboardButton(text=ADMIN_MENU_SELECT_TOPIC)],
            [KeyboardButton(text=ADMIN_MENU_ADD_POSTS)],
            [KeyboardButton(text=ADMIN_MENU_CHECK_DATA)],
            [KeyboardButton(text=ADMIN_MENU_ADD_PROFILE)],
            [KeyboardButton(text=ADMIN_MENU_SELECT_PROFILE)],
            [KeyboardButton(text=ADMIN_MENU_ADD_PROFILE_POSTS)],
            [KeyboardButton(text=ADMIN_MENU_CHECK_PROFILE)],
            [KeyboardButton(text=ADMIN_MENU_SAVE_AND_TRAIN)],
            [KeyboardButton(text=BACK_TO_MAIN_MENU)],
        ],
        resize_keyboard=True,
    )


def admin_topics_keyboard(topics: list[str] | tuple[str, ...] | None = None) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=topic)] for topic in (topics or STANDARD_TOPICS)]
    rows.append([KeyboardButton(text=CUSTOM_TOPIC)])
    rows.append([KeyboardButton(text=BACK_TO_ADMIN_MENU)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_profiles_keyboard(profiles: list[str] | tuple[str, ...]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=profile)] for profile in profiles]
    rows.append([KeyboardButton(text=BACK_TO_ADMIN_MENU)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def delete_post_keyboard(*, post_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Удалить",
                    callback_data=f"admin_delete_post:{post_id}",
                )
            ]
        ]
    )
