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

class AdminFlow:
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector
        self.selected_variants = {}
        self.not_selected_variants = {}
        self.sent_messages = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        logger.debug(f"{ADMIN} {user_id} called {inspect.currentframe().f_code.co_name}")
        logger.debug(f"update: {update}")
        logger.debug(f"context: {context}")
        # TODO: separate this
        internal_user = self.connector.get_internal_user_by_telegram_id(ROOT_ID)
        if internal_user is None:
            logger.debug(f"Internal user for ROOT_ID {ROOT_ID} не найден. Создаем нового.")
            internal_user = self.connector.create_internal_user(
                telegram_id=user_id,
                state=ADMIN_OPTIONS,
                # object_id=user_id,
            )
            logger.debug(f"ADMIN_OPTIONS = {ADMIN_OPTIONS}, internal_user_id = {internal_user.id}")
            logger.debug(f"internal_user = {internal_user}")
            logger.info(f"Создан внутренний пользователь: {internal_user}")
        else:
            logger.info(f"Внутренний пользователь для ROOT_ID {ROOT_ID} уже существует: {internal_user}")
        self.connector.update_internal_user_state(user_id, ADMIN_OPTIONS, internal_user.id)

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
        logger.debug(f"objects: {objects}")
        logger.debug(f"paga: {page}")
        # TODO: shange to 6 or 8 after tests
        per_page = 2
        total_objects = len(objects)
        if total_objects == 0:
            logger.error("List is empty")
            return
        total_pages = (total_objects + per_page - 1) // per_page # round up

        start = page * per_page
        end = start + per_page
        page_objects = objects[start:end]

        buttons = []
        type_to_attr = {
            Game: 'title',
            Question: 'question_text',
            Variant: 'answer_text',
        }
        attr_name = type_to_attr.get(type(objects[0]))
        for object in page_objects:
            text = getattr(object, attr_name, None)
            logger.debug(f"text: {text}")
            logger.debug(f"object.id: {object.id}")
            button = InlineKeyboardButton(
                text,
                callback_data=object.id,
            )
            buttons.append(button)

        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        logger.debug(f"keyboard before navigation_buttons: {keyboard}")
        navigation_buttons = []
        if page > 0:
            navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{PAGE}|{page - 1}"))
        if page < total_pages - 1:
            navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{PAGE}|{page + 1}"))
        if navigation_buttons:
            keyboard.append(navigation_buttons)
        type_to_backward_state = {
            Game: ADMIN_OPTIONS,
            Question: GAME_OPTIONS,
            Variant: VARIANT_OPTIONS,
        }
        callback_state = type_to_backward_state.get(type(objects[0]))
        keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=callback_state)])
        logger.debug(f"generated keyboard = {keyboard}")
        return InlineKeyboardMarkup(keyboard)

    async def generate_list_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE, internal_user_id: str, page: int = 0):
        games = self.connector.get_games_by_creator_id(internal_user_id)
        return await self.generate_list_objects(update, context, games, page)

    async def generate_list_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, page: int = 0):
        questions = self.connector.get_questions_by_game(game_id)
        return await self.generate_list_objects(update, context, questions, page)

    async def generate_list_variants(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str, page: int = 0):
        logger.debug(f"question_id: {question_id}")
        logger.debug(f"page: {page}")
        variants = self.connector.get_variants_by_question(question_id)
        logger.debug(f"variants: {variants}")
        return await self.generate_list_objects(update, context, variants, page)

    async def generate_buttons_for_change_correctness(self, update: Update, context: ContextTypes, question_id: str):
        admin_id = update.effective_chat.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        question = self.connector.get_question(question_id)
        question_text = question.question_text
        variants = self.connector.get_variants_by_question(question_id)

        self.selected_variants[question_id] = set(variant.id for variant in variants if variant.is_correct)

        buttons = [
            InlineKeyboardButton(
                f"✅ {variant.answer_text}" if variant.id in self.selected_variants[question_id] else variant.answer_text, callback_data=f"{variant.id}",
            )
            for variant in variants
        ]
        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        keyboard.append([InlineKeyboardButton(DONE_LABEL, callback_data=f"{DONE}")])
        return InlineKeyboardMarkup(keyboard)

    # TODO: remove update and context from here
    async def generate_inline_buttons_by_state_rewrite(self, update, context, state: str, object_id: str | None = None, page: int = 0):
        logger.debug(f"state = {state}, object_id = {object_id}")
        if ADMIN_STATES[state][ACTION] == LIST:
            assert(object_id != None)
            list_types = state.split("_")[0]
            logger.debug(f"list_types: {list_types}")
            if list_types == "game":
                return await self.generate_list_games(update, context, object_id, page)
            elif list_types == "question":
                return await self.generate_list_questions(update, context, object_id, page)
            elif list_types == "variant":
                return await self.generate_list_variants(update, context, object_id, page)
            else:
                logger.error("object type should be game/question/variant")
                return

        if state == CHANGE_CORRECTNESS:
            return await self.generate_buttons_for_change_correctness(update, context, object_id)

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
        return None if len(keyboard) == 0 else InlineKeyboardMarkup(keyboard)

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
        # TODO: rewrite this??
        if state == CHANGE_CORRECTNESS:
            text += "\nВопрос: " + self.connector.get_question(object_id).question_text
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
        logger.debug(f"new_state: {state}, object_id: {object_id}")
        user_id = update.effective_user.id
        internal_user = self.connector.get_internal_user_by_telegram_id(user_id)
        internal_user.state = state
        internal_user.object_id = object_id
        self.connector.commit()
        await self.send_end_message(update, context, internal_user.state)
        await self.send_begin_message(update, context, state, object_id)

    async def handle_selection(self, update: Update, context: ContextTypes, variant_id: str):
        variant = self.connector.change_variant_correctness(variant_id)
        new_reply_markup = await self.generate_buttons_for_change_correctness(update, context, variant.question_id)
        await update.callback_query.edit_message_reply_markup(reply_markup=new_reply_markup)

    # TODO: separate this handler, to make it more readable
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        logger.debug(f"{ADMIN} {user_id} called {inspect.currentframe().f_code.co_name}")
        query = update.callback_query
        await query.answer("Заебись")
        data = query.data
        logger.debug(f"{ADMIN} {user_id} calback_data = {data}")
        internal_user = self.connector.get_internal_user_by_telegram_id(user_id)
        current_state = internal_user.state
        logger.debug(f"current_state: {current_state}")
        new_state = None
        object_id = internal_user.object_id
        # TODO: rewrite this
        if ADMIN_STATES[current_state][ACTION] == LIST:
            new_state = ADMIN_STATES[current_state][FORWARD_STATES]
            if ADMIN_STATES[current_state][FORWARD_STATES] != ADMIN_STATES[current_state][BACKWARD_STATES]:
                if data == ADMIN_STATES[current_state][BACKWARD_STATES]:
                    new_state = data
                elif data.startswith(f"{PAGE}|"):
                    new_page = int(data.split("|")[-1])
                    new_reply_keyboard = await self.generate_inline_buttons_by_state_rewrite(update, context, current_state, object_id, new_page)
                    await update.callback_query.edit_message_reply_markup(reply_markup=new_reply_keyboard)
                    return
                else:
                    assert(is_valid_uuid4(data))
                    object_id = data
        elif current_state == CHANGE_CORRECTNESS:
            if data == DONE:
                new_state = QUESTION_OPTIONS
            else:
                assert(is_valid_uuid4(data))
                await self.handle_selection(update, context, data)
                return
        else:
            assert(not is_valid_uuid4(data))
            new_state = data

        await query.edit_message_reply_markup(reply_markup=None)
        logger.debug(f"new_state: {new_state}")
        await self.handle_state(update, context, new_state, object_id)

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
        if current_state == EDIT_VARIANT_TEXT:
            object_id = query.question_id
        next_state = ADMIN_STATES[current_state][FORWARD_STATES]
        await self.handle_state(update, context, next_state, object_id)

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

# Глобальный объект AdminFlow; если у вас может быть несколько администраторов, лучше создавать его при /start для каждого.
# Здесь мы инициализируем его с использованием сессии из db_connector.
from queries import db_connector
admin_flow = AdminFlow(db_connector)
