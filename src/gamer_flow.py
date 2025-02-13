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
# from gamer_constants import *
from gamer_settings import *
# from constants import *
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
        await update.message.reply_text("Добро пожаловать, игрок!\nНапиши, как тебя называть?")
        username = update.effective_user.username
        game_session_id = self.connector.get_game_session_by_code("LEXA").id
        player = self.connector.create_player(gamer_id, username, f"{NICKNAME_TO_USER}", None, game_session_id)
        self.connector.create_or_update_result(player.id, game_session_id, 0)
        logger.debug("Режим игрока запущен.")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        gamer_id = update.effective_user.id
        logger.debug(f"{GAMER} {gamer_id} called {inspect.currentframe().f_code.co_name}")
        # await update.message.reply_text("Игрок: ваше сообщение получено.")
        # state = self.connector.get_player_by_telegram_id(gamer_id).

        text = update.message.text.strip()
        logger.debug(f"Сообщение от игрока получено. text = {text}")

        player = self.connector.get_player_by_telegram_id(gamer_id)
        # if state == f"{CODE_TO_GAME}":
        #     try:
        #         game_session_id = self.connector.get_game_session_by_code(text).id
        #     except Exception as e:
        #         logger.error("User entered incorrect game code")
        #         await context.bot.send_message(
        #             chat_id=gamer_id,
        #             text="Такой игры нет, попробуй другой код",
        #         )
        #         return
        #     # self.connector.update_player_state_by_telegram_id(gamer_id, f"{NICKNAME_TO_USER}")
        #     # self.connector.update_player_game_session_by_telegram_id(gamer_id, game_session_id)
        #     # replase two database queries to one
        #     player = self.connector.get_player_by_telegram_id(gamer_id)
        #     player.state = f"{NICKNAME_TO_USER}"
        #     player.game_session_id = game_session_id
        #     self.connector.commit()
        #     await context.bot.send_message(
        #         chat_id=gamer_id,
        #         text="Отлично, теперь нужно ввести свой никнейм",
        #     )
        #     return
        # el
        if player.state == NICKNAME_TO_USER:
            player.nickname = text
            player.state = f"{WAITING_START}"
            self.connector.commit()
            await context.bot.send_message(
                chat_id=gamer_id,
                text="Теперь ждём всех",
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        player_telegram_id = update.effective_user.id
        logger.debug(f"{GAMER} {player_telegram_id} called {inspect.currentframe().f_code.co_name}")
        query = update.callback_query
        try:
            answers = ["Ок", "Заебись", "Хорошо", "Пиздато", "Класс", "Ахуенно"]
            await query.answer(random.choice(answers))
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            logger.error(f"Something went wrong, while hiding old keyboard in gamer callback: {e}")
        variant_id = query.data
        logger.debug(f"got {variant_id} callback from {player_telegram_id} user")
        try:
            new_variant = self.connector.get_variant(variant_id)
            player = self.connector.get_player_by_telegram_id(player_telegram_id)
            last_answer = self.connector.get_answers_by_user(player.id)[-1]
            old_variant = self.connector.get_variant(last_answer.variant_id)
            if new_variant.question_id != old_variant.question_id:
                self.connector.create_answer(new_variant.id, player.id, new_variant.answer_text, time.time())
                self.connector.increase_result_score(player.id, player.game_session_id, int(new_variant.is_correct))
        except Exception as e:
            logger.error(f"Something gone wrong, while handling user answer: {e}")

from queries import db_connector
gamer_flow = GamerFlow(db_connector)
