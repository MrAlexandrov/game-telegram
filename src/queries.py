# queries.py
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from models import (
    Base,
    # AdminSession,
    Player,
    GameSession,
    Game,
    Question,
    Variants,
    Answer,
    Media,
    Result,
    InternalUser,
)
from uuid import uuid4
from logger import get_logger

logger = get_logger(__name__)

class DatabaseConnector:
    def __init__(self, session: Session):
        self.session = session

    # def get_admin_session(self, admin_id: int) -> AdminSession:
    #     """
    #     Получает сессию администратора по его Telegram ID.
    #     """
    #     return self.session.query(AdminSession).filter(AdminSession.admin_id == admin_id).first()

    # def create_admin_session(self, admin_id: int) -> AdminSession:
    #     """
    #     Создает новую сессию администратора, если её ещё нет.
    #     """
    #     admin_session = self.get_admin_session(admin_id)
    #     if not admin_session:
    #         admin_session = AdminSession(admin_id=admin_id, state="start")
    #         self.session.add(admin_session)
    #         self.session.commit()
    #     return admin_session

    # def update_admin_session_state(self, admin_id: int, new_state: str, **kwargs) -> AdminSession:
    #     """
    #     Обновляет состояние сессии администратора.
    #     Дополнительно можно передать ключевые параметры (например, current_game_id, current_question_text, и т.д.).
    #     """
    #     admin_session = self.get_admin_session(admin_id)
    #     if not admin_session:
    #         admin_session = self.create_admin_session(admin_id)
    #     admin_session.state = new_state
    #     for key, value in kwargs.items():
    #         if hasattr(admin_session, key):
    #             setattr(admin_session, key, value)
    #     self.session.commit()
    #     return admin_session

    # ---------------------------
    # Работа с игроками (Player)
    # ---------------------------
    def create_player(self, telegram_id: int, telegram_name: str, nickname: str, game_id: str = None) -> Player:
        """
        Создает нового игрока.
        """
        new_player = Player(
            telegram_id=telegram_id,
            telegram_name=telegram_name,
            nickname=nickname,
            game_id=game_id
        )
        self.session.add(new_player)
        self.session.commit()
        return new_player

    def get_player_by_telegram_id(self, telegram_id: int) -> Player:
        """
        Получает игрока по его Telegram ID.
        """
        return self.session.query(Player).filter(Player.telegram_id == telegram_id).first()

    def update_player_nickname(self, player_id: str, new_nickname: str) -> Player:
        """
        Обновляет nickname игрока.
        """
        player = self.session.query(Player).filter(Player.id == player_id).first()
        if player:
            player.nickname = new_nickname
            self.session.commit()
        return player

    # ---------------------------
    # Работа с результатами (Result)
    # ---------------------------
    def create_or_update_result(self, player_id: str, game_id: str, score: int) -> Result:
        """
        Если результат для игрока в игре существует, обновляет его; иначе – создает новую запись.
        """
        result = self.session.query(Result).filter(
            Result.user_id == player_id,
            Result.game_id == game_id
        ).first()
        if result:
            result.score = score
        else:
            result = Result(
                id=str(uuid4()),
                user_id=player_id,
                game_id=game_id,
                score=score
            )
            self.session.add(result)
        self.session.commit()
        return result

    def increase_result_score(self, player_id: str, game_id: str, increment: int = 1) -> Result:
        """
        Увеличивает счет результата для игрока в игре на заданное значение.
        """
        result = self.session.query(Result).filter(
            Result.user_id == player_id,
            Result.game_id == game_id
        ).first()
        if result:
            result.score += increment
        else:
            # Если записи нет, создаем её с начальным счетом равным increment
            result = Result(
                id=str(uuid4()),
                user_id=player_id,
                game_id=game_id,
                score=increment
            )
            self.session.add(result)
        self.session.commit()
        return result

    def get_all_nicknames_and_scores(self):
        """
        Возвращает список кортежей (nickname, score) для всех игроков.
        """
        results = self.session.query(Player.nickname, Result.score).join(Result, Player.id == Result.user_id).all()
        return results

    # ---------------------------
    # Работа с вопросами (Question)
    # ---------------------------
    def create_question(self, game_id: str, question_text: str, has_media: bool = False) -> Question:
        """
        Создает новый вопрос для игры.
        """
        new_question = Question(
            game_id=game_id,
            question_text=question_text,
            has_media=has_media
        )
        self.session.add(new_question)
        self.session.commit()
        return new_question

    def get_question(self, question_id: str) -> Question:
        """
        Получает вопрос по его ID.
        """
        return self.session.query(Question).filter(Question.id == question_id).first()

    def get_questions_by_game(self, game_id: str):
        """
        Возвращает все вопросы для заданной игры.
        """
        return self.session.query(Question).filter(Question.game_id == game_id).all()

    # ---------------------------
    # Работа с вариантами (Variant)
    # ---------------------------
    def create_variant(self, question_id: str, answer_text: str, is_correct: bool = False) -> Variants:
        """
        Создает новый ответ.
        """
        new_variant = Variants(
            question_id=question_id,
            answer_text=answer_text,
            is_correct=is_correct,
        )
        self.session.add(new_variant)
        self.session.commit()
        return new_variant

    def get_variant(self, variant_id: str) -> Variants:
        return self.session.query(Variants).filter(Variants.id == variant_id).first()

    def update_variant_correctness(self, variant_id: str, is_correct: bool) -> Variants:
        variant = self.get_variant(variant_id)
        if variant is None:
            raise ValueError(f"Variant with id {variant_id} not found")
        variant.is_correct = is_correct
        self.session.commit()
        return variant

    def get_variants_by_question(self, question_id: str):
        """
        Возвращает все ответы для заданного вопроса.
        """
        return self.session.query(Variants).filter(Variants.question_id == question_id).all()


    # ---------------------------
    # Работа с ответами (Answer)
    # ---------------------------
    def create_answer(self, question_id: str, player_id: str, answer_text: str, is_correct: bool = False, answered_at: int = 0) -> Answer:
        """
        Создает новый ответ.
        """
        new_answer = Answer(
            question_id=question_id,
            user_id=player_id,
            answer_text=answer_text,
            is_correct=is_correct,
            answered_at=answered_at
        )
        self.session.add(new_answer)
        self.session.commit()
        return new_answer

    def get_answers_by_question(self, question_id: str):
        """
        Возвращает все ответы для заданного вопроса.
        """
        return self.session.query(Answer).filter(Answer.question_id == question_id).all()

    # ---------------------------
    # Работа с медиа (Media)
    # ---------------------------
    def create_media(self, question_id: str, media_type: str, url: str, description: str, display_type: str) -> Media:
        """
        Создает запись для медиафайла, связанного с вопросом.
        """
        new_media = Media(
            question_id=question_id,
            media_type=media_type,
            url=url,
            description=description,
            display_type=display_type
        )
        self.session.add(new_media)
        self.session.commit()
        return new_media

    def get_media_by_question(self, question_id: str):
        """
        Возвращает список медиафайлов для заданного вопроса.
        """
        return self.session.query(Media).filter(Media.question_id == question_id).all()

    # ---------------------------
    # Работа с игровыми сессиями (GameSession)
    # ---------------------------
    def create_game_session(self, game_id: str, game_code: str, status: str, current_question_id: str = None) -> GameSession:
        """
        Создает новую игровую сессию.
        """
        new_session = GameSession(
            game_id=game_id,
            game_code=game_code,
            status=status,
            current_question_id=current_question_id
        )
        self.session.add(new_session)
        self.session.commit()
        return new_session

    def get_game_session(self, session_id: str) -> GameSession:
        """
        Получает игровую сессию по её ID.
        """
        return self.session.query(GameSession).filter(GameSession.id == session_id).first()

    # ---------------------------
    # Работа с играми (Game) и внутренними пользователями (InternalUser)
    # ---------------------------
    def create_game(self, game_type: str, title: str, created_by: str = None) -> Game:
        """
        Создает новую игру.
        """
        new_game = Game(
            type=game_type,
            title=title,
            created_by=created_by
        )
        self.session.add(new_game)
        self.session.commit()
        return new_game

    def get_game(self, game_id: str) -> Game:
        """
        Получает игру по её ID.
        """
        return self.session.query(Game).filter(Game.id == game_id).first()

    def create_internal_user(self, telegram_id: int, nickname: str, hashed_password: str) -> InternalUser:
        logger.info(f"called {__name__}")
        new_user = InternalUser(
            telegram_id=telegram_id,
            nickname=nickname,
            hashed_password=hashed_password
        )
        self.session.add(new_user)
        self.session.commit()
        return new_user

    def get_internal_user_by_telegram_id(self, telegram_id: int) -> InternalUser:
        return self.session.query(InternalUser).filter(InternalUser.telegram_id == telegram_id).first()

    def update_internal_user_state(self, telegram_id: int, new_state: str) -> InternalUser:
        """
        Обновляет состояние внутреннего пользователя (администратора).
        """
        user = self.get_internal_user_by_telegram_id(telegram_id)
        if user:
            user.state = new_state
            self.session.commit()
        return user

    def get_internal_user_state(self, telegram_id: int) -> str:
        user = self.get_internal_user_by_telegram_id(telegram_id)
        return user.state if user else None
    
    def commit(self):
        self.session.commit()

# При необходимости можно добавлять дополнительные функции для обновления или удаления записей.

def init_db_connector():
    engine = create_engine('sqlite:///your_database.db', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info("База данных успешно инициализирована.")
    db_connector = DatabaseConnector(session)
    return db_connector

db_connector = init_db_connector()
