# admin_options.py
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
)
import inspect
from logger import get_logger
from admin_constants import *

logger = get_logger(__name__)

async def admin_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    keyboard = [
        [InlineKeyboardButton("Создать новую игру",     callback_data=f"{ADMIN}:{CREATE_GAME}")],
        [InlineKeyboardButton("Редактировать игру",     callback_data=f"{ADMIN}:{GAME_TO_EDIT}")],
        [InlineKeyboardButton("Удалить игру",           callback_data=f"{ADMIN}:{GAME_TO_DELETE}")],
        [InlineKeyboardButton("Другие команды",         callback_data=f"{ADMIN}:{START_GAME}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=admin_id,
        text="Добро пожаловать, администратор!\nВыберите действие:",
        reply_markup=reply_markup,
    )

async def game_options(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id):
    admin_id = update.effective_user.id
    logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    keyboard = [
        [InlineKeyboardButton(ADD_QUESTION_LABEL,           callback_data=f"{ADMIN}:{ADD_QUESTION}:{game_id}")],
        [InlineKeyboardButton(QUESTION_TO_EDIT_LABEL,       callback_data=f"{ADMIN}:{QUESTION_TO_EDIT}:{game_id}")],
        [InlineKeyboardButton(QUESTION_TO_DELETE_LABEL,     callback_data=f"{ADMIN}:{QUESTION_TO_DELETE}:{game_id}")],
        [InlineKeyboardButton(CANCEL_LABEL,                 callback_data=f"{ADMIN}:{ADMIN_OPTIONS}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=admin_id,
        text=f"Что вы хотите сделать с игрой? (from current_state == \"{ADMIN}:{CREATE_GAME}\")",
        reply_markup=reply_markup,
    )

async def question_options(update: Update, context: ContextTypes.DEFAULT_TYPE, question_id, game_id):
    admin_id = update.effective_user.id
    logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    keyboard = [
        [InlineKeyboardButton(EDIT_QUESTION_TEXT_LABEL,         callback_data=f"{ADMIN}:{EDIT_QUESTION_TEXT}:{question_id}")],
        [InlineKeyboardButton(VARIANT_OPTIONS_LABEL,            callback_data=f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}")],
        [InlineKeyboardButton(UPDATE_IMAGE_LABEL,               callback_data=f"{ADMIN}:{UPDATE_IMAGE}:{question_id}")],
        [InlineKeyboardButton(CHANGE_CORRECTNESS_LABEL,         callback_data=f"{ADMIN}:{CHANGE_CORRECTNESS}:{question_id}")],
        [InlineKeyboardButton(CANCEL_LABEL,                     callback_data=f"{ADMIN}:{GAME_OPTIONS}:{game_id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=admin_id,
        text="Можете редактировать вопрос",
        reply_markup=reply_markup,
    )

async def variant_options(update: Update, context: ContextTypes.DEFAULT_TYPE, question_id):
    admin_id = update.effective_user.id
    logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    keyboard = [
        [InlineKeyboardButton(ADD_VARIANT_LABEL,                callback_data=f"{ADMIN}:{ADD_VARIANT}:{question_id}")],
        [InlineKeyboardButton(EDIT_VARIANT_LABEL,               callback_data=f"{ADMIN}:{VARIANT_TO_EDIT}:{question_id}")],
        [InlineKeyboardButton(VARIANT_TO_DELETE_LABEL,          callback_data=f"{ADMIN}:{VARIANT_TO_DELETE}:{question_id}")],
        [InlineKeyboardButton(CANCEL_LABEL,                     callback_data=f"{ADMIN}:{QUESTION_OPTIONS}:{question_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=admin_id,
        text=f"Что вы хотите сделать с вариантами ответов? (from current_state == \"{ADMIN}:{VARIANT_OPTIONS}:\")",
        reply_markup=reply_markup,
    )
