"""
Integration tests for the quiz module system
Tests the complete flow from question processing to result calculation
"""

import pytest
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from game_modules.quiz.quiz_module import QuizModule
from game_modules.quiz.question_types import create_question_from_dict
from game_modules.quiz.schemas import QuizPackSchema, validate_question_by_type
from game_modules.base.game_module import Question, Answer, GameSession


class TestQuizModuleIntegration:
    """Integration tests for quiz module"""
    
    @pytest.fixture
    def quiz_module(self):
        """Create quiz module instance"""
        return QuizModule()
    
    @pytest.fixture
    def sample_session(self):
        """Create sample game session"""
        return GameSession(
            id="test_session_001",
            game_id="test_game_001",
            admin_id="admin_001",
            players=["player_001", "player_002", "player_003"],
            current_question=None,
            status="active",
            config={
                "time_limit": 30,
                "points_per_question": 10,
                "shuffle_options": True,
                "allow_partial_credit": True,
                "case_sensitive": False
            },
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_questions(self):
        """Create sample questions of different types"""
        return [
            {
                "id": "mc_001",
                "type": "multiple_choice",
                "text": "Какая планета самая большая?",
                "options": [
                    {"text": "Юпитер"},
                    {"text": "Сатурн"},
                    {"text": "Земля"},
                    {"text": "Марс"}
                ],
                "correct_answers": ["Юпитер"],
                "points": 10,
                "time_limit": 30,
                "explanation": "Юпитер - самая большая планета"
            },
            {
                "id": "text_001",
                "type": "text_input",
                "text": "Столица Франции?",
                "correct_answers": ["Париж", "париж"],
                "points": 10,
                "time_limit": 20,
                "validation_rules": {
                    "case_sensitive": False,
                    "allow_partial": True
                }
            },
            {
                "id": "tf_001",
                "type": "true_false",
                "text": "Кит - это рыба?",
                "correct_answer": False,
                "points": 8,
                "time_limit": 15
            }
        ]
    
    @pytest.mark.asyncio
    async def test_module_initialization(self, quiz_module):
        """Test quiz module initialization"""
        assert quiz_module.game_type == "quiz"
        assert quiz_module.name == "Advanced Quiz Module"
        assert quiz_module.version == "2.0.0"
        
        supported_types = quiz_module.get_supported_question_types()
        assert "multiple_choice" in supported_types
        assert "text_input" in supported_types
        assert "true_false" in supported_types
        assert "media_question" in supported_types
    
    @pytest.mark.asyncio
    async def test_question_validation(self, quiz_module, sample_questions):
        """Test question validation using schemas"""
        for question_data in sample_questions:
            validation_result = quiz_module.validate_question(question_data)
            assert validation_result["is_valid"], f"Question {question_data['id']} should be valid"
            assert len(validation_result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_question_processing(self, quiz_module, sample_session, sample_questions):
        """Test question processing"""
        for question_data in sample_questions:
            # Convert to Question object
            question = Question(
                id=question_data["id"],
                content=question_data,
                question_type=question_data["type"],
                correct_answers=question_data.get("correct_answers", []),
                points=question_data.get("points", 10),
                time_limit=question_data.get("time_limit", 30),
                explanation=question_data.get("explanation")
            )
            
            # Process question
            processed = await quiz_module.process_question(question, sample_session)
            
            assert processed["question_id"] == question_data["id"]
            assert processed["type"] == question_data["type"]
            assert processed["points"] == question_data.get("points", 10)
            
            # Sensitive data should be removed
            assert "correct_answers" not in processed
    
    @pytest.mark.asyncio
    async def test_answer_validation(self, quiz_module, sample_questions):
        """Test answer validation for different question types"""
        # Test multiple choice
        mc_question = sample_questions[0]
        question_obj = Question(
            id=mc_question["id"],
            content=mc_question,
            question_type=mc_question["type"],
            correct_answers=mc_question["correct_answers"],
            points=mc_question["points"],
            time_limit=mc_question["time_limit"]
        )
        
        # Correct answer
        answer = Answer(
            user_id="player_001",
            question_id=mc_question["id"],
            session_id="test_session",
            answer_text="Юпитер",
            answered_at=datetime.utcnow()
        )
        
        result = await quiz_module.validate_answer(answer, question_obj)
        assert result["is_correct"] == True
        assert result["points_earned"] > 0
        
        # Incorrect answer
        answer.answer_text = "Марс"
        result = await quiz_module.validate_answer(answer, question_obj)
        assert result["is_correct"] == False
        assert result["points_earned"] == 0
    
    @pytest.mark.asyncio
    async def test_text_input_validation(self, quiz_module, sample_questions):
        """Test text input validation with partial matching"""
        text_question = sample_questions[1]
        question_obj = Question(
            id=text_question["id"],
            content=text_question,
            question_type=text_question["type"],
            correct_answers=text_question["correct_answers"],
            points=text_question["points"],
            time_limit=text_question["time_limit"]
        )
        
        # Exact match
        answer = Answer(
            user_id="player_001",
            question_id=text_question["id"],
            session_id="test_session",
            answer_text="Париж",
            answered_at=datetime.utcnow()
        )
        
        result = await quiz_module.validate_answer(answer, question_obj)
        assert result["is_correct"] == True
        
        # Case insensitive match
        answer.answer_text = "париж"
        result = await quiz_module.validate_answer(answer, question_obj)
        assert result["is_correct"] == True
    
    @pytest.mark.asyncio
    async def test_true_false_validation(self, quiz_module, sample_questions):
        """Test true/false question validation"""
        tf_question = sample_questions[2]
        question_obj = Question(
            id=tf_question["id"],
            content=tf_question,
            question_type=tf_question["type"],
            correct_answers=[str(tf_question["correct_answer"]).lower()],
            points=tf_question["points"],
            time_limit=tf_question["time_limit"]
        )
        
        # Correct answer (False)
        answer = Answer(
            user_id="player_001",
            question_id=tf_question["id"],
            session_id="test_session",
            answer_text="false",
            answered_at=datetime.utcnow()
        )
        
        result = await quiz_module.validate_answer(answer, question_obj)
        assert result["is_correct"] == True
        
        # Incorrect answer
        answer.answer_text = "true"
        result = await quiz_module.validate_answer(answer, question_obj)
        assert result["is_correct"] == False
    
    @pytest.mark.asyncio
    async def test_score_calculation(self, quiz_module, sample_session, sample_questions):
        """Test score calculation for multiple players"""
        question_data = sample_questions[0]  # Multiple choice question
        question_obj = Question(
            id=question_data["id"],
            content=question_data,
            question_type=question_data["type"],
            correct_answers=question_data["correct_answers"],
            points=question_data["points"],
            time_limit=question_data["time_limit"]
        )
        
        # Create answers from different players
        answers = [
            Answer(
                user_id="player_001",
                question_id=question_data["id"],
                session_id="test_session",
                answer_text="Юпитер",  # Correct
                answered_at=datetime.utcnow(),
                is_correct=True,
                points_earned=10
            ),
            Answer(
                user_id="player_002",
                question_id=question_data["id"],
                session_id="test_session",
                answer_text="Марс",  # Incorrect
                answered_at=datetime.utcnow(),
                is_correct=False,
                points_earned=0
            ),
            Answer(
                user_id="player_003",
                question_id=question_data["id"],
                session_id="test_session",
                answer_text="Юпитер",  # Correct
                answered_at=datetime.utcnow(),
                is_correct=True,
                points_earned=10
            )
        ]
        
        scores = await quiz_module.calculate_score(answers, question_obj)
        
        assert scores["player_001"] == 10
        assert scores["player_002"] == 0
        assert scores["player_003"] == 10
    
    @pytest.mark.asyncio
    async def test_session_results(self, quiz_module, sample_session):
        """Test comprehensive session results calculation"""
        # Create sample answers for the session
        all_answers = [
            Answer(
                user_id="player_001",
                question_id="q1",
                session_id=sample_session.id,
                answer_text="answer1",
                answered_at=datetime.utcnow(),
                is_correct=True,
                points_earned=10,
                time_taken=15.5
            ),
            Answer(
                user_id="player_001",
                question_id="q2",
                session_id=sample_session.id,
                answer_text="answer2",
                answered_at=datetime.utcnow(),
                is_correct=False,
                points_earned=0,
                time_taken=25.0
            ),
            Answer(
                user_id="player_002",
                question_id="q1",
                session_id=sample_session.id,
                answer_text="answer1",
                answered_at=datetime.utcnow(),
                is_correct=True,
                points_earned=10,
                time_taken=20.0
            )
        ]
        
        results = await quiz_module.get_results(sample_session, all_answers)
        
        assert results["game_type"] == "quiz"
        assert results["session_id"] == sample_session.id
        assert results["total_players"] == 3
        assert len(results["leaderboard"]) > 0
        
        # Check leaderboard structure
        leaderboard = results["leaderboard"]
        for player in leaderboard:
            assert "user_id" in player
            assert "total_score" in player
            assert "correct_answers" in player
            assert "accuracy" in player
            assert "rank" in player
    
    @pytest.mark.asyncio
    async def test_session_initialization_and_finalization(self, quiz_module, sample_session):
        """Test session lifecycle management"""
        # Initialize session
        init_result = await quiz_module.initialize_session(sample_session)
        
        assert init_result["status"] == "initialized"
        assert init_result["game_type"] == "quiz"
        assert init_result["module"] == quiz_module.name
        
        # Finalize session
        final_result = await quiz_module.finalize_session(sample_session)
        
        assert final_result["status"] == "finalized"
        assert final_result["game_type"] == "quiz"
    
    def test_question_type_factory(self, sample_questions):
        """Test question type factory function"""
        for question_data in sample_questions:
            question_obj = create_question_from_dict(question_data)
            
            assert question_obj.question_id == question_data["id"]
            assert question_obj.text == question_data["text"]
            assert question_obj.points == question_data.get("points", 10)
            
            # Test validation
            validation_result = question_obj.validate_answer("test_answer")
            assert isinstance(validation_result, dict)
            assert "is_correct" in validation_result
            assert "points_earned" in validation_result
    
    def test_schema_validation(self, sample_questions):
        """Test Pydantic schema validation"""
        for question_data in sample_questions:
            try:
                validated_question = validate_question_by_type(question_data)
                assert validated_question.id == question_data["id"]
                assert validated_question.type.value == question_data["type"]
            except Exception as e:
                pytest.fail(f"Schema validation failed for {question_data['id']}: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_comprehensive_game_pack_loading(self):
        """Test loading and validating a comprehensive game pack"""
        # Load the comprehensive quiz pack
        pack_file = Path(__file__).parent.parent / "game-packs" / "quiz" / "comprehensive_quiz.json"
        
        if pack_file.exists():
            with open(pack_file, 'r', encoding='utf-8') as f:
                pack_data = json.load(f)
            
            # Validate pack structure
            assert "metadata" in pack_data
            assert "config" in pack_data
            assert "questions" in pack_data
            
            # Test each question
            quiz_module = QuizModule()
            for question_data in pack_data["questions"]:
                validation_result = quiz_module.validate_question(question_data)
                assert validation_result["is_valid"], f"Question {question_data['id']} validation failed: {validation_result['errors']}"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, quiz_module):
        """Test error handling in various scenarios"""
        # Test with invalid question data
        invalid_question = {
            "id": "invalid_001",
            "type": "unknown_type",
            "text": "Invalid question"
        }
        
        validation_result = quiz_module.validate_question(invalid_question)
        assert not validation_result["is_valid"]
        assert len(validation_result["errors"]) > 0
        
        # Test with missing required fields
        incomplete_question = {
            "id": "incomplete_001"
            # Missing text and type
        }
        
        validation_result = quiz_module.validate_question(incomplete_question)
        assert not validation_result["is_valid"]
        assert len(validation_result["errors"]) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
