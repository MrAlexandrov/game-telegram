# admin_flow.py
"""
Модуль, инкапсулирующий админскую логику.
Состояние администратора хранится в базе данных (через модель AdminSession).
Методы класса AdminFlow получают актуальное состояние из базы и обновляют его,
что позволяет сохранять данные даже при перезапуске приложения.
"""

import os
from telegram import (
    CallbackQuery,
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
)
from logger import get_logger
from sqlalchemy.orm import Session
from queries import DatabaseConnector
from models import Game, Question, Variant
from settings import ROOT_ID
import inspect
from admin_constants import *
from admin_options import (
    admin_options,
    game_options,
    question_options,
    variant_options,
)
from admin_settings import *
from inline_buttons_generator import generate_inline_buttons_by_state
import asyncio
from utils import generate_qr_code

logger = get_logger(__name__)

CHANGE_QUESTION = "change_question"

class AdminFlow:
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector
        self.selected_variants = {}
        self.not_selected_variants = {}
        self.sent_messages = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_id = update.effective_user.id
        logger.debug(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        internal_user = self.connector.get_internal_user_by_telegram_id(ROOT_ID)
        if internal_user is None:
            logger.info(f"Internal user for ROOT_ID {ROOT_ID} не найден. Создаем нового.")
            internal_user = self.connector.create_internal_user(telegram_id=ROOT_ID, nickname="Это же я", hashed_password="Он пока не нужен")
            logger.info(f"Создан внутренний пользователь: {internal_user}")
        else:
            logger.info(f"Внутренний пользователь для ROOT_ID {ROOT_ID} уже существует: {internal_user}")

        internal_user = self.connector.get_internal_user_by_telegram_id(admin_id)
        current_state = internal_user.state 
        if current_state.startswith(f"{ADMIN}:{GAME_WORKFLOW}:"):
            game_session_id = current_state.split(":")[-1]
            game_session = self.connector.get_game_session(game_session_id)
            if game_session is not None:
                current_question_id = game_session.current_question_id
                questions = self.connector.get_questions_by_game(game_session.game_id)
                question_number = next(i for i, q in enumerate(questions) if q.id == current_question_id)
                await self.send_question_to_everyone(update, context, game_session_id, question_number)
                return

        new_state = f"{ADMIN}:{ADMIN_OPTIONS}"
        self.connector.update_internal_user_state(admin_id, new_state)
        # await admin_options(update, context)
        reply_markup = await generate_inline_buttons_by_state(state=ADMIN_OPTIONS)
        await context.bot.send_message(
            chat_id=admin_id,
            text=ADMIN_STATES[ADMIN_OPTIONS][BEGIN_MESSAGE],
            reply_markup=reply_markup,
        )
        logger.info(f"Админ {admin_id} запущен в режиме '{ADMIN_OPTIONS}'.")

    # TODO: separate this handler, to make it more readable
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обрабатывает inline callback-ы.
        """
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        query = update.callback_query
        data = query.data  # ожидается формат "{ADMIN}:<команда>"

        logger.info(f"{ADMIN} {admin_id} calback_data = {data}")

        if not data.startswith(f"{ADMIN}:"):
            await query.answer("Некорректный callback.")
            return
        next_state = data.split(":", 1)[1]
        logger.debug(f"next_state = {next_state}")

        # state = admin:<action>:<maybe id>
        current_state = self.connector.get_internal_user_state(admin_id).split(":")[1]
        logger.info(f"current_state = {current_state}")
        raw_state = next_state.split(":")[0]
        logger.debug(f"raw_state = {raw_state}")

        if next_state.startswith(f"{SHOW_RESULTS}:"):
            await query.edit_message_reply_markup(reply_markup=None)
            game_session_id = next_state.split(":")[-1]
            await self.generate_results(update, context, game_session_id)
            return

        if next_state.startswith(f"{GAME_WORKFLOW}:"):
            await query.edit_message_reply_markup(reply_markup=None)
            game_session_id = next_state.split(":")[-1]
            logger.debug("game is starting")
            await self.start_game(update, context, game_session_id)
            return

        if next_state.startswith(f"{DONE}"):
            await query.edit_message_reply_markup(reply_markup=None)
            question_id = next_state.split(":")[-1]
            new_state = f"{ADMIN}:{QUESTION_OPTIONS}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            for variant in self.selected_variants[question_id]:
                self.connector.update_variant_correctness(variant, True)
            for variant in self.not_selected_variants[question_id]:
                self.connector.update_variant_correctness(variant, False)
            logger.info("Correct varians are saved")
            await context.bot.send_message(
                chat_id=admin_id,
                text="Правильные ответы сохранены",
            )
            game_id = self.connector.get_question(question_id).game_id

            await question_options(update, context, question_id, game_id)
            return

        if next_state.startswith(f"{SELECT}|"):
            variant_id = next_state.split("|")[-1]
            await self.handle_selection(update, context, query, variant_id)
            return

        if next_state.startswith(f"{CHANGE_QUESTION}|"):
            await query.edit_message_reply_markup(reply_markup=None)
            await self.remove_inline_keyboards(update, context)
            admin_id = update.effective_user.id
            game_session_id = self.connector.get_internal_user_by_telegram_id(admin_id).state.split(":")[-1]
            new_question = next_state.split("|")[-1]
            await self.send_question_to_everyone(update, context, game_session_id, int(new_question))
            return

        if next_state.startswith(f"{PAGE_GAMES}"):
            # raw_state = page_games|<number>
            # if len(ADMIN_STATES[raw_state][FORWARD_STATES]) != 1:
            #     logger.error(f"should be only one FORWARD_STATES, got: {ADMIN_STATES[raw_state][FORWARD_STATES]}")
            # action = ADMIN_STATES[raw_state][FORWARD_STATES][0]
            internal_user_state_in_db = self.connector.get_internal_user_state(admin_id)
            action = internal_user_state_in_db.split(":")[1]
            if action == GAME_TO_EDIT:
                action = GAME_OPTIONS
            # TODO: resolve it
            # elif action == GAME_TO_DELETE:
            #     action = 
            logger.debug(f"state = {internal_user_state_in_db}")
            new_page = int(next_state.split("|", 1)[-1])
            await self.handle_changing_page_games(update, context, admin_id, new_page, action)
            return

        if next_state.startswith(f"{PAGE_QUESTIONS}"):
            # raw_state = page_question|<number>
            # if len(ADMIN_STATES[raw_state][FORWARD_STATES]) != 1:
            #     logger.error(f"should be only one FORWARD_STATES, got: {ADMIN_STATES[raw_state][FORWARD_STATES]}")
            # action = ADMIN_STATES[raw_state][FORWARD_STATES][0]
            internal_user_state_in_db = self.connector.get_internal_user_state(admin_id)
            action = internal_user_state_in_db.split(":")[1]
            if action == QUESTION_TO_EDIT:
                action = QUESTION_OPTIONS
            # TODO: write unify handler, using config
            logger.debug(f"state = {internal_user_state_in_db}")
            new_page = int(next_state.split("|", 1)[-1])
            game_id = self.connector.get_internal_user_state(admin_id).split(":")[-1]
            logger.info(f"next_state.startswith(\"{PAGE_QUESTIONS}\") game_id = {game_id}")
            await self.handle_changing_page_questions(update, context, game_id, new_page, action)
            return

        if next_state.startswith(f"{PAGE_VARIANTS}"):
            # if len(ADMIN_STATES[raw_state][FORWARD_STATES]) != 1:
            #     logger.error(f"should be only one FORWARD_STATES, got: {ADMIN_STATES[raw_state][FORWARD_STATES]}")
            # action = ADMIN_STATES[raw_state][FORWARD_STATES][0]
            internal_user_state_in_db = self.connector.get_internal_user_state(admin_id)
            action = internal_user_state_in_db.split(":")[1]
            if action == VARIANT_TO_EDIT:
                action = VARIANT_OPTIONS
            # TODO: rewrite
            logger.debug(f"state = {internal_user_state_in_db}")
            new_page = int(next_state.split("|", 1)[-1])
            question_id = self.connector.get_internal_user_state(admin_id).split(":")[-1]
            await self.handle_changing_page_variants(update, context, question_id, new_page, action)
            return

        if next_state.startswith(f"{CHANGE_CORRECTNESS}"):
            question_id = next_state.split(":")[-1]
            await query.edit_message_reply_markup(reply_markup=None)
            await self.change_correctness(update, context, question_id)
            return

        if next_state.startswith(f"{WAITING_START}:"):
            game_id = next_state.split(":")[-1]
            await query.edit_message_reply_markup(reply_markup=None)
            await self.waiting_start(update, context, game_id, "LEXA")
            generate_qr_code("<ссылка на бота>")
            return

        if current_state not in ADMIN_STATES:
            await context.bot.send_message(
                chat_id=admin_id,
                text="Неизвестное состояние",
            )
            return
        if (ADMIN_STATES[current_state][ACTION] != CALLBACK
            or ADMIN_STATES[current_state][ACTION] != LIST):
            await context.bot.send_message(
                chat_id=admin_id,
                text="На данном состоянии не ожидается нажатие кнопок",
            )
        await query.edit_message_reply_markup(reply_markup=None)
        # if ADMIN_STATES[current_state][END_MESSAGE]:
        #     await context.bot.send_message(
        #         chat_id=admin_id,
        #         text=ADMIN_STATES[current_state][END_MESSAGE],
        #     )
        # new_state = f"{ADMIN}:{next_state}"
        logger.debug(f"new_state in db = {data}")
        self.connector.update_internal_user_state(admin_id, data)
        reply_markup = None
        if ADMIN_STATES[raw_state][FORWARD_STATES]:
            game_id, question_id, variant_id = None, None, None
            if raw_state == GAME_OPTIONS or raw_state == GAME_TO_START:
                game_id = next_state.split(":")[-1]
            elif raw_state == QUESTION_OPTIONS:
                question_id = next_state.split(":")[-1]
                game_id = self.connector.get_question(question_id).game_id
            elif raw_state == VARIANT_OPTIONS:
                question_id = next_state.split(":")[-1]
                game_id = self.connector.get_question(question_id).game_id
            # TODO: add handle deleting

            reply_markup = await generate_inline_buttons_by_state(state=raw_state, game_id=game_id, question_id=question_id)
        if ADMIN_STATES[raw_state][ACTION] == LIST:
            reply_markup = await self.handle_listing(update, context, next_state)
        logger.debug(f"reply_markup = {reply_markup}")
        await context.bot.send_message(
            chat_id=admin_id,
            text=ADMIN_STATES[raw_state][BEGIN_MESSAGE],
            reply_markup=reply_markup,
        )
        return

        if command.startswith(f"{SELECT}|"):
            variant_id = command.split("|")[-1]
            await self.handle_selection(update, context, query, variant_id)
            return

        if command.startswith(f"{PAGE_GAMES}"):
            new_page = int(command.split("|", 1)[-1])
            await self.handle_changing_page_games(update, context, admin_id, new_page)
            return
        
        if command.startswith(f"{PAGE_QUESTIONS}"):
            new_page = int(command.split("|", 1)[-1])
            game_id = self.connector.get_internal_user_state(admin_id).split(":")[-1]
            logger.info(f"command.startswith(\"{PAGE_QUESTIONS}\") game_id = {game_id}")
            await self.handle_changing_page_questions(update, context, game_id, new_page)
            return

        await query.edit_message_reply_markup(reply_markup=None)
        # TODO: add state checking for all callback
        if command == f"{ADMIN_OPTIONS}":
            await self.start(update, context)
        elif command.startswith(f"{DONE}:"):                                    # question_id
            # TODO: rewrite this
            # state = {ADMIN}:{VARIANT_OPTIONS}:
            question_id = command.split(":")[-1]
            self.connector.update_internal_user_state(admin_id, question_id)
            for variant in self.selected_variants[question_id]:
                self.connector.update_variant_correctness(variant, True)
            for variant in self.not_selected_variants[question_id]:
                self.connector.update_variant_correctness(variant, False)
            logger.info("Correct varians are saved")
            await context.bot.send_message(
                chat_id=admin_id,
                text="Правильные ответы сохранены",
            )
            game_id = self.connector.get_question(question_id).game_id

            await question_options(update, context, question_id, game_id)
        # TODO: unify this
        elif command == f"{CREATE_GAME}":                                       # nothing
            self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{CREATE_GAME}")
            await self.create_game(update, context)
        elif command == f"{GAME_TO_EDIT}":
            await self.game_to_edit(update, context, admin_id)
        elif command == f"{GAME_TO_DELETE}":                                       # noting
            await self.game_to_delete(update, context, admin_id)
        elif (
               command.startswith(f"{GAME_OPTIONS}:")
            or command.startswith(f"{ADD_QUESTION}:")
            or command.startswith(f"{QUESTION_TO_EDIT}:")
            or command.startswith(f"{QUESTION_TO_DELETE}:")
            or command.startswith(f"{GAME_TO_DELETE}:")
        ):
            game_id = command.split(":")[-1]
            action = command.split(":")[0]
            self.connector.update_internal_user_state(admin_id, data)
            if action == GAME_OPTIONS:
                await self.edit_game_by_game_id(update, context, admin_id, game_id)
            elif action == ADD_QUESTION:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text="Введите текст вопроса",
                )
            elif action == QUESTION_TO_EDIT:
                await self.question_to_edit(update, context, game_id)
            elif action == QUESTION_TO_DELETE:
                await self.question_to_delete(update, context, game_id)
            elif action == GAME_TO_DELETE:
                await self.delete_game_by_game_id(update, context, admin_id, game_id)
            else:
                logger.error("Unmatched pattern with game_id")
        elif (
               command.startswith(f"{QUESTION_OPTIONS}:")
            or command.startswith(f"{DELETE_QUESTION}:")
            or command.startswith(f"{EDIT_QUESTION_TEXT}:")
            or command.startswith(f"{VARIANT_OPTIONS}:")
            or command.startswith(f"{ADD_VARIANT}:")
            or command.startswith(f"{UPDATE_IMAGE}:")
            or command.startswith(f"{CHANGE_CORRECTNESS}:")
            # or command.startswith(f"{VARIANT_TO_DELETE}:")
        ):
            question_id = command.split(":")[-1]
            action = command.split(":")[0]
            self.connector.update_internal_user_state(admin_id, data)
            if action == QUESTION_OPTIONS:
                game_id = self.connector.get_question(question_id).game_id
                await question_options(update, context, question_id, game_id)
            elif action == DELETE_QUESTION:
                await self.delete_question_by_question_id(update, context, question_id)
            elif action == EDIT_QUESTION_TEXT:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text="Введите текст вопроса",
                )
            elif action == VARIANT_OPTIONS:
                await variant_options(update, context, question_id)
            elif action == ADD_VARIANT:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text="Введите текст варианта",
                )
            elif action == UPDATE_IMAGE:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text="Пришлите изображение в виде фото",
                )
            elif action == CHANGE_CORRECTNESS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text="Выберите правильные варианты ответов",
                )
            # elif action == VARIANT_TO_DELETE:
            #     await context.bot.send_message(
            #         chat_id=admin_id,
            #         text="Выберите вариант, который хотите удалить",
            #     )
            #     await self.variant_to_delete()
            #     await variant_options(...)
            else:
                logger.error("Unmatched pattern with game_id")
        else:
            await query.answer("Неизвестная команда.")

    async def handle_listing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: str):
        admin_id = update.effective_user.id
        logger.debug(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")

        logger.debug(f"state = {state}")
        action = state.split(":")[0]
        if action == GAME_TO_EDIT:
            internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
            return await self.game_to_edit(update, context, internal_user_id)
        elif action == GAME_TO_DELETE:
            internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
            return await self.game_to_delete(update, context, internal_user_id)
        elif action == QUESTION_TO_EDIT:
            game_id = state.split(":")[-1]
            return await self.question_to_edit(update, context, game_id)
        elif action == QUESTION_TO_DELETE:
            game_id = state.split(":")[-1]
            return await self.question_to_delete(update, context, game_id)
        elif action == VARIANT_TO_EDIT:
            question_id = state.split(":")[-1]
            return await self.variant_to_edit(update, context, question_id)
        elif action == VARIANT_TO_DELETE:
            question_id = state.split(":")[-1]
            return await self.variant_to_delete(update, context, question_id)
        elif action == GAME_TO_START:
            internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
            return await self.game_to_start(update, context, internal_user_id)
        else:
            logger.error("incorrect state")

    async def handle_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery, variant_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        print(f"variant_id = {variant_id}")
        self.update_variant_correctness(update, context, variant_id)
        # question_text = self.connector.get_question(question_id).question_text
        question_id = self.connector.get_variant(variant_id).question_id
        variants = self.connector.get_variants_by_question(question_id)

        buttons = [
            InlineKeyboardButton(
                f"✅ {variant.answer_text}" if variant.id in self.selected_variants[question_id] else variant.answer_text, 
                callback_data=f"{ADMIN}:{SELECT}|{variant.id}",
            )
            for variant in variants
        ]
        # Разбиваем кнопки на строки по 2 кнопки
        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        # Добавляем строку с кнопкой DONE_LABEL
        keyboard.append([InlineKeyboardButton(DONE_LABEL, callback_data=f"{ADMIN}:{DONE}:{question_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    async def waiting_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, game_code: str, game_session_state = f"{WAITING_START}"):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")

        game_session_id = self.connector.create_game_session(game_id, "LEXA", f"{WAITING_START}").id
        self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{WAITING_START}:{game_session_id}")
        keyboard = [
            [InlineKeyboardButton("Поехали", callback_data=f"{ADMIN}:{GAME_WORKFLOW}:{game_session_id}")] 
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=admin_id,
            text="Можешь жмакнуть \"Поехали\"",
            reply_markup=reply_markup,
        )

    async def create_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Запускает процесс создания игры.
        Обновляет состояние в базе до f"{ADMIN}:{CREATE_GAME}" и запрашивает название игры.
        """
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")

        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Введите название игры:")
        logger.info(f"Админ {admin_id} переведен в состояние '{ADMIN}:{CREATE_GAME}' (ожидание названия игры).")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обрабатывает текстовые сообщения.
        В зависимости от текущего состояния (из базы), принимает ввод:
        """
        admin_id = update.effective_user.id
        text = update.message.text.strip()
        if not text:
            await update.message.reply_text("Нужно что-то ввести!")
            return
        internal_user = self.connector.get_internal_user_by_telegram_id(admin_id)
        self.connector.get_games_by_creator_id(internal_user.id)
        self.connector.get_players_by_game_session_id()
        self.send_message_to_everyone(update, context,)
        current_state = self.connector.get_internal_user_state(admin_id).split(":", 1)[1]
        action = current_state.split(":")[0]
        if ADMIN_STATES[action][ACTION] != TEXT:
            logger.debug("text was inserted while it does not expected")
            await context.bot.send_message(
                chat_id=admin_id,
                text="В данном состоянни текст не ожидается",
            )
            return
        if action == CREATE_GAME:
            internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
            game = self.connector.create_game("quiz", text, created_by=internal_user_id)

            game_id = game.id
            new_state = f"{ADMIN}:{ADMIN_OPTIONS}"

            self.connector.update_internal_user_state(admin_id, new_state)
            logger.info(f"Game {game_id} created. State updated to {new_state}.")
            await admin_options(update, context)
        elif action == ADD_QUESTION:
            game_id = current_state.split(":")[-1]
            question = self.connector.create_question(game_id, text)
            question_id = question.id

            new_state = f"{ADMIN}:{GAME_OPTIONS}:{game_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            logger.info(f"Question {question_id} created. State updated to {new_state}.")
            await game_options(update, context, game_id)
            # await question_options(update, context, question_id, game_id)
        elif action == EDIT_QUESTION_TEXT:
            question_id = current_state.split(":")[-1]
            game_id = self.connector.update_question_text(question_id, text).game_id

            new_state = f"{ADMIN}:{QUESTION_OPTIONS}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            await question_options(update, context, question_id, game_id)
        elif action == ADD_VARIANT:
            question_id = current_state.split(":")[-1]
            self.connector.create_variant(question_id, text)
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"Вариант ответа {text} сохранён",
            )
            new_state = f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            await variant_options(update, context, question_id)
        elif action == EDIT_VARIANT_TEXT:
            variant_id = current_state.split(":")[-1]
            question_id = self.connector.update_variant_text(variant_id, text).question_id

            new_state = f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            await variant_options(update, context, question_id)
        else:
            logger.error("Unknows state")
            await context.bot.send_message(
                chat_id=admin_id,
                text="Неизвестное состояние, попробуйте ввести /start"
            )
        # if current_state == f"{ADMIN}:{CREATE_GAME}":
        #     internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
        #     game = self.connector.create_game("quiz", text, created_by=internal_user_id)

        #     game_id = game.id
        #     new_state = f"{ADMIN}:{GAME_OPTIONS}:{game_id}"

        #     self.connector.update_internal_user_state(admin_id, new_state)
        #     logger.info(f"Game {game_id} created. State updated to {new_state}.")

        #     await update.message.reply_text(f"Игра '{text}' создана.")
        #     await game_options(update, context, game_id)
        # elif current_state.startswith(f"{ADMIN}:{ADD_QUESTION}:"):
        #     game_id = current_state.split(":")[-1]
        #     question = self.connector.create_question(game_id, text)
        #     question_id = question.id

        #     new_state = f"{ADMIN}:{EDIT_QUESTION_TEXT}:{question_id}"
        #     self.connector.update_internal_user_state(admin_id, new_state)
        #     logger.info(f"Question {question_id} created. State updated to {new_state}.")
        #     await question_options(update, context, question_id, game_id)
        # elif current_state.startswith(f"{ADMIN}:{EDIT_QUESTION_TEXT}:"):
        #     question_id = current_state.split(":")[-1]
        #     print(f"************************** question_id = {question_id}")
        #     print(f"***************** current_state = {current_state}")
        #     self.connector.update_question_text(question_id, text)
        #     new_state = f"{ADMIN}:{QUESTION_OPTIONS}:{question_id}"
        #     self.connector.update_internal_user_state(admin_id, new_state)
        #     game_id = self.connector.get_question(question_id).game_id
        #     await question_options(update, context, question_id, game_id)
        # elif current_state.startswith(f"{ADMIN}:{ADD_VARIANT}:"):
        #     question_id = current_state.split(":")[-1]
        #     self.connector.create_variant(question_id, text)
        #     await context.bot.send_message(
        #         chat_id=admin_id,
        #         text=f"Вариант ответа {text} сохранён",
        #     )
        #     new_state = f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}"
        #     self.connector.update_internal_user_state(admin_id, new_state)
        #     await variant_options(update, context, question_id)
        # else:
        #     await update.message.reply_text("Неизвестное состояние. Попробуйте ввести /start.")

    async def change_correctness(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите правильные ответы",
        )
        await self.display_question(update, context, question_id)
        return

    def get_question_data_to_send_players(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
        admin_id = update.effective_chat.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        question = self.connector.get_question(question_id)
        question_text = question.question_text
        variants = self.connector.get_variants_by_question(question_id)

        raw_variants = self.connector.get_correct_variants_by_question_id(question_id)
        self.selected_variants[question_id] = set(variant.id for variant in raw_variants)

        buttons = [
            InlineKeyboardButton(
                variant.answer_text, callback_data=f"{GAME_WORKFLOW}:{variant.id}",
            )
            for variant in variants
        ]
        # Разбиваем кнопки на строки по 2 кнопки
        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        # Добавляем строку с кнопкой DONE_LABEL
        # keyboard.append([InlineKeyboardButton(DONE_LABEL, callback_data=f"{ADMIN}:{DONE}:{question_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        path_to_media = question.path_to_media
        return question_text, reply_markup, path_to_media
        # if path_to_media is None:
        #     await context.bot.send_message(
        #         chat_id=admin_id,
        #         text=question_text,
        #         reply_markup=reply_markup,
        #     )
        # else:
        #     await context.bot.send_photo(
        #         chat_id=admin_id,
        #         caption=question_text,
        #         reply_markup=reply_markup,
        #         photo=path_to_media,
        #     )
        # return


    async def display_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
        admin_id = update.effective_chat.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        question = self.connector.get_question(question_id)
        question_text = question.question_text
        variants = self.connector.get_variants_by_question(question_id)

        raw_variants = self.connector.get_correct_variants_by_question_id(question_id)
        self.selected_variants[question_id] = set(variant.id for variant in raw_variants)

        buttons = [
            InlineKeyboardButton(
                f"✅ {variant.answer_text}" if variant.id in self.selected_variants[question_id] else variant.answer_text, callback_data=f"{ADMIN}:{SELECT}|{variant.id}",
            )
            for variant in variants
        ]
        # Разбиваем кнопки на строки по 2 кнопки
        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        # Добавляем строку с кнопкой DONE_LABEL
        keyboard.append([InlineKeyboardButton(DONE_LABEL, callback_data=f"{ADMIN}:{DONE}:{question_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        path_to_media = question.path_to_media
        if path_to_media is None:
            await context.bot.send_message(
                chat_id=admin_id,
                text=question_text,
                reply_markup=reply_markup,
            )
        else:
            await context.bot.send_photo(
                chat_id=admin_id,
                caption=question_text,
                reply_markup=reply_markup,
                photo=path_to_media,
            )
        return

    def update_variant_correctness(self, update: Update, context: ContextTypes.DEFAULT_TYPE, variant_id: str, is_correct: bool = True):
        variant = self.connector.get_variant(variant_id)
        self.update_variant_correctness_cached(update=update, context=context, variant_id=variant_id, question_id=variant.question_id)

    def update_variant_correctness_cached(self, update: Update, context: ContextTypes.DEFAULT_TYPE, variant_id: str, question_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        if question_id not in self.selected_variants:
            self.selected_variants[question_id] = set()
        if question_id not in self.not_selected_variants:
            self.not_selected_variants[question_id] = set()
        if variant_id in self.selected_variants[question_id]:
            try:
                self.selected_variants[question_id].remove(variant_id)
            except Exception as e:
                logger.error(f"Caught exception: {e}")
            try:
                self.not_selected_variants[question_id].add(variant_id)
            except Exception as e:
                logger.error(f"Caught exception: {e}")
        else:
            try:
                self.selected_variants[question_id].add(variant_id)
            except Exception as e:
                logger.error(f"Caught exception: {e}")
            try:
                self.not_selected_variants[question_id].remove(variant_id)
            except Exception as e:
                logger.error(f"Caught exception: {e}")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обрабатывает фото, если администратор решил прикрепить изображение к вопросу.
        """
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        current_state = self.connector.get_internal_user_state(admin_id)
        if not current_state.startswith(f"{ADMIN}:{UPDATE_IMAGE}:"):
            await update.message.reply_text("Фото не ожидается в текущем состоянии.")
            return
        # {ADMIN}:{UPDATE_IMAGE}:<question_id>
        question_id = current_state.split(":")[-1]
        question = self.connector.get_question(question_id)
        game_id = question.game_id
        # Предположим, текст вопроса уже введён и сохранён; извлекаем его из базы, если нужно
        # question_text = "текст_из_базы"  # Здесь вы должны получить фактический текст вопроса, если он сохранён в таблице Question
        # question = self.connector.create_question(game_id, question_text, path_to_media=None)

        photo_file = await update.message.photo[-1].get_file()
        folder = os.path.join("media", game_id)
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f"{question_id}.jpg")
        await photo_file.download_to_drive(file_path)
        self.connector.create_media(
            question_id=question_id,
            media_type="image",
            url=file_path,
            description="",
            display_type="individual",
        )
        question.path_to_media = file_path

        self.connector.commit()
    
        await update.message.reply_text("Фото добавлено к вопросу.")

        # После фото можно перейти к вводу вариантов (если ещё не введены)
        logger.info("Photo processed for question.")

        new_state = f"{ADMIN}:{QUESTION_OPTIONS}:{question_id}"
        self.connector.update_internal_user_state(admin_id, new_state)

        await question_options(update, context, question_id, game_id)

    async def variant_to_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        variants = self.connector.get_variants_by_question(question_id)
        reply_markup = self.generate_inline_buttons_for_variants(update, context, variants, 1, f"{EDIT_VARIANT_TEXT}")
        return reply_markup
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите вариант, который хотите изменить",
            reply_markup=reply_markup,
        )
        return
    
    async def variant_to_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        variants = self.connector.get_variants_by_question(question_id)
        reply_markup = self.generate_inline_buttons_for_variants(update, context, variants, 1, f"{DELETE_VARIANT}")
        return reply_markup
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите вариант, который хотите удалить",
            reply_markup=reply_markup,
        )
        return

    async def question_to_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        questions = self.connector.get_questions_by_game(game_id)
        reply_markup = self.generate_inline_buttons_for_questions(update, context, questions, 1, f"{QUESTION_OPTIONS}")
        return reply_markup
        print(f"**************************************** game_id = {game_id}, reply_markup = {reply_markup}")
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите вопрос, который хотите изменить",
            reply_markup=reply_markup,
        )
        return

    async def question_to_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        questions = self.connector.get_questions_by_game(game_id)
        reply_markup = self.generate_inline_buttons_for_questions(update, context, questions, 1, f"{DELETE_QUESTION}")
        return reply_markup
        print(f"**************************************** game_id = {game_id}, reply_markup = {reply_markup}")
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите вопрос, который хотите удалить",
            reply_markup=reply_markup,
        )
        return

    async def game_to_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, internal_user_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        games = self.connector.get_games_by_creator_id(internal_user_id)
        reply_markup = self.generate_inline_buttons_for_games(update, context, games, 1, f"{GAME_OPTIONS}")
        return reply_markup
        print(f"***************************************** admin_id = {admin_id}, reply_markup = {reply_markup}")
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите игру, которую хотите изменить",
            reply_markup=reply_markup,
        )
        return

    async def game_to_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, internal_user_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        games = self.connector.get_games_by_creator_id(internal_user_id)
        reply_markup = self.generate_inline_buttons_for_games(update, context, games, 1, f"{DELETE_GAME}")
        return reply_markup
        print(f"***************************************** admin_id = {admin_id}, reply_markup = {reply_markup}")
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите игру, которую хотите удалить",
            reply_markup=reply_markup,
        )
        return

    async def remove_inline_keyboards(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_id = update.effective_user.id
        logger.debug(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        # Проходим по всем сохранённым сообщениям
        for chat_id, message_ids in list(self.sent_messages.items()):
            for message_id in list(message_ids):
                try:
                    await context.bot.edit_message_reply_markup(
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=None
                    )
                except Exception as e:
                    logger.error(f"Ошибка при редактировании сообщения {message_id} для {chat_id}: {e}")
                    # Удаляем сообщение из списка, если редактирование не удалось
                    try:
                        message_ids.remove(message_id)
                    except Exception as e1:
                        logger.error(f"Cant remove message: {message_id}")
            # Если для chat_id больше нет сообщений, удаляем ключ из словаря
            if not message_ids:
                del self.sent_messages[chat_id]

    async def generate_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_session_id: str):
        logger.debug(f"game_session_id: {game_session_id}")
        results = self.connector.get_results_for_game_session(game_session_id)
        logger.debug(f"results: {results}")
        message = "Итак, вот результаты:\n"
        for i, (nickname, score, total_time) in enumerate(results, start=1):
            message += f"{i}. {nickname}: {score}\n"
        players = self.connector.get_players_by_game_session_id(game_session_id)
        player_ids = [player.telegram_id for player in players]
        await self.send_message_to_everyone(update, context, player_ids, message, None)

    async def finish_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_session_id: str):
        players = self.connector.get_players_by_game_session_id(game_session_id)
        player_ids = [player.telegram_id for player in players]
        await self.send_message_to_everyone(update, context, player_ids, "Игра закончена!\nГотовы к реультатам?", None, None)
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Показать результаты", callback_data=f"{ADMIN}:{SHOW_RESULTS}:{game_session_id}")]
        ])
        admin_id = update.effective_user.id
        await context.bot.send_message(
            chat_id=admin_id,
            text="Теперь можно показать результаты",
            reply_markup=reply_markup,
        )

    async def send_message_to_everyone(self, update, context, user_ids, text, reply_markup, path_to_image=None):
        max_retries = 5
        retry_delay = 0.5
        for player in user_ids:
            attempts = 0
            while attempts < max_retries:
                try:
                    if path_to_image:
                        sent_message = await context.bot.send_photo(
                            chat_id=player,
                            photo=path_to_image,
                            caption=text,
                            reply_markup=reply_markup,
                        )
                    else:
                        sent_message = await context.bot.send_message(
                            chat_id=player,
                            text=text,
                            reply_markup=reply_markup,
                        )

                    # Сохраняем message_id в словаре для данного chat_id
                    self.sent_messages.setdefault(player, []).append(sent_message.message_id)
                    break  # Если отправка успешна, выходим из цикла
                except Exception as e:
                    attempts += 1
                    logger.error(f"Ошибка при отправке сообщения {player} (попытка {attempts}/{max_retries}): {e}")
                    if attempts < max_retries:
                        await asyncio.sleep(retry_delay)  # Ждём перед повторной попыткой
                    else:
                        logger.error(f"Не удалось отправить сообщение {player} после {max_retries} попыток.")

        logger.debug(f"sent messages = {self.sent_messages}")

    async def wait_and_hide_keyboards(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_number: int):
        admin_id = update.effective_user.id
        await asyncio.sleep(15)
        await self.remove_inline_keyboards(update, context)
        logger.debug(f"woke up, removed keyboards")

        keyboard = [
            [InlineKeyboardButton("➡️", callback_data=f"{ADMIN}:{CHANGE_QUESTION}|{question_number + 1}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=admin_id,
            text="Можешь переключать вопросы",
            reply_markup=reply_markup,
        )
        return

    async def send_question_to_everyone(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_session_id: str, question_number: int):
        admin_id = update.effective_user.id
        logger.debug(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        players = self.connector.get_players_by_game_session_id(game_session_id)
        game_id = self.connector.get_game_session(game_session_id).game_id
        questions = self.connector.get_questions_by_game(game_id)
        logger.debug(f"questions = {questions}")
        if len(questions) <= question_number:
            await self.finish_game(update, context, game_session_id)
            return
        current_question_id = questions[question_number].id
        logger.debug(f"current_question_id = {current_question_id}")
        self.connector.update_game_session_state(game_session_id, current_question_id)
        self.connector.update_game_session_question_id(game_session_id, current_question_id)
        text, reply_markup, path_to_image = self.get_question_data_to_send_players(update, context, current_question_id)
        logger.debug(f"text = {text}, reply_markup = {reply_markup}, path_to_image = {path_to_image}")
        player_ids = [player.telegram_id for player in players]
        await self.send_message_to_everyone(update, context, player_ids, text, reply_markup, path_to_image)

        logger.debug(f"going sleep")
        asyncio.create_task(self.wait_and_hide_keyboards(update, context, question_number))
        # await asyncio.sleep(3)
        # await self.remove_inline_keyboards(update, context)

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_session_id: str):
        admin_id = update.effective_user.id
        self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{GAME_WORKFLOW}:{game_session_id}")
        await self.send_question_to_everyone(update, context, game_session_id, 0)

    async def game_to_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, internal_user_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        games = self.connector.get_games_by_creator_id(internal_user_id)
        reply_markup = self.generate_inline_buttons_for_games(update, context, games, 1, f"{WAITING_START}")
        return reply_markup

    async def edit_game_by_game_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: str, game_id: str):
        new_state = f"{ADMIN}:{GAME_OPTIONS}:{game_id}"
        self.connector.update_internal_user_state(admin_id, new_state)
        await game_options(update, context, game_id)

    async def delete_question_by_question_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
        game_id = self.connector.get_question(question_id).game_id
        new_state = f"{ADMIN}:{GAME_OPTIONS}:{game_id}"
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        self.connector.update_internal_user_state(admin_id, new_state)
        await context.bot.send_message(
            chat_id=admin_id,
            text="Функционал удаления вопроса, пока что, замокан 🙁",
        )
        await game_options(update, context, game_id)

    async def delete_game_by_game_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: str, game_id: str):
        new_state = f"{ADMIN}:{ADMIN_OPTIONS}"
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        self.connector.update_internal_user_state(admin_id, new_state)
        await context.bot.send_message(
            chat_id=admin_id,
            text="Функционал удаления игры, пока что, замокан 🙁",
        )
        await admin_options(update, context)
        logger.info(f"Админ {admin_id} запущен в режиме '{ADMIN_OPTIONS}'.")

    async def delete_variant_by_variant_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, variant_id: str):
        question_id = self.connector.get_variant(variant_id)
        new_state = f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}"
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called delete_variant_by_variant_id")
        self.connector.delete_variant(variant_id)
        await variant_options(update, context, question_id)

    def generate_inline_buttons_for_variants(self, update: Update, context: ContextTypes.DEFAULT_TYPE, variants: list[Variant], page = 1, action: str = f"{VARIANT_OPTIONS}"):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        per_page = 6
        total_variants = len(variants)
        total_pages = (total_variants + per_page - 1) // per_page # round up

        start = (page - 1) * per_page
        end = start + per_page
        page_variants = variants[start:end]

        buttons = []
        for variant in page_variants:
            # for question its title, TODO: add unify method for any object
            button = InlineKeyboardButton(variant.answer_text, callback_data=f"{ADMIN}:{action}:{variant.id}")
            buttons.append(button)

        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{ADMIN}:{PAGE_VARIANTS}|{page - 1}"))
        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{ADMIN}:{PAGE_VARIANTS}|{page + 1}"))
        if navigation_buttons:
            keyboard.append(navigation_buttons)
        question_id = self.connector.get_internal_user_state(admin_id).split(":")[-1]
        keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}")])
        logger.debug(f"generated keyboard = {keyboard}")
        return InlineKeyboardMarkup(keyboard)

    def generate_inline_buttons_for_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, questions: list[Question], page = 1, action: str = f"{QUESTION_OPTIONS}"):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        per_page = 6
        total_questions = len(questions)
        total_pages = (total_questions + per_page - 1) // per_page # round up

        start = (page - 1) * per_page
        end = start + per_page
        page_questions = questions[start:end]

        buttons = []
        for question in page_questions:
            # for question its title, TODO: add unify method for any object
            button = InlineKeyboardButton(question.question_text, callback_data=f"{ADMIN}:{action}:{question.id}")
            buttons.append(button)

        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{ADMIN}:{PAGE_QUESTIONS}|{page - 1}"))
        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{ADMIN}:{PAGE_QUESTIONS}|{page + 1}"))
        if navigation_buttons:
            keyboard.append(navigation_buttons)
        game_id = self.connector.get_internal_user_state(admin_id).split(":")[-1]
        keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=f"{ADMIN}:{GAME_OPTIONS}:{game_id}")])
        logger.debug(f"generated keyboard = {keyboard}")
        return InlineKeyboardMarkup(keyboard)

    def generate_inline_buttons_for_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE, games: list[Game], page = 1, action: str = f"{GAME_OPTIONS}"):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        per_page = 6
        total_games = len(games)
        total_pages = (total_games + per_page - 1) // per_page # round up

        start = (page - 1) * per_page
        end = start + per_page
        page_games = games[start:end]

        buttons = []
        for game in page_games:
            # for game its title, TODO: add unify method for any object
            button = InlineKeyboardButton(game.title, callback_data=f"{ADMIN}:{action}:{game.id}")
            buttons.append(button)

        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{ADMIN}:{PAGE_GAMES}|{page - 1}"))
        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{ADMIN}:{PAGE_GAMES}|{page + 1}"))
        if navigation_buttons:
            keyboard.append(navigation_buttons)
        keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=f"{ADMIN}:{ADMIN_OPTIONS}")])
        logger.debug(f"generated keyboard = {keyboard}")
        return InlineKeyboardMarkup(keyboard)

    async def handle_changing_page_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, new_page: int, action: str):
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
        games = self.connector.get_games_by_creator_id(internal_user_id)
        reply_markup = self.generate_inline_buttons_for_games(update, context, games, new_page, action)
        logger.debug(f"new reply_markup = {reply_markup}")
        query = update.callback_query
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        await query.answer()  # Обязательно вызываем query.answer(), чтобы убрать "часики" у кнопки

    async def handle_changing_page_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, new_page: int, action: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        questions = self.connector.get_questions_by_game(game_id)
        print(f"********************** (from handle_changing_page_questions): game_id = {game_id}")
        print(f"********************** (from handle_changing_page_questions): questions = {questions}")
        reply_markup = self.generate_inline_buttons_for_questions(update, context, questions, new_page, action)
        logger.debug(f"new reply_markup = {reply_markup}")
        query = update.callback_query
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        await query.answer()  # Обязательно вызываем query.answer(), чтобы убрать "часики" у кнопки

    async def handle_changing_page_variants(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str, new_page: int, action: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        variants = self.connector.get_variants_by_question(question_id)
        reply_markup = self.generate_inline_buttons_for_variants(update, context, variants, new_page, action)
        logger.debug(f"new reply_markup = {reply_markup}")
        query = update.callback_query
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        await query.answer()  # Обязательно вызываем query.answer(), чтобы убрать "часики" у кнопки

# Глобальный объект AdminFlow; если у вас может быть несколько администраторов, лучше создавать его при /start для каждого.
# Здесь мы инициализируем его с использованием сессии из db_connector.
from queries import db_connector
admin_flow = AdminFlow(db_connector)
