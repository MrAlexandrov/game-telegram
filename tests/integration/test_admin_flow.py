import pytest
import asyncio
from unittest.mock import AsyncMock
from admin_flow import AdminFlow
from queries import DatabaseConnector
from conftest import *
from admin_constants import *
from admin_settings import *
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import json
import copy
import pprint

async def simulate_start(admin_flow, update: Update, context: AsyncMock):
    """
    Симулирует отправку команды (например, "/start") и возвращает ответ бота.
    """
    # new_update = copy.deepcopy(update)
    # new_update.message.text = command

    await admin_flow.start(update, context)

# async def simulate_callback(admin_flow, update: Update, context: AsyncMock, callback_data: str):
#     """
#     Симулирует нажатие inline-кнопки (отправку callback) и возвращает ответ бота.
#     """
#     update.callback_query = AsyncMock()
#     update.callback_query.data = callback_data
#     update.callback_query.from_user = update.effective_user
#     update.callback_query.message.chat_id = update.effective_user.id

#     await admin_flow.handle_callback(update, context)

async def simulate_callback(admin_flow, update: Update, context: AsyncMock, callback_data: str):
    """
    Симулирует нажатие inline-кнопки (отправку callback) и возвращает ответ бота.
    """
    update.callback_query = AsyncMock()
    update.callback_query.data = callback_data
    update.callback_query.from_user = update.effective_user

    # ✅ Добавляем message в callback_query
    update.callback_query.message = AsyncMock()
    update.callback_query.message.chat_id = update.effective_user.id
    update.callback_query.message.message_id = 123  # 🔹 Любой ID, лишь бы не пустой

    await admin_flow.handle_callback(update, context)


async def simulate_text(admin_flow, update: Update, context: AsyncMock, text: str):
    update.message.text = text

    await admin_flow.handle_text(update, context)

def get_last_bot_message(context: AsyncMock):
    """
    Возвращает последнее сообщение, отправленное ботом.
    """
    assert context.bot.send_message.call_count > 0, "Бот не отправил ни одного сообщения!"
    return context.bot.send_message.call_args.kwargs  # Получаем последний вызов send_message

def get_last_updated_keyboard(update: Update, context: AsyncMock):
    """
    Возвращает последнюю измененную клавиатуру.
    """
    assert update.callback_query.edit_message_reply_markup.call_count > 0, "Бот не изменил клавиатуру!"
    return update.callback_query.edit_message_reply_markup.call_args.kwargs  # Получаем последний вызов edit_message_reply_markup

@pytest.mark.asyncio
async def test_admin_start_with_keyboard(admin_flow, db_connector: DatabaseConnector, mock_update, mock_context):
    """Тестируем команду /start, проверяем отправку inline-клавиатуры."""

    await admin_flow.start(mock_update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    called_args, called_kwargs = mock_context.bot.send_message.call_args

    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"

    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"

    # 📌 Ожидаемая клавиатура (замени на свою!)
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Создать игру", callback_data=f"{CREATE_GAME}")],
        [InlineKeyboardButton("Редактировать игру", callback_data=f"{GAME_TO_EDIT}")],
        [InlineKeyboardButton("Удалить игру", callback_data=f"{GAME_TO_DELETE}")],
        [InlineKeyboardButton("Начать игру", callback_data=f"{GAME_TO_START}")]
    ])

    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()

    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)

    # 📌 Сравниваем содержимое клавиатуры
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"


@pytest.mark.asyncio
async def test_admin_creates_game(admin_flow, db_connector: DatabaseConnector, mock_update, mock_context):
    """Тестируем переход администратора в создание игры после нажатия кнопки."""
    
    # 📌 1. Отправляем команду /start
    await simulate_start(admin_flow, mock_update, mock_context)

    # Проверяем, что администратор зарегистрирован и состояние обновилось
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin is not None
    assert admin.state == f"{ADMIN_OPTIONS}"

    # 📌 2. Эмулируем нажатие кнопки "Создать игру"
    await simulate_callback(admin_flow, mock_update, mock_context, f"{CREATE_GAME}")

    # Проверяем, что состояние изменилось в БД
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{CREATE_GAME}"

    # 📌 3. Проверяем текст последнего сообщения
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[CREATE_GAME][BEGIN_MESSAGE]

    # 📌 4. Проверяем inline-клавиатуру
    assert last_message["reply_markup"] == None


@pytest.mark.asyncio
async def test_full_admin_game_creation_workflow(admin_flow, db_connector: DatabaseConnector, mock_update, mock_context):
    await simulate_start(admin_flow, mock_update, mock_context)
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin is not None
    assert admin.state == f"{ADMIN_OPTIONS}"

    await simulate_callback(admin_flow, mock_update, mock_context, f"{CREATE_GAME}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{CREATE_GAME}"
    assert admin.object_id == admin.id
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[CREATE_GAME][BEGIN_MESSAGE]
    assert last_message["reply_markup"] == None

    game_title = "Название игры"
    await simulate_text(admin_flow, mock_update, mock_context, game_title)
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{GAME_OPTIONS}"                                                                     # состояние должно обновиться
    game = db_connector.get_games_by_creator_id(admin.id)[-1]
    assert admin.object_id == game.id                                                                           # id объекта должен стать game_id
    assert game.created_by == admin.id                                                                          # игра должна быть создана текущим пользователем
    assert game.title == game_title                                                                             # у игры должно быть заданное название
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[GAME_OPTIONS][BEGIN_MESSAGE]                                    # сообщение должно соответствовать сообщению состояния
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить вопрос", callback_data=f"{ADD_QUESTION}")],
        [InlineKeyboardButton("Выбрать вопрос для редактирования", callback_data=f"{QUESTION_TO_EDIT}")],
        [InlineKeyboardButton("Выбрать вопрос для удаления", callback_data=f"{QUESTION_TO_DELETE}")],
        [InlineKeyboardButton("Опции администратора", callback_data=f"{ADMIN_OPTIONS}")]
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"                              # кнопки должны сопадать

    await simulate_callback(admin_flow, mock_update, mock_context, f"{ADD_QUESTION}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{ADD_QUESTION}"
    assert admin.object_id == game.id
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[ADD_QUESTION][BEGIN_MESSAGE]

    question_text = "Первый вопрос"
    await simulate_text(admin_flow, mock_update, mock_context, question_text)
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{QUESTION_OPTIONS}"
    questions = db_connector.get_questions_by_game(game.id)
    assert len(questions) == 1, "Вопрос должен был добавиться"
    question = questions[-1]
    assert admin.object_id == question.id
    assert question.game_id == game.id
    assert question.question_text == question_text
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[QUESTION_OPTIONS][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Редактировать текст вопроса", callback_data=f"{EDIT_QUESTION_TEXT}")],
        [InlineKeyboardButton("Редактировть вариант", callback_data=f"{VARIANT_OPTIONS}")],
        [InlineKeyboardButton("Изменить картинку", callback_data=f"{UPDATE_IMAGE}")],
        [InlineKeyboardButton("Изменить правильные ответы", callback_data=f"{CHANGE_CORRECTNESS}")],
        [InlineKeyboardButton("Редактирование игры", callback_data=f"{GAME_OPTIONS}")]
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"
    
    await simulate_callback(admin_flow, mock_update, mock_context, f"{EDIT_QUESTION_TEXT}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{EDIT_QUESTION_TEXT}"
    assert admin.object_id == question.id
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[EDIT_QUESTION_TEXT][BEGIN_MESSAGE]
    assert last_message["reply_markup"] == None

    new_question_text = "Новый первый вопрос"
    await simulate_text(admin_flow, mock_update, mock_context, new_question_text)
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{QUESTION_OPTIONS}"
    assert admin.object_id == question.id
    question = db_connector.get_question(question.id)
    assert question.question_text == new_question_text

    await simulate_callback(admin_flow, mock_update, mock_context, f"{VARIANT_OPTIONS}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{VARIANT_OPTIONS}"
    assert admin.object_id == question.id
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[VARIANT_OPTIONS][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить вариант", callback_data=f"{ADD_VARIANT}")],
        [InlineKeyboardButton("Выбрать вариант для редактирования", callback_data=f"{VARIANT_TO_EDIT}")],
        [InlineKeyboardButton("Выбрать вариант для удаления", callback_data=f"{VARIANT_TO_DELETE}")],
        [InlineKeyboardButton("Редактировать вопрос", callback_data=f"{QUESTION_OPTIONS}")],
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"

    await simulate_callback(admin_flow, mock_update, mock_context, f"{ADD_VARIANT}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{ADD_VARIANT}"
    assert admin.object_id == question.id
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[ADD_VARIANT][BEGIN_MESSAGE]
    assert last_message["reply_markup"] == None

    variant_text = "Первый вариант"
    await simulate_text(admin_flow, mock_update, mock_context, variant_text)
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{VARIANT_OPTIONS}"
    variants = db_connector.get_variants_by_question(question.id)
    assert len(variants) == 1, "Вариант должен был добавиться"
    variant = variants[-1]
    assert admin.object_id == question.id
    assert variant.question_id == question.id
    assert variant.answer_text == variant_text
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[VARIANT_OPTIONS][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить вариант", callback_data=f"{ADD_VARIANT}")],
        [InlineKeyboardButton("Выбрать вариант для редактирования", callback_data=f"{VARIANT_TO_EDIT}")],
        [InlineKeyboardButton("Выбрать вариант для удаления", callback_data=f"{VARIANT_TO_DELETE}")],
        [InlineKeyboardButton("Редактировать вопрос", callback_data=f"{QUESTION_OPTIONS}")],
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"

    await simulate_callback(admin_flow, mock_update, mock_context, f"{VARIANT_TO_EDIT}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{VARIANT_TO_EDIT}"
    assert admin.object_id == question.id
    variants = db_connector.get_variants_by_question(question.id)
    variant = variants[-1]
    assert len(variants) == 1, "Вариант, пока что, должен быть один"
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[VARIANT_TO_EDIT][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(variant_text, callback_data=f"{variant.id}")],
        [InlineKeyboardButton("Отмена", callback_data=f"{VARIANT_OPTIONS}")],
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"

    await simulate_callback(admin_flow, mock_update, mock_context, f"{VARIANT_OPTIONS}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{VARIANT_OPTIONS}"
    assert admin.object_id == question.id
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[VARIANT_OPTIONS][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить вариант", callback_data=f"{ADD_VARIANT}")],
        [InlineKeyboardButton("Выбрать вариант для редактирования", callback_data=f"{VARIANT_TO_EDIT}")],
        [InlineKeyboardButton("Выбрать вариант для удаления", callback_data=f"{VARIANT_TO_DELETE}")],
        [InlineKeyboardButton("Редактировать вопрос", callback_data=f"{QUESTION_OPTIONS}")],
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"

    await simulate_callback(admin_flow, mock_update, mock_context, f"{ADD_VARIANT}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{ADD_VARIANT}"
    assert admin.object_id == question.id
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[ADD_VARIANT][BEGIN_MESSAGE]
    assert last_message["reply_markup"] == None

    variant_text = "Второй вариант"
    await simulate_text(admin_flow, mock_update, mock_context, variant_text)
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{VARIANT_OPTIONS}"
    variants = db_connector.get_variants_by_question(question.id)
    assert len(variants) == 2, "Вариант должен был добавиться"
    variant = variants[-1]
    assert admin.object_id == question.id
    assert variant.question_id == question.id
    assert variant.answer_text == variant_text
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[VARIANT_OPTIONS][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить вариант", callback_data=f"{ADD_VARIANT}")],
        [InlineKeyboardButton("Выбрать вариант для редактирования", callback_data=f"{VARIANT_TO_EDIT}")],
        [InlineKeyboardButton("Выбрать вариант для удаления", callback_data=f"{VARIANT_TO_DELETE}")],
        [InlineKeyboardButton("Редактировать вопрос", callback_data=f"{QUESTION_OPTIONS}")],
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"
    
    await simulate_callback(admin_flow, mock_update, mock_context, f"{ADD_VARIANT}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{ADD_VARIANT}"
    assert admin.object_id == question.id
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[ADD_VARIANT][BEGIN_MESSAGE]
    assert last_message["reply_markup"] == None

    variant_text = "Третий вариант"
    await simulate_text(admin_flow, mock_update, mock_context, variant_text)
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{VARIANT_OPTIONS}"
    variants = db_connector.get_variants_by_question(question.id)
    assert len(variants) == 3, "Вариант должен был добавиться"
    variant = variants[-1]
    assert admin.object_id == question.id
    assert variant.question_id == question.id
    assert variant.answer_text == variant_text
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[VARIANT_OPTIONS][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить вариант", callback_data=f"{ADD_VARIANT}")],
        [InlineKeyboardButton("Выбрать вариант для редактирования", callback_data=f"{VARIANT_TO_EDIT}")],
        [InlineKeyboardButton("Выбрать вариант для удаления", callback_data=f"{VARIANT_TO_DELETE}")],
        [InlineKeyboardButton("Редактировать вопрос", callback_data=f"{QUESTION_OPTIONS}")],
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"
    
    await simulate_callback(admin_flow, mock_update, mock_context, f"{VARIANT_TO_EDIT}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{VARIANT_TO_EDIT}"
    assert admin.object_id == question.id
    variants = db_connector.get_variants_by_question(question.id)
    assert len(variants) == 3, "Вариантов должно быть 3"
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[VARIANT_TO_EDIT][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(variants[0].answer_text, callback_data=f"{variants[0].id}"),
         InlineKeyboardButton(variants[1].answer_text, callback_data=f"{variants[1].id}")],
        [InlineKeyboardButton("➡️", callback_data=f"{PAGE}|{1}")],
        [InlineKeyboardButton("Отмена", callback_data=f"{VARIANT_OPTIONS}")],
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"
    
    await simulate_callback(admin_flow, mock_update, mock_context, f"{PAGE}|{1}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{VARIANT_TO_EDIT}"
    assert admin.object_id == question.id
    variants = db_connector.get_variants_by_question(question.id)
    assert len(variants) == 3, "Вариантов должно быть 3"
    last_message = get_last_updated_keyboard(mock_update, mock_context)
    # assert last_message["text"] == ADMIN_STATES[VARIANT_TO_EDIT][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_update.callback_query.edit_message_reply_markup.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    variant = variants[2]
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(variant.answer_text, callback_data=f"{variant.id}")],
        [InlineKeyboardButton("⬅️", callback_data=f"{PAGE}|{0}")],
        [InlineKeyboardButton("Отмена", callback_data=f"{VARIANT_OPTIONS}")],
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"
    
    await simulate_callback(admin_flow, mock_update, mock_context, f"{variant.id}")
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == EDIT_VARIANT_TEXT
    assert admin.object_id == variant.id
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[EDIT_VARIANT_TEXT][BEGIN_MESSAGE]
    variants = db_connector.get_variants_by_question(question.id)
    assert len(variants) == 3, "Вариантов должно быть 3"
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is None, "Ожидается текст"

    new_variant_text = "Новый третий вариант"
    await simulate_text(admin_flow, mock_update, mock_context, new_variant_text)
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{VARIANT_OPTIONS}"
    variants = db_connector.get_variants_by_question(question.id)
    assert len(variants) == 3, "Вариант должен был добавиться"
    variant = variants[-1]
    assert admin.object_id == question.id
    assert variant.question_id == question.id
    assert variant.answer_text == new_variant_text
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[VARIANT_OPTIONS][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить вариант", callback_data=f"{ADD_VARIANT}")],
        [InlineKeyboardButton("Выбрать вариант для редактирования", callback_data=f"{VARIANT_TO_EDIT}")],
        [InlineKeyboardButton("Выбрать вариант для удаления", callback_data=f"{VARIANT_TO_DELETE}")],
        [InlineKeyboardButton("Редактировать вопрос", callback_data=f"{QUESTION_OPTIONS}")],
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"

    await simulate_callback(admin_flow, mock_update, mock_context, QUESTION_OPTIONS)
    admin = db_connector.get_internal_user_by_telegram_id(mock_update.effective_user.id)
    assert admin.state == f"{QUESTION_OPTIONS}"
    questions = db_connector.get_questions_by_game(game.id)
    assert len(questions) == 1, "Вопрос должен быть один"
    question = questions[-1]
    assert admin.object_id == question.id
    assert question.game_id == game.id
    assert question.question_text == new_question_text
    last_message = get_last_bot_message(mock_context)
    assert last_message["text"] == ADMIN_STATES[QUESTION_OPTIONS][BEGIN_MESSAGE]
    called_args, called_kwargs = mock_context.bot.send_message.call_args
    reply_markup = called_kwargs.get("reply_markup")
    assert reply_markup is not None, "Ожидалась inline-клавиатура, но её нет"                                   # в этот состоянии должы быть кнопки
    assert isinstance(reply_markup, InlineKeyboardMarkup), "reply_markup должен быть InlineKeyboardMarkup"
    expected_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Редактировать текст вопроса", callback_data=f"{EDIT_QUESTION_TEXT}")],
        [InlineKeyboardButton("Редактировть вариант", callback_data=f"{VARIANT_OPTIONS}")],
        [InlineKeyboardButton("Изменить картинку", callback_data=f"{UPDATE_IMAGE}")],
        [InlineKeyboardButton("Изменить правильные ответы", callback_data=f"{CHANGE_CORRECTNESS}")],
        [InlineKeyboardButton("Редактирование игры", callback_data=f"{GAME_OPTIONS}")]
    ])
    actual_keyboard = reply_markup.to_dict()
    expected_keyboard = expected_keyboard.to_dict()
    actual_json = json.dumps(actual_keyboard, indent=4, ensure_ascii=False)
    expected_json = json.dumps(expected_keyboard, indent=4, ensure_ascii=False)
    assert actual_keyboard == expected_keyboard, \
        f"\nОжидалась клавиатура:\n{expected_json}\n\nНо получили:\n{actual_json}"
    
    await simulate_callback(admin_flow, mock_update, mock_context, CHANGE_CORRECTNESS)
    