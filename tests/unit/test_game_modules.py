"""
Unit tests for game modules and game logic.
"""
import pytest
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch
import json


class TestQuizModule:
    """Test quiz game module functionality."""
    
    def test_quiz_module_initialization(self):
        """Test quiz module can be initialized properly."""
        from game_modules.quiz.quiz_module import QuizModule
        
        quiz_data = {
            "id": "test-quiz",
            "title": "Test Quiz",
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "question": "What is 2+2?",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": 1,
                    "points": 10
                }
            ]
        }
        
        quiz = QuizModule(quiz_data)
        assert quiz.game_id == "test-quiz"
        assert quiz.title == "Test Quiz"
        assert len(quiz.questions) == 1
    
    def test_single_choice_question_validation(self):
        """Test single choice question validation."""
        from game_modules.quiz.question_types import SingleChoiceQuestion
        
        question_data = {
            "id": "q1",
            "question": "What is the capital of France?",
            "options": ["London", "Paris", "Berlin", "Madrid"],
            "correct_answer": 1,
            "points": 10,
            "time_limit": 30
        }
        
        question = SingleChoiceQuestion(**question_data)
        
        # Test correct answer
        assert question.check_answer(1) == True
        assert question.check_answer("1") == True  # String conversion
        
        # Test incorrect answer
        assert question.check_answer(0) == False
        assert question.check_answer(2) == False
        
        # Test invalid answer
        assert question.check_answer(5) == False
        assert question.check_answer(-1) == False
    
    def test_multiple_choice_question_validation(self):
        """Test multiple choice question validation."""
        from game_modules.quiz.question_types import MultipleChoiceQuestion
        
        question_data = {
            "id": "q2",
            "question": "Which are programming languages?",
            "options": ["Python", "JavaScript", "HTML", "CSS"],
            "correct_answers": [0, 1],
            "points": 15,
            "time_limit": 45
        }
        
        question = MultipleChoiceQuestion(**question_data)
        
        # Test correct answers
        assert question.check_answer([0, 1]) == True
        assert question.check_answer([1, 0]) == True  # Order doesn't matter
        
        # Test partial correct
        assert question.check_answer([0]) == False  # Incomplete
        assert question.check_answer([1]) == False  # Incomplete
        
        # Test incorrect answers
        assert question.check_answer([2, 3]) == False
        assert question.check_answer([0, 1, 2]) == False  # Too many
        
        # Test empty answer
        assert question.check_answer([]) == False
    
    def test_true_false_question_validation(self):
        """Test true/false question validation."""
        from game_modules.quiz.question_types import TrueFalseQuestion
        
        question_data = {
            "id": "q3",
            "question": "Python is a programming language",
            "correct_answer": True,
            "points": 5,
            "time_limit": 15
        }
        
        question = TrueFalseQuestion(**question_data)
        
        # Test correct answers
        assert question.check_answer(True) == True
        assert question.check_answer("true") == True
        assert question.check_answer("True") == True
        assert question.check_answer(1) == True
        
        # Test incorrect answers
        assert question.check_answer(False) == False
        assert question.check_answer("false") == False
        assert question.check_answer(0) == False
    
    def test_text_input_question_validation(self):
        """Test text input question validation."""
        from game_modules.quiz.question_types import TextInputQuestion
        
        question_data = {
            "id": "q4",
            "question": "What is the capital of Italy?",
            "correct_answers": ["Rome", "roma", "ROME"],
            "points": 12,
            "time_limit": 60,
            "case_sensitive": False
        }
        
        question = TextInputQuestion(**question_data)
        
        # Test correct answers
        assert question.check_answer("Rome") == True
        assert question.check_answer("roma") == True
        assert question.check_answer("ROME") == True
        assert question.check_answer("  Rome  ") == True  # Whitespace trimmed
        
        # Test incorrect answers
        assert question.check_answer("Paris") == False
        assert question.check_answer("Milan") == False
        assert question.check_answer("") == False
    
    def test_quiz_scoring_system(self):
        """Test quiz scoring calculations."""
        from game_modules.quiz.quiz_module import QuizModule
        
        quiz_data = {
            "id": "scoring-test",
            "title": "Scoring Test",
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "question": "Easy question",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "points": 10
                },
                {
                    "id": "q2",
                    "type": "multiple_choice",
                    "question": "Hard question",
                    "options": ["A", "B", "C", "D"],
                    "correct_answers": [0, 2],
                    "points": 20
                }
            ]
        }
        
        quiz = QuizModule(quiz_data)
        
        # Test perfect score
        answers = [
            {"question_id": "q1", "answer": 0},
            {"question_id": "q2", "answer": [0, 2]}
        ]
        
        score = quiz.calculate_score(answers)
        assert score["total_score"] == 30
        assert score["correct_answers"] == 2
        assert score["total_questions"] == 2
        
        # Test partial score
        answers = [
            {"question_id": "q1", "answer": 1},  # Wrong
            {"question_id": "q2", "answer": [0, 2]}  # Correct
        ]
        
        score = quiz.calculate_score(answers)
        assert score["total_score"] == 20
        assert score["correct_answers"] == 1
        assert score["total_questions"] == 2
    
    def test_quiz_time_limits(self):
        """Test quiz time limit functionality."""
        from game_modules.quiz.quiz_module import QuizModule
        import time
        
        quiz_data = {
            "id": "time-test",
            "title": "Time Test",
            "settings": {"time_limit": 60},
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "question": "Quick question",
                    "options": ["A", "B"],
                    "correct_answer": 0,
                    "points": 10,
                    "time_limit": 5
                }
            ]
        }
        
        quiz = QuizModule(quiz_data)
        
        # Test time limit checking
        start_time = time.time()
        
        # Simulate answer within time limit
        answer_time = start_time + 3  # 3 seconds later
        is_within_limit = quiz.is_answer_within_time_limit("q1", start_time, answer_time)
        assert is_within_limit == True
        
        # Simulate answer after time limit
        answer_time = start_time + 10  # 10 seconds later
        is_within_limit = quiz.is_answer_within_time_limit("q1", start_time, answer_time)
        assert is_within_limit == False


class TestFamilyFeudModule:
    """Test family feud game module functionality."""
    
    def test_family_feud_initialization(self):
        """Test family feud module initialization."""
        from game_modules.family_feud.family_feud_module import FamilyFeudModule
        
        game_data = {
            "id": "ff-test",
            "title": "Family Test",
            "questions": [
                {
                    "id": "ff1",
                    "question": "Name something in a kitchen",
                    "answers": [
                        {"text": "Refrigerator", "points": 45},
                        {"text": "Stove", "points": 30},
                        {"text": "Sink", "points": 15},
                        {"text": "Microwave", "points": 10}
                    ]
                }
            ],
            "settings": {
                "teams": 2,
                "strikes_limit": 3,
                "rounds": 3
            }
        }
        
        ff_game = FamilyFeudModule(game_data)
        assert ff_game.game_id == "ff-test"
        assert ff_game.settings["teams"] == 2
        assert len(ff_game.questions) == 1
    
    def test_answer_matching(self):
        """Test family feud answer matching logic."""
        from game_modules.family_feud.family_feud_module import FamilyFeudModule
        
        question_data = {
            "id": "ff1",
            "question": "Name a pet",
            "answers": [
                {"text": "Dog", "points": 40},
                {"text": "Cat", "points": 35},
                {"text": "Fish", "points": 15},
                {"text": "Bird", "points": 10}
            ]
        }
        
        ff_game = FamilyFeudModule({"id": "test", "questions": [question_data]})
        
        # Test exact matches
        match = ff_game.find_answer_match("ff1", "Dog")
        assert match is not None
        assert match["points"] == 40
        
        # Test case insensitive
        match = ff_game.find_answer_match("ff1", "dog")
        assert match is not None
        assert match["points"] == 40
        
        # Test partial matches
        match = ff_game.find_answer_match("ff1", "Dogs")
        assert match is not None
        assert match["points"] == 40
        
        # Test no match
        match = ff_game.find_answer_match("ff1", "Elephant")
        assert match is None
    
    def test_team_scoring(self):
        """Test family feud team scoring system."""
        from game_modules.family_feud.family_feud_module import FamilyFeudModule
        
        game_data = {
            "id": "scoring-test",
            "questions": [
                {
                    "id": "ff1",
                    "question": "Name a color",
                    "answers": [
                        {"text": "Red", "points": 30},
                        {"text": "Blue", "points": 25},
                        {"text": "Green", "points": 20}
                    ]
                }
            ],
            "settings": {"teams": 2}
        }
        
        ff_game = FamilyFeudModule(game_data)
        
        # Initialize teams
        ff_game.initialize_teams(["Team A", "Team B"])
        
        # Team A gets correct answers
        ff_game.add_team_points("Team A", 30)
        ff_game.add_team_points("Team A", 25)
        
        # Team B gets one correct answer
        ff_game.add_team_points("Team B", 20)
        
        scores = ff_game.get_team_scores()
        assert scores["Team A"] == 55
        assert scores["Team B"] == 20
    
    def test_strikes_system(self):
        """Test family feud strikes system."""
        from game_modules.family_feud.family_feud_module import FamilyFeudModule
        
        game_data = {
            "id": "strikes-test",
            "questions": [{"id": "ff1", "question": "Test", "answers": []}],
            "settings": {"strikes_limit": 3}
        }
        
        ff_game = FamilyFeudModule(game_data)
        ff_game.initialize_teams(["Team A", "Team B"])
        
        # Add strikes to Team A
        ff_game.add_strike("Team A")
        assert ff_game.get_team_strikes("Team A") == 1
        
        ff_game.add_strike("Team A")
        ff_game.add_strike("Team A")
        assert ff_game.get_team_strikes("Team A") == 3
        
        # Check if team is eliminated
        assert ff_game.is_team_eliminated("Team A") == True
        assert ff_game.is_team_eliminated("Team B") == False


class TestGameModuleBase:
    """Test base game module functionality."""
    
    def test_base_module_interface(self):
        """Test base game module interface."""
        from game_modules.base.game_module import BaseGameModule
        
        # Test abstract methods exist
        assert hasattr(BaseGameModule, 'initialize')
        assert hasattr(BaseGameModule, 'process_answer')
        assert hasattr(BaseGameModule, 'calculate_score')
        assert hasattr(BaseGameModule, 'get_next_question')
        assert hasattr(BaseGameModule, 'is_game_complete')
    
    def test_game_state_management(self):
        """Test game state management in base module."""
        from game_modules.base.game_module import BaseGameModule
        
        class TestGameModule(BaseGameModule):
            def initialize(self):
                self.state = "initialized"
            
            def process_answer(self, question_id, answer, user_id):
                return {"correct": True, "points": 10}
            
            def calculate_score(self, answers):
                return {"total_score": sum(a.get("points", 0) for a in answers)}
            
            def get_next_question(self):
                return None
            
            def is_game_complete(self):
                return True
        
        game = TestGameModule({"id": "test", "title": "Test Game"})
        game.initialize()
        
        assert game.state == "initialized"
        assert game.game_id == "test"
        assert game.title == "Test Game"


class TestQuestionTypes:
    """Test individual question type implementations."""
    
    def test_question_type_factory(self):
        """Test question type factory creates correct types."""
        from game_modules.quiz.question_types import create_question
        
        # Single choice question
        single_choice_data = {
            "id": "q1",
            "type": "single_choice",
            "question": "Test?",
            "options": ["A", "B"],
            "correct_answer": 0,
            "points": 10
        }
        
        question = create_question(single_choice_data)
        assert question.__class__.__name__ == "SingleChoiceQuestion"
        
        # Multiple choice question
        multiple_choice_data = {
            "id": "q2",
            "type": "multiple_choice",
            "question": "Test?",
            "options": ["A", "B", "C"],
            "correct_answers": [0, 2],
            "points": 15
        }
        
        question = create_question(multiple_choice_data)
        assert question.__class__.__name__ == "MultipleChoiceQuestion"
        
        # True/False question
        true_false_data = {
            "id": "q3",
            "type": "true_false",
            "question": "Test?",
            "correct_answer": True,
            "points": 5
        }
        
        question = create_question(true_false_data)
        assert question.__class__.__name__ == "TrueFalseQuestion"
    
    def test_question_serialization(self):
        """Test question serialization for API responses."""
        from game_modules.quiz.question_types import SingleChoiceQuestion
        
        question_data = {
            "id": "q1",
            "question": "What is 1+1?",
            "options": ["1", "2", "3", "4"],
            "correct_answer": 1,
            "points": 10,
            "time_limit": 30
        }
        
        question = SingleChoiceQuestion(**question_data)
        
        # Test serialization (without correct answer for players)
        player_data = question.to_player_dict()
        assert "correct_answer" not in player_data
        assert "options" in player_data
        assert "question" in player_data
        
        # Test full serialization (for admin)
        admin_data = question.to_admin_dict()
        assert "correct_answer" in admin_data
        assert admin_data["correct_answer"] == 1
    
    def test_question_validation(self):
        """Test question data validation."""
        from game_modules.quiz.question_types import SingleChoiceQuestion
        from pydantic import ValidationError
        
        # Test valid question
        valid_data = {
            "id": "q1",
            "question": "Test question?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": 2,
            "points": 10
        }
        
        question = SingleChoiceQuestion(**valid_data)
        assert question.id == "q1"
        
        # Test invalid question - correct_answer out of range
        invalid_data = {
            "id": "q2",
            "question": "Test question?",
            "options": ["A", "B"],
            "correct_answer": 5,  # Out of range
            "points": 10
        }
        
        with pytest.raises(ValidationError):
            SingleChoiceQuestion(**invalid_data)
        
        # Test invalid question - missing required fields
        incomplete_data = {
            "id": "q3",
            "question": "Test question?"
            # Missing options, correct_answer, points
        }
        
        with pytest.raises(ValidationError):
            SingleChoiceQuestion(**incomplete_data)


class TestGameModuleIntegration:
    """Test integration between different game modules."""
    
    def test_module_switching(self):
        """Test switching between different game modules."""
        from game_modules.quiz.quiz_module import QuizModule
        from game_modules.family_feud.family_feud_module import FamilyFeudModule
        
        # Create quiz game
        quiz_data = {
            "id": "quiz-1",
            "type": "quiz",
            "title": "Quiz Game",
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
        
        quiz = QuizModule(quiz_data)
        assert quiz.game_type == "quiz"
        
        # Create family feud game
        ff_data = {
            "id": "ff-1",
            "type": "family_feud",
            "title": "Family Feud Game",
            "questions": [
                {
                    "id": "ff1",
                    "question": "Name something",
                    "answers": [{"text": "Answer", "points": 50}]
                }
            ]
        }
        
        ff_game = FamilyFeudModule(ff_data)
        assert ff_game.game_type == "family_feud"
        
        # Test they have different interfaces
        assert hasattr(quiz, 'calculate_score')
        assert hasattr(ff_game, 'add_team_points')
    
    def test_game_module_factory(self):
        """Test game module factory pattern."""
        
        def create_game_module(game_data):
            """Factory function to create appropriate game module."""
            game_type = game_data.get("type", "quiz")
            
            if game_type == "quiz":
                from game_modules.quiz.quiz_module import QuizModule
                return QuizModule(game_data)
            elif game_type == "family_feud":
                from game_modules.family_feud.family_feud_module import FamilyFeudModule
                return FamilyFeudModule(game_data)
            else:
                raise ValueError(f"Unknown game type: {game_type}")
        
        # Test quiz creation
        quiz_data = {"id": "test", "type": "quiz", "questions": []}
        quiz = create_game_module(quiz_data)
        assert quiz.__class__.__name__ == "QuizModule"
        
        # Test family feud creation
        ff_data = {"id": "test", "type": "family_feud", "questions": []}
        ff_game = create_game_module(ff_data)
        assert ff_game.__class__.__name__ == "FamilyFeudModule"
        
        # Test unknown type
        with pytest.raises(ValueError):
            create_game_module({"id": "test", "type": "unknown"})


class TestGameModulePerformance:
    """Test game module performance characteristics."""
    
    @pytest.mark.performance
    def test_large_quiz_performance(self):
        """Test performance with large number of questions."""
        from game_modules.quiz.quiz_module import QuizModule
        import time
        
        # Create quiz with many questions
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
        
        quiz_data = {
            "id": "large-quiz",
            "title": "Large Quiz",
            "questions": questions
        }
        
        # Test initialization time
        start_time = time.time()
        quiz = QuizModule(quiz_data)
        init_time = time.time() - start_time
        
        assert init_time < 1.0  # Should initialize in less than 1 second
        assert len(quiz.questions) == 1000
        
        # Test scoring performance
        answers = [{"question_id": f"q{i}", "answer": i % 4} for i in range(1000)]
        
        start_time = time.time()
        score = quiz.calculate_score(answers)
        scoring_time = time.time() - start_time
        
        assert scoring_time < 0.5  # Should score in less than 0.5 seconds
        assert score["total_score"] == 10000  # All correct
    
    @pytest.mark.performance
    def test_concurrent_answer_processing(self):
        """Test concurrent answer processing."""
        from game_modules.quiz.quiz_module import QuizModule
        import asyncio
        
        quiz_data = {
            "id": "concurrent-test",
            "title": "Concurrent Test",
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "question": "Test?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "points": 10
                }
            ]
        }
        
        quiz = QuizModule(quiz_data)
        
        async def process_answer(user_id):
            """Simulate processing answer from user."""
            return quiz.process_answer("q1", 0, user_id)
        
        async def test_concurrent():
            # Simulate 100 users answering simultaneously
            tasks = [process_answer(f"user_{i}") for i in range(100)]
            results = await asyncio.gather(*tasks)
            return results
        
        # Run the concurrent test
        results = asyncio.run(test_concurrent())
        
        # All should succeed
        assert len(results) == 100
        assert all(result["correct"] for result in results)


class TestGameModuleErrorHandling:
    """Test error handling in game modules."""
    
    def test_invalid_question_handling(self):
        """Test handling of invalid questions."""
        from game_modules.quiz.quiz_module import QuizModule
        
        # Quiz with invalid question
        invalid_quiz_data = {
            "id": "invalid-quiz",
            "title": "Invalid Quiz",
            "questions": [
                {
                    "id": "q1",
                    "type": "invalid_type",  # Invalid type
                    "question": "Test?",
                    "points": 10
                }
            ]
        }
        
        with pytest.raises(ValueError):
            QuizModule(invalid_quiz_data)
    
    def test_missing_question_data(self):
        """Test handling of missing question data."""
        from game_modules.quiz.quiz_module import QuizModule
        
        quiz_data = {
            "id": "test-quiz",
            "title": "Test Quiz",
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
        
        quiz = QuizModule(quiz_data)
        
        # Test answering non-existent question
        result = quiz.process_answer("non_existent", 0, "user1")
        assert result["error"] == "Question not found"
        
        # Test invalid answer format
        result = quiz.process_answer("q1", "invalid", "user1")
        assert result["correct"] == False
    
    def test_game_state_corruption_recovery(self):
        """Test recovery from corrupted game state."""
        from game_modules.quiz.quiz_module import QuizModule
        
        quiz_data = {
            "id": "recovery-test",
            "title": "Recovery Test",
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
        
        quiz = QuizModule(quiz_data)
        
        # Simulate state corruption
        quiz.current_question_index = 999  # Invalid index
        
        # Should handle gracefully
        next_question = quiz.get_next_question()
        assert next_question is None  # No more questions
        
        # Should reset to valid state
        quiz.reset_game_state()
        assert quiz.current_question_index == 0