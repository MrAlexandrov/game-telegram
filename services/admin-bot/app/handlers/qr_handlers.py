"""
Admin Bot QR Code Handlers
Handles QR code generation and management for game sessions
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
import structlog
import io
import base64
from typing import Optional, Dict, Any

from ..states import AdminStates, SessionManagementStates
from ..keyboards import SessionControlKeyboard, MainMenuKeyboard
from ..services.api_client import APIClient, APIClientError
from ..services.qr_generator import QRGenerator
from ..config import settings

logger = structlog.get_logger()
router = Router()


class QRCodeManager:
    """Manages QR code generation and distribution"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.qr_generator = QRGenerator(settings.PLAYER_BOT_USERNAME)
    
    async def generate_session_qr(
        self,
        session_id: str,
        game_code: str,
        game_title: str,
        include_text: bool = True,
        size: int = 300
    ) -> Dict[str, Any]:
        """Generate QR code for session"""
        try:
            if include_text:
                qr_data = self.qr_generator.generate_qr_with_text(game_code, game_title)
            else:
                qr_data = self.qr_generator.generate_session_qr(game_code, session_id)
            
            # Create deep link
            deep_link = self.qr_generator.generate_session_link(game_code)
            
            return {
                "success": True,
                "qr_data": qr_data,
                "deep_link": deep_link,
                "game_code": game_code,
                "share_message": self.qr_generator.create_shareable_message(game_code, game_title)
            }
            
        except Exception as e:
            logger.error("Error generating QR code", session_id=session_id, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_new_game_code(
        self,
        session_id: str,
        code_length: int = 6,
        expires_in_minutes: int = 60,
        max_uses: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new game code for session"""
        try:
            # Request new code from session manager
            response = await self.api_client.generate_session_code(
                session_id=session_id,
                code_length=code_length,
                expires_in_minutes=expires_in_minutes,
                max_uses=max_uses
            )
            
            return {
                "success": True,
                "code_data": response
            }
            
        except APIClientError as e:
            logger.error("Error creating game code", session_id=session_id, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_session_codes(self, session_id: str) -> Dict[str, Any]:
        """Get all active codes for session"""
        try:
            codes = await self.api_client.get_session_codes(session_id)
            return {
                "success": True,
                "codes": codes
            }
        except APIClientError as e:
            logger.error("Error getting session codes", session_id=session_id, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def deactivate_code(self, session_id: str, code: str) -> bool:
        """Deactivate a game code"""
        try:
            await self.api_client.deactivate_session_code(session_id, code)
            return True
        except APIClientError as e:
            logger.error("Error deactivating code", session_id=session_id, code=code, error=str(e))
            return False


# Global QR manager instance
qr_manager = None


def get_qr_manager(api_client: APIClient) -> QRCodeManager:
    """Get or create QR manager instance"""
    global qr_manager
    if qr_manager is None:
        qr_manager = QRCodeManager(api_client)
    return qr_manager


@router.callback_query(F.data.startswith("generate_qr:"))
async def generate_qr_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Generate QR code for session"""
    session_id = callback.data.split(":", 1)[1]
    
    # Get session data from state
    state_data = await state.get_data()
    current_session = state_data.get("current_session", {})
    
    if not current_session or current_session.get("id") != session_id:
        await callback.answer("❌ Сессия не найдена", show_alert=True)
        return
    
    # Show generating message
    await callback.message.edit_text(
        "🔄 <b>Генерируем QR-код...</b>\n\n"
        "Пожалуйста, подождите...",
        parse_mode="HTML"
    )
    
    try:
        manager = get_qr_manager(api_client)
        
        # Generate QR code
        result = await manager.generate_session_qr(
            session_id=session_id,
            game_code=current_session.get("session_code", ""),
            game_title=current_session.get("title", "Игра"),
            include_text=True
        )
        
        if result["success"]:
            # Send QR code as photo
            qr_file = BufferedInputFile(
                result["qr_data"],
                filename=f"qr_code_{current_session.get('session_code', 'game')}.png"
            )
            
            caption = (
                f"📱 <b>QR-код для подключения</b>\n\n"
                f"<b>Игра:</b> {current_session.get('title', 'Неизвестная')}\n"
                f"<b>Код:</b> <code>{current_session.get('session_code', '')}</code>\n"
                f"<b>Ссылка:</b> {result['deep_link']}\n\n"
                f"<b>Игроков:</b> {current_session.get('current_players', 0)}/{current_session.get('max_players', 0)}\n\n"
                "Игроки могут:\n"
                "• Отсканировать QR-код камерой\n"
                "• Ввести код вручную в боте\n"
                "• Перейти по ссылке"
            )
            
            await callback.message.answer_photo(
                photo=qr_file,
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_qr_management_keyboard(session_id, current_session.get("session_code", ""))
            )
            
            # Update original message
            await callback.message.edit_text(
                "✅ QR-код успешно сгенерирован!",
                reply_markup=SessionControlKeyboard.get_session_management(session_id)
            )
            
        else:
            await callback.message.edit_text(
                f"❌ Ошибка генерации QR-кода:\n{result.get('error', 'Неизвестная ошибка')}",
                reply_markup=SessionControlKeyboard.get_session_management(session_id)
            )
        
    except Exception as e:
        logger.error("Error in QR generation handler", session_id=session_id, error=str(e))
        await callback.message.edit_text(
            "❌ Произошла ошибка при генерации QR-кода",
            reply_markup=SessionControlKeyboard.get_session_management(session_id)
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("qr_options:"))
async def qr_options_handler(callback: CallbackQuery, state: FSMContext):
    """Show QR code options"""
    session_id = callback.data.split(":", 1)[1]
    
    state_data = await state.get_data()
    current_session = state_data.get("current_session", {})
    
    options_text = (
        f"📱 <b>Опции QR-кода</b>\n\n"
        f"<b>Игра:</b> {current_session.get('title', 'Неизвестная')}\n"
        f"<b>Код:</b> <code>{current_session.get('session_code', '')}</code>\n\n"
        "Выберите действие:"
    )
    
    await callback.message.edit_text(
        options_text,
        parse_mode="HTML",
        reply_markup=get_qr_options_keyboard(session_id)
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("regenerate_qr:"))
async def regenerate_qr_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Regenerate QR code with new options"""
    session_id = callback.data.split(":", 1)[1]
    
    await callback.message.edit_text(
        "⚙️ <b>Настройки QR-кода</b>\n\n"
        "Выберите параметры для генерации:",
        parse_mode="HTML",
        reply_markup=get_qr_settings_keyboard(session_id)
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("qr_size:"))
async def qr_size_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle QR code size selection"""
    parts = callback.data.split(":")
    session_id = parts[1]
    size = int(parts[2])
    
    # Store size preference
    await state.update_data(qr_size=size)
    
    await callback.answer(f"✅ Размер установлен: {size}x{size}")
    
    # Regenerate with new size
    await generate_qr_with_settings(callback, state, api_client, session_id)


@router.callback_query(F.data.startswith("qr_style:"))
async def qr_style_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle QR code style selection"""
    parts = callback.data.split(":")
    session_id = parts[1]
    style = parts[2]  # "simple" or "with_text"
    
    # Store style preference
    await state.update_data(qr_style=style)
    
    await callback.answer(f"✅ Стиль установлен: {'с текстом' if style == 'with_text' else 'простой'}")
    
    # Regenerate with new style
    await generate_qr_with_settings(callback, state, api_client, session_id)


async def generate_qr_with_settings(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: APIClient,
    session_id: str
):
    """Generate QR code with custom settings"""
    state_data = await state.get_data()
    current_session = state_data.get("current_session", {})
    qr_size = state_data.get("qr_size", 300)
    qr_style = state_data.get("qr_style", "with_text")
    
    try:
        manager = get_qr_manager(api_client)
        
        result = await manager.generate_session_qr(
            session_id=session_id,
            game_code=current_session.get("session_code", ""),
            game_title=current_session.get("title", "Игра"),
            include_text=(qr_style == "with_text"),
            size=qr_size
        )
        
        if result["success"]:
            qr_file = BufferedInputFile(
                result["qr_data"],
                filename=f"qr_code_{current_session.get('session_code', 'game')}_{qr_size}.png"
            )
            
            caption = (
                f"📱 <b>Обновленный QR-код</b>\n\n"
                f"<b>Размер:</b> {qr_size}x{qr_size}\n"
                f"<b>Стиль:</b> {'с текстом' if qr_style == 'with_text' else 'простой'}\n"
                f"<b>Код:</b> <code>{current_session.get('session_code', '')}</code>"
            )
            
            await callback.message.answer_photo(
                photo=qr_file,
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_qr_management_keyboard(session_id, current_session.get("session_code", ""))
            )
            
        else:
            await callback.answer(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}", show_alert=True)
            
    except Exception as e:
        logger.error("Error generating QR with settings", session_id=session_id, error=str(e))
        await callback.answer("❌ Ошибка генерации QR-кода", show_alert=True)


@router.callback_query(F.data.startswith("share_qr:"))
async def share_qr_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Share QR code and game information"""
    session_id = callback.data.split(":", 1)[1]
    
    state_data = await state.get_data()
    current_session = state_data.get("current_session", {})
    
    try:
        manager = get_qr_manager(api_client)
        
        result = await manager.generate_session_qr(
            session_id=session_id,
            game_code=current_session.get("session_code", ""),
            game_title=current_session.get("title", "Игра")
        )
        
        if result["success"]:
            share_text = result["share_message"]
            
            await callback.message.answer(
                f"📤 <b>Поделиться игрой</b>\n\n"
                f"Скопируйте и отправьте это сообщение игрокам:\n\n"
                f"<code>{share_text}</code>",
                parse_mode="HTML",
                reply_markup=get_share_options_keyboard(session_id)
            )
            
        else:
            await callback.answer("❌ Ошибка создания сообщения для шаринга", show_alert=True)
            
    except Exception as e:
        logger.error("Error sharing QR", session_id=session_id, error=str(e))
        await callback.answer("❌ Ошибка создания сообщения", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("manage_codes:"))
async def manage_codes_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Manage game codes for session"""
    session_id = callback.data.split(":", 1)[1]
    
    try:
        manager = get_qr_manager(api_client)
        result = await manager.get_session_codes(session_id)
        
        if result["success"]:
            codes = result["codes"]
            
            if not codes:
                codes_text = "📝 <b>Коды игры</b>\n\nАктивных кодов нет."
            else:
                codes_text = f"📝 <b>Коды игры ({len(codes)})</b>\n\n"
                
                for i, code_data in enumerate(codes, 1):
                    status_emoji = {
                        "active": "🟢",
                        "expired": "🔴",
                        "disabled": "⚫"
                    }.get(code_data.get("status", "unknown"), "❓")
                    
                    codes_text += (
                        f"{i}. {status_emoji} <code>{code_data.get('code', 'N/A')}</code>\n"
                        f"   Использований: {code_data.get('current_uses', 0)}"
                    )
                    
                    if code_data.get("max_uses"):
                        codes_text += f"/{code_data['max_uses']}"
                    
                    codes_text += f"\n   Истекает: {code_data.get('expires_at', 'Никогда')}\n\n"
            
            await callback.message.edit_text(
                codes_text,
                parse_mode="HTML",
                reply_markup=get_codes_management_keyboard(session_id, codes)
            )
            
        else:
            await callback.answer("❌ Ошибка получения кодов", show_alert=True)
            
    except Exception as e:
        logger.error("Error managing codes", session_id=session_id, error=str(e))
        await callback.answer("❌ Ошибка управления кодами", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("create_new_code:"))
async def create_new_code_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Create new game code"""
    session_id = callback.data.split(":", 1)[1]
    
    await state.set_state(SessionManagementStates.CREATING_CODE)
    await state.update_data(target_session_id=session_id)
    
    await callback.message.edit_text(
        "🆕 <b>Создание нового кода</b>\n\n"
        "Выберите параметры кода:",
        parse_mode="HTML",
        reply_markup=get_code_creation_keyboard(session_id)
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("deactivate_code:"))
async def deactivate_code_handler(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Deactivate a game code"""
    parts = callback.data.split(":")
    session_id = parts[1]
    code = parts[2]
    
    try:
        manager = get_qr_manager(api_client)
        success = await manager.deactivate_code(session_id, code)
        
        if success:
            await callback.answer(f"✅ Код {code} деактивирован")
            # Refresh the codes list
            await manage_codes_handler(callback, state, api_client)
        else:
            await callback.answer("❌ Ошибка деактивации кода", show_alert=True)
            
    except Exception as e:
        logger.error("Error deactivating code", session_id=session_id, code=code, error=str(e))
        await callback.answer("❌ Ошибка деактивации", show_alert=True)


def get_qr_management_keyboard(session_id: str, game_code: str):
    """Get QR code management keyboard"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="⚙️ Настройки QR",
            callback_data=f"qr_options:{session_id}"
        ),
        InlineKeyboardButton(
            text="📤 Поделиться",
            callback_data=f"share_qr:{session_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Управление кодами",
            callback_data=f"manage_codes:{session_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 К управлению сессией",
            callback_data=f"session_control:{session_id}"
        )
    )
    
    return builder.as_markup()


def get_qr_options_keyboard(session_id: str):
    """Get QR options keyboard"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Перегенерировать",
            callback_data=f"regenerate_qr:{session_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📏 Размер",
            callback_data=f"qr_size_menu:{session_id}"
        ),
        InlineKeyboardButton(
            text="🎨 Стиль",
            callback_data=f"qr_style_menu:{session_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"generate_qr:{session_id}"
        )
    )
    
    return builder.as_markup()


def get_qr_settings_keyboard(session_id: str):
    """Get QR settings keyboard"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    # Size options
    builder.row(
        InlineKeyboardButton(
            text="📏 200x200",
            callback_data=f"qr_size:{session_id}:200"
        ),
        InlineKeyboardButton(
            text="📏 300x300",
            callback_data=f"qr_size:{session_id}:300"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📏 400x400",
            callback_data=f"qr_size:{session_id}:400"
        ),
        InlineKeyboardButton(
            text="📏 500x500",
            callback_data=f"qr_size:{session_id}:500"
        )
    )
    
    # Style options
    builder.row(
        InlineKeyboardButton(
            text="🎨 Простой",
            callback_data=f"qr_style:{session_id}:simple"
        ),
        InlineKeyboardButton(
            text="🎨 С текстом",
            callback_data=f"qr_style:{session_id}:with_text"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"qr_options:{session_id}"
        )
    )
    
    return builder.as_markup()


def get_share_options_keyboard(session_id: str):
    """Get share options keyboard"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📋 Скопировать текст",
            callback_data=f"copy_share_text:{session_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔗 Создать ссылку",
            callback_data=f"create_share_link:{session_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"qr_options:{session_id}"
        )
    )
    
    return builder.as_markup()


def get_codes_management_keyboard(session_id: str, codes: list):
    """Get codes management keyboard"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🆕 Создать код",
            callback_data=f"create_new_code:{session_id}"
        ),
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=f"manage_codes:{session_id}"
        )
    )
    
    # Add deactivation buttons for active codes
    active_codes = [c for c in codes if c.get("status") == "active"]
    if active_codes:
        builder.row(
            InlineKeyboardButton(
                text="❌ Деактивировать все",
                callback_data=f"deactivate_all_codes:{session_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 К QR-коду",
            callback_data=f"generate_qr:{session_id}"
        )
    )
    
    return builder.as_markup()


def get_code_creation_keyboard(session_id: str):
    """Get code creation keyboard"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    # Quick presets
    builder.row(
        InlineKeyboardButton(
            text="⚡ Быстрый (1 час)",
            callback_data=f"create_code_preset:{session_id}:quick"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📅 Стандартный (24 часа)",
            callback_data=f"create_code_preset:{session_id}:standard"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔒 Ограниченный (10 использований)",
            callback_data=f"create_code_preset:{session_id}:limited"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="⚙️ Настроить вручную",
            callback_data=f"create_code_custom:{session_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"manage_codes:{session_id}"
        )
    )
    
    return builder.as_markup()