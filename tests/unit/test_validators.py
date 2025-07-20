"""
Unit tests for Pydantic schemas and validation logic.
"""
import pytest
from typing import Dict, Any, List
from pydantic import ValidationError
from datetime import datetime


class TestGameSchemas:
    """Test game-related Pydantic schemas."""
    
    def test_game_creation_schema(self):
        """Test game creation schema validation."""
        from shared.schemas.game_schemas import GameCreateSchema
        
        # Valid game data
        valid_data = {
            "title": "Test Quiz Game",
            "description": "A test quiz for validation",
            "type": "quiz",
            "settings": {
                "time_limit": 30,
                "max_players": 10,
                "show_correct_answers": True
            },
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "question": "What is 2+2?",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": 1,
                    "points": 10,
                    "time_limit": 15
                }
            ]
        }
        
        game = GameCreateSchema(**valid_data)
        assert game.title == "Test Quiz Game"
        assert game.type == "quiz"
        assert len(game.questions) == 1
        assert game.settings.max_players == 10
    
    def test_game_schema_validation_errors(self):
        """Test game schema validation errors."""
        from shared.schemas.game_schemas import GameCreateSchema
        
        # Missing required fields
        with pytest.raises(ValidationError) as exc_info:
            GameCreateSchema(title="Test")
        
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "type" in error_fields
        assert "questions" in error_fields
    
    def test_question_schema_validation(self):
        """Test question schema validation."""
        from shared.schemas.question_schemas import SingleChoiceQuestionSchema
        
        # Valid single choice question
        valid_question = {
            "id": "q1",
            "question": "What is the capital of France?",
            "options": ["London", "Paris", "Berlin", "Madrid"],
            "correct_answer": 1,
            "points": 10,
            "time_limit": 30
        }
        
        question = SingleChoiceQuestionSchema(**valid_question)
        assert question.id == "q1"
        assert len(question.options) == 4
        assert question.correct_answer == 1
    
    def test_question_validation_constraints(self):
        """Test question validation constraints."""
        from shared.schemas.question_schemas import SingleChoiceQuestionSchema
        
        # Test correct_answer out of range
        with pytest.raises(ValidationError):
            SingleChoiceQuestionSchema(
                id="q1",
                question="Test?",
                options=["A", "B"],
                correct_answer=5,  # Out of range
                points=10
            )
        
        # Test negative points
        with pytest.raises(ValidationError):
            SingleChoiceQuestionSchema(
                id="q1",
                question="Test?",
                options=["A", "B"],
                correct_answer=0,
                points=-5  # Negative points
            )
        
        # Test empty options
        with pytest.raises(ValidationError):
            SingleChoiceQuestionSchema(
                id="q1",
                question="Test?",
                options=[],  # Empty options
                correct_answer=0,
                points=10
            )
    
    def test_multiple_choice_question_schema(self):
        """Test multiple choice question schema."""
        from shared.schemas.question_schemas import MultipleChoiceQuestionSchema
        
        valid_question = {
            "id": "q2",
            "question": "Which are programming languages?",
            "options": ["Python", "JavaScript", "HTML", "CSS"],
            "correct_answers": [0, 1],
            "points": 15,
            "time_limit": 45
        }
        
        question = MultipleChoiceQuestionSchema(**valid_question)
        assert question.id == "q2"
        assert question.correct_answers == [0, 1]
        
        # Test validation - correct_answers out of range
        with pytest.raises(ValidationError):
            MultipleChoiceQuestionSchema(
                id="q2",
                question="Test?",
                options=["A", "B"],
                correct_answers=[0, 5],  # 5 is out of range
                points=15
            )
        
        # Test validation - empty correct_answers
        with pytest.raises(ValidationError):
            MultipleChoiceQuestionSchema(
                id="q2",
                question="Test?",
                options=["A", "B", "C"],
                correct_answers=[],  # Empty
                points=15
            )


class TestSessionSchemas:
    """Test session-related schemas."""
    
    def test_session_creation_schema(self):
        """Test session creation schema."""
        from shared.schemas.session_schemas import SessionCreateSchema
        
        valid_data = {
            "game_id": "game-123",
            "admin_id": 123456789,
            "settings": {
                "max_players": 10,
                "auto_start": False,
                "allow_late_join": True
            }
        }
        
        session = SessionCreateSchema(**valid_data)
        assert session.game_id == "game-123"
        assert session.admin_id == 123456789
        assert session.settings.max_players == 10
    
    def test_player_join_schema(self):
        """Test player join schema."""
        from shared.schemas.session_schemas import PlayerJoinSchema
        
        valid_data = {
            "user_id": 987654321,
            "username": "test_player",
            "first_name": "Test",
            "last_name": "Player"
        }
        
        player = PlayerJoinSchema(**valid_data)
        assert player.user_id == 987654321
        assert player.username == "test_player"
        
        # Test optional fields
        minimal_data = {
            "user_id": 987654321,
            "first_name": "Test"
        }
        
        player = PlayerJoinSchema(**minimal_data)
        assert player.user_id == 987654321
        assert player.username is None
    
    def test_answer_submission_schema(self):
        """Test answer submission schema."""
        from shared.schemas.session_schemas import AnswerSubmissionSchema
        
        # Single choice answer
        single_choice_data = {
            "session_id": "session-123",
            "question_id": "q1",
            "answer": 1,
            "timestamp": datetime.now()
        }
        
        answer = AnswerSubmissionSchema(**single_choice_data)
        assert answer.session_id == "session-123"
        assert answer.answer == 1
        
        # Multiple choice answer
        multiple_choice_data = {
            "session_id": "session-123",
            "question_id": "q2",
            "answer": [0, 2],
            "timestamp": datetime.now()
        }
        
        answer = AnswerSubmissionSchema(**multiple_choice_data)
        assert answer.answer == [0, 2]
        
        # Text answer
        text_data = {
            "session_id": "session-123",
            "question_id": "q3",
            "answer": "Paris",
            "timestamp": datetime.now()
        }
        
        answer = AnswerSubmissionSchema(**text_data)
        assert answer.answer == "Paris"


class TestUserSchemas:
    """Test user-related schemas."""
    
    def test_user_creation_schema(self):
        """Test user creation schema."""
        from shared.schemas.user_schemas import UserCreateSchema
        
        valid_data = {
            "user_id": 123456789,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "language_code": "en"
        }
        
        user = UserCreateSchema(**valid_data)
        assert user.user_id == 123456789
        assert user.username == "testuser"
        assert user.language_code == "en"
    
    def test_user_update_schema(self):
        """Test user update schema."""
        from shared.schemas.user_schemas import UserUpdateSchema
        
        # All fields optional for updates
        update_data = {
            "first_name": "Updated Name",
            "language_code": "ru"
        }
        
        user_update = UserUpdateSchema(**update_data)
        assert user_update.first_name == "Updated Name"
        assert user_update.language_code == "ru"
        assert user_update.username is None  # Not provided
    
    def test_user_profile_schema(self):
        """Test user profile response schema."""
        from shared.schemas.user_schemas import UserProfileSchema
        
        profile_data = {
            "user_id": 123456789,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "games_played": 15,
            "total_score": 1250,
            "average_score": 83.33,
            "achievements": ["first_game", "high_scorer"],
            "created_at": datetime.now(),
            "last_active": datetime.now()
        }
        
        profile = UserProfileSchema(**profile_data)
        assert profile.games_played == 15
        assert profile.total_score == 1250
        assert len(profile.achievements) == 2


class TestAnalyticsSchemas:
    """Test analytics-related schemas."""
    
    def test_game_result_schema(self):
        """Test game result schema."""
        from shared.schemas.analytics_schemas import GameResultSchema
        
        result_data = {
            "session_id": "session-123",
            "user_id": 987654321,
            "game_id": "game-456",
            "score": 85,
            "max_score": 100,
            "correct_answers": 8,
            "total_questions": 10,
            "completion_time": 120,
            "answers": [
                {
                    "question_id": "q1",
                    "answer": 1,
                    "correct": True,
                    "points": 10,
                    "time_taken": 5
                }
            ],
            "timestamp": datetime.now()
        }
        
        result = GameResultSchema(**result_data)
        assert result.score == 85
        assert result.completion_time == 120
        assert len(result.answers) == 1
    
    def test_leaderboard_entry_schema(self):
        """Test leaderboard entry schema."""
        from shared.schemas.analytics_schemas import LeaderboardEntrySchema
        
        entry_data = {
            "user_id": 123456789,
            "username": "top_player",
            "first_name": "Top",
            "score": 95,
            "rank": 1,
            "games_played": 5,
            "average_score": 88.5
        }
        
        entry = LeaderboardEntrySchema(**entry_data)
        assert entry.rank == 1
        assert entry.score == 95
        assert entry.average_score == 88.5
    
    def test_analytics_summary_schema(self):
        """Test analytics summary schema."""
        from shared.schemas.analytics_schemas import AnalyticsSummarySchema
        
        summary_data = {
            "game_id": "game-123",
            "total_sessions": 25,
            "total_players": 150,
            "average_score": 75.5,
            "completion_rate": 0.85,
            "average_completion_time": 180,
            "question_statistics": [
                {
                    "question_id": "q1",
                    "correct_rate": 0.8,
                    "average_time": 15
                }
            ],
            "date_range": {
                "start": datetime.now(),
                "end": datetime.now()
            }
        }
        
        summary = AnalyticsSummarySchema(**summary_data)
        assert summary.total_sessions == 25
        assert summary.completion_rate == 0.85
        assert len(summary.question_statistics) == 1


class TestValidationHelpers:
    """Test custom validation helpers."""
    
    def test_session_code_validator(self):
        """Test session code validation."""
        from shared.validators.session_validators import validate_session_code
        
        # Valid codes
        assert validate_session_code("ABC123") == True
        assert validate_session_code("XYZ789") == True
        
        # Invalid codes
        assert validate_session_code("abc123") == False  # Lowercase
        assert validate_session_code("AB12") == False    # Too short
        assert validate_session_code("ABCD123") == False # Too long
        assert validate_session_code("AB@123") == False  # Special chars
    
    def test_game_id_validator(self):
        """Test game ID validation."""
        from shared.validators.game_validators import validate_game_id
        
        # Valid IDs
        assert validate_game_id("game-123") == True
        assert validate_game_id("quiz_game_1") == True
        assert validate_game_id("family-feud-2024") == True
        
        # Invalid IDs
        assert validate_game_id("") == False           # Empty
        assert validate_game_id("a" * 101) == False    # Too long
        assert validate_game_id("game@123") == False   # Invalid chars
        assert validate_game_id("123game") == False    # Starts with number
    
    def test_user_id_validator(self):
        """Test Telegram user ID validation."""
        from shared.validators.user_validators import validate_telegram_user_id
        
        # Valid user IDs
        assert validate_telegram_user_id(123456789) == True
        assert validate_telegram_user_id(987654321) == True
        
        # Invalid user IDs
        assert validate_telegram_user_id(0) == False      # Zero
        assert validate_telegram_user_id(-123) == False   # Negative
        assert validate_telegram_user_id(12) == False     # Too small
    
    def test_answer_format_validator(self):
        """Test answer format validation."""
        from shared.validators.answer_validators import validate_answer_format
        
        # Single choice answers
        assert validate_answer_format(1, "single_choice") == True
        assert validate_answer_format("1", "single_choice") == True
        
        # Multiple choice answers
        assert validate_answer_format([0, 2], "multiple_choice") == True
        assert validate_answer_format(["0", "2"], "multiple_choice") == True
        
        # Text answers
        assert validate_answer_format("Paris", "text_input") == True
        assert validate_answer_format("", "text_input") == False  # Empty
        
        # True/False answers
        assert validate_answer_format(True, "true_false") == True
        assert validate_answer_format("true", "true_false") == True
        assert validate_answer_format(1, "true_false") == True
        
        # Invalid formats
        assert validate_answer_format([1, 2], "single_choice") == False
        assert validate_answer_format(1, "multiple_choice") == False


class TestSchemaTransformations:
    """Test schema transformations and serialization."""
    
    def test_game_to_api_response(self):
        """Test game schema to API response transformation."""
        from shared.schemas.game_schemas import GameSchema, GameResponseSchema
        
        game_data = {
            "id": "game-123",
            "title": "Test Game",
            "description": "A test game",
            "type": "quiz",
            "created_by": 123456789,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "settings": {"max_players": 10},
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "question": "Test?",
                    "options": ["A", "B"],
                    "correct_answer": 0,
                    "points": 10
                }
            ]
        }
        
        game = GameSchema(**game_data)
        
        # Transform to API response (hide sensitive data)
        api_response = GameResponseSchema.from_game(game)
        
        # Should not include correct answers for players
        question = api_response.questions[0]
        assert "correct_answer" not in question.dict()
        assert "options" in question.dict()
    
    def test_session_state_serialization(self):
        """Test session state serialization."""
        from shared.schemas.session_schemas import SessionStateSchema
        
        session_data = {
            "session_id": "session-123",
            "game_id": "game-456",
            "admin_id": 123456789,
            "status": "in_progress",
            "current_question": 2,
            "players": [
                {
                    "user_id": 987654321,
                    "username": "player1",
                    "score": 25,
                    "answered": True
                }
            ],
            "settings": {"max_players": 10},
            "created_at": datetime.now(),
            "started_at": datetime.now()
        }
        
        session = SessionStateSchema(**session_data)
        
        # Test serialization
        serialized = session.dict()
        assert serialized["session_id"] == "session-123"
        assert len(serialized["players"]) == 1
        
        # Test JSON serialization
        json_data = session.json()
        assert "session-123" in json_data
    
    def test_error_response_schema(self):
        """Test error response schema."""
        from shared.schemas.common_schemas import ErrorResponseSchema
        
        error_data = {
            "error": "validation_error",
            "message": "Invalid input data",
            "details": {
                "field": "username",
                "issue": "too_short"
            },
            "timestamp": datetime.now()
        }
        
        error = ErrorResponseSchema(**error_data)
        assert error.error == "validation_error"
        assert error.details["field"] == "username"


class TestSchemaPerformance:
    """Test schema validation performance."""
    
    @pytest.mark.performance
    def test_large_game_validation_performance(self):
        """Test validation performance with large game data."""
        from shared.schemas.game_schemas import GameCreateSchema
        import time
        
        # Create game with many questions
        questions = []
        for i in range(1000):
            questions.append({
                "id": f"q{i}",
                "type": "single_choice",
                "question": f"Question {i}?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": i % 4,
                "points": 10
            })
        
        game_data = {
            "title": "Large Game",
            "description": "Game with many questions",
            "type": "quiz",
            "settings": {"max_players": 100},
            "questions": questions
        }
        
        # Test validation time
        start_time = time.time()
        game = GameCreateSchema(**game_data)
        validation_time = time.time() - start_time
        
        assert validation_time < 1.0  # Should validate in less than 1 second
        assert len(game.questions) == 1000
    
    @pytest.mark.performance
    def test_bulk_answer_validation_performance(self):
        """Test bulk answer validation performance."""
        from shared.schemas.session_schemas import AnswerSubmissionSchema
        import time
        
        # Create many answer submissions
        answers = []
        for i in range(1000):
            answers.append({
                "session_id": f"session-{i % 10}",
                "question_id": f"q{i % 50}",
                "answer": i % 4,
                "timestamp": datetime.now()
            })
        
        # Test validation time
        start_time = time.time()
        validated_answers = [AnswerSubmissionSchema(**answer) for answer in answers]
        validation_time = time.time() - start_time
        
        assert validation_time < 0.5  # Should validate in less than 0.5 seconds
        assert len(validated_answers) == 1000


class TestCustomValidators:
    """Test custom field validators."""
    
    def test_email_validator(self):
        """Test email validation."""
        from shared.validators.common_validators import validate_email
        
        # Valid emails
        assert validate_email("test@example.com") == True
        assert validate_email("user.name@domain.co.uk") == True
        
        # Invalid emails
        assert validate_email("invalid-email") == False
        assert validate_email("@domain.com") == False
        assert validate_email("user@") == False
    
    def test_url_validator(self):
        """Test URL validation."""
        from shared.validators.common_validators import validate_url
        
        # Valid URLs
        assert validate_url("https://example.com") == True
        assert validate_url("http://localhost:8000") == True
        
        # Invalid URLs
        assert validate_url("not-a-url") == False
        assert validate_url("ftp://example.com") == False  # Only http/https allowed
    
    def test_phone_number_validator(self):
        """Test phone number validation."""
        from shared.validators.common_validators import validate_phone_number
        
        # Valid phone numbers
        assert validate_phone_number("+1234567890") == True
        assert validate_phone_number("+7-123-456-78-90") == True
        
        # Invalid phone numbers
        assert validate_phone_number("123") == False      # Too short
        assert validate_phone_number("abc123") == False   # Contains letters
        assert validate_phone_number("123456789012345678901") == False  # Too long