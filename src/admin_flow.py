# admin_flow.py
"""
Модуль, инкапсулирующий админскую логику.
Состояние администратора хранится в базе данных (через модель AdminSession).
Методы класса AdminFlow получают актуальное состояние из базы и обновляют его,
что позволяет сохранять данные даже при перезапуске приложения.
"""

import os
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    Update,
)
from logger import get_logger
from sqlalchemy.orm import Session
from queries import DatabaseConnector
from settings import ROOT_ID
import pprint

logger = get_logger(__name__)

# Константы для этапов создания игры
STATE_TITLE = "awaiting_title"
STATE_QUESTION_TEXT = "awaiting_question_text"
STATE_QUESTION_OPTIONS = "awaiting_question_options"
STATE_QUESTION_IMAGE = "awaiting_question_image"
STATE_AFTER_QUESTION = "after_question"

class AdminFlow:
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector
        self.selected_variants = {}

    async def start(self, update: Update, context):
        """
        Запускает админский режим.
        Обновляет состояние администратора до "start" и выводит главное меню.
        """
        internal_user = self.connector.get_internal_user_by_telegram_id(ROOT_ID)
        if internal_user is None:
            logger.info(f"Internal user for ROOT_ID {ROOT_ID} не найден. Создаем нового.")
            internal_user = self.connector.create_internal_user(telegram_id=ROOT_ID, nickname="Это же я", hashed_password="Он пока не нужен")
            logger.info(f"Создан внутренний пользователь: {internal_user}")
        else:
            logger.info(f"Внутренний пользователь для ROOT_ID {ROOT_ID} уже существует: {internal_user}")
        admin_id = update.effective_user.id
        logger.info(f"admin {admin_id} called {__name__}")
        self.connector.update_internal_user_state(admin_id, "start")
        keyboard = [
            [InlineKeyboardButton("Создать новую игру", callback_data="admin:create_game")],
            [InlineKeyboardButton("Другие команды", callback_data="admin:other")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=admin_id,
            text="Добро пожаловать, администратор!\nВыберите действие:",
            reply_markup=reply_markup,
        )
        logger.info(f"Админ {admin_id} запущен в режиме 'start'.")

    async def handle_callback(self, update: Update, context):
        """
        Обрабатывает inline callback-ы.
        """
        query = update.callback_query
        data = query.data  # ожидается формат "admin:<команда>"

        if data.startswith("select|"):
            variant_id = data.split('|')[-1]
            print(f"data.startswith, date.split = {variant_id}")
            self.update_variant_correctness(update, context, variant_id)
            # question_text = self.connector.get_question(question_id).question_text
            question_id = self.connector.get_variant(variant_id).question_id
            variants = self.connector.get_variants_by_question(question_id)
            # update.message.reply_text(question_text)
            # Для каждого варианта создаём кнопку. Callback data имеет формат "select|<variant_id>"
            # buttons = [
            #    InlineKeyboardButton(
            #         f"✅ {opt}" if opt in selected_options else opt,
            #         callback_data=f"select|{opt}"
            #     )
            #     for opt in options
            # ]
            buttons = [
                InlineKeyboardButton(
                    f"✅ {variant.answer_text}" if variant.id in self.selected_variants[question_id] else variant.answer_text, 
                    callback_data=f"select|{variant.id}"
                )
                for variant in variants
            ]
            # Разбиваем кнопки на строки по 2 кнопки
            keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
            # Добавляем строку с кнопкой "Готово"
            keyboard.append([InlineKeyboardButton("Готово", callback_data="admin:done")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)
            return

        if not data.startswith("admin:"):
            await query.answer("Некорректный callback.")
            return
        command = data.split(":", 1)[1]

        if command == "done":
            question_id = (self.connector.get_internal_user_state(update.effective_user.id)).split(":")[3]
            for variant in self.selected_variants[question_id]:
                self.connector.update_variant_correctness(variant, True)
            logger.info("Correct varians are saved")
            await query.edit_message_reply_markup(reply_markup=None)
            await query.edit_message_text("Правильные ответы сохранены")
            return
        elif command == "create_game":
            await self.start_game_creation(update, context)
        elif command == "add_variant":
            # Переводим состояние на ввод варианта (если, например, состояние выглядит как "...:variants:<n>")
            await query.answer("Введите вариант ответа.")
            await query.edit_message_text("Введите вариант ответа:")
        elif command == "attach_image":
            await query.answer("Пришлите изображение в виде фото.")
            await query.edit_message_text("Пришлите изображение в виде фото.")
        elif command == "skip_image":
            await self.finish_question_without_image(update, context)
        elif command == "choose_correct_variants":
            await query.edit_message_text("Выбери правильные варианты ответов")
            # TODO: separate this logic
            # state = admin:edit:<game_id>:<question_id>:variants
            print(f"********************************************************************************** {self.connector.get_internal_user_state(update.effective_user.id)}")
            question_id = (self.connector.get_internal_user_state(update.effective_user.id)).split(":")[3]
            await self.choose_correct_variants(update, context, question_id)
        elif command == "finish_question":
            await self.finish_question(update, context)
        elif command == "add_question":
            await self.start_question(update, context)
        elif command == "finish_game":
            await self.finish_game(update, context)
        else:
            await query.answer("Неизвестная команда.")

    async def start_game_creation(self, update: Update, context):
        """
        Запускает процесс создания игры.
        Обновляет состояние в базе до "admin:creating_game" и запрашивает название игры.
        """
        admin_id = update.effective_user.id
        logger.info(f"admin {admin_id} called {__name__}")
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Введите название игры:")
        self.connector.update_internal_user_state(admin_id, "admin:creating_game")
        # Устанавливаем локальное состояние в базе (читайте его из AdminSession)
        logger.info(f"Админ {admin_id} переведен в состояние 'admin:creating_game' (ожидание названия игры).")

    async def handle_text(self, update: Update, context):
        """
        Обрабатывает текстовые сообщения.
        В зависимости от текущего состояния (из базы), принимает ввод:
          - Если состояние "admin:creating_game": текст = название игры
          - Если состояние "admin:edit:<game_id>": текст = вопрос
          - Если состояние "admin:edit:<game_id>:<question_id>:variants:<n>" или "...:variants": текст = вариант ответа
        """
        admin_id = update.effective_user.id
        text = update.message.text.strip()
        if not text:
            await update.message.reply_text("Нужно что-то ввести!")
            return
        current_state = self.connector.get_internal_user_state(admin_id)
        if current_state == "admin:creating_game":
            game = self.connector.create_game("quiz", text, created_by=admin_id)

            game_id = game.id
            new_state = f"admin:edit:{game_id}"

            self.connector.update_internal_user_state(admin_id, new_state)
            logger.info(f"Game {game_id} created. State updated to {new_state}.")

            await update.message.reply_text(f"Игра '{text}' создана.\nВведите текст первого вопроса:")
        elif current_state.startswith("admin:edit:") and ":" not in current_state.split("admin:edit:")[-1]:
            # Состояние вида "admin:edit:<game_id>" — ожидаем текст вопроса
            game_id = current_state.split("admin:edit:")[-1]
            question = self.connector.create_question(game_id, text)

            new_state = f"{current_state}:{question.id}:variants"
            self.connector.update_internal_user_state(admin_id, new_state)
            logger.info(f"Question {question.id} created. State updated to {new_state}.")

            await update.message.reply_text("Введите первый вариант ответа:")
        elif current_state.endswith(":variants"):
            # Состояние для ввода вариантов ответа
            # Создаем вариант ответа; здесь можно расширить логику, чтобы разрешить ввод нескольких вариантов
            # Например, мы сразу сохраняем вариант и предлагаем inline меню для добавления ещё варианта или перехода дальше
            # (В данной реализации сохраняется каждый введённый вариант)
            # Предположим, что функция create_variant уже реализована (ее можно добавить в DatabaseConnector)
            # from queries import db_connector  # если не импортирован глобально
            game_id = current_state.split(":")[2]
            question_id = current_state.split(":")[3]
            variant = self.connector.create_variant(question_id, text)  # Здесь, возможно, потребуется уточнить логику

            logger.info(f"Variant created. Waiting for further action.")
            await update.message.reply_text(f"Вариант '{text}' сохранён.")

            # Отправляем меню: "Добавить ещё вариант" или "Продолжить"
            keyboard = [
                [InlineKeyboardButton("Добавить ещё вариант", callback_data="admin:add_variant")],
                [InlineKeyboardButton("Продолжить", callback_data="admin:choose_correct_variants")],
                # [InlineKeyboardButton("Продолжить", callback_data="admin:attach_image")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Неизвестное состояние. Попробуйте ввести /start.")

    async def choose_correct_variants(self, update: Update, context, question_id: str):
        admin_id = update.effective_user.id
        await self.display_question(update, context, question_id)
        return

    async def display_question(self, update: Update, context, question_id: str):
        question_text = self.connector.get_question(question_id).question_text
        variants = self.connector.get_variants_by_question(question_id)
        # update.message.reply_text(question_text)
        # Для каждого варианта создаём кнопку. Callback data имеет формат "select|<variant_id>"
        buttons = [
            InlineKeyboardButton(variant.answer_text, callback_data=f"select|{variant.id}")
            for variant in variants
        ]
        # Разбиваем кнопки на строки по 2 кнопки
        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        # Добавляем строку с кнопкой "Готово"
        keyboard.append([InlineKeyboardButton("Готово", callback_data="admin:done")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=question_text,
            reply_markup=reply_markup,
        )
        return

    def update_variant_correctness(self, update: Update, context, variant_id: str, is_correct: bool = True):
        variant = self.connector.get_variant(variant_id)
        self.update_variant_correctness_cached(update=update, context=context, variant_id=variant_id, question_id=variant.question_id)
        # print(f"************************************** update_variant_correctness, variant_id = {variant_id}")
        # self.connector.update_variant_correctness(variant_id, is_correct)

    def update_variant_correctness_cached(self, update: Update, context, variant_id: str, question_id: str):
        if question_id not in self.selected_variants:
            self.selected_variants[question_id] = set()
        if variant_id in self.selected_variants[question_id]:
            self.selected_variants[question_id].remove(variant_id)
        else:
            self.selected_variants[question_id].add(variant_id)

    async def handle_photo(self, update: Update, context):
        """
        Обрабатывает фото, если администратор решил прикрепить изображение к вопросу.
        """
        admin_id = update.effective_user.id
        current_state = self.connector.get_internal_user_state(admin_id)
        if not current_state.startswith("admin:edit:"):
            await update.message.reply_text("Фото не ожидается в текущем состоянии.")
            return
        game_id = current_state.split("admin:edit:")[-1].split(":")[0]
        question_id = current_state.split("admin:edit:")[-1].split(":")[1]
        # Предположим, текст вопроса уже введён и сохранён; извлекаем его из базы, если нужно
        # question_text = "текст_из_базы"  # Здесь вы должны получить фактический текст вопроса, если он сохранён в таблице Question
        # question = self.connector.create_question(game_id, question_text, has_media=False)
        question = self.connector.get_question(question_id)

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
            display_type="individual"
        )
        question.has_media = True

        self.connector.commit()
    
        await update.message.reply_text("Фото добавлено к вопросу.")

        # После фото можно перейти к вводу вариантов (если ещё не введены)
        await self.send_after_question_menu(update, context)
        logger.info("Photo processed for question.")

    async def send_after_question_menu(self, update: Update):
        """
        Отправляет inline-меню после добавления вопроса.
        """
        logger.info(f"admin {update.effective_user.id} called {__name__}")
        keyboard = [
            [InlineKeyboardButton("Добавить еще вопрос", callback_data="admin:add_question")],
            [InlineKeyboardButton("Завершить создание игры", callback_data="admin:finish_game")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if hasattr(update, "edit_message_text"):
            await update.edit_message_text("Выберите действие:", reply_markup=reply_markup)
        else:
            await update.reply_text("Выберите действие:", reply_markup=reply_markup)
        logger.info("Отправлено меню после вопроса.")

# Глобальный объект AdminFlow; если у вас может быть несколько администраторов, лучше создавать его при /start для каждого.
# Здесь мы инициализируем его с использованием сессии из db_connector.
from queries import db_connector
admin_flow = AdminFlow(db_connector)
