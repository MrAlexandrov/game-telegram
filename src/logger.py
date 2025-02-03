import logging
from settings import BOT_TOKEN  # Предполагается, что BOT_TOKEN определяется в settings.py

class SensitiveDataFilter(logging.Filter):
    """
    Фильтр, который заменяет в лог-сообщениях все вхождения токена бота на '***'.
    """
    def __init__(self, token):
        super().__init__()
        self.token = token

    def filter(self, record):
        message = record.getMessage()
        if self.token in message:
            # Заменяем токен на '***'
            record.msg = message.replace(self.token, "***")
        return True

def get_logger(name: str = None) -> logging.Logger:
    """
    Возвращает настроенный логгер с именем name.
    Если name не указан, используется корневой логгер.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Если у логгера ещё нет обработчиков, добавляем консольный обработчик
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
        console_handler.setFormatter(formatter)
        console_handler.addFilter(SensitiveDataFilter(BOT_TOKEN))
        logger.addHandler(console_handler)
    
    return logger
