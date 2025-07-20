"""
QR Code Generator for Admin Bot
Генерация QR-кодов для подключения к игровым сессиям
"""

import qrcode
import io
import base64
from typing import Optional
import structlog

logger = structlog.get_logger()


class QRGenerator:
    """Генератор QR-кодов"""
    
    def __init__(self, bot_username: str = "your_player_bot"):
        self.bot_username = bot_username
    
    def generate_session_qr(self, session_code: str, session_id: str = None) -> bytes:
        """Генерировать QR-код для подключения к сессии"""
        # Создаем ссылку для подключения к боту игроков
        bot_link = f"https://t.me/{self.bot_username}?start={session_code}"
        
        # Создаем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(bot_link)
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем в bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        logger.info(f"QR code generated for session {session_code}")
        return img_buffer.getvalue()
    
    def generate_session_link(self, session_code: str) -> str:
        """Генерировать ссылку для подключения к сессии"""
        return f"https://t.me/{self.bot_username}?start={session_code}"
    
    def generate_qr_with_text(self, session_code: str, game_title: str = None) -> bytes:
        """Генерировать QR-код с дополнительным текстом"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Генерируем базовый QR-код
        qr_data = self.generate_session_qr(session_code)
        qr_img = Image.open(io.BytesIO(qr_data))
        
        # Создаем новое изображение с местом для текста
        width, height = qr_img.size
        new_height = height + 100  # Добавляем место для текста
        
        new_img = Image.new('RGB', (width, new_height), 'white')
        new_img.paste(qr_img, (0, 0))
        
        # Добавляем текст
        draw = ImageDraw.Draw(new_img)
        
        try:
            # Пытаемся использовать системный шрифт
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except:
            # Используем стандартный шрифт если системный недоступен
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Заголовок
        title_text = game_title if game_title else "Подключение к игре"
        title_bbox = draw.textbbox((0, 0), title_text, font=font_large)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, height + 10), title_text, fill='black', font=font_large)
        
        # Код сессии
        code_text = f"Код: {session_code}"
        code_bbox = draw.textbbox((0, 0), code_text, font=font_small)
        code_width = code_bbox[2] - code_bbox[0]
        code_x = (width - code_width) // 2
        draw.text((code_x, height + 45), code_text, fill='black', font=font_small)
        
        # Инструкция
        instruction_text = "Отсканируйте QR-код или введите код в боте"
        instruction_bbox = draw.textbbox((0, 0), instruction_text, font=font_small)
        instruction_width = instruction_bbox[2] - instruction_bbox[0]
        instruction_x = (width - instruction_width) // 2
        draw.text((instruction_x, height + 70), instruction_text, fill='gray', font=font_small)
        
        # Конвертируем в bytes
        img_buffer = io.BytesIO()
        new_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
    
    def generate_base64_qr(self, session_code: str) -> str:
        """Генерировать QR-код в формате base64"""
        qr_data = self.generate_session_qr(session_code)
        return base64.b64encode(qr_data).decode('utf-8')
    
    def validate_session_code(self, session_code: str) -> bool:
        """Валидировать код сессии"""
        if not session_code:
            return False
        
        # Код должен быть строкой из 6-8 символов (буквы и цифры)
        if not (6 <= len(session_code) <= 8):
            return False
        
        # Только буквы и цифры
        if not session_code.isalnum():
            return False
        
        return True
    
    def create_shareable_message(self, session_code: str, game_title: str = None) -> str:
        """Создать сообщение для шаринга"""
        bot_link = self.generate_session_link(session_code)
        
        if game_title:
            message = f"🎮 Присоединяйтесь к игре '{game_title}'!\n\n"
        else:
            message = "🎮 Присоединяйтесь к игре!\n\n"
        
        message += f"📱 Код для подключения: `{session_code}`\n"
        message += f"🔗 Или перейдите по ссылке: {bot_link}\n\n"
        message += "Удачи в игре! 🍀"
        
        return message