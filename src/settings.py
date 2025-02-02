from os import getenv
from dotenv import load_dotenv
from constants import *

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота из переменной окружения
BOT_TOKEN = getenv('BOT_TOKEN')

# BOT_TOKEN = getenv('RELEASE_BOT_TOKEN')
ROOT_ID = int(getenv('ROOT_ID'))

if BOT_TOKEN is None:
    raise ValueError("Токен не найден! Убедитесь, что файл .env правильно настроен.")

try:
    ROOT_ID = int(ROOT_ID)
except (TypeError, ValueError):
    raise ValueError("ROOT_ID не найден или указан неверно")

ADMIN_IDS = {
    ROOT_ID,
}

BEGINING = [
    {
        STATE:                  USERNAME,
        LABEL:                  "Имя пользователя",
        MESSAGE:                "Должно собраться автоматически",
    },
    {
        STATE:                  NICKNAME,
        LABEL:                  "Никнейм",
        MESSAGE:                "Введи имя пользователя",
    }
]

QUIZ = [
    {
        MESSAGE:                """Тебе 10 лет?""",
        OPTIONS:                YES_NO,
    },
    {
        MESSAGE:                """Тебе 5 лет?""",
        OPTIONS:                YES_NO,
    },
]

ADMIN_STATES = {
    START_GAME: {
        BUTTONS: [
            ["Начать игру"],
        ],
    },
    BLOCK_BUTTONS: {
        BUTTONS: [
            ["Заблокировать кнопки"],
        ],
    },
    SHOW_ANSWERS: {
        BUTTONS: [
            ["Показать ответы"],
        ],
    },
    CHANGE_STATE: {
        BUTTONS: [
            ["Предыдущий вопрос", "Следующий вопрос"],
        ],
    },
    BREAK: {
        BUTTONS: [
            ["Закончить перекур"],
        ],
    },
    RESULTS: {
        BUTTONS: [
            ["Вернуться"],
        ],
    },
}
