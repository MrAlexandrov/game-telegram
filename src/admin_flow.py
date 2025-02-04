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
from models import Game, Question
from settings import ROOT_ID
import inspect
from admin_constants import *

logger = get_logger(__name__)

class AdminFlow:
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector
        self.selected_variants = {}
        self.not_selected_variants = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.admin_options(update, context)

    async def admin_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Запускает админский режим.
        Обновляет состояние администратора до "GAME_OPTIONS" и выводит главное меню.
        """
        internal_user = self.connector.get_internal_user_by_telegram_id(ROOT_ID)
        if internal_user is None:
            logger.info(f"Internal user for ROOT_ID {ROOT_ID} не найден. Создаем нового.")
            internal_user = self.connector.create_internal_user(telegram_id=ROOT_ID, nickname="Это же я", hashed_password="Он пока не нужен")
            logger.info(f"Создан внутренний пользователь: {internal_user}")
        else:
            logger.info(f"Внутренний пользователь для ROOT_ID {ROOT_ID} уже существует: {internal_user}")

        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{GAME_OPTIONS}")
        await self.admin_options(update, context)
        logger.info(f"Админ {admin_id} запущен в режиме '{GAME_OPTIONS}'.")

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
        command = data.split(":", 1)[1]

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
        if command == f"{GAME_OPTIONS}":
            await self.admin_options(update, context)
        elif command.startswith(f"{DONE}:"):
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

            await self.question_options(update, context, question_id)

        elif command == f"{CREATE_GAME}":
            await self.create_game(update, context)
        elif command == f"{GAME_TO_EDIT}":
            await self.game_to_edit(update, context, admin_id)
        elif command.startswith(f"{GAME_OPTIONS}:"):
            # state = {ADMIN}:{GAME_OPTIONS}:<game_id>
            game_id = command.split(":")[-1]
            new_state = f"{ADMIN}:{GAME_OPTIONS}:{game_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            await self.edit_game_by_game_id(update, context, admin_id, game_id)
        elif command == f"{DELETE_GAME}":
            await self.delete_game(update, context, admin_id)
        elif command.startswith(f"{DELETE_GAME}:"):
            game_id = command.split(":")[-1]
            await self.delete_game_by_game_id(update, context, admin_id, game_id)
        elif command.startswith(f"{QUESTION_TO_EDIT}:"):
            game_id = command.split(":")[-1]
            self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{QUESTION_TO_EDIT}:{game_id}")
            await self.question_to_edit(update, context, game_id)
        elif command.startswith(f"{QUESTION_TO_DELETE}:"):
            game_id = command.split(":")[-1]
            self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{QUESTION_TO_DELETE}:{game_id}")
            await self.question_to_delete(update, context, game_id)
        elif command.startswith(f"{QUESTION_OPTIONS}:"):
            question_id = command.split(":")[-1]
            self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{QUESTION_OPTIONS}:{question_id}")
            game_id = self.connector.get_question(question_id).game_id
            await self.question_options(update, context, question_id)
        elif command.startswith(f"{DELETE_QUESTION}:"):
            question_id = command.split(":")[-1]
            await self.delete_question_by_question_id(update, context, question_id)
        elif command.startswith(f"{EDIT_QUESTION_TEXT}:"):
            # state = {ADMIN}:{EDIT_QUESTION_TEXT}:<question_id>
            question_id = command.split(":")[-1]
            logger.info(f'command.startswith("{EDIT_QUESTION_TEXT}:") question_id = {question_id}')
            new_state = f"{ADMIN}:{EDIT_QUESTION_TEXT}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"Введите текст вопроса (from command.startswith(\"{EDIT_QUESTION_TEXT}:\"))",
            )
        elif command.startswith(f"{VARIANT_OPTIONS}:"):
            question_id = command.split(":")[-1]
            new_state = f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            await self.variant_options(update, context, question_id)
        elif command.startswith(f"{ADD_VARIANT}:"):
            # Переводим состояние на ввод варианта (если, например, состояние выглядит как "...:variants:<n>")
            await query.answer("Введите вариант ответа.")
            await query.edit_message_text("Введите вариант ответа:")
            question_id = command.split(":")[-1]
            new_state = f"{ADMIN}:{ADD_VARIANT}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
        # elif command.startswith(f"{VARIANT_TO_DELETE}:"):
        #     await query.answer("Выберите вариант, который хотите удалить")
        #     await query.edit_message_text("Выберите вариант, который хотите удалить")
        #     question_id = command.split(":")[-1]
        #     new_state = f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}"
        #     self.connector.update_internal_user_state(admin_id, new_state)
        #     await self.variant_to_delete()
        #     await self.variant_options(update, context, question_id)
        elif command.startswith(f"{UPDATE_IMAGE}:"):
            await query.edit_message_text("Пришлите изображение в виде фото.")
            question_id = command.split(":")[-1]
            new_state = f"{ADMIN}:{UPDATE_IMAGE}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
        elif command.startswith(f"{CHANGE_CORRECTNESS}:"):
            await query.edit_message_text("Выбери правильные варианты ответов")
            question_id = command.split(":")[-1]
            await self.change_correctness(update, context, question_id)
        # elif command == "finish_question":
        #     await self.finish_question(update, context)
        elif command.startswith(f"{ADD_QUESTION}"):
            # callback = {ADMIN}:{ADD_QUESTION}:<game_id>
            game_id = command.split(":")[-1]
            new_state = f"{ADMIN}:{ADD_QUESTION}:{game_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            await context.bot.send_message(
                chat_id=admin_id,
                text="Введите текст вопроса",
            )
            # await self.add_question(update, context, game_id)
        else:
            await query.answer("Неизвестная команда.")

    async def handle_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery, variant_id: str):
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

    async def create_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Запускает процесс создания игры.
        Обновляет состояние в базе до "{ADMIN}:{CREATE_GAME}" и запрашивает название игры.
        """
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Введите название игры:")
        self.connector.update_internal_user_state(admin_id, f"{ADMIN}:{CREATE_GAME}")
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
        current_state = self.connector.get_internal_user_state(admin_id)
        if current_state == f"{ADMIN}:{CREATE_GAME}":
            internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
            game = self.connector.create_game("quiz", text, created_by=internal_user_id)

            game_id = game.id
            new_state = f"{ADMIN}:{GAME_OPTIONS}:{game_id}"

            self.connector.update_internal_user_state(admin_id, new_state)
            logger.info(f"Game {game_id} created. State updated to {new_state}.")

            await update.message.reply_text(f"Игра '{text}' создана.")
            await self.game_options(update, context, game_id)
        elif current_state.startswith(f"{ADMIN}:{ADD_QUESTION}:"):
            game_id = current_state.split(":")[-1]
            question = self.connector.create_question(game_id, text)
            question_id = question.id

            new_state = f"{ADMIN}:{EDIT_QUESTION_TEXT}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            logger.info(f"Question {question_id} created. State updated to {new_state}.")
            await self.question_options(update, context, question_id)
        elif current_state.startswith(f"{ADMIN}:{EDIT_QUESTION_TEXT}:"):
            question_id = current_state.split(":")[-1]
            print(f"************************** question_id = {question_id}")
            print(f"***************** current_state = {current_state}")
            self.connector.update_question_text(question_id, text)
            new_state = f"{ADMIN}:{QUESTION_OPTIONS}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            game_id = self.connector.get_question(question_id).game_id
            await self.question_options(update, context, question_id)
        elif current_state.startswith(f"{ADMIN}:{ADD_VARIANT}:"):
            question_id = current_state.split(":")[-1]
            self.connector.create_variant(question_id, text)
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"Вариант ответа {text} сохранён",
            )
            new_state = f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}"
            self.connector.update_internal_user_state(admin_id, new_state)
            await self.variant_options(update, context, question_id)
        # elif current_state.endswith(":variants"):
        #     # Состояние для ввода вариантов ответа
        #     # Создаем вариант ответа; здесь можно расширить логику, чтобы разрешить ввод нескольких вариантов
        #     # Например, мы сразу сохраняем вариант и предлагаем inline меню для добавления ещё варианта или перехода дальше
        #     # (В данной реализации сохраняется каждый введённый вариант)
        #     # Предположим, что функция create_variant уже реализована (ее можно добавить в DatabaseConnector)
        #     # from queries import db_connector  # если не импортирован глобально
        #     game_id = current_state.split(":")[2]
        #     question_id = current_state.split(":")[3]
        #     variant = self.connector.create_variant(question_id, text)  # Здесь, возможно, потребуется уточнить логику

        #     logger.info(f"Variant created. Waiting for further action.")
        #     await update.message.reply_text(f"Вариант '{text}' сохранён.")

        #     # Отправляем меню: "Добавить ещё вариант" или "Продолжить"
        #     keyboard = [
        #         [InlineKeyboardButton("Добавить ещё вариант", callback_data=f"{ADMIN}:{ADD_VARIANT}")],
        #         [InlineKeyboardButton("Продолжить", callback_data=f"{ADMIN}:{CHANGE_CORRECTNESS}")],
        #         # [InlineKeyboardButton("Продолжить", callback_data="{ADMIN}:attach_image")],
        #     ]
        #     reply_markup = InlineKeyboardMarkup(keyboard)
        #     await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Неизвестное состояние. Попробуйте ввести /start.")

    async def change_correctness(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите правильные ответы",
        )
        await self.display_question(update, context, question_id)
        return

    async def display_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: str):
        admin_id = update.effective_chat.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        question = self.connector.get_question(question_id)
        question_text = question.question_text
        variants = self.connector.get_variants_by_question(question_id)
        # update.message.reply_text(question_text)
        # Для каждого варианта создаём кнопку. Callback data имеет формат "{ADMIN}:{SELECT}|<variant_id>"

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
        # print(f"************************************** update_variant_correctness, variant_id = {variant_id}")
        # self.connector.update_variant_correctness(variant_id, is_correct)

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

    async def admin_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ):
        admin_id = update.effective_user.id
        keyboard = [
            [InlineKeyboardButton("Создать новую игру",     callback_data=f"{ADMIN}:{CREATE_GAME}")],
            [InlineKeyboardButton("Редактировать игру",     callback_data=f"{ADMIN}:{GAME_TO_EDIT}")],
            [InlineKeyboardButton("Удалить игру",           callback_data=f"{ADMIN}:{DELETE_GAME}")],
            [InlineKeyboardButton("Другие команды",         callback_data=f"{ADMIN}:{START_GAME}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=admin_id,
            text="Добро пожаловать, администратор!\nВыберите действие:",
            reply_markup=reply_markup,
        )

    async def game_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        keyboard = [
            [InlineKeyboardButton(ADD_QUESTION_LABEL,           callback_data=f"{ADMIN}:{ADD_QUESTION}:{game_id}")],
            [InlineKeyboardButton(QUESTION_TO_EDIT_LABEL,       callback_data=f"{ADMIN}:{QUESTION_TO_EDIT}:{game_id}")],
            [InlineKeyboardButton(QUESTION_TO_DELETE_LABEL,     callback_data=f"{ADMIN}:{QUESTION_TO_DELETE}:{game_id}")],
            [InlineKeyboardButton(CANCEL_LABEL,                 callback_data=f"{ADMIN}:{GAME_OPTIONS}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"Что вы хотите сделать с игрой? (from current_state == \"{ADMIN}:{CREATE_GAME}\")",
            reply_markup=reply_markup,
        )

    async def question_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        game_id = self.connector.get_question(question_id).game_id
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

    async def variant_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question_id):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        keyboard = [
            [InlineKeyboardButton(ADD_VARIANT_LABEL,                callback_data=f"{ADMIN}:{ADD_VARIANT}:{question_id}")],
            [InlineKeyboardButton(EDIT_VARIANT_LABEL,               callback_data=f"{ADMIN}:{EDIT_VARIANT}:{question_id}")],
            [InlineKeyboardButton(VARIANT_TO_DELETE_LABEL,          callback_data=f"{ADMIN}:{VARIANT_TO_DELETE}:{question_id}")],
            [InlineKeyboardButton(CANCEL_LABEL,                     callback_data=f"{ADMIN}:{QUESTION_OPTIONS}:{question_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"Что вы хотите сделать с вариантами ответов? (from current_state == \"{ADMIN}:{VARIANT_OPTIONS}:\")",
            reply_markup=reply_markup,
        )

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

        await self.question_options(update, context, question_id)

    # async def send_after_question_menu(self, update: Update):
    #     """
    #     Отправляет inline-меню после добавления вопроса.
    #     """
    #     logger.info(f"{ADMIN} {update.effective_user.id} called {inspect.currentframe().f_code.co_name}")
    #     keyboard = [
    #         [InlineKeyboardButton("Добавить еще вопрос", callback_data=f"{ADMIN}:{ADD_QUESTION}")],
    #         [InlineKeyboardButton("Завершить создание игры", callback_data=f"{ADMIN}:finish_game")],
    #     ]
    #     reply_markup = InlineKeyboardMarkup(keyboard)
    #     if hasattr(update, "edit_message_text"):
    #         await update.edit_message_text("Выберите действие:", reply_markup=reply_markup)
    #     else:
    #         await update.reply_text("Выберите действие:", reply_markup=reply_markup)
    #     logger.info("Отправлено меню после вопроса.")

    async def question_to_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        questions = self.connector.get_questions_by_game(game_id)
        reply_markup = self.generate_inline_buttons_for_questions(update, context, questions, 1, f"{QUESTION_OPTIONS}")
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
        print(f"**************************************** game_id = {game_id}, reply_markup = {reply_markup}")
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите вопрос, который хотите удалить",
            reply_markup=reply_markup,
        )
        return

    async def game_to_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int):
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
        games = self.connector.get_games_by_creator_id(internal_user_id)
        reply_markup = self.generate_inline_buttons_for_game(update, context, games, 1, f"{GAME_OPTIONS}")
        print(f"***************************************** admin_id = {admin_id}, reply_markup = {reply_markup}")
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите игру, которую хотите изменить",
            reply_markup=reply_markup,
        )
        return

    async def delete_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int):
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
        games = self.connector.get_games_by_creator_id(internal_user_id)
        reply_markup = self.generate_inline_buttons_for_game(update, context, games, 1, f"{DELETE_GAME}")
        print(f"***************************************** admin_id = {admin_id}, reply_markup = {reply_markup}")
        await context.bot.send_message(
            chat_id=admin_id,
            text="Выберите игру, которую хотите удалить",
            reply_markup=reply_markup,
        )
        return

    async def edit_game_by_game_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: str, game_id: str):
        new_state = f"{ADMIN}:{GAME_OPTIONS}:{game_id}"
        self.connector.update_internal_user_state(admin_id, new_state)
        await self.game_options(update, context, game_id)

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
        await self.game_options(update, context, game_id)

    async def delete_game_by_game_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: str, game_id: str):
        new_state = f"{ADMIN}:{GAME_OPTIONS}"
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        self.connector.update_internal_user_state(admin_id, new_state)
        await context.bot.send_message(
            chat_id=admin_id,
            text="Функционал удаления игры, пока что, замокан 🙁",
        )
        await self.admin_options(update, context)
        logger.info(f"Админ {admin_id} запущен в режиме '{GAME_OPTIONS}'.")

    async def delete_variant_by_variant_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, variant_id: str):
        question_id = self.connector.get_variant(variant_id)
        new_state = f"{ADMIN}:{VARIANT_OPTIONS}:{question_id}"
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called delete_variant_by_variant_id")
        self.connector.delete_variant(variant_id)
        await self.variant_options(update, context, question_id)

    def generate_inline_buttons_for_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, questions: list[Question], page = 1, action: str = f"{QUESTION_OPTIONS}"):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        per_page = 2
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
        game_id = questions[0].game_id
        keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=f"{ADMIN}:{GAME_OPTIONS}:{game_id}")])

        return InlineKeyboardMarkup(keyboard)

    def generate_inline_buttons_for_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, games: list[Game], page = 1, action: str = f"{GAME_OPTIONS}"):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        per_page = 2
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
        keyboard.append([InlineKeyboardButton(CANCEL_LABEL, callback_data=f"{ADMIN}:{GAME_OPTIONS}")])

        return InlineKeyboardMarkup(keyboard)

    async def handle_changing_page_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, new_page: int):
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        internal_user_id = self.connector.get_internal_user_by_telegram_id(admin_id).id
        games = self.connector.get_games_by_creator_id(internal_user_id)
        reply_markup = self.generate_inline_buttons_for_game(update, context, games, new_page)
        query = update.callback_query
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        await query.answer()  # Обязательно вызываем query.answer(), чтобы убрать "часики" у кнопки

    async def handle_changing_page_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, new_page: int):
        admin_id = update.effective_user.id
        logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
        questions = self.connector.get_questions_by_game(game_id)
        print(f"********************** (from handle_changing_page_questions): game_id = {game_id}")
        print(f"********************** (from handle_changing_page_questions): questions = {questions}")
        reply_markup = self.generate_inline_buttons_for_questions(update, context, questions, new_page)
        query = update.callback_query
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        await query.answer()  # Обязательно вызываем query.answer(), чтобы убрать "часики" у кнопки

    # async def add_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    #     admin_id = update.effective_user.id
    #     logger.info(f"{ADMIN} {admin_id} called {inspect.currentframe().f_code.co_name}")
    #     question_id = self.connector.create_question(game_id=game_id, question_text="", path_to_media=None)
    #     new_state = f"{ADMIN}:{EDIT_QUESTION_TEXT}:{question_id}"
    #     self.connector.update_internal_user_state(admin_id, new_state)

# Глобальный объект AdminFlow; если у вас может быть несколько администраторов, лучше создавать его при /start для каждого.
# Здесь мы инициализируем его с использованием сессии из db_connector.
from queries import db_connector
admin_flow = AdminFlow(db_connector)
