"""
Генератор кодов для сессий
"""
import secrets
import string
from typing import Set
from src.settings import settings


class CodeGenerator:
    """Генератор уникальных кодов для сессий"""
    
    def __init__(self):
        self._used_codes: Set[str] = set()
        # Используем только заглавные буквы и цифры для удобства ввода
        self._alphabet = string.ascii_uppercase + string.digits
        # Исключаем похожие символы для избежания путаницы
        self._excluded_chars = {'0', 'O', '1', 'I', 'L'}
        self._alphabet = ''.join(c for c in self._alphabet if c not in self._excluded_chars)
    
    def generate_session_code(self, length: int = None) -> str:
        """
        Генерация уникального кода сессии
        
        Args:
            length: Длина кода (по умолчанию из настроек)
            
        Returns:
            Уникальный код сессии
        """
        if length is None:
            length = settings.session_code_length
        
        max_attempts = 100
        attempts = 0
        
        while attempts < max_attempts:
            code = ''.join(secrets.choice(self._alphabet) for _ in range(length))
            
            if code not in self._used_codes:
                self._used_codes.add(code)
                return code
            
            attempts += 1
        
        # Если не удалось сгенерировать уникальный код, очищаем кэш и пробуем еще раз
        self._used_codes.clear()
        code = ''.join(secrets.choice(self._alphabet) for _ in range(length))
        self._used_codes.add(code)
        return code
    
    def is_valid_code(self, code: str) -> bool:
        """
        Проверка валидности кода
        
        Args:
            code: Код для проверки
            
        Returns:
            True если код валиден
        """
        if not code or len(code) != settings.session_code_length:
            return False
        
        return all(c in self._alphabet for c in code.upper())
    
    def normalize_code(self, code: str) -> str:
        """
        Нормализация кода (приведение к верхнему регистру)
        
        Args:
            code: Код для нормализации
            
        Returns:
            Нормализованный код
        """
        return code.upper().strip()
    
    def release_code(self, code: str) -> None:
        """
        Освобождение кода (удаление из списка используемых)
        
        Args:
            code: Код для освобождения
        """
        self._used_codes.discard(code)
    
    def get_used_codes_count(self) -> int:
        """
        Получение количества используемых кодов
        
        Returns:
            Количество используемых кодов
        """
        return len(self._used_codes)
    
    def clear_used_codes(self) -> None:
        """Очистка списка используемых кодов"""
        self._used_codes.clear()


# Глобальный экземпляр генератора кодов
code_generator = CodeGenerator()


def generate_session_code() -> str:
    """Быстрый доступ к генерации кода сессии"""
    return code_generator.generate_session_code()


def validate_session_code(code: str) -> bool:
    """Быстрый доступ к валидации кода сессии"""
    return code_generator.is_valid_code(code)


def normalize_session_code(code: str) -> str:
    """Быстрый доступ к нормализации кода сессии"""
    return code_generator.normalize_code(code)