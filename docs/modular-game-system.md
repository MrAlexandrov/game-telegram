# Modular Game System Documentation

## Overview

The modular game system provides a flexible, extensible architecture for implementing various types of interactive games in the Telegram bot platform. The system supports multiple game types with unified interfaces, comprehensive validation, and advanced scoring mechanisms.

## Architecture

### Core Components

1. **Base Game Module** (`game-modules/base/game_module.py`)
   - Abstract base class defining the unified interface
   - Provides common functionality and data structures
   - Handles data conversion between different formats

2. **Quiz Module** (`game-modules/quiz/`)
   - Comprehensive implementation supporting 7 question types
   - Advanced validation and scoring systems
   - Pydantic schemas for data validation

3. **Module Loader** (`services/game-engine/app/services/module_loader.py`)
   - Dynamic loading of game modules
   - Registry management and module metadata
   - Legacy module wrapper for backward compatibility

4. **Game Processor** (`services/game-engine/app/services/game_processor.py`)
   - Session management and question processing
   - Answer validation and result calculation
   - Game pack import and validation

## Supported Question Types

### 1. Multiple Choice Questions
```json
{
  "id": "mc_001",
  "type": "multiple_choice",
  "text": "Question text",
  "options": [
    {"text": "Option 1", "explanation": "Why this is correct/incorrect"},
    {"text": "Option 2", "explanation": "Explanation"}
  ],
  "correct_answers": ["Option 1"],
  "points": 10,
  "time_limit": 30,
  "shuffle_options": true
}
```

### 2. Text Input Questions
```json
{
  "id": "text_001",
  "type": "text_input",
  "text": "Question text",
  "correct_answers": ["Answer 1", "Answer 2", "Alternative"],
  "points": 10,
  "time_limit": 30,
  "validation_rules": {
    "case_sensitive": false,
    "exact_match": false,
    "allow_partial": true,
    "similarity_threshold": 0.8
  }
}
```

### 3. True/False Questions
```json
{
  "id": "tf_001",
  "type": "true_false",
  "text": "Statement to evaluate",
  "correct_answer": true,
  "points": 8,
  "time_limit": 15
}
```

### 4. Media Questions
```json
{
  "id": "media_001",
  "type": "media_question",
  "text": "What is shown in this image?",
  "media_content": {
    "media_type": "image",
    "media_url": "https://example.com/image.jpg",
    "thumbnail_url": "https://example.com/thumb.jpg",
    "description": "Image description"
  },
  "correct_answers": ["Expected answer"],
  "points": 15,
  "time_limit": 60
}
```

### 5. Validation Required Questions
```json
{
  "id": "validation_001",
  "type": "validation_required",
  "text": "Complex question requiring manual review",
  "validation_criteria": "Criteria for manual validation",
  "points": 25,
  "time_limit": 120,
  "requires_validation": true
}
```

### 6. Timed Questions (with bonus scoring)
```json
{
  "id": "timed_001",
  "type": "timed_question",
  "text": "Quick calculation question",
  "correct_answers": ["42"],
  "points": 20,
  "time_limit": 30,
  "time_bonus_multiplier": 2.0,
  "minimum_time_for_bonus": 10
}
```

### 7. Weighted Questions (difficulty-based scoring)
```json
{
  "id": "weighted_001",
  "type": "weighted_question",
  "text": "Advanced question",
  "correct_answers": ["Complex answer"],
  "points": 15,
  "time_limit": 45,
  "difficulty_level": "expert",
  "point_multipliers": {
    "easy": 1.0,
    "medium": 1.5,
    "hard": 2.0,
    "expert": 3.0
  }
}
```

## Game Pack Structure

### Complete Game Pack Format
```json
{
  "metadata": {
    "title": "Game Title",
    "description": "Game description",
    "version": "1.0.0",
    "author": "Author Name",
    "game_type": "quiz",
    "created_at": "2024-01-20T10:00:00Z",
    "category": "education",
    "difficulty": "medium",
    "estimated_duration": 900,
    "language": "ru",
    "tags": ["tag1", "tag2"]
  },
  "config": {
    "time_limit": 30,
    "points_per_question": 10,
    "shuffle_options": true,
    "allow_partial_credit": true,
    "case_sensitive": false,
    "show_correct_answers": true,
    "show_explanations": true,
    "time_bonus_enabled": true,
    "difficulty_scaling": true,
    "max_attempts": 1
  },
  "questions": [
    // Array of question objects
  ]
}
```

## Module Development

### Creating a New Game Module

1. **Inherit from GameModule**
```python
from game_modules.base.game_module import GameModule

class MyGameModule(GameModule):
    def __init__(self):
        super().__init__(
            game_type="my_game",
            name="My Game Module",
            version="1.0.0",
            description="Description of my game"
        )
```

2. **Implement Required Methods**
```python
async def process_question(self, question, session):
    # Process question for display
    pass

async def validate_answer(self, answer, question, **kwargs):
    # Validate player answer
    pass

async def calculate_score(self, answers, question):
    # Calculate scores for all players
    pass

async def get_results(self, session, all_answers):
    # Calculate final game results
    pass

def get_supported_question_types(self):
    # Return list of supported question types
    return ["my_question_type"]
```

3. **Add Configuration Schema**
```python
def get_config_schema(self):
    return {
        "type": "object",
        "properties": {
            "my_setting": {
                "type": "boolean",
                "default": True
            }
        }
    }
```

### Module Registration

Modules are automatically discovered and loaded by the ModuleLoader:

1. **Built-in modules**: Located in `services/game-engine/app/services/`
2. **External modules**: Located in `game-modules/` directory
3. **Module files**: Named `{module_name}_module.py` or `module.py`

## API Usage

### Initialize Module Loader
```python
from services.game_engine.app.services.module_loader import ModuleLoader

loader = ModuleLoader()
await loader.load_all_modules()
```

### Process Questions
```python
from services.game_engine.app.services.game_processor import GameProcessor

processor = GameProcessor(loader)
await processor.initialize()

result = await processor.process_question(
    session_id="session_001",
    question_id=uuid.uuid4(),
    game_type="quiz"
)
```

### Validate Answers
```python
validation_result = await processor.validate_answer(
    session_id="session_001",
    question_id="question_001",
    user_id="player_001",
    answer_text="Player's answer",
    time_taken=15.5
)
```

### Calculate Results
```python
results = await processor.calculate_session_results(
    session_id="session_001",
    include_detailed_stats=True
)
```

## Validation System

### Question Validation
- **Schema validation**: Using Pydantic models
- **Type-specific validation**: Each question type has custom rules
- **Content validation**: Checking required fields and formats

### Game Pack Validation
```python
validation_result = await processor.validate_game_pack(
    game_type="quiz",
    pack_data=game_pack_json
)

if validation_result["is_valid"]:
    # Create game from pack
    game_result = await processor.create_game_from_pack(
        pack_data=game_pack_json,
        created_by=admin_user_id
    )
```

## Error Handling

### Exception Types
- `ModuleError`: Base exception for module errors
- `ValidationError`: Data validation failures
- `ProcessingError`: Question/answer processing errors
- `GameProcessingError`: Game session processing errors

### Error Logging
All operations are logged using structured logging:
```python
logger.info("Question processed", 
           session_id=session_id,
           question_id=question_id,
           game_type=game_type)
```

## Testing

### Running Integration Tests
```bash
# Run all tests
python -m pytest tests/test_quiz_module_integration.py -v

# Run specific test
python -m pytest tests/test_quiz_module_integration.py::TestQuizModuleIntegration::test_question_validation -v
```

### Test Coverage
- Question type validation
- Answer processing and scoring
- Session lifecycle management
- Error handling scenarios
- Game pack loading and validation

## Performance Considerations

### Caching
- Question objects cached during session
- Validation results cached to avoid recomputation
- Module metadata cached for quick access

### Memory Management
- Session cleanup after completion
- Cache clearing on session finalization
- Inactive session cleanup (configurable)

### Scalability
- Async/await throughout for non-blocking operations
- Database connection pooling
- Stateless module design for horizontal scaling

## Configuration

### Module Configuration
Each module can define its own configuration schema and defaults:
```python
def get_default_config(self):
    return {
        "time_limit": 30,
        "points_per_question": 10,
        "shuffle_options": True
    }
```

### System Configuration
Global settings in `services/game-engine/app/config.py`:
- `GAME_MODULES_PATH`: Path to external modules
- Database connection settings
- Logging configuration

## Deployment

### Docker Support
The system is containerized with Docker:
```dockerfile
# Game Engine Service
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost/gamedb
REDIS_URL=redis://localhost:6379
GAME_MODULES_PATH=./game-modules
LOG_LEVEL=INFO
```

## Future Extensions

### Planned Features
1. **Real-time multiplayer**: WebSocket support for live games
2. **AI-powered questions**: Dynamic question generation
3. **Advanced analytics**: Player behavior analysis
4. **Mobile app integration**: Native mobile client support
5. **Tournament system**: Multi-round competitive games

### Module Ideas
1. **Puzzle games**: Logic puzzles and brain teasers
2. **Word games**: Crosswords, word association
3. **Math challenges**: Equation solving, geometry
4. **Code challenges**: Programming problems
5. **Trivia categories**: Specialized knowledge areas

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up database: `alembic upgrade head`
4. Run tests: `pytest`
5. Start development server: `uvicorn app.main:app --reload`

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints throughout
- Write comprehensive tests
- Document all public APIs
- Use structured logging

### Pull Request Process
1. Create feature branch
2. Implement changes with tests
3. Update documentation
4. Submit pull request
5. Code review and approval
6. Merge to main branch

## Support

For questions, issues, or contributions:
- Create GitHub issues for bugs
- Use discussions for questions
- Submit pull requests for features
- Check documentation for common issues

---

*This documentation covers the modular game system as implemented in version 2.0.0. For the latest updates, check the repository.*