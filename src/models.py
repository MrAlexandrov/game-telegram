# models.py
import uuid
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

# Таблица игроков
class Player(Base):
    __tablename__ = 'players'

    id = Column(String, primary_key=True, default=generate_uuid)
    telegram_id = Column(Integer, nullable=False)
    telegram_name = Column(String, nullable=True)
    state = Column(String, nullable=True)
    nickname = Column(String, nullable=True)
    game_session_id = Column(String, ForeignKey('game_sessions.id'), nullable=True)

    # Отношения
    game = relationship("GameSession", back_populates="players")
    answer = relationship("Answer", back_populates="player", cascade="all, delete-orphan")
    result = relationship("Result", back_populates="player", uselist=False)

    def __repr__(self):
        return f"<Player(id='{self.id}', nickname='{self.nickname}', game_session_id='{self.game_session_id}')>"

# Таблица внутренних пользователей
class InternalUser(Base):
    __tablename__ = 'internal_users'

    id = Column(String, primary_key=True, default=generate_uuid)
    telegram_id = Column(Integer, nullable=False)
    nickname = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    state = Column(String, nullable=False, default="start")

    # Отношения
    games_created = relationship("Game", back_populates="created_by_user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InternalUser(id='{self.id}', telegram_id='{self.telegram_id}', nickname='{self.nickname}')>"

# Таблица игр
class Game(Base):
    __tablename__ = 'games'

    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    created_by = Column(String, ForeignKey('internal_users.id'), nullable=True)

    # Отношения
    created_by_user = relationship("InternalUser", back_populates="games_created")
    questions = relationship("Question", back_populates="game", cascade="all, delete-orphan")
    sessions = relationship("GameSession", back_populates="game", cascade="all, delete-orphan")
    # Удаляем или не используем отношение к результатам напрямую:
    # results = relationship("Result", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(id='{self.id}', title='{self.title}')>"

# Таблица вопросов
class Question(Base):
    __tablename__ = 'questions'

    id = Column(String, primary_key=True, default=generate_uuid)
    game_id = Column(String, ForeignKey('games.id'), nullable=True)
    question_text = Column(Text, nullable=True)
    path_to_media = Column(String, default=None)

    # Отношения
    game = relationship("Game", back_populates="questions")
    # Связь с вариантами ответов
    variant = relationship("Variant", back_populates="question", cascade="all, delete-orphan")
    # answer = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Question(id='{self.id}', text='{self.question_text}')>"

# Таблица вариантов ответа
class Variant(Base):
    __tablename__ = 'variant'
    id = Column(String, primary_key=True, default=generate_uuid)
    question_id = Column(String, ForeignKey('questions.id'), nullable=False)
    answer_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    
    question = relationship("Question", back_populates="variant")
    answer = relationship("Answer", back_populates="variant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Variant(id='{self.id}', answer_text='{self.answer_text}')>"

# Таблица ответов пользователей
class Answer(Base):
    __tablename__ = 'answer'

    id = Column(String, primary_key=True, default=generate_uuid)
    variant_id = Column(String, ForeignKey('variant.id'), nullable=False)
    user_id = Column(String, ForeignKey('players.id'), nullable=False)
    answer_text = Column(Text, nullable=False)
    answered_at = Column(Integer, default=0)  # Можно хранить timestamp в секундах

    # Отношения
    variant = relationship("Variant", back_populates="answer")
    player = relationship("Player", back_populates="answer")

    def __repr__(self):
        return f"<Answer(id='{self.id}', user_id='{self.user_id}', answer_text='{self.answer_text}', answered_at='{self.answered_at}')>"

# Таблица медиафайлов
class Media(Base):
    __tablename__ = 'media'

    id = Column(String, primary_key=True, default=generate_uuid)
    question_id = Column(String, ForeignKey('questions.id'), nullable=False)
    media_type = Column(String, nullable=False)
    url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    display_type = Column(String, nullable=False)  # Options: individual, shared, both

    # Отношения
    question = relationship("Question", back_populates="media")

    def __repr__(self):
        return f"<Media(id='{self.id}', media_type='{self.media_type}')>"

# Таблица результатов
class Result(Base):
    __tablename__ = 'results'

    id = Column(String, primary_key=True, default=generate_uuid)
    game_session_id = Column(String, ForeignKey('game_sessions.id'), nullable=False)
    user_id = Column(String, ForeignKey('players.id'), nullable=False)
    score = Column(Integer, nullable=False)

    # Отношения
    game_session = relationship("GameSession", back_populates="results")
    player = relationship("Player", back_populates="result")

    def __repr__(self):
        return f"<Result(id='{self.id}', game_session_id='{self.game_session_id}', user_id='{self.user_id}', score={self.score})>"

# Таблица сессий игры
class GameSession(Base):
    __tablename__ = 'game_sessions'

    id = Column(String, primary_key=True, default=generate_uuid)
    game_id = Column(String, ForeignKey('games.id'), nullable=True)
    game_code = Column(String, nullable=False)
    status = Column(String, nullable=False)
    current_question_id = Column(String, ForeignKey('questions.id'), nullable=True)

    # Отношения
    game = relationship("Game", back_populates="sessions")
    players = relationship("Player", back_populates="game", cascade="all, delete-orphan")
    current_question = relationship("Question")
    results = relationship("Result", back_populates="game_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GameSession(id='{self.id}', game_code='{self.game_code}')>"
