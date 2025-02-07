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
from utils import is_valid_uuid4

logger = get_logger(__name__)

CHANGE_QUESTION     = "change_question"
PAGE                = "page"

class AdminFlow:
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector
        self.selected_variants = {}
        self.not_selected_variants = {}
        self.sent_messages = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        logger.debug(f"{ADMIN} {user_id} called {inspect.currentframe().f_code.co_name}")
        # TODO: separate this
        internal_user = self.connector.get_internal_user_by_telegram_id(ROOT_ID)
        if internal_user is None:
            logger.debug(f"Internal user for ROOT_ID {ROOT_ID} не найден. Создаем нового.")
            internal_user = self.connector.create_internal_user(
                telegram_id=user_id,
                state=ADMIN_OPTIONS,
                # object_id=user_id,
            )
            self.connector.update_internal_user_state(user_id, ADMIN_OPTIONS, internal_user.id)
            logger.info(f"Создан внутренний пользователь: {internal_user}")
        else:
            logger.info(f"Внутренний пользователь для ROOT_ID {ROOT_ID} уже существует: {internal_user}")

        # TODO: rewrite this, route admin to his state if user already exsist
        reply_markup = await self.generate_inline_buttons_by_state_rewrite(
            update,
            context,
            ADMIN_OPTIONS,
            user_id,
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=ADMIN_STATES[ADMIN_OPTIONS][BEGIN_MESSAGE],
            reply_markup=reply_markup,
        )
        logger.info(f"Админ {user_id} запущен в режиме '{ADMIN_OPTIONS}'.")

    async def generate_list_objects(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            objects: list[Game | Question | Variant],
            page: int = 0,
        ):
        # TODO: shange to 6 or 8 after tests
        per_page = 2
        total_objects = len(objects)
        total_pages = (total_objects + per_page - 1) // per_page # round up

        start = (page - 1) * per_page
        end = start + per_page
        page_objects = objects[start:end]

        buttons = []
        type_to_attr = {
            Game: 'title',
            Question: 'question_text',
            Variant: 'answer_text',
        }
        attr_name = type_to_attr.get(type(object))
        text = getattr(object, attr_name, None)
        for object in page_objects:
            button = InlineKeyboardButton(
                text,
                callback_data=object.id,
            )
            buttons.append(button)

        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{PAGE}|{page - 1}"))
        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{PAGE}|{page + 1}"))
        if navigation_buttons:
            keyboard.append(navigation_buttons)
        type_to_backward_state = {
            Game: ADMIN_OPTIONS,
            Question: GAME_OPTIONS,
            Variant: QUESTION_OPTIONS,
        }
        callback_state = type_to_backward_state.get(type(object))
        keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=callback_state)])
        logger.debug(f"generated keyboard = {keyboard}")
        return InlineKeyboardMarkup(keyboard)

    async def generate_list_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE, internal_user_id: str, page: int = 0):
        games = self.connector.get_games_by_creator_id(internal_user_id)
        return self.generate_list_objects(update, context, games, page)

    async def generate_list_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, page: int = 0):
        questions = self.connector.get_questions_by_game(game_id)
        return self.generate_list_objects(update, context, questions, page)

    async def generate_list_variants(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str, page: int = 0):
        variants = self.connector.get_games_by_creator_id(question_id)
        return self.generate_list_objects(update, context, variants, page)

    # TODO: remove update and context from here
    async def generate_inline_buttons_by_state_rewrite(self, update, context, state: str, object_id: str | None = None):
        logger.debug(f"state = {state}, object_id = {object_id}")
        if ADMIN_STATES[state][ACTION] == LIST:
            assert(object_id != None)
            list_types = state.split("_")[0]
            if list_types == "game":
                return await self.generate_list_games(update, context, object_id)
            elif list_types == "question":
                return await self.generate_list_questions(update, context, object_id)
            elif list_types == "variants":
                return await self.generate_list_variants(update, context, object_id)
            else:
                logger.error("object type should be game/question/variant")
                return

        keyboard = []
        if ADMIN_STATES[state][ACTION] == CALLBACK:
            for button in ADMIN_STATES[state][FORWARD_STATES]:
                keyboard.append([InlineKeyboardButton(ADMIN_STATES[button][LABEL], callback_data=button)])
            if ADMIN_STATES[state][BACKWARD_STATES]:
                button = ADMIN_STATES[state][BACKWARD_STATES]
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            ADMIN_STATES[button][LABEL],
                            callback_data=button,
                        )
                    ]
                )
        return InlineKeyboardMarkup(keyboard)

    async def get_end_message(self, state: str):
        text = None
        if (
                state in ADMIN_STATES
            and END_MESSAGE in ADMIN_STATES[state]
            and ADMIN_STATES[state][END_MESSAGE]
            ):
            text = ADMIN_STATES[state][END_MESSAGE]
        return text

    async def send_end_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state):
        user_id = update.effective_user.id
        text = await self.get_end_message(state)
        if not text:
            return
        await context.bot.send_message(
            chat_id=user_id,
            text=ADMIN_STATES[state][END_MESSAGE],
        )

    async def get_begin_message(self, state: str):
        text = None
        if (
            state in ADMIN_STATES
        and BEGIN_MESSAGE in ADMIN_STATES[state]
        and ADMIN_STATES[state][BEGIN_MESSAGE]
        ):
            text = ADMIN_STATES[state][BEGIN_MESSAGE]
        return text

    async def send_begin_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: str, object_id: str | None = None):
        user_id = update.effective_user.id
        text = await self.get_begin_message(state)
        reply_markup = await self.generate_inline_buttons_by_state_rewrite(update, context, state, object_id)
        logger.debug(f"text = {text}")
        logger.debug(f"reply_markup = {reply_markup}")
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup,
        )

    async def handle_state(
            self, 
            update: Update, 
            context: ContextTypes.DEFAULT_TYPE, 
            state: str,
            object_id: str,
            data = None,
            ):
        user_id = update.effective_user.id
        internal_user = self.connector.get_internal_user_by_telegram_id(user_id)
        await self.send_end_message(update, context, internal_user.state)
        # the only state, that updates with callback
        # if state == CHANGE_CORRECTNESS:
        #     self.change_correctness(update, context, object_id)
        internal_user.state = state
        internal_user.object_id = object_id
        self.connector.commit()
        await self.send_begin_message(update, context, state, object_id)

    # TODO: separate this handler, to make it more readable
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        logger.info(f"{ADMIN} {user_id} called {inspect.currentframe().f_code.co_name}")
        query = update.callback_query
        await query.answer("Заебись")
        await query.edit_message_reply_markup(reply_markup=None)
        data = query.data
        logger.info(f"{ADMIN} {user_id} calback_data = {data}")
        internal_user = self.connector.get_internal_user_by_telegram_id(user_id)
        current_state = internal_user.state
        new_state = None
        object_id = internal_user.object_id
        # TODO: rewrite this
        if ADMIN_STATES[current_state][ACTION] == LIST:
            new_state = ADMIN_STATES[current_state][FORWARD_STATES]
            if ADMIN_STATES[current_state][FORWARD_STATES] != ADMIN_STATES[current_state][BACKWARD_STATES]:
                assert(is_valid_uuid4(data))
                object_id = data
        else:
            assert(not is_valid_uuid4(data))
            new_state = data
        # TODO: add change correctness handler
        await self.handle_state(update, context, new_state, object_id)

    # async def handle_listing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: str):
    #     admin_id = update.effective_user.id
    #     logger.debug(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")

    #     logger.debug(f"state = {state}")
    #     action = state.split(":")[0]
    #     if action == GAME_TO_EDIT:
    #         internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
    #         return await self.game_to_edit(update, context, internal_user_id)
    #     elif action == GAME_TO_DELETE:
    #         internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
    #         return await self.game_to_delete(update, context, internal_user_id)
    #     elif action == QUESTION_TO_EDIT:
    #         game_id = state.split(":")[-1]
    #         return await self.question_to_edit(update, context, game_id)
    #     elif action == QUESTION_TO_DELETE:
    #         game_id = state.split(":")[-1]
    #         return await self.question_to_delete(update, context, game_id)
    #     elif action == VARIANT_TO_EDIT:
    #         question_id = state.split(":")[-1]
    #         return await self.variant_to_edit(update, context, question_id)
    #     elif action == VARIANT_TO_DELETE:
    #         question_id = state.split(":")[-1]
    #         return await self.variant_to_delete(update, context, question_id)
    #     elif action == GAME_TO_START:
    #         internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
    #         return await self.game_to_start(update, context, internal_user_id)
    #     else:
    #         logger.error("incorrect state")

    # async def handle_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery, variant_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     print(f"variant_id = {variant_id}")
    #     self.update_variant_correctness(update, context, variant_id)
    #     # question_text = self.connector.get_question(question_id).question_text
    #     question_id = self.connector.get_variant(variant_id).question_id
    #     variants = self.connector.get_variants_by_question(question_id)

    #     buttons = [
    #         InlineKeyboardButton(
    #             f"✅ {variant.answer_text}" if variant.id in self.selected_variants[question_id] else variant.answer_text, 
    #             callback_data=f"{ADMIN}:{SELECT}|{variant.id}",
    #         )
    #         for variant in variants
    #     ]
    #     # Разбиваем кнопки на строки по 2 кнопки
    #     keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    #     # Добавляем строку с кнопкой DONE_LABEL
    #     keyboard.append([InlineKeyboardButton(DONE_LABEL, callback_data=f"{ADMIN}:{DONE}:{question_id}")])
    #     reply_markup = InlineKeyboardMarkup(keyboard)
    #     await query.edit_message_reply_markup(reply_markup=reply_markup)

    # async def waiting_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, game_code: str, game_session_state = f"{WAITING_START}"):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")

    #     game_session_id = self.connector.create_game_session(game_id, "ASDF", f"{WAITING_START}").id
    #     self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{WAITING_START}:{game_session_id}")
    #     keyboard = [
    #         [InlineKeyboardButton("Поехали", callback_data=f"{ADMIN}:{GAME_WORKFLOW}:{game_session_id}")] 
    #     ]
    #     reply_markup = InlineKeyboardMarkup(keyboard)
    #     await context.bot.send_message(
    #         chat_id=admin_id,
    #         text="Можешь жмакнуть \"Поехали\"",
    #         reply_markup=reply_markup,
    #     )

    # async def create_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """
    #     Запускает процесс создания игры.
    #     Обновляет состояние в базе до f"{ADMIN}:{CREATE_GAME}" и запрашивает название игры.
    #     """
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")

    #     query = update.callback_query
    #     await query.answer()
    #     await query.edit_message_text("Введите название игры:")
    #     logger.info(f"Админ {admin_id} переведен в состояние '{ADMIN}:{CREATE_GAME}' (ожидание названия игры).")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обрабатывает текстовые сообщения.
        В зависимости от текущего состояния (из базы), принимает ввод:
        """
        user_id = update.effective_user.id
        text = update.message.text.strip()
        if not text:
            await update.message.reply_text("Нужно что-то ввести!")
            return
        internal_user = self.connector.get_internal_user_by_telegram_id(user_id)
        current_state = internal_user.state
        object_id = internal_user.object_id
        state_to_method = {
            CREATE_GAME: self.connector.create_game,
            ADD_QUESTION: self.connector.create_question,
            EDIT_QUESTION_TEXT: self.connector.update_question_text,
            ADD_VARIANT: self.connector.create_variant,
            EDIT_VARIANT_TEXT: self.connector.update_variant_text,
        }
        if current_state not in state_to_method:
            logger.debug(f"got text in state {current_state}, while was not expected")
            await context.bot.send_message(
                chat_id=user_id,
                text="В этом состоянии текст не ожидается",
            )
            return
        query = state_to_method[current_state](object_id, text)
        if current_state == CREATE_GAME or current_state == ADD_QUESTION:
            object_id = query.id
        next_state = ADMIN_STATES[current_state][FORWARD_STATES]
        await self.handle_state(update, context, next_state, object_id)

    # async def change_correctness(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     await context.bot.send_message(
    #         chat_id=admin_id,
    #         text="Выберите правильные ответы",
    #     )
    #     await self.display_question(update, context, question_id)
    #     return

    # def get_question_data_to_send_players(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
    #     admin_id = update.effective_chat.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     question = self.connector.get_question(question_id)
    #     question_text = question.question_text
    #     variants = self.connector.get_variants_by_question(question_id)

    #     raw_variants = self.connector.get_correct_variants_by_question_id(question_id)
    #     self.selected_variants[question_id] = set(variant.id for variant in raw_variants)

    #     buttons = [
    #         InlineKeyboardButton(
    #             variant.answer_text, callback_data=f"{GAME_WORKFLOW}:{variant.id}",
    #         )
    #         for variant in variants
    #     ]
    #     # Разбиваем кнопки на строки по 2 кнопки
    #     keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    #     # Добавляем строку с кнопкой DONE_LABEL
    #     # keyboard.append([InlineKeyboardButton(DONE_LABEL, callback_data=f"{ADMIN}:{DONE}:{question_id}")])
    #     reply_markup = InlineKeyboardMarkup(keyboard)
    #     path_to_media = question.path_to_media
    #     return question_text, reply_markup, path_to_media

    # async def display_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
    #     admin_id = update.effective_chat.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     question = self.connector.get_question(question_id)
    #     question_text = question.question_text
    #     variants = self.connector.get_variants_by_question(question_id)

    #     raw_variants = self.connector.get_correct_variants_by_question_id(question_id)
    #     self.selected_variants[question_id] = set(variant.id for variant in raw_variants)

    #     buttons = [
    #         InlineKeyboardButton(
    #             f"✅ {variant.answer_text}" if variant.id in self.selected_variants[question_id] else variant.answer_text, callback_data=f"{ADMIN}:{SELECT}|{variant.id}",
    #         )
    #         for variant in variants
    #     ]
    #     # Разбиваем кнопки на строки по 2 кнопки
    #     keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    #     # Добавляем строку с кнопкой DONE_LABEL
    #     keyboard.append([InlineKeyboardButton(DONE_LABEL, callback_data=f"{ADMIN}:{DONE}:{question_id}")])
    #     reply_markup = InlineKeyboardMarkup(keyboard)
    #     path_to_media = question.path_to_media
    #     if path_to_media is None:
    #         await context.bot.send_message(
    #             chat_id=admin_id,
    #             text=question_text,
    #             reply_markup=reply_markup,
    #         )
    #     else:
    #         await context.bot.send_photo(
    #             chat_id=admin_id,
    #             caption=question_text,
    #             reply_markup=reply_markup,
    #             photo=path_to_media,
    #         )
    #     return

    # def update_variant_correctness(self, update: Update, context: ContextTypes.DEFAULT_TYPE, variant_id: str, is_correct: bool = True):
    #     variant = self.connector.get_variant(variant_id)
    #     self.update_variant_correctness_cached(update=update, context=context, variant_id=variant_id, question_id=variant.question_id)

    # def update_variant_correctness_cached(self, update: Update, context: ContextTypes.DEFAULT_TYPE, variant_id: str, question_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     if question_id not in self.selected_variants:
    #         self.selected_variants[question_id] = set()
    #     if question_id not in self.not_selected_variants:
    #         self.not_selected_variants[question_id] = set()
    #     if variant_id in self.selected_variants[question_id]:
    #         try:
    #             self.selected_variants[question_id].remove(variant_id)
    #         except Exception as e:
    #             logger.error(f"Caught exception: {e}")
    #         try:
    #             self.not_selected_variants[question_id].add(variant_id)
    #         except Exception as e:
    #             logger.error(f"Caught exception: {e}")
    #     else:
    #         try:
    #             self.selected_variants[question_id].add(variant_id)
    #         except Exception as e:
    #             logger.error(f"Caught exception: {e}")
    #         try:
    #             self.not_selected_variants[question_id].remove(variant_id)
    #         except Exception as e:
    #             logger.error(f"Caught exception: {e}")

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

    # async def variant_to_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     variants = self.connector.get_variants_by_question(question_id)
    #     reply_markup = self.generate_inline_buttons_for_variants(update, context, variants, 1, f"{EDIT_VARIANT_TEXT}")
    #     return reply_markup

    # async def variant_to_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     variants = self.connector.get_variants_by_question(question_id)
    #     reply_markup = self.generate_inline_buttons_for_variants(update, context, variants, 1, f"{DELETE_VARIANT}")
    #     return reply_markup

    # async def question_to_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     questions = self.connector.get_questions_by_game(game_id)
    #     reply_markup = self.generate_inline_buttons_for_questions(update, context, questions, 1, f"{QUESTION_OPTIONS}")
    #     return reply_markup

    # async def question_to_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     questions = self.connector.get_questions_by_game(game_id)
    #     reply_markup = self.generate_inline_buttons_for_questions(update, context, questions, 1, f"{DELETE_QUESTION}")
    #     return reply_markup

    # async def game_to_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, internal_user_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     games = self.connector.get_games_by_creator_id(internal_user_id)
    #     reply_markup = self.generate_inline_buttons_for_games(update, context, games, 1, f"{GAME_OPTIONS}")
    #     return reply_markup

    # async def game_to_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, internal_user_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     games = self.connector.get_games_by_creator_id(internal_user_id)
    #     reply_markup = self.generate_inline_buttons_for_games(update, context, games, 1, f"{DELETE_GAME}")
    #     return reply_markup

    # async def remove_inline_keyboards(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     admin_id = update.effective_user.id
    #     logger.debug(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     # Проходим по всем сохранённым сообщениям
    #     for chat_id, message_ids in list(self.sent_messages.items()):
    #         for message_id in list(message_ids):
    #             try:
    #                 await context.bot.edit_message_reply_markup(
    #                     chat_id=chat_id,
    #                     message_id=message_id,
    #                     reply_markup=None
    #                 )
    #             except Exception as e:
    #                 logger.error(f"Ошибка при редактировании сообщения {message_id} для {chat_id}: {e}")
    #                 # Удаляем сообщение из списка, если редактирование не удалось
    #                 message_ids.remove(message_id)
    #         # Если для chat_id больше нет сообщений, удаляем ключ из словаря
    #         if not message_ids:
    #             del self.sent_messages[chat_id]

    # async def finish_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_session_id: str):
    #     players = self.connector.get_players_by_game_session_id(game_session_id)
    #     player_ids = [player.telegram_id for player in players]
    #     await self.send_message_to_everyone(update, context, player_ids, "Игра закончена!", None, None)

    # async def send_message_to_everyone(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_ids: list, text: str, reply_markup, path_to_image: str | None = None):
    #     for player in user_ids:
    #         try:
    #             if path_to_image:
    #                 sent_message = await context.bot.send_photo(
    #                     chat_id=player,
    #                     photo=path_to_image,
    #                     caption=text,
    #                     reply_markup=reply_markup,
    #                 )
    #             else:
    #                 sent_message = await context.bot.send_message(
    #                     chat_id=player,
    #                     text=text,
    #                     reply_markup=reply_markup,
    #                 )
    #             # Сохраняем message_id в словаре для данного chat_id
    #             self.sent_messages.setdefault(player, []).append(sent_message.message_id)
    #         except Exception as e:
    #             logger.error(f"Ошибка при отправке сообщения для {player}: {e}")
    #     logger.debug(f"sent messages = {self.sent_messages}")

    # async def send_question_to_everyone(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_session_id: str, question_number: int):
    #     admin_id = update.effective_user.id
    #     logger.debug(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     players = self.connector.get_players_by_game_session_id(game_session_id)
    #     game_id = self.connector.get_game_session(game_session_id).game_id
    #     questions = self.connector.get_questions_by_game(game_id)
    #     logger.debug(f"questions = {questions}")
    #     if len(questions) <= question_number:
    #         await self.finish_game(update, context, game_session_id)
    #         return
    #     current_question_id = questions[question_number].id
    #     logger.debug(f"current_question_id = {current_question_id}")
    #     self.connector.update_game_session_state(game_session_id, current_question_id)
    #     self.connector.update_game_session_question_id(game_session_id, current_question_id)
    #     text, reply_markup, path_to_image = self.get_question_data_to_send_players(update, context, current_question_id)
    #     logger.debug(f"text = {text}, reply_markup = {reply_markup}, path_to_image = {path_to_image}")
    #     player_ids = [player.telegram_id for player in players]
    #     await self.send_message_to_everyone(update, context, player_ids, text, reply_markup, path_to_image)

    #     keyboard = [
    #         [InlineKeyboardButton("➡️", callback_data=f"{ADMIN}:{CHANGE_QUESTION}|{question_number + 1}")]
    #     ]
    #     reply_markup = InlineKeyboardMarkup(keyboard)
    #     await context.bot.send_message(
    #         chat_id=admin_id,
    #         text="Можешь переключать вопросы",
    #         reply_markup=reply_markup,
    #     )
    #     return

    # async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_session_id: str):
    #     admin_id = update.effective_user.id
    #     self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{GAME_WORKFLOW}:{game_session_id}")
    #     await self.send_question_to_everyone(update, context, game_session_id, 0)

    # async def game_to_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, internal_user_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     games = self.connector.get_games_by_creator_id(internal_user_id)
    #     reply_markup = self.generate_inline_buttons_for_games(update, context, games, 1, f"{WAITING_START}")
    #     return reply_markup

    # async def edit_game_by_game_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: str, game_id: str):
    #     new_state = f"{ADMIN}:{GAME_OPTIONS}:{game_id}"
    #     self.connector.update_internal_user_state(admin_id, new_state)
    #     await game_options(update, context, game_id)

    # async def delete_question_by_question_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
    #     game_id = self.connector.get_question(question_id).game_id
    #     new_state = f"{ADMIN}:{GAME_OPTIONS}:{game_id}"
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     self.connector.update_internal_user_state(admin_id, new_state)
    #     await context.bot.send_message(
    #         chat_id=admin_id,
    #         text="Функционал удаления вопроса, пока что, замокан 🙁",
    #     )
    #     await game_options(update, context, game_id)

    # async def delete_game_by_game_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: str, game_id: str):
    #     new_state = f"{ADMIN}:{ADMIN_OPTIONS}"
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     self.connector.update_internal_user_state(admin_id, new_state)
    #     await context.bot.send_message(
    #         chat_id=admin_id,
    #         text="Функционал удаления игры, пока что, замокан 🙁",
    #     )
    #     await admin_options(update, context)
    #     logger.info(f"Админ {admin_id} запущен в режиме '{ADMIN_OPTIONS}'.")

    # async def delete_variant_by_variant_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, variant_id: str):
    #     question_id = self.connector.get_variant(variant_id)
    #     new_state = f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}"
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called delete_variant_by_variant_id")
    #     self.connector.delete_variant(variant_id)
    #     await variant_options(update, context, question_id)

    # def generate_inline_buttons_for_variants(self, update: Update, context: ContextTypes.DEFAULT_TYPE, variants: list[Variant], page = 1, action: str = f"{VARIANT_OPTIONS}"):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     per_page = 2
    #     total_variants = len(variants)
    #     total_pages = (total_variants + per_page - 1) // per_page # round up

    #     start = (page - 1) * per_page
    #     end = start + per_page
    #     page_variants = variants[start:end]

    #     buttons = []
    #     for variant in page_variants:
    #         # for question its title, TODO: add unify method for any object
    #         button = InlineKeyboardButton(variant.answer_text, callback_data=f"{ADMIN}:{action}:{variant.id}")
    #         buttons.append(button)

    #     keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    #     navigation_buttons = []
    #     if page > 1:
    #         navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{ADMIN}:{PAGE_VARIANTS}|{page - 1}"))
    #     if page < total_pages:
    #         navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{ADMIN}:{PAGE_VARIANTS}|{page + 1}"))
    #     if navigation_buttons:
    #         keyboard.append(navigation_buttons)
    #     question_id = self.connector.get_internal_user_state(admin_id).split(":")[-1]
    #     keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}")])
    #     logger.debug(f"generated keyboard = {keyboard}")
    #     return InlineKeyboardMarkup(keyboard)

    # def generate_inline_buttons_for_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, questions: list[Question], page = 1, action: str = f"{QUESTION_OPTIONS}"):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     per_page = 2
    #     total_questions = len(questions)
    #     total_pages = (total_questions + per_page - 1) // per_page # round up

    #     start = (page - 1) * per_page
    #     end = start + per_page
    #     page_questions = questions[start:end]

    #     buttons = []
    #     for question in page_questions:
    #         # for question its title, TODO: add unify method for any object
    #         button = InlineKeyboardButton(question.question_text, callback_data=f"{ADMIN}:{action}:{question.id}")
    #         buttons.append(button)

    #     keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    #     navigation_buttons = []
    #     if page > 1:
    #         navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{ADMIN}:{PAGE_QUESTIONS}|{page - 1}"))
    #     if page < total_pages:
    #         navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{ADMIN}:{PAGE_QUESTIONS}|{page + 1}"))
    #     if navigation_buttons:
    #         keyboard.append(navigation_buttons)
    #     game_id = self.connector.get_internal_user_state(admin_id).split(":")[-1]
    #     keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=f"{ADMIN}:{GAME_OPTIONS}:{game_id}")])
    #     logger.debug(f"generated keyboard = {keyboard}")
    #     return InlineKeyboardMarkup(keyboard)

    # def generate_inline_buttons_for_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE, games: list[Game], page = 1, action: str = f"{GAME_OPTIONS}"):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     per_page = 2
    #     total_games = len(games)
    #     total_pages = (total_games + per_page - 1) // per_page # round up

    #     start = (page - 1) * per_page
    #     end = start + per_page
    #     page_games = games[start:end]

    #     buttons = []
    #     for game in page_games:
    #         # for game its title, TODO: add unify method for any object
    #         button = InlineKeyboardButton(game.title, callback_data=f"{ADMIN}:{action}:{game.id}")
    #         buttons.append(button)

    #     keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    #     navigation_buttons = []
    #     if page > 1:
    #         navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{ADMIN}:{PAGE_GAMES}|{page - 1}"))
    #     if page < total_pages:
    #         navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{ADMIN}:{PAGE_GAMES}|{page + 1}"))
    #     if navigation_buttons:
    #         keyboard.append(navigation_buttons)
    #     keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=f"{ADMIN}:{ADMIN_OPTIONS}")])
    #     logger.debug(f"generated keyboard = {keyboard}")
    #     return InlineKeyboardMarkup(keyboard)

    # async def handle_changing_page_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, new_page: int, action: str):
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
    #     games = self.connector.get_games_by_creator_id(internal_user_id)
    #     reply_markup = self.generate_inline_buttons_for_games(update, context, games, new_page, action)
    #     logger.debug(f"new reply_markup = {reply_markup}")
    #     query = update.callback_query
    #     await query.edit_message_reply_markup(reply_markup=reply_markup)
    #     await query.answer()  # Обязательно вызываем query.answer(), чтобы убрать "часики" у кнопки

    # async def handle_changing_page_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, new_page: int, action: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     questions = self.connector.get_questions_by_game(game_id)
    #     print(f"********************** (from handle_changing_page_questions): game_id = {game_id}")
    #     print(f"********************** (from handle_changing_page_questions): questions = {questions}")
    #     reply_markup = self.generate_inline_buttons_for_questions(update, context, questions, new_page, action)
    #     logger.debug(f"new reply_markup = {reply_markup}")
    #     query = update.callback_query
    #     await query.edit_message_reply_markup(reply_markup=reply_markup)
    #     await query.answer()  # Обязательно вызываем query.answer(), чтобы убрать "часики" у кнопки

    # async def handle_changing_page_variants(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str, new_page: int, action: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     variants = self.connector.get_variants_by_question(question_id)
    #     reply_markup = self.generate_inline_buttons_for_variants(update, context, variants, new_page, action)
    #     logger.debug(f"new reply_markup = {reply_markup}")
    #     query = update.callback_query
    #     await query.edit_message_reply_markup(reply_markup=reply_markup)
    #     await query.answer()  # Обязательно вызываем query.answer(), чтобы убрать "часики" у кнопки

# Глобальный объект AdminFlow; если у вас может быть несколько администраторов, лучше создавать его при /start для каждого.
# Здесь мы инициализируем его с использованием сессии из db_connector.
from queries import db_connector
admin_flow = AdminFlow(db_connector)
