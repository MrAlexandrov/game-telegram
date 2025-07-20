"""
Player Bot Connection Handlers
Handles player connections via QR codes, deep links, and manual code entry
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
import structlog
import re
import uuid
from typing import Optional, Dict, Any

from ..states import GameJoinStates, PlayerStates
from ..keyboards import GameJoinKeyboard, MainMenuKeyboard
from ..services.api_client import APIClient, APIClientError

logger = structlog.get_logger()
router = Router()


class ConnectionHandler:
    """Handles player connection logic"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    async def validate_game_code(self, code: str) -> Dict[str, Any]:
        """Validate a game code format and existence"""
        # Clean and validate format
        code = code.strip().upper()
        
        if not re.match(r'^[A-Z0-9]{4,10}$', code):
            return {
                "valid": False,
                "error_code": "INVALID_FORMAT",
                "error_message": "Код должен содержать 4-10 символов (буквы и цифры)"
            }
        
        try:
            # Check with session manager
            response = await self.api_client.validate_connection_code(code)
            return {
                "valid": response.get("valid", False),
                "error_code": response.get("error_code"),
                "error_message": response.get("error_message"),
                "session_info": response.get("session_info"),
                "can_join": response.get("can_join", False),
                "reason": response.get("reason")
            }
        except APIClientError as e:
            logger.error("Error validating code", code=code, error=str(e))
            return {
                "valid": False,
                "error_code": "SYSTEM_ERROR",
                "error_message": "Ошибка проверки кода. Попробуйте позже."
            }
    
    async def connect_to_session(
        self,
        user_id: int,
        display_name: str,
        game_code: str,
        connection_method: str = "manual_code",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Connect user to a game session"""
        try:
            # Attempt connection via API
            response = await self.api_client.join_session_by_code(
                game_code=game_code,
                user_id=user_id,
                display_name=display_name,
                connection_method=connection_method
            )
            
            return {
                "success": response.get("success", False),
                "session_id": response.get("session_id"),
                "participant_id": response.get("participant_id"),
                "session_info": response.get("session_info"),
                "player_number": response.get("player_number"),
                "total_players": response.get("total_players"),
                "error_code": response.get("error_code"),
                "error_message": response.get("error_message")
            }
            
        except APIClientError as e:
            logger.error("Error connecting to session", user_id=user_id, code=game_code, error=str(e))
            return {
                "success": False,
                "error_code": "SYSTEM_ERROR",
                "error_message": "Ошибка подключения к игре. Попробуйте позже."
            }
    
    def parse_deep_link(self, start_param: str) -> Optional[Dict[str, Any]]:
        """Parse deep link parameters from /start command"""
        if not start_param:
            return None
        
        # Simple game code format
        if re.match(r'^[A-Z0-9]{4,10}$', start_param.upper()):
            return {
                "type": "game_code",
                "game_code": start_param.upper(),
                "connection_method": "deep_link"
            }
        
        # Extended format with parameters (e.g., CODE_param1_param2)
        parts = start_param.split('_')
        if len(parts) >= 1 and re.match(r'^[A-Z0-9]{4,10}$', parts[0].upper()):
            result = {
                "type": "game_code",
                "game_code": parts[0].upper(),
                "connection_method": "deep_link"
            }
            
            # Parse additional parameters
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    result[parts[i]] = parts[i + 1]
            
            return result
        
        return None
    
    def format_error_message(self, error_code: str, error_message: str) -> str:
        """Format error message for user display"""
        error_messages = {
            "INVALID_CODE": "❌ Неверный код игры",
            "CODE_NOT_FOUND": "❌ Игра с таким кодом не найдена",
            "CODE_EXPIRED": "❌ Код игры истек",
            "CODE_DISABLED": "❌ Код игры отключен",
            "CODE_MAX_USES": "❌ Код игры исчерпал лимит использований",
            "SESSION_NOT_FOUND": "❌ Игра не найдена",
            "SESSION_FULL": "❌ Игра переполнена",
            "SESSION_ENDED": "❌ Игра уже завершена",
            "SESSION_NOT_STARTED": "❌ Игра еще не началась",
            "ALREADY_CONNECTED": "❌ Вы уже подключены к этой игре",
            "LATE_JOIN_DISABLED": "❌ Присоединение к начавшейся игре отключено",
            "SYSTEM_ERROR": "❌ Системная ошибка",
            "INVALID_FORMAT": "❌ Неверный формат кода"
        }
        
        return error_messages.get(error_code, f"❌ {error_message}")


# Global connection handler instance
connection_handler = None


def get_connection_handler(api_client: APIClient) -> ConnectionHandler:
    """Get or create connection handler instance"""
    global connection_handler
    if connection_handler is None:
        connection_handler = ConnectionHandler(api_client)
    return connection_handler


@router.message(CommandStart())
async def enhanced_start_handler(message: Message, state: FSMContext, api_client: APIClient):
    """Enhanced start handler with deep link support"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Get connection handler
    handler = get_connection_handler(api_client)
    
    # Parse start parameters
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    start_param = args[0] if args else None
    
    try:
        # Register/update player
        try:
            await api_client.register_player(
                telegram_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
        except APIClientError:
            # Player already exists, this is normal
            pass
        
        # Check for deep link parameters
        if start_param:
            deep_link_data = handler.parse_deep_link(start_param)
            
            if deep_link_data and deep_link_data["type"] == "game_code":
                game_code = deep_link_data["game_code"]
                
                # Validate the code first
                validation_result = await handler.validate_game_code(game_code)
                
                if validation_result["valid"] and validation_result["can_join"]:
                    # Show connection confirmation
                    session_info = validation_result["session_info"]
                    
                    await state.set_state(GameJoinStates.CONFIRMING_JOIN)
                    await state.update_data(
                        game_code=game_code,
                        connection_method="deep_link",
                        session_info=session_info
                    )
                    
                    await message.answer(
                        f"🎮 <b>Подключение к игре</b>\n\n"
                        f"<b>Игра:</b> {session_info.get('title', 'Неизвестная игра')}\n"
                        f"<b>Код:</b> <code>{game_code}</code>\n"
                        f"<b>Игроков:</b> {session_info.get('current_players', 0)}/{session_info.get('max_players', 0)}\n"
                        f"<b>Статус:</b> {session_info.get('status', 'unknown')}\n\n"
                        "Присоединиться к этой игре?",
                        parse_mode="HTML",
                        reply_markup=GameJoinKeyboard.get_join_confirmation(
                            game_code, 
                            session_info.get('title', 'Игра')
                        )
                    )
                    return
                else:
                    # Show error and continue to main menu
                    error_msg = handler.format_error_message(
                        validation_result.get("error_code", "UNKNOWN"),
                        validation_result.get("error_message", "Неизвестная ошибка")
                    )
                    
                    if not validation_result["can_join"] and validation_result["valid"]:
                        error_msg += f"\n\nПричина: {validation_result.get('reason', 'Неизвестно')}"
                    
                    await message.answer(error_msg)
        
        # Show normal welcome message
        await state.set_state(PlayerStates.MAIN_MENU)
        
        welcome_text = (
            f"👋 Привет, {first_name}!\n\n"
            "🎮 Добро пожаловать в игровую систему!\n\n"
            "Здесь ты можешь:\n"
            "• Присоединяться к играм по коду или QR-коду\n"
            "• Отвечать на вопросы и зарабатывать очки\n"
            "• Соревноваться с другими игроками\n"
            "• Просматривать свою статистику\n\n"
            "Что хочешь делать?"
        )
        
        await message.answer(
            welcome_text,
            reply_markup=MainMenuKeyboard.get_main_menu()
        )
        
        logger.info(
            "Player started bot",
            user_id=user_id,
            username=username,
            deep_link=bool(start_param)
        )
        
    except APIClientError as e:
        logger.error("API error in enhanced start handler", error=str(e))
        await message.answer(
            "❌ Ошибка подключения к системе. Попробуйте позже."
        )


@router.callback_query(F.data == "join_game_enhanced")
async def enhanced_join_game_handler(callback: CallbackQuery, state: FSMContext):
    """Enhanced join game handler with multiple options"""
    await state.set_state(GameJoinStates.CHOOSING_METHOD)
    
    await callback.message.edit_text(
        "🎮 <b>Подключение к игре</b>\n\n"
        "Выберите способ подключения:",
        parse_mode="HTML",
        reply_markup=GameJoinKeyboard.get_connection_methods()
    )
    
    await callback.answer()


@router.callback_query(F.data == "connect_by_code")
async def connect_by_code_handler(callback: CallbackQuery, state: FSMContext):
    """Handle manual code entry"""
    await state.set_state(GameJoinStates.ENTERING_CODE)
    
    await callback.message.edit_text(
        "🔤 <b>Ввод кода игры</b>\n\n"
        "Введите код игры (4-10 символов):\n\n"
        "Код можно получить от администратора игры "
        "или найти под QR-кодом.",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.get_back_button("join_game_enhanced")
    )
    
    await callback.answer()


@router.callback_query(F.data == "connect_by_qr_info")
async def qr_connection_info_handler(callback: CallbackQuery):
    """Show QR code connection information"""
    info_text = (
        "📱 <b>Подключение через QR-код</b>\n\n"
        "К сожалению, прямое сканирование QR-кода "
        "в Telegram боте невозможно.\n\n"
        "<b>Как использовать QR-код:</b>\n"
        "1. Отсканируйте QR-код камерой телефона\n"
        "2. Перейдите по ссылке\n"
        "3. Бот автоматически подключит вас к игре\n\n"
        "<b>Или:</b>\n"
        "Введите код игры вручную - он указан под QR-кодом."
    )
    
    await callback.message.edit_text(
        info_text,
        parse_mode="HTML",
        reply_markup=GameJoinKeyboard.get_qr_info_keyboard()
    )
    
    await callback.answer()


@router.message(F.text, GameJoinStates.ENTERING_CODE)
async def enhanced_process_game_code(message: Message, state: FSMContext, api_client: APIClient):
    """Enhanced game code processing with better validation"""
    code = message.text.strip().upper()
    user_id = message.from_user.id
    display_name = message.from_user.first_name or message.from_user.username or f"Player{user_id}"
    
    # Get connection handler
    handler = get_connection_handler(api_client)
    
    # Validate code format first
    if not re.match(r'^[A-Z0-9]{4,10}$', code):
        await message.answer(
            "❌ Неверный формат кода!\n\n"
            "Код должен содержать 4-10 символов (буквы и цифры).\n"
            "Попробуйте еще раз:"
        )
        return
    
    # Show processing message
    processing_msg = await message.answer("🔄 Проверяем код игры...")
    
    try:
        # Validate code
        validation_result = await handler.validate_game_code(code)
        
        if not validation_result["valid"]:
            error_msg = handler.format_error_message(
                validation_result.get("error_code", "UNKNOWN"),
                validation_result.get("error_message", "Неизвестная ошибка")
            )
            
            await processing_msg.edit_text(
                f"{error_msg}\n\n"
                "Проверьте правильность кода и попробуйте еще раз:"
            )
            return
        
        # Check if can join
        if not validation_result["can_join"]:
            reason = validation_result.get("reason", "Неизвестная причина")
            await processing_msg.edit_text(
                f"❌ Невозможно присоединиться к игре\n\n"
                f"Причина: {reason}\n\n"
                "Попробуйте другой код или обратитесь к администратору."
            )
            return
        
        # Show confirmation
        session_info = validation_result["session_info"]
        
        await state.update_data(
            game_code=code,
            connection_method="manual_code",
            session_info=session_info
        )
        await state.set_state(GameJoinStates.CONFIRMING_JOIN)
        
        # Format session status
        status_text = {
            "waiting": "Ожидание игроков",
            "in_progress": "Игра идет",
            "paused": "На паузе"
        }.get(session_info.get("status"), "Неизвестно")
        
        confirm_text = (
            f"✅ <b>Игра найдена!</b>\n\n"
            f"<b>Название:</b> {session_info.get('title', 'Неизвестная игра')}\n"
            f"<b>Тип:</b> {session_info.get('game_type', 'unknown')}\n"
            f"<b>Код:</b> <code>{code}</code>\n"
            f"<b>Игроков:</b> {session_info.get('current_players', 0)}/{session_info.get('max_players', 0)}\n"
            f"<b>Статус:</b> {status_text}\n\n"
            "Присоединиться к этой игре?"
        )
        
        await processing_msg.edit_text(
            confirm_text,
            parse_mode="HTML",
            reply_markup=GameJoinKeyboard.get_join_confirmation(
                code, 
                session_info.get('title', 'Игра')
            )
        )
        
    except Exception as e:
        logger.error("Error processing game code", code=code, user_id=user_id, error=str(e))
        await processing_msg.edit_text(
            "❌ Ошибка при проверке кода игры.\n"
            "Попробуйте позже или обратитесь к администратору."
        )


@router.callback_query(F.data.startswith("confirm_join:"))
async def enhanced_confirm_join_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Enhanced join confirmation with better error handling"""
    game_code = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    display_name = callback.from_user.first_name or callback.from_user.username or f"Player{user_id}"
    
    # Get connection handler and state data
    handler = get_connection_handler(api_client)
    state_data = await state.get_data()
    connection_method = state_data.get("connection_method", "manual_code")
    
    # Show connecting message
    await callback.message.edit_text(
        "🔄 <b>Подключаемся к игре...</b>\n\n"
        "Пожалуйста, подождите...",
        parse_mode="HTML"
    )
    
    try:
        # Attempt connection
        connection_result = await handler.connect_to_session(
            user_id=user_id,
            display_name=display_name,
            game_code=game_code,
            connection_method=connection_method
        )
        
        if connection_result["success"]:
            # Success - update state and show success message
            await state.set_state(GameJoinStates.WAITING_GAME_START)
            await state.update_data(
                session_id=connection_result["session_id"],
                participant_id=connection_result["participant_id"],
                game_code=game_code
            )
            
            session_info = connection_result.get("session_info", {})
            
            success_text = (
                f"✅ <b>Вы присоединились к игре!</b>\n\n"
                f"<b>Игра:</b> {session_info.get('title', 'Неизвестная')}\n"
                f"<b>Ваш номер:</b> {connection_result.get('player_number', '?')}\n"
                f"<b>Игроков в сессии:</b> {connection_result.get('total_players', 1)}\n\n"
            )
            
            if session_info.get("status") == "waiting":
                success_text += (
                    "⏳ Ожидание начала игры...\n\n"
                    "Администратор запустит игру, когда все будут готовы."
                )
            else:
                success_text += (
                    "🎮 Игра уже идет!\n\n"
                    "Вы присоединились к игре в процессе."
                )
            
            await callback.message.edit_text(
                success_text,
                parse_mode="HTML",
                reply_markup=GameJoinKeyboard.get_waiting_game_start()
            )
            
            logger.info(
                "Player successfully joined session",
                user_id=user_id,
                game_code=game_code,
                session_id=connection_result["session_id"],
                connection_method=connection_method
            )
            
        else:
            # Connection failed
            error_msg = handler.format_error_message(
                connection_result.get("error_code", "UNKNOWN"),
                connection_result.get("error_message", "Неизвестная ошибка")
            )
            
            await callback.message.edit_text(
                f"{error_msg}\n\n"
                "Попробуйте еще раз или обратитесь к администратору игры.",
                reply_markup=MainMenuKeyboard.get_back_button("back_to_main")
            )
            
            logger.warning(
                "Player connection failed",
                user_id=user_id,
                game_code=game_code,
                error_code=connection_result.get("error_code"),
                connection_method=connection_method
            )
        
    except Exception as e:
        logger.error("Error in join confirmation", user_id=user_id, game_code=game_code, error=str(e))
        await callback.message.edit_text(
            "❌ Произошла ошибка при подключении к игре.\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            reply_markup=MainMenuKeyboard.get_back_button("back_to_main")
        )
    
    await callback.answer()


@router.callback_query(F.data == "refresh_session_info")
async def refresh_session_info_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Refresh session information"""
    state_data = await state.get_data()
    game_code = state_data.get("game_code")
    
    if not game_code:
        await callback.answer("❌ Код игры не найден", show_alert=True)
        return
    
    try:
        handler = get_connection_handler(api_client)
        validation_result = await handler.validate_game_code(game_code)
        
        if validation_result["valid"]:
            session_info = validation_result["session_info"]
            
            # Update state data
            await state.update_data(session_info=session_info)
            
            # Update message
            status_text = {
                "waiting": "Ожидание игроков",
                "in_progress": "Игра идет",
                "paused": "На паузе"
            }.get(session_info.get("status"), "Неизвестно")
            
            updated_text = (
                f"🔄 <b>Обновленная информация</b>\n\n"
                f"<b>Игра:</b> {session_info.get('title', 'Неизвестная')}\n"
                f"<b>Игроков:</b> {session_info.get('current_players', 0)}/{session_info.get('max_players', 0)}\n"
                f"<b>Статус:</b> {status_text}\n\n"
                "Ожидание начала игры..."
            )
            
            await callback.message.edit_text(
                updated_text,
                parse_mode="HTML",
                reply_markup=GameJoinKeyboard.get_waiting_game_start()
            )
            
            await callback.answer("✅ Информация обновлена")
        else:
            await callback.answer("❌ Не удалось обновить информацию", show_alert=True)
            
    except Exception as e:
        logger.error("Error refreshing session info", error=str(e))
        await callback.answer("❌ Ошибка обновления", show_alert=True)


# Quick join handler for direct code input
@router.message(F.text.regexp(r'^[A-Z0-9]{4,10}$'), PlayerStates.MAIN_MENU)
async def quick_join_by_code(message: Message, state: FSMContext, api_client: APIClient):
    """Quick join when user sends a game code directly"""
    code = message.text.strip().upper()
    
    # Set state and process as if entered through normal flow
    await state.set_state(GameJoinStates.ENTERING_CODE)
    await enhanced_process_game_code(message, state, api_client)