# gamer_flow.py
"""
Модуль для логики обычного игрока.
"""

import asyncio
from telegram import (
    CallbackQuery,
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    Update,
)
from telegram.ext import (
    ContextTypes,
)
from queries import DatabaseConnector
from logger import get_logger
from gamer_constants import *
from constants import *
import inspect
import time

logger = get_logger(__name__)


class GamerFlow:
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        gamer_id = update.effective_user.id
        logger.info(f"{GAMER} {gamer_id} called {inspect.currentframe().f_code.co_name}")
        await update.message.reply_text("Добро пожаловать, игрок!\nПрисоединитесь к игре, введя код \"ASDF\"")
        username = update.effective_user.username
        self.connector.create_player(gamer_id, username, f"{CODE_TO_GAME}", None, None)
        logger.info("Режим игрока запущен.")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        gamer_id = update.effective_user.id
        logger.info(f"{GAMER} {gamer_id} called {inspect.currentframe().f_code.co_name}")
        # await update.message.reply_text("Игрок: ваше сообщение получено.")
        # state = self.connector.get_player_by_telegram_id(gamer_id).

        text = update.message.text.strip()
        logger.info(f"Сообщение от игрока получено. text = {text}")

        state = self.connector.get_player_by_telegram_id(gamer_id).state
        if state == f"{CODE_TO_GAME}":
            try:
                game_session_id = self.connector.get_game_session_by_code(text).id
            except Exception as e:
                logger.error("User entered incorrect game code")
                await context.bot.send_message(
                    chat_id=gamer_id,
                    text="Такой игры нет, попробуй другой код",
                )
                return
            # self.connector.update_player_state_by_telegram_id(gamer_id, f"{NICKNAME_TO_USER}")
            # self.connector.update_player_game_session_by_telegram_id(gamer_id, game_session_id)
            # replase two database queries to one
            player = self.connector.get_player_by_telegram_id(gamer_id)
            player.state = f"{NICKNAME_TO_USER}"
            player.game_session_id = game_session_id
            self.connector.commit()
            await context.bot.send_message(
                chat_id=gamer_id,
                text="Отлично, теперь нужно ввести свой никнейм",
            )
            return
        elif state == f"{NICKNAME_TO_USER}":
            player = self.connector.get_player_by_telegram_id(gamer_id)
            player.nickname = text
            player.state = f"{WAITING_START}"
            game_session_id = player.game_session_id
            self.connector.commit()
            await context.bot.send_message(
                chat_id=gamer_id,
                text="Теперь ждём всех",
            )
            self.connector.create_or_update_result(gamer_id, game_session_id, 0)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        gamer_id = update.effective_user.id
        logger.info(f"{GAMER} {gamer_id} called {inspect.currentframe().f_code.co_name}")
        query = update.callback_query
        try:
            await query.answer("Ок")
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            logger.error(f"Something went wrong, while hiding old keyboard in gamer callback")
        data = query.data
        logger.debug(f"got {data} callback from {gamer_id} user")
        variant_id = data.split(":")[-1]
        variant = self.connector.get_variant(variant_id)
        logger.debug(f"variant = {variant}")
        self.connector.create_answer(variant_id, gamer_id, data, time.time())
        game_session_id = self.connector.get_player_by_telegram_id(gamer_id).game_session_id
        self.connector.increase_result_score(gamer_id, game_session_id, int(variant.is_correct))

from queries import db_connector
gamer_flow = GamerFlow(db_connector)
