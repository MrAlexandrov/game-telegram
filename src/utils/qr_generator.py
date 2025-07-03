"""
Генератор QR-кодов
"""
import qrcode
import io
from typing import Optional
from src.settings import settings
import os


class QRGenerator:
    """Генератор QR-кодов для подключения к играм"""
    
    def __init__(self):
        self.qr_codes_dir = settings.qr_codes_dir
        # Создаем директорию если не существует
        os.makedirs(self.qr_codes_dir, exist_ok=True)
    
    def generate_qr_code(self, data: str, save_path: Optional[str] = None) -> bytes:
        """
        Генерация QR-кода
        
        Args:
            data: Данные для кодирования
            save_path: Путь для сохранения файла (опционально)
            
        Returns:
            QR-код в виде байтов (PNG)
        """
        # Создаем QR-код
        qr = qrcode.QRCode(
            version=1,  # Размер QR-кода (1-40)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Уровень коррекции ошибок
            box_size=10,  # Размер каждого блока в пикселях
            border=4,  # Размер границы
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем в байты
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Сохраняем файл если указан путь
        if save_path:
            full_path = os.path.join(self.qr_codes_dir, save_path)
            img.save(full_path)
        
        return img_bytes.getvalue()
    
    def generate_session_qr(self, session_code: str, bot_username: Optional[str] = None) -> bytes:
        """
        Генерация QR-кода для подключения к сессии
        
        Args:
            session_code: Код сессии
            bot_username: Username бота (без @)
            
        Returns:
            QR-код в виде байтов
        """
        if bot_username:
            # Создаем deep link для Telegram
            url = f"https://t.me/{bot_username}?start=join_{session_code}"
        else:
            # Простой текст с кодом
            url = f"Код игры: {session_code}"
        
        filename = f"session_{session_code}.png"
        return self.generate_qr_code(url, filename)
    
    def generate_bot_qr(self, bot_username: str, start_parameter: Optional[str] = None) -> bytes:
        """
        Генерация QR-кода для бота
        
        Args:
            bot_username: Username бота (без @)
            start_parameter: Параметр для команды /start
            
        Returns:
            QR-код в виде байтов
        """
        if start_parameter:
            url = f"https://t.me/{bot_username}?start={start_parameter}"
        else:
            url = f"https://t.me/{bot_username}"
        
        return self.generate_qr_code(url)
    
    def cleanup_old_qr_codes(self, max_age_hours: int = 24) -> int:
        """
        Очистка старых QR-кодов
        
        Args:
            max_age_hours: Максимальный возраст файлов в часах
            
        Returns:
            Количество удаленных файлов
        """
        import time
        
        if not os.path.exists(self.qr_codes_dir):
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for filename in os.listdir(self.qr_codes_dir):
            if filename.endswith('.png'):
                file_path = os.path.join(self.qr_codes_dir, filename)
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except OSError:
                        pass  # Игнорируем ошибки удаления
        
        return deleted_count


# Глобальный экземпляр генератора QR-кодов
qr_generator = QRGenerator()


def generate_session_qr_code(session_code: str, bot_username: Optional[str] = None) -> bytes:
    """Быстрый доступ к генерации QR-кода для сессии"""
    return qr_generator.generate_session_qr(session_code, bot_username)


def generate_qr_code(data: str) -> bytes:
    """Быстрый доступ к генерации QR-кода"""
    return qr_generator.generate_qr_code(data)