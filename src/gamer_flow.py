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
import random

logger = get_logger(__name__)


class GamerFlow:
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        gamer_id = update.effective_user.id
        logger.debug(f"{GAMER} {gamer_id} called {inspect.currentframe().f_code.co_name}")
        try:
            await update.message.reply_text("Добро пожаловать, игрок!\nНапиши, как тебя называть?")
        except Exception as e:
            logger.error(f"Error, while sending message to user: {e}")
        username = update.effective_user.username
        game_session_id = self.connector.get_game_session_by_code("LEXA").id
        player = self.connector.create_player(gamer_id, username, f"{NICKNAME_TO_USER}", None, game_session_id)
        self.connector.create_or_update_result(gamer_id, game_session_id, 0)
        logger.debug("Режим игрока запущен.")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        gamer_id = update.effective_user.id
        logger.info(f"{GAMER} {gamer_id} called {inspect.currentframe().f_code.co_name}")
        # await update.message.reply_text("Игрок: ваше сообщение получено.")
        # state = self.connector.get_player_by_telegram_id(gamer_id).

        text = update.message.text.strip()
        logger.info(f"Сообщение от игрока получено. text = {text}")

        state = self.connector.get_player_by_telegram_id(gamer_id).state
        if state == f"{NICKNAME_TO_USER}":
            player = self.connector.get_player_by_telegram_id(gamer_id)
            player.nickname = text
            player.state = f"{WAITING_START}"
            self.connector.commit()
            try:
                await context.bot.send_photo(
                    chat_id=gamer_id,
                    caption="Теперь ждём всех, можешь поделиться ссылкой: <ссылка на бота> или qr-чиком",
                    photo="qr/qr.jpeg"
                )
            except Exception as e:
                logger.error(f"Error, while sending message to user: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        player_telegram_id = update.effective_user.id
        logger.debug(f"{GAMER} {player_telegram_id} called {inspect.currentframe().f_code.co_name}")
        query = update.callback_query
        logger.debug(f"query: {query}")
        try:
            answers = ["Ок", "Заебись", "Хорошо", "Пиздато", "Класс", "Ахуенно"]
            await query.answer(random.choice(answers))
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            logger.error(f"Something went wrong, while hiding old keyboard in gamer callback: {e}")
        variant_id = query.data.split(":")[-1]
        logger.debug(f"got {variant_id} callback from {player_telegram_id} user")
        try:
            new_variant = self.connector.get_variant(variant_id)
            player = self.connector.get_player_by_telegram_id(player_telegram_id)
            all_answers = self.connector.get_answers_by_user(player.id)
            logger.debug(f"new_variant: {new_variant}")
            logger.debug(f"player: {player}")
            logger.debug(f"all_answers: {all_answers}")
            if len(all_answers) < 1:
                self.connector.create_answer(new_variant.id, player.telegram_id, new_variant.answer_text, time.time())
                self.connector.increase_result_score(player_telegram_id, player.game_session_id, int(new_variant.is_correct))
                return
            last_answer = all_answers[-1]
            logger.debug(f"last_answer: {last_answer}")
            # if last_answer is None:
            #     self.connector.create_answer(new_variant.id, player.id, new_variant.answer_text, time.time())
            #     self.connector.increase_result_score(player.id, player.game_session_id, int(new_variant.is_correct))
            # else:
            old_variant = self.connector.get_variant(last_answer.variant_id)
            logger.debug(f"old_variant: {old_variant}")
            if old_variant is not None:
                if new_variant.question_id != old_variant.question_id:
                    self.connector.create_answer(new_variant.id, player_telegram_id, new_variant.answer_text, time.time())
                    self.connector.increase_result_score(player_telegram_id, player.game_session_id, int(new_variant.is_correct))
        except Exception as e:
            logger.error(f"Something gone wrong, while handling user answer: {e}")

from queries import db_connector
gamer_flow = GamerFlow(db_connector)
