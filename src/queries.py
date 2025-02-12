# queries.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.sql.functions import coalesce
from models import (
    Base,
    Player,
    GameSession,
    Game,
    Question,
    Variant,
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

    # ---------------------------
    # Работа с игроками (Player)
    # ---------------------------
    def create_player(self, telegram_id: int, telegram_name: str | None, state: str, nickname: str | None, game_session_id: str | None = None) -> Player:
        new_player = Player(
            telegram_id=telegram_id,
            telegram_name=telegram_name,
            state=state,
            nickname=nickname,
            game_session_id=game_session_id,
        )
        self.session.add(new_player)
        self.session.commit()
        return new_player

    def get_player_by_telegram_id(self, telegram_id: int) -> Player:
        return self.session.query(Player).filter(Player.telegram_id == telegram_id).first()

    def update_player_nickname(self, player_id: str, new_nickname: str) -> Player:
        player = self.session.query(Player).filter(Player.id == player_id).first()
        if player:
            player.nickname = new_nickname
            self.session.commit()
        return player

    def update_player_state_by_telegram_id(self, telegram_id: int, new_state: str) -> Player:
        player = self.get_player_by_telegram_id(telegram_id)
        if player:
            player.state = new_state
            self.session.commit()
        return player

    def update_player_game_session_by_telegram_id(self, telegram_id: int, new_game_session_id: str) -> Player:
        """
        Обновляет поле game_session_id у игрока (Player) по его telegram_id.
        
        :param telegram_id: Telegram ID игрока.
        :param new_game_session_id: Новый идентификатор игровой сессии, который необходимо установить.
        :return: Обновлённый объект Player.
        :raises ValueError: Если игрок с указанным Telegram ID не найден.
        """
        player = self.session.query(Player).filter(Player.telegram_id == telegram_id).first()
        if player is None:
            raise ValueError(f"Player with telegram_id {telegram_id} not found.")
        
        player.game_session_id = new_game_session_id
        self.session.commit()
        return player

    # ---------------------------
    # Работа с результатами (Result)
    # ---------------------------
    def create_or_update_result(self, player_id: str, game_session_id: str, score: int) -> Result:
        result = self.session.query(Result).filter(
            Result.user_id == player_id,
            Result.game_session_id == game_session_id,
        ).first()
        if result:
            result.score = score
        else:
            result = Result(
                id=str(uuid4()),
                user_id=player_id,
                game_session_id=game_session_id,
                score=score,
            )
            self.session.add(result)
        self.session.commit()
        return result

    def increase_result_score(self, player_id: str, game_session_id: str, increment: int = 1) -> Result:
        result = self.session.query(Result).filter(
            Result.user_id == player_id,
            Result.game_session_id == game_session_id,
        ).first()
        if result:
            result.score += increment
        else:
            result = Result(
                id=str(uuid4()),
                user_id=player_id,
                game_session_id=game_session_id,
                score=increment,
            )
            self.session.add(result)
        self.session.commit()
        return result

    def get_results_for_game_session(self, game_session_id: str):
        time_subq = (
            self.session.query(
                Answer.user_id.label("player_id"),
                coalesce(func.sum(Answer.answered_at), 0).label("total_time")
            )
            .group_by(Answer.user_id)
            .subquery()
        )

        results = (
            self.session.query(
                Player.nickname,
                Result.score,
                time_subq.c.total_time
            )
            .join(Result, Player.telegram_id == Result.user_id)
            .outerjoin(time_subq, Player.telegram_id == time_subq.c.player_id)
            .filter(Result.game_session_id == game_session_id)
            .all()
        )
        return results

    # ---------------------------
    # Работа с вопросами (Question)
    # ---------------------------
    def create_question(self, game_id: str, question_text: str, path_to_media: str | None = None) -> Question:
        new_question = Question(
            game_id=game_id,
            question_text=question_text,
            path_to_media=path_to_media,
        )
        self.session.add(new_question)
        self.session.commit()
        return new_question

    def get_question(self, question_id: str) -> Question:
        return self.session.query(Question).filter(Question.id == question_id).first()

    def get_questions_by_game(self, game_id: str) -> list[Question]:
        return self.session.query(Question).filter(Question.game_id == game_id).all()

    def update_question_text(self, question_id: str, new_text: str) -> Question:
        question = self.get_question(question_id)
        if question is None:
            raise ValueError(f"Question with id {question_id} not found.")
        question.question_text = new_text
        self.session.commit()
        return question

    # ---------------------------
    # Работа с вариантами (Variant)
    # ---------------------------
    def create_variant(self, question_id: str, answer_text: str, is_correct: bool = False) -> Variant:
        new_variant = Variant(
            question_id=question_id,
            answer_text=answer_text,
            is_correct=is_correct,
        )
        self.session.add(new_variant)
        self.session.commit()
        return new_variant

    def get_variant(self, variant_id: str) -> Variant:
        return self.session.query(Variant).filter(Variant.id == variant_id).first()

    def get_correct_variants_by_question_id(self, question_id: str) -> list[Variant]:
        return (
            self.session.query(Variant)
            .filter(Variant.question_id == question_id, Variant.is_correct == True)
            .all()
        )

    def update_variant_correctness(self, variant_id: str, is_correct: bool) -> Variant:
        variant = self.get_variant(variant_id)
        if variant is None:
            raise ValueError(f"Variant with id {variant_id} not found.")
        variant.is_correct = is_correct
        self.session.commit()
        return variant

    def update_variant_text(self, variant_id: str, new_text: str) -> Variant:
        variant = self.get_variant(variant_id)
        if variant is None:
            raise ValueError(f"Variant with id {variant_id} not found.")
        variant.answer_text = new_text
        self.session.commit()
        return variant

    def get_variants_by_question(self, question_id: str) -> list[Variant]:
        return self.session.query(Variant).filter(Variant.question_id == question_id).all()

    def delete_variant(self, variant_id: str) -> None:
        variant = self.get_variant(variant_id)
        if variant is None:
            raise ValueError(f"Variant with id {variant_id} not found.")
        self.session.delete(variant)
        self.session.commit()

    # ---------------------------
    # Работа с ответами (Answer)
    # ---------------------------
    def create_answer(
            self, 
            variant_id: str, 
            player_id: str, 
            answer_text: str, 
            answered_at: int = 0, 
            # is_correct: bool = False,
            ) -> Answer:
        new_answer = Answer(
            variant_id=variant_id,
            user_id=player_id,
            answer_text=answer_text,
            answered_at=answered_at,
            # is_correct=is_correct,
        )
        self.session.add(new_answer)
        self.session.commit()
        return new_answer

    def get_answers_by_question(self, question_id: str):
        return self.session.query(Answer).filter(Answer.question_id == question_id).all()

    # ---------------------------
    # Работа с медиа (Media)
    # ---------------------------
    def create_media(self, question_id: str, media_type: str, url: str, description: str, display_type: str) -> Media:
        new_media = Media(
            question_id=question_id,
            media_type=media_type,
            url=url,
            description=description,
            display_type=display_type,
        )
        self.session.add(new_media)
        self.session.commit()
        return new_media

    def get_media_by_question(self, question_id: str):
        return self.session.query(Media).filter(Media.question_id == question_id).all()

    # ---------------------------
    # Работа с игровыми сессиями (GameSession)
    # ---------------------------
    def create_game_session(self, game_id: str, game_code: str, status: str, current_question_id: str = None) -> GameSession:
        new_session = GameSession(
            game_id=game_id,
            game_code=game_code,
            status=status,
            current_question_id=current_question_id,
        )
        self.session.add(new_session)
        self.session.commit()
        return new_session

    def update_game_session_state(self, game_session_id: str, new_status: str) -> GameSession:
        game_session = self.get_game_session(game_session_id)
        if game_session:
            game_session.status = new_status
            self.session.commit()
        return game_session

    def update_game_session_question_id(self, game_session_id: str, question_id: str) -> GameSession:
        game_session = self.get_game_session(game_session_id)
        if game_session:
            game_session.current_question_id = question_id
            self.session.commit()
        return game_session

    def get_players_by_game_session_id(self, game_session_id: str) -> list[Player]:
        return self.session.query(Player).filter(Player.game_session_id == game_session_id).all()

    def get_game_session_by_code(self, code: str) -> GameSession:
        return self.session.query(GameSession).filter(GameSession.game_code == code).first()

    def get_game_session(self, game_session_id: str) -> GameSession:
        return self.session.query(GameSession).filter(GameSession.id == game_session_id).first()

    # ---------------------------
    # Работа с играми (Game) и внутренними пользователями (InternalUser)
    # ---------------------------
    def create_game(self, game_type: str, title: str, created_by: str = None) -> Game:
        new_game = Game(
            type=game_type,
            title=title,
            created_by=created_by,
        )
        self.session.add(new_game)
        self.session.commit()
        return new_game

    def get_games_by_creator_id(self, admin_id: str) -> list[Game]:
        return self.session.query(Game).filter(Game.created_by == admin_id).all()

    def get_game(self, game_id: str) -> Game:
        return self.session.query(Game).filter(Game.id == game_id).first()

    def create_internal_user(self, telegram_id: int, nickname: str, hashed_password: str) -> InternalUser:
        logger.info(f"called {__name__}")
        new_user = InternalUser(
            telegram_id=telegram_id,
            nickname=nickname,
            hashed_password=hashed_password,
        )
        self.session.add(new_user)
        self.session.commit()
        return new_user

    def get_internal_user_by_id(self, id: str) -> InternalUser:
        return self.session.query(InternalUser).filter(InternalUser.id == id).first()

    def get_internal_user_by_telegram_id(self, telegram_id: int) -> InternalUser:
        return self.session.query(InternalUser).filter(InternalUser.telegram_id == telegram_id).first()

    def update_internal_user_state(self, telegram_id: int, new_state: str) -> InternalUser:
        logger.debug(f"admin {telegram_id} change state to {new_state}")
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

def init_db_connector():
    engine = create_engine('sqlite:///your_database.db', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info("База данных успешно инициализирована.")
    db_connector = DatabaseConnector(session)
    return db_connector

db_connector = init_db_connector()
