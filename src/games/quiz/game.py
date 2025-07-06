"""
Реализация игры-викторины
"""
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

from src.games.base import BaseGame
from src.models.game import RoundData, AnswerResult, GameResults, Question
from src.models.enums import QuestionType, GameType
from src.models.enums import GameState as GameStateEnum


class QuizGame(BaseGame):
    """Реализация игры-викторины"""
    
    def __init__(self, session_id: str, pack_data: Dict[str, Any]):
        super().__init__(session_id, pack_data)
        
        # Загружаем вопросы из пака
        self.questions: List[Question] = []
        questions_data = pack_data.get("questions", [])
        for q_data in questions_data:
            self.questions.append(Question(**q_data))
        
        # Текущий вопрос и данные раунда
        self.current_question: Optional[Question] = None
        self.round_answers: Dict[int, Dict[str, Any]] = {}
        self.round_start_time: Optional[float] = None
        
        # Настройки викторины
        self.time_per_question = self.settings.get("time_per_question", 30)
        self.show_correct_answer = self.settings.get("show_correct_answer", True)
        self.allow_skip = self.settings.get("allow_skip", False)
        self.points_per_correct = self.settings.get("points_per_correct", 10)
        self.penalty_for_wrong = self.settings.get("penalty_for_wrong", 0)
        self.shuffle_questions = self.settings.get("shuffle_questions", False)
        self.shuffle_options = self.settings.get("shuffle_options", False)
    
    async def initialize(self) -> None:
        """Инициализация викторины"""
        if self.shuffle_questions:
            import random
            random.shuffle(self.questions)
        
        self.game_state = GameStateEnum.READY
    
    async def start_round(self) -> Optional[RoundData]:
        """Начало нового раунда (вопроса)"""
        if self.current_round >= len(self.questions):
            return None
        
        self.current_question = self.questions[self.current_round]
        self.round_answers = {}
        self.round_start_time = asyncio.get_event_loop().time()
        self.game_state = GameStateEnum.ACTIVE
        
        # Подготавливаем варианты ответов
        options = None
        if self.current_question.options:
            options = self.current_question.options.copy()
            if self.shuffle_options:
                import random
                random.shuffle(options)
        
        return RoundData(
            round_number=self.current_round + 1,
            question=self.current_question.question,
            options=options,
            time_limit=self.current_question.time_limit or self.time_per_question,
            image_url=self.current_question.image_url,
            audio_url=self.current_question.audio_url,
            hint=self.current_question.hint
        )
    
    async def process_answer(self, user_id: int, answer: str) -> AnswerResult:
        """Обработка ответа игрока"""
        if self.game_state != GameStateEnum.ACTIVE or not self.current_question:
            return AnswerResult(
                success=False,
                message="Игра не активна или вопрос не задан"
            )
        
        if user_id in self.round_answers:
            return AnswerResult(
                success=False,
                message="Вы уже ответили на этот вопрос"
            )
        
        # Проверка времени
        current_time = asyncio.get_event_loop().time()
        time_limit = self.current_question.time_limit or self.time_per_question
        
        if self.round_start_time and current_time - self.round_start_time > time_limit:
            return AnswerResult(
                success=False,
                message="⏰ Время на ответ истекло"
            )
        
        # Проверка правильности ответа
        is_correct = self._check_answer(answer)
        points = 0
        
        if is_correct:
            points = self.current_question.points or self.points_per_correct
            self.update_player_score(user_id, points)
        else:
            penalty = self.penalty_for_wrong
            if penalty < 0:
                self.update_player_score(user_id, penalty)
        
        # Сохраняем ответ
        self.round_answers[user_id] = {
            "answer": answer,
            "is_correct": is_correct,
            "points": points,
            "timestamp": current_time
        }
        
        # Подготавливаем результат
        result = AnswerResult(
            success=True,
            is_correct=is_correct,
            points=points,
            message="✅ Правильно!" if is_correct else "❌ Неправильно"
        )
        
        # Добавляем объяснение если есть и настройка включена
        if self.show_correct_answer and self.current_question.explanation:
            result.explanation = self.current_question.explanation
        
        # Показываем правильный ответ если неправильно ответил
        if not is_correct and self.show_correct_answer:
            result.correct_answer = self._get_correct_answer_text()
        
        return result
    
    def _check_answer(self, answer: str) -> bool:
        """Проверка правильности ответа"""
        if not self.current_question:
            return False
        
        question_type = self.current_question.type
        
        if question_type == QuestionType.MULTIPLE_CHOICE:
            try:
                # Пользователь может ввести номер варианта (1-4) или текст варианта
                if answer.isdigit():
                    answer_index = int(answer) - 1  # Пользователь вводит 1-4, а индексы 0-3
                    correct_index = self.current_question.correct_answer
                    return answer_index == correct_index
                else:
                    # Проверяем по тексту варианта
                    if self.current_question.options:
                        correct_index = self.current_question.correct_answer
                        correct_text = self.current_question.options[correct_index]
                        return answer.lower().strip() == correct_text.lower().strip()
                    return False
            except (ValueError, IndexError, TypeError):
                return False
        
        elif question_type == QuestionType.TEXT_INPUT:
            correct_answers = self.current_question.correct_answers or []
            case_sensitive = self.current_question.case_sensitive
            
            if not case_sensitive:
                answer = answer.lower().strip()
                correct_answers = [ans.lower().strip() for ans in correct_answers]
            else:
                answer = answer.strip()
                correct_answers = [ans.strip() for ans in correct_answers]
            
            return answer in correct_answers
        
        elif question_type == QuestionType.TRUE_FALSE:
            correct_answer = self.current_question.correct_answer
            answer_lower = answer.lower().strip()
            
            true_variants = ["да", "yes", "true", "1", "+", "правда"]
            false_variants = ["нет", "no", "false", "0", "-", "ложь"]
            
            if answer_lower in true_variants:
                return correct_answer is True
            elif answer_lower in false_variants:
                return correct_answer is False
            else:
                return False
        
        elif question_type == QuestionType.NUMERIC:
            try:
                answer_num = float(answer.replace(",", "."))
                correct_num = float(self.current_question.correct_answer)
                tolerance = self.current_question.tolerance or 0
                
                return abs(answer_num - correct_num) <= tolerance
            except (ValueError, TypeError):
                return False
        
        return False
    
    def _get_correct_answer_text(self) -> str:
        """Получение текста правильного ответа"""
        if not self.current_question:
            return ""
        
        question_type = self.current_question.type
        
        if question_type == QuestionType.MULTIPLE_CHOICE:
            if self.current_question.options and self.current_question.correct_answer is not None:
                try:
                    correct_index = self.current_question.correct_answer
                    return f"{correct_index + 1}. {self.current_question.options[correct_index]}"
                except (IndexError, TypeError):
                    return str(self.current_question.correct_answer)
        
        elif question_type == QuestionType.TEXT_INPUT:
            if self.current_question.correct_answers:
                return self.current_question.correct_answers[0]
        
        elif question_type == QuestionType.TRUE_FALSE:
            return "Да" if self.current_question.correct_answer else "Нет"
        
        elif question_type == QuestionType.NUMERIC:
            return str(self.current_question.correct_answer)
        
        return str(self.current_question.correct_answer)
    
    async def next_round(self) -> Optional[RoundData]:
        """Переход к следующему раунду"""
        self.current_round += 1
        
        if self.current_round >= len(self.questions):
            self.game_state = GameStateEnum.FINISHED
            return None
        
        return await self.start_round()
    
    async def finish_game(self) -> GameResults:
        """Завершение игры и подсчет результатов"""
        self.game_state = GameStateEnum.FINISHED
        self.finished_at = datetime.now()
        
        # Сортировка игроков по очкам
        sorted_players = self.get_leaderboard()
        
        # Подсчет статистики
        total_questions = len(self.questions)
        statistics = {
            "total_questions": total_questions,
            "average_score": sum(self.players_scores.values()) / len(self.players_scores) if self.players_scores else 0,
            "highest_score": max(self.players_scores.values()) if self.players_scores else 0,
            "lowest_score": min(self.players_scores.values()) if self.players_scores else 0,
            "completion_rate": len([p for p in self.players_scores.values() if p > 0]) / len(self.players_scores) if self.players_scores else 0
        }
        
        return GameResults(
            session_id=self.session_id,
            game_type=GameType.QUIZ,
            total_rounds=total_questions,
            players_results=sorted_players,
            winner=self.get_winner(),
            game_duration=self.get_game_duration(),
            started_at=self.started_at,
            finished_at=self.finished_at,
            statistics=statistics
        )
    
    async def get_current_state(self) -> Dict[str, Any]:
        """Получение текущего состояния игры"""
        return {
            "session_id": self.session_id,
            "game_state": self.game_state,
            "current_round": self.current_round,
            "total_rounds": len(self.questions),
            "players_count": self.get_players_count(),
            "scores": self.players_scores,
            "current_question": {
                "question": self.current_question.question if self.current_question else None,
                "type": self.current_question.type if self.current_question else None,
                "time_limit": self.current_question.time_limit or self.time_per_question if self.current_question else None
            } if self.current_question else None,
            "round_answers_count": len(self.round_answers),
            "time_remaining": self._get_time_remaining()
        }
    
    def _get_time_remaining(self) -> Optional[int]:
        """Получение оставшегося времени на ответ"""
        if not self.round_start_time or not self.current_question:
            return None
        
        current_time = asyncio.get_event_loop().time()
        time_limit = self.current_question.time_limit or self.time_per_question
        elapsed = current_time - self.round_start_time
        remaining = max(0, int(time_limit - elapsed))
        
        return remaining if remaining > 0 else 0
    
    def get_round_results(self) -> Dict[str, Any]:
        """Получение результатов текущего раунда"""
        if not self.current_question:
            return {}
        
        correct_count = sum(1 for answer_data in self.round_answers.values() if answer_data["is_correct"])
        total_count = len(self.round_answers)
        
        return {
            "question": self.current_question.question,
            "correct_answer": self._get_correct_answer_text(),
            "explanation": self.current_question.explanation,
            "correct_count": correct_count,
            "total_count": total_count,
            "accuracy": (correct_count / total_count * 100) if total_count > 0 else 0,
            "answers": self.round_answers
        }