# Demo Data and Examples

This directory contains sample data, example configurations, and demonstration scripts for the Game Telegram system.

## Contents

- [`sample-games/`](sample-games/) - Sample game configurations for different game types
- [`test-data/`](test-data/) - Test data for development and testing
- [`examples/`](examples/) - Code examples and usage demonstrations
- [`scripts/`](scripts/) - Demo and setup scripts
- [`postman/`](postman/) - Postman collection for API testing

## Quick Start

### 1. Load Sample Games

```bash
# Load sample quiz games
python scripts/load_sample_games.py --type quiz

# Load sample family feud games
python scripts/load_sample_games.py --type family_feud

# Load all sample games
python scripts/load_sample_games.py --all
```

### 2. Create Test Users

```bash
# Create test users for development
python scripts/create_test_users.py --count 10
```

### 3. Run Demo Session

```bash
# Start a demo game session
python scripts/demo_session.py --game-id sample_quiz_001
```

## Sample Games

### Quiz Games
- **General Knowledge Quiz** - Mixed topics with multiple choice questions
- **Science Quiz** - Science and technology focused questions
- **History Quiz** - Historical events and figures
- **Geography Quiz** - Countries, capitals, and landmarks

### Family Feud Games
- **Popular Answers** - Common survey-style questions
- **Food & Drinks** - Culinary themed questions
- **Entertainment** - Movies, music, and TV shows

### Word Games
- **Word Scramble** - Unscramble common words
- **Vocabulary Challenge** - Definition-based word guessing

## API Examples

See [`examples/api/`](examples/api/) for complete API usage examples:

- Game creation and management
- Session handling
- User authentication
- Analytics queries
- Bot interactions

## Testing Data

The [`test-data/`](test-data/) directory contains:

- User profiles for testing
- Game results and analytics data
- Session state examples
- Error scenarios for testing

## Development Tools

Use the provided scripts for development:

```bash
# Reset demo data
./scripts/reset_demo_data.sh

# Generate random test data
python scripts/generate_test_data.py

# Simulate game sessions
python scripts/simulate_sessions.py --sessions 50
```

For detailed usage instructions, see the individual README files in each subdirectory.