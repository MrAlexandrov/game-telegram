# План реализации телеграм-бота для игр

## Обзор

Этот документ содержит детальный план реализации системы телеграм-бота для проведения различных игр с модульной архитектурой.

## Структура проекта

```
game-telegram/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Точка входа
│   ├── settings.py             # Конфигурация
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bot.py             # Основной менеджер ботов
│   │   ├── router.py          # Маршрутизация команд
│   │   └── middleware.py      # Middleware для авторизации
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py           # Модель пользователя
│   │   ├── game.py           # Модели игр
│   │   ├── session.py        # Модель сессии
│   │   └── enums.py          # Перечисления
│   ├── games/
│   │   ├── __init__.py
│   │   ├── base.py           # Базовый класс игры
│   │   ├── engine.py         # Игровой движок
│   │   ├── quiz/
│   │   │   ├── __init__.py
│   │   │   └── game.py       # Реализация викторины
│   │   └── hundred_to_one/
│   │       ├── __init__.py
│   │       └── game.py       # Реализация "100 к 1"
│   ├── sessions/
│   │   ├── __init__.py
│   │   └── manager.py        # Менеджер сессий
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── session_storage.py # Хранение сессий
│   │   ├── pack_storage.py    # Хранение паков
│   │   └── user_storage.py    # Хранение пользователей
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── admin.py          # Админские команды
│   │   ├── player.py         # Игровые команды
│   │   └── common.py         # Общие команды
│   └── utils/
│       ├── __init__.py
│       ├── qr_generator.py   # Генерация QR-кодов
│       ├── code_generator.py # Генерация кодов сессий
│       └── validators.py     # Валидаторы
├── game_packs/
│   ├── quiz/
│   │   └── example_quiz.json
│   └── hundred_to_one/
│       └── example_hundred.json
├── temp/
│   ├── qr_codes/
│   └── exports/
├── tests/
│   ├── unit/
│   └── integration/
├── .env.example
├── requirements.txt
├── README.md
└── ARCHITECTURE.md
```

## Фаза 1: Основа системы

### 1.1 Настройка конфигурации

**Файл: `src/settings.py`**
```python
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Bot Configuration
    admin_bot_token: str
    player_bot_token: str
    root_id: int
    
    # Storage Configuration
    game_packs_dir: str = "./game_packs"
    temp_dir: str = "./temp"
    qr_codes_dir: str = "./temp/qr_codes"
    
    # Game Settings
    session_code_length: int = 6
    session_timeout_minutes: int = 60
    max_players_per_session: int = 50
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/bot.log"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 1.2 Базовые модели данных

**Файл: `src/models/enums.py`**
```python
from enum import Enum

class SessionStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class GameType(str, Enum):
    QUIZ = "quiz"
    HUNDRED_TO_ONE = "hundred_to_one"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    TRUE_FALSE = "true_false"
```

**Файл: `src/models/user.py`**
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class User(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool = False
    created_at: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### 1.3 Core Bot Manager

**Файл: `src/core/bot.py`**
```python
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from src.settings import settings
from src.handlers.admin import AdminHandlers
from src.handlers.player import PlayerHandlers
from src.handlers.common import CommonHandlers

class BotManager:
    def __init__(self):
        self.admin_app = None
        self.player_app = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Инициализация ботов"""
        # Админский бот
        self.admin_app = Application.builder().token(settings.admin_bot_token).build()
        admin_handlers = AdminHandlers()
        self._setup_admin_handlers(admin_handlers)
        
        # Игровой бот
        self.player_app = Application.builder().token(settings.player_bot_token).build()
        player_handlers = PlayerHandlers()
        self._setup_player_handlers(player_handlers)
        
    def _setup_admin_handlers(self, handlers):
        """Настройка обработчиков для админского бота"""
        self.admin_app.add_handler(CommandHandler("start", handlers.start))
        self.admin_app.add_handler(CommandHandler("create_pack", handlers.create_pack))
        self.admin_app.add_handler(CommandHandler("list_packs", handlers.list_packs))
        self.admin_app.add_handler(CommandHandler("create_session", handlers.create_session))
        self.admin_app.add_handler(CommandHandler("start_game", handlers.start_game))
        self.admin_app.add_handler(CommandHandler("end_game", handlers.end_game))
        
    def _setup_player_handlers(self, handlers):
        """Настройка обработчиков для игрового бота"""
        self.player_app.add_handler(CommandHandler("start", handlers.start))
        self.player_app.add_handler(CommandHandler("join", handlers.join_session))
        self.player_app.add_handler(MessageHandler(filters.TEXT, handlers.handle_answer))
        
    async def start(self):
        """Запуск ботов"""
        await self.admin_app.initialize()
        await self.player_app.initialize()
        
        await self.admin_app.start()
        await self.player_app.start()
        
        self.logger.info("Боты запущены")
        
    async def stop(self):
        """Остановка ботов"""
        if self.admin_app:
            await self.admin_app.stop()
        if self.player_app:
            await self.player_app.stop()
            
        self.logger.info("Боты остановлены")
```

## Фаза 2: Игровой движок

### 2.1 Базовый класс игры

**Файл: `src/games/base.py`**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.models.game import GameState, RoundData, AnswerResult, GameResults

class BaseGame(ABC):
    def __init__(self, session_id: str, pack_data: Dict[str, Any]):
        self.session_id = session_id
        self.pack_data = pack_data
        self.current_round = 0
        self.players_scores = {}
        self.game_state = GameState.WAITING
        
    @abstractmethod
    async def initialize(self) -> None:
        """Инициализация игры"""
        pass
        
    @abstractmethod
    async def start_round(self) -> RoundData:
        """Начало нового раунда"""
        pass
        
    @abstractmethod
    async def process_answer(self, user_id: int, answer: str) -> AnswerResult:
        """Обработка ответа игрока"""
        pass
        
    @abstractmethod
    async def next_round(self) -> Optional[RoundData]:
        """Переход к следующему раунду"""
        pass
        
    @abstractmethod
    async def finish_game(self) -> GameResults:
        """Завершение игры и подсчет результатов"""
        pass
        
    @abstractmethod
    async def get_current_state(self) -> Dict[str, Any]:
        """Получение текущего состояния игры"""
        pass
        
    def add_player(self, user_id: int) -> None:
        """Добавление игрока"""
        if user_id not in self.players_scores:
            self.players_scores[user_id] = 0
            
    def remove_player(self, user_id: int) -> None:
        """Удаление игрока"""
        self.players_scores.pop(user_id, None)
        
    def get_players(self) -> List[int]:
        """Получение списка игроков"""
        return list(self.players_scores.keys())
```

### 2.2 Реализация викторины

**Файл: `src/games/quiz/game.py`**
```python
from typing import Dict, Any, Optional, List
from src.games.base import BaseGame
from src.models.game import GameState, RoundData, AnswerResult, GameResults
from src.models.enums import QuestionType
import asyncio

class QuizGame(BaseGame):
    def __init__(self, session_id: str, pack_data: Dict[str, Any]):
        super().__init__(session_id, pack_data)
        self.questions = pack_data.get("questions", [])
        self.settings = pack_data.get("settings", {})
        self.current_question = None
        self.round_answers = {}
        self.round_start_time = None
        
    async def initialize(self) -> None:
        """Инициализация викторины"""
        self.game_state = GameState.READY
        
    async def start_round(self) -> RoundData:
        """Начало нового раунда (вопроса)"""
        if self.current_round >= len(self.questions):
            return None
            
        self.current_question = self.questions[self.current_round]
        self.round_answers = {}
        self.round_start_time = asyncio.get_event_loop().time()
        self.game_state = GameState.ACTIVE
        
        return RoundData(
            round_number=self.current_round + 1,
            question=self.current_question["question"],
            options=self.current_question.get("options", []),
            time_limit=self.current_question.get("time_limit", 
                      self.settings.get("time_per_question", 30))
        )
        
    async def process_answer(self, user_id: int, answer: str) -> AnswerResult:
        """Обработка ответа игрока"""
        if self.game_state != GameState.ACTIVE:
            return AnswerResult(success=False, message="Игра не активна")
            
        if user_id in self.round_answers:
            return AnswerResult(success=False, message="Вы уже ответили на этот вопрос")
            
        # Проверка времени
        current_time = asyncio.get_event_loop().time()
        time_limit = self.current_question.get("time_limit", 
                    self.settings.get("time_per_question", 30))
        
        if current_time - self.round_start_time > time_limit:
            return AnswerResult(success=False, message="Время на ответ истекло")
            
        # Проверка правильности ответа
        is_correct = self._check_answer(answer)
        points = 0
        
        if is_correct:
            points = self.current_question.get("points", 
                    self.settings.get("points_per_correct", 10))
            self.players_scores[user_id] += points
        else:
            penalty = self.settings.get("penalty_for_wrong", 0)
            self.players_scores[user_id] += penalty
            
        self.round_answers[user_id] = {
            "answer": answer,
            "is_correct": is_correct,
            "points": points,
            "timestamp": current_time
        }
        
        return AnswerResult(
            success=True,
            is_correct=is_correct,
            points=points,
            message="Ответ принят" if is_correct else "Неправильный ответ"
        )
        
    def _check_answer(self, answer: str) -> bool:
        """Проверка правильности ответа"""
        question_type = self.current_question.get("type", QuestionType.MULTIPLE_CHOICE)
        
        if question_type == QuestionType.MULTIPLE_CHOICE:
            try:
                answer_index = int(answer) - 1  # Пользователь вводит 1-4, а индексы 0-3
                correct_index = self.current_question["correct_answer"]
                return answer_index == correct_index
            except (ValueError, KeyError):
                return False
                
        elif question_type == QuestionType.TEXT_INPUT:
            correct_answers = self.current_question.get("correct_answers", [])
            case_sensitive = self.current_question.get("case_sensitive", False)
            
            if not case_sensitive:
                answer = answer.lower()
                correct_answers = [ans.lower() for ans in correct_answers]
                
            return answer in correct_answers
            
        elif question_type == QuestionType.TRUE_FALSE:
            correct_answer = self.current_question["correct_answer"]
            return answer.lower() in ["да", "yes", "true"] if correct_answer else answer.lower() in ["нет", "no", "false"]
            
        return False
        
    async def next_round(self) -> Optional[RoundData]:
        """Переход к следующему раунду"""
        self.current_round += 1
        
        if self.current_round >= len(self.questions):
            self.game_state = GameState.FINISHED
            return None
            
        return await self.start_round()
        
    async def finish_game(self) -> GameResults:
        """Завершение игры и подсчет результатов"""
        self.game_state = GameState.FINISHED
        
        # Сортировка игроков по очкам
        sorted_players = sorted(
            self.players_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return GameResults(
            session_id=self.session_id,
            total_rounds=len(self.questions),
            players_results=sorted_players,
            winner=sorted_players[0][0] if sorted_players else None
        )
        
    async def get_current_state(self) -> Dict[str, Any]:
        """Получение текущего состояния игры"""
        return {
            "session_id": self.session_id,
            "game_state": self.game_state,
            "current_round": self.current_round,
            "total_rounds": len(self.questions),
            "players_count": len(self.players_scores),
            "scores": self.players_scores
        }
```

## Фаза 3: Менеджер сессий

### 3.1 Session Manager

**Файл: `src/sessions/manager.py`**
```python
import asyncio
import secrets
import string
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from src.models.session import Session
from src.models.enums import SessionStatus, GameType
from src.storage.session_storage import SessionStorage
from src.storage.pack_storage import PackStorage
from src.games.engine import GameEngine
from src.utils.qr_generator import QRGenerator
from src.settings import settings

class SessionManager:
    def __init__(self):
        self.session_storage = SessionStorage()
        self.pack_storage = PackStorage()
        self.game_engine = GameEngine()
        self.qr_generator = QRGenerator()
        
    async def create_session(self, pack_id: str, admin_id: int) -> Optional[Session]:
        """Создание новой игровой сессии"""
        # Загрузка игрового пака
        pack = await self.pack_storage.load_pack(pack_id)
        if not pack:
            return None
            
        # Генерация уникального кода сессии
        session_code = self._generate_session_code()
        
        # Создание сессии
        session = Session(
            id=f"session_{session_code}",
            code=session_code,
            admin_id=admin_id,
            game_pack_id=pack_id,
            game_type=pack.game_type,
            status=SessionStatus.WAITING,
            players=[],
            current_round=0,
            created_at=datetime.now()
        )
        
        # Сохранение сессии
        session_id = await self.session_storage.create_session(session)
        if session_id:
            session.id = session_id
            return session
            
        return None
        
    async def join_session(self, session_code: str, user_id: int) -> bool:
        """Подключение игрока к сессии"""
        session = await self.session_storage.get_session_by_code(session_code)
        if not session:
            return False
            
        if session.status != SessionStatus.WAITING:
            return False
            
        if user_id in session.players:
            return True  # Уже подключен
            
        if len(session.players) >= settings.max_players_per_session:
            return False
            
        session.players.append(user_id)
        await self.session_storage.update_session(session.id, {"players": session.players})
        
        return True
        
    async def start_session(self, session_id: str) -> bool:
        """Запуск игровой сессии"""
        session = await self.session_storage.get_session(session_id)
        if not session or session.status != SessionStatus.WAITING:
            return False
            
        # Загрузка игрового пака
        pack = await self.pack_storage.load_pack(session.game_pack_id)
        if not pack:
            return False
            
        # Инициализация игры
        game_initialized = await self.game_engine.initialize_game(
            session_id, session.game_type, pack.data
        )
        
        if not game_initialized:
            return False
            
        # Обновление статуса сессии
        session.status = SessionStatus.ACTIVE
        session.started_at = datetime.now()
        
        await self.session_storage.update_session(session_id, {
            "status": session.status,
            "started_at": session.started_at
        })
        
        return True
        
    async def end_session(self, session_id: str) -> Optional[Dict]:
        """Завершение игровой сессии"""
        session = await self.session_storage.get_session(session_id)
        if not session:
            return None
            
        # Получение результатов игры
        results = await self.game_engine.finish_game(session_id)
        
        # Обновление сессии
        session.status = SessionStatus.FINISHED
        session.ended_at = datetime.now()
        session.results = results.dict() if results else None
        
        await self.session_storage.update_session(session_id, {
            "status": session.status,
            "ended_at": session.ended_at,
            "results": session.results
        })
        
        # Очистка игрового состояния
        await self.game_engine.cleanup_game(session_id)
        
        return session.results
        
    async def get_session_info(self, session_id: str) -> Optional[Session]:
        """Получение информации о сессии"""
        return await self.session_storage.get_session(session_id)
        
    async def generate_qr_code(self, session_code: str) -> bytes:
        """Генерация QR-кода для сессии"""
        join_url = f"https://t.me/{settings.player_bot_username}?start=join_{session_code}"
        return await self.qr_generator.generate(join_url)
        
    def _generate_session_code(self) -> str:
        """Генерация уникального кода сессии"""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(settings.session_code_length))
        
    async def cleanup_expired_sessions(self):
        """Очистка истекших сессий"""
        timeout = timedelta(minutes=settings.session_timeout_minutes)
        cutoff_time = datetime.now() - timeout
        
        expired_sessions = await self.session_storage.get_expired_sessions(cutoff_time)
        
        for session in expired_sessions:
            await self.end_session(session.id)
            await self.session_storage.delete_session(session.id)
```

## Фаза 4: Обработчики команд

### 4.1 Админские команды

**Файл: `src/handlers/admin.py`**
```python
from telegram import Update
from telegram.ext import ContextTypes
from src.sessions.manager import SessionManager
from src.storage.pack_storage import PackStorage
from src.settings import settings
import logging

class AdminHandlers:
    def __init__(self):
        self.session_manager = SessionManager()
        self.pack_storage = PackStorage()
        self.logger = logging.getLogger(__name__)
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start для админа"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("У вас нет прав администратора.")
            return
            
        welcome_text = """
🎮 Добро пожаловать в админ-панель игрового бота!

Доступные команды:
/create_pack - Создать новый игровой пак
/list_packs - Список игровых паков
/create_session <pack_id> - Создать игровую сессию
/start_game <session_id> - Запустить игру
/end_game <session_id> - Завершить игру
/session_info <session_id> - Информация о сессии
        """
        
        await update.message.reply_text(welcome_text)
        
    async def create_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создание новой игровой сессии"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("У вас нет прав администратора.")
            return
            
        if not context.args:
            await update.message.reply_text("Укажите ID игрового пака: /create_session <pack_id>")
            return
            
        pack_id = context.args[0]
        
        try:
            session = await self.session_manager.create_session(pack_id, user_id)
            
            if session:
                # Генерация QR-кода
                qr_code = await self.session_manager.generate_qr_code(session.code)
                
                message_text = f"""
✅ Сессия создана!

🆔 ID сессии: {session.id}
🔢 Код для подключения: {session.code}
👥 Игроков подключено: 0/{settings.max_players_per_session}

Игроки могут подключиться:
1. По коду: отправить /join {session.code} боту @{settings.player_bot_username}
2. По QR-коду (см. ниже)

Для запуска игры используйте: /start_game {session.id}
                """
                
                await update.message.reply_text(message_text)
                
                # Отправка QR-кода
                await update.message.reply_photo(
                    photo=qr_code,
                    caption=f"QR-код для подключения к игре {session.code}"
                )
                
            else:
                await update.message.reply_text("❌ Ошибка создания сессии. Проверьте ID пака.")
                
        except Exception as e:
            self.logger.error(f"Ошибка создания сессии: {e}")
            await update.message.reply_text("❌ Произошла ошибка при создании сессии.")
            
    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск игровой сессии"""
        user_id = update.effective_user.id
        
        if user_id != settings.root_id:
            await update.message.reply_text("У вас нет прав администратора.")
            return
            
        if not context.args:
            await update.message.reply_text("Укажите ID сессии: /start_game <session_id>")
            return
            
        session_id = context.args[0]
        
        try:
            success = await self.session_manager.start_session(session_id)
            
            if success:
                session = await self.session_manager.get_session_info(session_id)
                await update.message.reply_text(
                    f"🎮 Игра запущена!\n"
                    f"👥 Участников: {len(session.players)}\n"
                    f"🎯 Тип игры: {session.game_type}"
                )
            else:
                await update.message.reply_text("❌ Не удалось запустить игру. Проверьте ID сессии.")
                
        except Exception as e:
            self.logger.error(f"Ошибка запуска игры: {e}")
            await update.message.reply_text("❌ Произошла ошибка при запуске игры.")
```

### 4.2 Игровые команды

**Файл: `src/handlers/player.py`**
```python
from telegram import Update
from telegram.ext import ContextTypes
from src.sessions.manager import SessionManager
from src.games.engine import GameEngine
from src.storage.user_storage import UserStorage
import logging

class PlayerHandlers:
    def __init__(self):
        self.session_manager = SessionManager()
        self.game_engine = GameEngine()
        self.user_storage = UserStorage()
        self.logger = logging.getLogger(__name__)
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start для игрока"""
        user = update.effective_user
        
        # Регистрация пользователя
        await self.user_storage.register_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Проверка на автоматическое подключение к игре
        if context.args and context.args[0].startswith("join_"):
            session_code = context.args[0][5:]  # Убираем "join_"
            await self._join_session_by_code(update, session_code)
            return
            
        welcome_text = """
🎮 Добро пожаловать в игрового бота!

Для подключения к игре:
/join <код_игры> - Подключиться к игре по коду

Удачной игры! 🍀
        """
        
        await update.message.reply_text(welcome_text)
        
    async def join_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подключение к игровой сессии"""
        if not context.args:
            await update.message.reply_text("Укажите код игры: /join <код>")
            return
            
        session_code = context.args[0].upper()
        await self._join_session_by_code(update, session_code)
        
    async def _join_session_by_code(self, update: Update, session_code: str):
        """Подключение к сессии по коду"""
        user_id = update.effective_user.id
        
        try:
            success = await self.session_manager.join_session(session_code, user_id)
            
            if success:
                await update.message.reply_text(
                    f"✅ Вы успешно подключились к игре {session_code}!\n"
                    f"Ожидайте начала игры..."
                )
            else:
                await update.message.reply_text(
                    f"❌ Не удалось подключиться к игре {session_code}.\n"
                    f"Возможные причины:\n"
                    f"• Неверный код игры\n"
                    f"• Игра уже началась\n"
                    f"• Достигнуто максимальное количество игроков"
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка подключения к сессии: {e}")
            await update.message.reply_text("❌ Произошла ошибка при подключении к игре.")
            
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ответов игрока"""
        user_id = update.effective_user