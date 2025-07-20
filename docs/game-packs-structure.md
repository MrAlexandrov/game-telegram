# Структура игровых паков

## Схема для игры "100 к одному"

```json
{
  "game_pack": {
    "meta": {
      "title": "100 к одному - Семья",
      "description": "Вопросы на семейную тематику",
      "version": "1.0.0",
      "author": "Admin",
      "game_type": "family_feud",
      "created_at": "2024-01-15T10:00:00Z"
    },
    "config": {
      "team_mode": true,
      "max_teams": 2,
      "rounds": 3,
      "strikes_limit": 3,
      "double_points_round": 2,
      "triple_points_round": 3
    },
    "questions": [
      {
        "id": "ff1",
        "order": 1,
        "type": "survey_question",
        "content": {
          "text": "Назовите самое популярное домашнее животное",
          "survey_size": 100,
          "answers": [
            {"text": "Кошка", "points": 45, "rank": 1},
            {"text": "Собака", "points": 38, "rank": 2},
            {"text": "Рыбка", "points": 8, "rank": 3},
            {"text": "Попугай", "points": 5, "rank": 4},
            {"text": "Хомяк", "points": 3, "rank": 5},
            {"text": "Черепаха", "points": 1, "rank": 6}
          ]
        },
        "points_multiplier": 1,
        "time_limit": 120
      }
    ]
  }
}
```

## Валидация игровых паков

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class GameType(str, Enum):
    QUIZ = "quiz"
    FAMILY_FEUD = "family_feud"
    CUSTOM = "custom"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    MEDIA_QUESTION = "media_question"
    SURVEY_QUESTION = "survey_question"

class GamePackMeta(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    version: str = Field(..., regex=r"^\d+\.\d+\.\d+$")
    author: str = Field(..., min_length=1, max_length=100)
    game_type: GameType
    created_at: str = Field(..., regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

class Question(BaseModel):
    id: str = Field(..., min_length=1, max_length=50)
    order: int = Field(..., ge=1)
    type: QuestionType
    content: Dict[str, Any]
    correct_answers: List[str]
    points: int = Field(..., ge=1, le=1000)
    time_limit: int = Field(30, ge=10, le=300)
    requires_validation: Optional[bool] = False
    explanation: Optional[str] = None

class MediaFile(BaseModel):
    id: str = Field(..., min_length=1, max_length=50)
    filename: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., regex=r"^(image|video|audio)$")
    description: Optional[str] = None
    admin_only: bool = False

class GamePack(BaseModel):
    meta: GamePackMeta
    config: Dict[str, Any]
    questions: List[Question] = Field(..., min_items=1, max_items=100)
    media: Optional[List[MediaFile]] = []

class GamePackValidator:
    @staticmethod
    def validate_pack(pack_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        errors = []
        try:
            pack = GamePack(**pack_data["game_pack"])
            
            # Дополнительные проверки
            if pack.meta.game_type == GameType.QUIZ:
                errors.extend(GamePackValidator._validate_quiz_pack(pack))
            elif pack.meta.game_type == GameType.FAMILY_FEUD:
                errors.extend(GamePackValidator._validate_family_feud_pack(pack))
            
            return len(errors) == 0, errors
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    @staticmethod
    def _validate_quiz_pack(pack: GamePack) -> List[str]:
        errors = []
        for question in pack.questions:
            if question.type == QuestionType.MULTIPLE_CHOICE:
                if "options" not in question.content:
                    errors.append(f"Question {question.id}: missing options for multiple choice")
                elif len(question.content["options"]) < 2:
                    errors.append(f"Question {question.id}: need at least 2 options")
        return errors
    
    @staticmethod
    def _validate_family_feud_pack(pack: GamePack) -> List[str]:
        errors = []
        for question in pack.questions:
            if question.type == QuestionType.SURVEY_QUESTION:
                if "answers" not in question.content:
                    errors.append(f"Question {question.id}: missing answers for survey question")
                elif len(question.content["answers"]) < 3:
                    errors.append(f"Question {question.id}: need at least 3 survey answers")
        return errors