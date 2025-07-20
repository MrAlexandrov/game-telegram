"""
Game Management Handlers for Admin Bot
Обработчики для управления играми
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Document
from aiogram.fsm.context import FSMContext
import structlog
import json

from ..states import GameCreationStates, AdminStates
from ..keyboards import MainMenuKeyboard, GameManagementKeyboard
from ..services.api_client import APIClient, APIClientError
from ..services.file_handler import FileHandler, FileHandlerError

logger = structlog.get_logger()
router = Router()


@router.callback_query(F.data == "create_game")
async def create_game_handler(callback: CallbackQuery, state: FSMContext):
    """Начало создания игры"""
    await state.set_state(GameCreationStates.SELECTING_TYPE)
    
    await callback.message.edit_text(
        "🎮 <b>Создание новой игры</b>\n\n"
        "Выберите способ создания игры:",
        parse_mode="HTML",
        reply_markup=GameManagementKeyboard.get_game_creation_options()
    )
    
    await callback.answer()


@router.callback_query(F.data == "upload_game_pack")
async def upload_game_pack_handler(callback: CallbackQuery, state: FSMContext):
    """Загрузка игрового пака"""
    await state.set_state(GameCreationStates.UPLOADING_PACK)
    
    await callback.message.edit_text(
        "📁 <b>Загрузка игрового пака</b>\n\n"
        "Отправьте JSON файл с игровым паком.\n\n"
        "<b>Требования к файлу:</b>\n"
        "• Формат: JSON\n"
        "• Размер: до 10 МБ\n"
        "• Структура согласно документации\n\n"
        "Примеры игровых паков можно найти в документации.",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.get_back_button("create_game")
    )
    
    await callback.answer()


@router.message(F.document, GameCreationStates.UPLOADING_PACK)
async def process_game_pack_upload(message: Message, state: FSMContext, api_client: APIClient):
    """Обработка загруженного игрового пака"""
    document: Document = message.document
    file_handler = FileHandler()
    
    # Проверяем тип файла
    if not file_handler.validate_file_type(document.file_name):
        await message.answer(
            "❌ Неподдерживаемый тип файла.\n"
            "Поддерживаются только JSON файлы."
        )
        return
    
    # Проверяем размер файла
    if not file_handler.validate_file_size(document.file_size):
        max_size = file_handler.format_file_size(file_handler.MAX_FILE_SIZE)
        await message.answer(
            f"❌ Файл слишком большой.\n"
            f"Максимальный размер: {max_size}"
        )
        return
    
    try:
        # Скачиваем файл
        file = await message.bot.get_file(document.file_id)
        file_content = await message.bot.download_file(file.file_path)
        
        # Сохраняем временно
        temp_path = await file_handler.save_temp_file(
            file_content.read(), 
            document.file_name
        )
        
        # Парсим игровой пак
        game_pack = await file_handler.parse_game_pack(temp_path)
        game_data = file_handler.extract_game_data(game_pack)
        
        # Сохраняем данные в состоянии
        await state.update_data(
            game_data=game_data,
            temp_file=temp_path,
            original_filename=document.file_name
        )
        
        await state.set_state(GameCreationStates.CONFIRMING_GAME)
        
        # Показываем превью игры
        preview_text = (
            "✅ <b>Игровой пак успешно загружен!</b>\n\n"
            f"<b>Название:</b> {game_data['title']}\n"
            f"<b>Описание:</b> {game_data['description']}\n"
            f"<b>Тип игры:</b> {game_data['game_type']}\n"
            f"<b>Количество вопросов:</b> {len(game_data['questions'])}\n"
            f"<b>Автор:</b> {game_data['author']}\n"
            f"<b>Версия:</b> {game_data['version']}\n\n"
            "Создать игру с этими данными?"
        )
        
        await message.answer(
            preview_text,
            parse_mode="HTML",
            reply_markup=GameManagementKeyboard.get_upload_confirmation(document.file_name)
        )
        
        # Очищаем временный файл
        await file_handler.cleanup_temp_file(temp_path)
        
    except FileHandlerError as e:
        await message.answer(f"❌ Ошибка обработки файла:\n{e}")
    except Exception as e:
        logger.error(f"Error processing game pack: {e}")
        await message.answer("❌ Произошла ошибка при обработке файла")


@router.callback_query(F.data.startswith("confirm_upload:"))
async def confirm_game_creation(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Подтверждение создания игры"""
    user_id = callback.from_user.id
    state_data = await state.get_data()
    game_data = state_data.get('game_data')
    
    if not game_data:
        await callback.answer("❌ Данные игры не найдены", show_alert=True)
        return
    
    try:
        # Создаем игру через API
        result = await api_client.create_game(
            title=game_data['title'],
            description=game_data['description'],
            game_type=game_data['game_type'],
            config=game_data['config'],
            questions=game_data['questions'],
            created_by=user_id
        )
        
        await state.set_state(AdminStates.MAIN_MENU)
        
        success_text = (
            "🎉 <b>Игра успешно создана!</b>\n\n"
            f"<b>ID игры:</b> <code>{result['id']}</code>\n"
            f"<b>Название:</b> {result['title']}\n"
            f"<b>Тип:</b> {result['game_type']}\n\n"
            "Теперь вы можете запустить игровую сессию!"
        )
        
        await callback.message.edit_text(
            success_text,
            parse_mode="HTML",
            reply_markup=MainMenuKeyboard.get_main_menu()
        )
        
        logger.info(f"Game created by user {user_id}: {result['id']}")
        
    except APIClientError as e:
        logger.error(f"Error creating game: {e}")
        await callback.answer("❌ Ошибка создания игры", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "cancel_upload")
async def cancel_upload_handler(callback: CallbackQuery, state: FSMContext):
    """Отмена загрузки"""
    await state.set_state(AdminStates.MAIN_MENU)
    
    await callback.message.edit_text(
        "❌ Загрузка отменена\n\nВозвращаемся в главное меню:",
        reply_markup=MainMenuKeyboard.get_main_menu()
    )
    
    await callback.answer()


@router.callback_query(F.data == "my_games")
async def my_games_handler(callback: CallbackQuery, api_client: APIClient):
    """Список игр пользователя"""
    user_id = callback.from_user.id
    
    try:
        games = await api_client.get_user_games(user_id)
        
        if not games:
            await callback.message.edit_text(
                "📋 <b>Ваши игры</b>\n\n"
                "У вас пока нет созданных игр.\n"
                "Создайте первую игру!",
                parse_mode="HTML",
                reply_markup=GameManagementKeyboard.get_games_list([])
            )
        else:
            await callback.message.edit_text(
                f"📋 <b>Ваши игры ({len(games)})</b>\n\n"
                "Выберите игру для управления:",
                parse_mode="HTML",
                reply_markup=GameManagementKeyboard.get_games_list(games)
            )
        
    except APIClientError as e:
        logger.error(f"Error getting user games: {e}")
        await callback.answer("❌ Ошибка получения списка игр", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("game_details:"))
async def game_details_handler(callback: CallbackQuery, api_client: APIClient):
    """Детали игры"""
    game_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    
    try:
        game = await api_client.get_game_details(game_id)
        if not game:
            await callback.answer("❌ Игра не найдена", show_alert=True)
            return
        
        # Проверяем активные сессии
        sessions = await api_client.get_user_sessions(user_id, status="active")
        has_active_session = any(s.get('game_id') == game_id for s in sessions)
        
        details_text = (
            f"🎮 <b>{game['title']}</b>\n\n"
            f"<b>Описание:</b> {game.get('description', 'Нет описания')}\n"
            f"<b>Тип игры:</b> {game['game_type']}\n"
            f"<b>Количество вопросов:</b> {len(game.get('questions', []))}\n"
            f"<b>Создана:</b> {game.get('created_at', 'Неизвестно')[:10]}\n\n"
        )
        
        if has_active_session:
            details_text += "⚡ <b>У этой игры есть активная сессия</b>"
        else:
            details_text += "💤 Нет активных сессий"
        
        await callback.message.edit_text(
            details_text,
            parse_mode="HTML",
            reply_markup=GameManagementKeyboard.get_game_details(game_id, has_active_session)
        )
        
    except APIClientError as e:
        logger.error(f"Error getting game details: {e}")
        await callback.answer("❌ Ошибка получения данных игры", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("delete_game:"))
async def delete_game_handler(callback: CallbackQuery, api_client: APIClient):
    """Удаление игры"""
    game_id = callback.data.split(":", 1)[1]
    
    try:
        game = await api_client.get_game_details(game_id)
        if not game:
            await callback.answer("❌ Игра не найдена", show_alert=True)
            return
        
        confirm_text = (
            f"⚠️ <b>Удаление игры</b>\n\n"
            f"Вы действительно хотите удалить игру:\n"
            f"<b>{game['title']}</b>?\n\n"
            "❗ Это действие нельзя отменить!"
        )
        
        await callback.message.edit_text(
            confirm_text,
            parse_mode="HTML",
            reply_markup=MainMenuKeyboard.get_confirmation("delete_game", game_id)
        )
        
    except APIClientError as e:
        logger.error(f"Error preparing game deletion: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:delete_game:"))
async def confirm_delete_game(callback: CallbackQuery, api_client: APIClient):
    """Подтверждение удаления игры"""
    game_id = callback.data.split(":", 2)[2]
    
    try:
        success = await api_client.delete_game(game_id)
        
        if success:
            await callback.message.edit_text(
                "✅ Игра успешно удалена",
                reply_markup=MainMenuKeyboard.get_back_button("my_games")
            )
            logger.info(f"Game {game_id} deleted by user {callback.from_user.id}")
        else:
            await callback.answer("❌ Ошибка удаления игры", show_alert=True)
            
    except APIClientError as e:
        logger.error(f"Error deleting game: {e}")
        await callback.answer("❌ Ошибка удаления игры", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("cancel:delete_game:"))
async def cancel_delete_game(callback: CallbackQuery):
    """Отмена удаления игры"""
    game_id = callback.data.split(":", 2)[2]
    
    await callback.message.edit_text(
        "❌ Удаление отменено",
        reply_markup=MainMenuKeyboard.get_back_button(f"game_details:{game_id}")
    )
    
    await callback.answer()


@router.callback_query(F.data == "use_template")
async def use_template_handler(callback: CallbackQuery, state: FSMContext):
    """Использование шаблона игры"""
    await callback.message.edit_text(
        "📋 <b>Шаблоны игр</b>\n\n"
        "Выберите шаблон для создания игры:",
        parse_mode="HTML",
        reply_markup=GameManagementKeyboard.get_game_templates()
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("template:"))
async def template_selected_handler(callback: CallbackQuery, state: FSMContext):
    """Выбор шаблона"""
    template_type = callback.data.split(":", 1)[1]
    file_handler = FileHandler()
    
    try:
        # Создаем шаблон
        if template_type.startswith("quiz"):
            template_path = await file_handler.create_game_pack_template("quiz")
        elif template_type.startswith("family_feud"):
            template_path = await file_handler.create_game_pack_template("family_feud")
        else:
            await callback.answer("❌ Неизвестный тип шаблона", show_alert=True)
            return
        
        # Отправляем шаблон пользователю
        with open(template_path, 'rb') as template_file:
            await callback.message.answer_document(
                document=template_file,
                caption=(
                    "📋 <b>Шаблон игры</b>\n\n"
                    "Скачайте этот файл, отредактируйте его и загрузите обратно "
                    "для создания игры.\n\n"
                    "Подробная документация по структуре файлов доступна в справке."
                ),
                parse_mode="HTML"
            )
        
        # Очищаем временный файл
        await file_handler.cleanup_temp_file(template_path)
        
        await callback.message.edit_text(
            "📋 Шаблон отправлен!\n\n"
            "Отредактируйте файл и загрузите его для создания игры.",
            reply_markup=MainMenuKeyboard.get_back_button("create_game")
        )
        
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        await callback.answer("❌ Ошибка создания шаблона", show_alert=True)
    
    await callback.answer()