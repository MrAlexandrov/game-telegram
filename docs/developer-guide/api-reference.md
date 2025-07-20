# API Reference Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Game Engine API](#game-engine-api)
5. [Session Manager API](#session-manager-api)
6. [User Manager API](#user-manager-api)
7. [Analytics Service API](#analytics-service-api)
8. [Notification Service API](#notification-service-api)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)
11. [WebSocket API](#websocket-api)
12. [SDK Examples](#sdk-examples)

## Overview

The Game Telegram System provides a comprehensive REST API for managing interactive games, sessions, users, and analytics. All APIs follow RESTful principles and return JSON responses.

### Base URLs

| Service | Base URL | Port |
|---------|----------|------|
| Game Engine | `http://localhost:8001` | 8001 |
| Session Manager | `http://localhost:8002` | 8002 |
| User Manager | `http://localhost:8003` | 8003 |
| Analytics Service | `http://localhost:8004` | 8004 |
| Notification Service | `http://localhost:8005` | 8005 |

### API Versioning

All APIs are versioned using URL path versioning:
```
/api/v1/endpoint
```

Current version: `v1`

## Authentication

### API Key Authentication

Most endpoints require API key authentication via header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Bot Token Authentication

Bot-specific endpoints use Telegram bot tokens:

```http
X-Bot-Token: YOUR_BOT_TOKEN
```

### Admin Authentication

Admin endpoints require additional admin token:

```http
X-Admin-Token: YOUR_ADMIN_TOKEN
```

## Common Patterns

### Request Format

All POST/PUT requests should include:

```http
Content-Type: application/json
Accept: application/json
```

### Response Format

All responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "title",
      "issue": "required"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Pagination

List endpoints support pagination:

```http
GET /api/v1/games?page=1&limit=20&sort=created_at&order=desc
```

Response includes pagination metadata:

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## Game Engine API

### Games

#### Create Game

```http
POST /api/v1/games
```

**Request Body:**

```json
{
  "title": "History Quiz",
  "description": "A quiz about world history",
  "type": "quiz",
  "category": "education",
  "settings": {
    "time_limit": 30,
    "max_players": 20,
    "show_correct_answers": true,
    "shuffle_questions": true,
    "shuffle_options": true
  },
  "questions": [
    {
      "id": "q1",
      "type": "single_choice",
      "question": "When was the Berlin Wall built?",
      "options": ["1959", "1961", "1963", "1965"],
      "correct_answer": 1,
      "points": 10,
      "time_limit": 25,
      "explanation": "The Berlin Wall was built in 1961 to separate East and West Berlin."
    }
  ],
  "tags": ["history", "world", "quiz"]
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "game_123456789",
    "title": "History Quiz",
    "description": "A quiz about world history",
    "type": "quiz",
    "category": "education",
    "created_by": "admin_user_123",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "settings": { ... },
    "questions": [ ... ],
    "tags": ["history", "world", "quiz"],
    "stats": {
      "total_questions": 1,
      "estimated_duration": 30
    }
  }
}
```

#### Get Game

```http
GET /api/v1/games/{game_id}
```

**Parameters:**
- `game_id` (string): Unique game identifier
- `include_answers` (boolean, optional): Include correct answers (admin only)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "game_123456789",
    "title": "History Quiz",
    "description": "A quiz about world history",
    "type": "quiz",
    "questions": [
      {
        "id": "q1",
        "type": "single_choice",
        "question": "When was the Berlin Wall built?",
        "options": ["1959", "1961", "1963", "1965"],
        "points": 10,
        "time_limit": 25
      }
    ]
  }
}
```

#### List Games

```http
GET /api/v1/games
```

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 20, max: 100)
- `type` (string): Filter by game type
- `category` (string): Filter by category
- `tags` (string): Comma-separated tags
- `search` (string): Search in title and description
- `created_by` (string): Filter by creator
- `sort` (string): Sort field (created_at, title, popularity)
- `order` (string): Sort order (asc, desc)

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "game_123456789",
      "title": "History Quiz",
      "description": "A quiz about world history",
      "type": "quiz",
      "category": "education",
      "created_by": "admin_user_123",
      "created_at": "2024-01-01T12:00:00Z",
      "stats": {
        "total_questions": 10,
        "total_sessions": 25,
        "average_score": 75.5
      }
    }
  ],
  "pagination": { ... }
}
```

#### Update Game

```http
PUT /api/v1/games/{game_id}
```

**Request Body:** Same as create game, all fields optional

#### Delete Game

```http
DELETE /api/v1/games/{game_id}
```

**Response:**

```json
{
  "success": true,
  "message": "Game deleted successfully"
}
```

### Game Import/Export

#### Import Game Pack

```http
POST /api/v1/games/import
```

**Request:** Multipart form data with file upload

```http
Content-Type: multipart/form-data

file: [game_pack.json]
validate_only: false
overwrite_existing: false
```

**Response:**

```json
{
  "success": true,
  "data": {
    "imported_games": 5,
    "skipped_games": 2,
    "errors": [],
    "games": [
      {
        "id": "imported_game_1",
        "title": "Science Quiz",
        "status": "imported"
      }
    ]
  }
}
```

#### Export Game Pack

```http
POST /api/v1/games/export
```

**Request Body:**

```json
{
  "game_ids": ["game_1", "game_2"],
  "include_stats": false,
  "format": "json"
}
```

**Response:** File download or JSON data

### Game Validation

#### Validate Game

```http
POST /api/v1/games/validate
```

**Request Body:** Game object (same as create)

**Response:**

```json
{
  "success": true,
  "data": {
    "valid": true,
    "errors": [],
    "warnings": [
      {
        "field": "questions[0].time_limit",
        "message": "Time limit is very short (5s)"
      }
    ],
    "stats": {
      "total_questions": 10,
      "estimated_duration": 300
    }
  }
}
```

## Session Manager API

### Sessions

#### Create Session

```http
POST /api/v1/sessions
```

**Request Body:**

```json
{
  "game_id": "game_123456789",
  "admin_id": 123456789,
  "settings": {
    "max_players": 20,
    "auto_start": false,
    "auto_start_delay": 30,
    "allow_late_join": true,
    "show_leaderboard": true,
    "enable_chat": true
  },
  "access_control": {
    "type": "open",
    "password": null,
    "whitelist": [],
    "blacklist": []
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "ABC123",
    "game_id": "game_123456789",
    "admin_id": 123456789,
    "status": "waiting",
    "created_at": "2024-01-01T12:00:00Z",
    "settings": { ... },
    "access_control": { ... },
    "connection_info": {
      "join_code": "ABC123",
      "join_url": "https://t.me/player_bot?start=join_ABC123",
      "qr_code_url": "/api/v1/sessions/ABC123/qr"
    },
    "stats": {
      "players_count": 0,
      "max_players": 20
    }
  }
}
```

#### Get Session

```http
GET /api/v1/sessions/{session_id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "ABC123",
    "game_id": "game_123456789",
    "status": "in_progress",
    "current_question": 3,
    "total_questions": 10,
    "players": [
      {
        "user_id": 987654321,
        "username": "player1",
        "first_name": "John",
        "score": 75,
        "answered": true,
        "connected": true,
        "joined_at": "2024-01-01T12:05:00Z"
      }
    ],
    "game_state": {
      "question_start_time": "2024-01-01T12:15:00Z",
      "time_remaining": 25,
      "answers_received": 8
    }
  }
}
```

#### Join Session

```http
POST /api/v1/sessions/{session_id}/join
```

**Request Body:**

```json
{
  "user_id": 987654321,
  "username": "player1",
  "first_name": "John",
  "last_name": "Doe",
  "password": null
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "player_id": "player_987654321",
    "session_id": "ABC123",
    "position": 5,
    "game_info": {
      "title": "History Quiz",
      "total_questions": 10,
      "time_per_question": 30
    }
  }
}
```

#### Leave Session

```http
POST /api/v1/sessions/{session_id}/leave
```

**Request Body:**

```json
{
  "user_id": 987654321
}
```

#### Start Session

```http
POST /api/v1/sessions/{session_id}/start
```

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "ABC123",
    "status": "in_progress",
    "started_at": "2024-01-01T12:10:00Z",
    "first_question": {
      "id": "q1",
      "question": "When was the Berlin Wall built?",
      "options": ["1959", "1961", "1963", "1965"],
      "time_limit": 25
    }
  }
}
```

#### Submit Answer

```http
POST /api/v1/sessions/{session_id}/answer
```

**Request Body:**

```json
{
  "user_id": 987654321,
  "question_id": "q1",
  "answer": 1,
  "timestamp": "2024-01-01T12:10:15Z"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "answer_id": "answer_123",
    "correct": true,
    "points": 10,
    "time_bonus": 2,
    "total_points": 12,
    "player_score": 87,
    "rank": 3
  }
}
```

#### Get Session Results

```http
GET /api/v1/sessions/{session_id}/results
```

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "ABC123",
    "status": "completed",
    "completed_at": "2024-01-01T12:25:00Z",
    "duration": 900,
    "leaderboard": [
      {
        "rank": 1,
        "user_id": 987654321,
        "username": "player1",
        "first_name": "John",
        "score": 95,
        "correct_answers": 9,
        "total_questions": 10,
        "average_time": 18.5
      }
    ],
    "question_stats": [
      {
        "question_id": "q1",
        "correct_rate": 0.8,
        "average_time": 22.3,
        "most_common_answer": 1
      }
    ]
  }
}
```

### Session Management

#### Pause Session

```http
POST /api/v1/sessions/{session_id}/pause
```

#### Resume Session

```http
POST /api/v1/sessions/{session_id}/resume
```

#### End Session

```http
POST /api/v1/sessions/{session_id}/end
```

#### Kick Player

```http
POST /api/v1/sessions/{session_id}/kick
```

**Request Body:**

```json
{
  "user_id": 987654321,
  "reason": "Inappropriate behavior"
}
```

### QR Code Generation

#### Get QR Code

```http
GET /api/v1/sessions/{session_id}/qr
```

**Query Parameters:**
- `size` (integer): QR code size in pixels (default: 256)
- `format` (string): Image format (png, jpg, svg)

**Response:** Image file

## User Manager API

### Users

#### Create User

```http
POST /api/v1/users
```

**Request Body:**

```json
{
  "user_id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "language_code": "en",
  "is_bot": false,
  "is_premium": false
}
```

#### Get User

```http
GET /api/v1/users/{user_id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "user_id": 123456789,
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "language_code": "en",
    "created_at": "2024-01-01T10:00:00Z",
    "last_active": "2024-01-01T12:00:00Z",
    "stats": {
      "games_played": 25,
      "games_won": 8,
      "total_score": 1875,
      "average_score": 75.0,
      "best_score": 98,
      "achievements_count": 12
    }
  }
}
```

#### Update User

```http
PUT /api/v1/users/{user_id}
```

#### Delete User

```http
DELETE /api/v1/users/{user_id}
```

### User Statistics

#### Get User Stats

```http
GET /api/v1/users/{user_id}/stats
```

**Query Parameters:**
- `period` (string): Time period (day, week, month, year, all)
- `game_type` (string): Filter by game type

**Response:**

```json
{
  "success": true,
  "data": {
    "user_id": 123456789,
    "period": "month",
    "games_played": 15,
    "games_won": 5,
    "win_rate": 0.33,
    "total_score": 1125,
    "average_score": 75.0,
    "best_score": 95,
    "total_time_played": 7200,
    "favorite_categories": ["history", "science"],
    "achievements_earned": 3,
    "rank": {
      "global": 247,
      "monthly": 45
    }
  }
}
```

#### Get User Achievements

```http
GET /api/v1/users/{user_id}/achievements
```

**Response:**

```json
{
  "success": true,
  "data": {
    "total_achievements": 12,
    "earned_achievements": [
      {
        "id": "first_game",
        "name": "First Game",
        "description": "Play your first game",
        "icon": "🎮",
        "earned_at": "2024-01-01T10:30:00Z"
      }
    ],
    "available_achievements": [
      {
        "id": "speed_demon",
        "name": "Speed Demon",
        "description": "Answer 100 questions in under 5 seconds",
        "icon": "⚡",
        "progress": 45,
        "target": 100
      }
    ]
  }
}
```

## Analytics Service API

### Game Analytics

#### Get Game Analytics

```http
GET /api/v1/analytics/games/{game_id}
```

**Query Parameters:**
- `period` (string): Time period (day, week, month, year)
- `start_date` (string): Start date (ISO 8601)
- `end_date` (string): End date (ISO 8601)

**Response:**

```json
{
  "success": true,
  "data": {
    "game_id": "game_123456789",
    "period": "month",
    "total_sessions": 45,
    "total_players": 234,
    "unique_players": 189,
    "average_players_per_session": 5.2,
    "completion_rate": 0.87,
    "average_score": 74.5,
    "average_duration": 420,
    "question_analytics": [
      {
        "question_id": "q1",
        "correct_rate": 0.82,
        "average_time": 18.5,
        "skip_rate": 0.03,
        "difficulty_score": 0.18
      }
    ],
    "player_analytics": {
      "new_players": 45,
      "returning_players": 144,
      "retention_rate": 0.76
    }
  }
}
```

#### Get Leaderboard

```http
GET /api/v1/analytics/leaderboard/{game_id}
```

**Query Parameters:**
- `period` (string): Time period
- `limit` (integer): Number of entries (default: 10, max: 100)
- `offset` (integer): Offset for pagination

**Response:**

```json
{
  "success": true,
  "data": {
    "game_id": "game_123456789",
    "period": "month",
    "leaderboard": [
      {
        "rank": 1,
        "user_id": 123456789,
        "username": "top_player",
        "first_name": "Alice",
        "score": 98,
        "games_played": 8,
        "win_rate": 0.75,
        "average_score": 89.5
      }
    ],
    "total_players": 189,
    "user_rank": 15
  }
}
```

### System Analytics

#### Get System Stats

```http
GET /api/v1/analytics/system
```

**Response:**

```json
{
  "success": true,
  "data": {
    "total_games": 156,
    "total_sessions": 1247,
    "total_players": 3456,
    "active_sessions": 12,
    "online_players": 89,
    "popular_games": [
      {
        "game_id": "game_123",
        "title": "History Quiz",
        "sessions_count": 45
      }
    ],
    "performance": {
      "average_response_time": 145,
      "uptime": 0.999,
      "error_rate": 0.001
    }
  }
}
```

### Export Analytics

#### Export Data

```http
POST /api/v1/analytics/export
```

**Request Body:**

```json
{
  "type": "game_results",
  "game_id": "game_123456789",
  "format": "csv",
  "period": "month",
  "include_personal_data": false
}
```

**Response:** File download

## Notification Service API

### Send Notifications

#### Send Notification

```http
POST /api/v1/notifications
```

**Request Body:**

```json
{
  "type": "game_start",
  "recipients": [123456789, 987654321],
  "message": {
    "text": "Game is starting!",
    "parse_mode": "Markdown",
    "reply_markup": {
      "inline_keyboard": [
        [{"text": "Join Game", "url": "https://t.me/bot?start=join_ABC123"}]
      ]
    }
  },
  "schedule_at": null,
  "priority": "normal"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "notification_id": "notif_123456",
    "status": "sent",
    "recipients_count": 2,
    "sent_count": 2,
    "failed_count": 0,
    "sent_at": "2024-01-01T12:00:00Z"
  }
}
```

#### Get Notification Status

```http
GET /api/v1/notifications/{notification_id}
```

#### Broadcast Notification

```http
POST /api/v1/notifications/broadcast
```

**Request Body:**

```json
{
  "type": "system_announcement",
  "filter": {
    "active_players": true,
    "min_games_played": 5
  },
  "message": {
    "text": "System maintenance in 30 minutes"
  }
}
```

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid request data |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Service down |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_ERROR` | Authentication failed |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `RESOURCE_CONFLICT` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `GAME_NOT_FOUND` | Game not found |
| `SESSION_NOT_FOUND` | Session not found |
| `SESSION_FULL` | Session has reached max players |
| `SESSION_ENDED` | Session has already ended |
| `INVALID_ANSWER` | Answer format is invalid |
| `TIME_EXPIRED` | Answer submitted after time limit |

### Error Response Examples

#### Validation Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "title",
        "message": "Title is required"
      },
      {
        "field": "questions",
        "message": "At least one question is required"
      }
    ]
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Resource Not Found

```json
{
  "success": false,
  "error": {
    "code": "GAME_NOT_FOUND",
    "message": "Game with ID 'invalid_game_id' not found"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limiting

### Rate Limits

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Game Creation | 10 requests | 1 hour |
| Session Management | 100 requests | 1 hour |
| Answer Submission | 1000 requests | 1 hour |
| Analytics | 500 requests | 1 hour |
| General API | 1000 requests | 1 hour |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded Response

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 3600 seconds.",
    "retry_after": 3600
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8002/ws/sessions/ABC123');
```

### Authentication

Send authentication message after connection:

```json
{
  "type": "auth",
  "data": {
    "user_id": 123456789,
    "session_id": "ABC123",
    "token": "user_token_here"
  }
}
```

### Message Types

#### Game Events

```json
{
  "type": "game_start",
  "data": {
    "session_id": "ABC123",
    "started_at": "2024-01-01T12:00:00Z"
  }
}
```

```json
{
  "type": "question",
  "data": {
    "question_id": "q1",
    "question": "When was the Berlin Wall built?",
    "options": ["1959", "1961", "1963", "1965"],
    "time_limit": 25,
    "starts_at": "2024-01-01T12:00:00Z"
  }
}
```

```json
{
  "type": "question_end",
  "data": {
    "question_id": "q1",
    "correct_answer": 1,
    "explanation": "The Berlin Wall was built in 1961.",
    "leaderboard": [
      {
        "user_id": 123456789,
        "score": 85,
        "rank": 1
      }
    ]
  }
}
```

#### Player Events

```json
{
  "type": "player_joined",
  "data": {
    "user_id": 987654321,
    "username": "new_player",
    "players_count": 8
  }
}
```

```json
{
  "type": "player_left",
  "data": {
    "user_id": 987654321,
    "players_count": 7
  }
}
```

#### Answer Submission

```json
{
  "type": "submit_answer",
  "data": {
    "question_id": "q1",
    "answer": 1,
    "timestamp": "2024-01-01T12:00:15Z"
  }
}
```

#### Chat Messages

```json
{
  "type": "chat_message",
  "data": {
    "user_id": 123456789,
    "username": "player1",
    "message": "Good luck everyone!",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## SDK Examples

### JavaScript/Node.js

```javascript
const GameAPI = require('./game-api-sdk');

const client = new GameAPI({
  baseURL: 'http://localhost:8001',
  apiKey: 'your-api-key'
});

// Create a game
const game = await client.games.create({
  title: 'My Quiz',
  type: 'quiz',
  questions: [
    {
      id: 'q1',
      type: 'single_choice',
      question: 'What is 2+2?',
      options: ['3', '4', '5', '6'],
      correct_answer: 1,
      points: 10
    }
  ]
});

// Create a session
const session = await client.sessions.create({
  game_id: game.id,
  admin_id: 123456789,
  settings: {
    max_players: 10
  }
});

console.log(`Join code: ${session.connection_info.join_code}`);
```

### Python

```python
from game_api_sdk import GameAPIClient

client = GameAPIClient(
    base_url='http://localhost:8001',
    api_key='your-api-key'
)

# Create a game
game = client.games.create({
    'title': 'My Quiz',
    'type': 'quiz',
    'questions': [
        {
            'id': 'q1',
            'type': 'single_choice',
            'question': 'What is 2+2?',
            'options': ['3', '4', '5', '6'],
            'correct_answer': 1,
            'points': 10
        }
    ]
})

# Create a session
session = client.sessions.create({
    'game_id': game['id'],
    'admin_id': 123456789,
    'settings': {
        'max_players': 10
    }
})

print(f"Join code: {session['connection_info']['join_code']}")
```

### cURL Examples

#### Create Game

```bash
curl -X POST http://localhost:8001/api/v1/games \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "title": "History Quiz",
    "type": "quiz",
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
  }'
```

#### Create Session

```bash
curl -X POST http://localhost:8002/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "game_id": "game_123456789",
    "admin_id": 123456789,
    "settings": {
      "max_players": 10
    }
  }'
```

#### Join Session

```bash
curl -X POST http://localhost:8002/api/v1/sessions/ABC123/join \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 987654321,
    "username": "player1",
    "first_name": "John"
  }'
```

#### Submit Answer

```bash
curl -X POST http://localhost:8002/api/v1/sessions/ABC123/answer \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 987654321,
    "question_id": "q1",
    "answer": 1,
    "timestamp": "2024-01-01T12:00:15Z"
  }'
```

---

## Conclusion

This API reference provides comprehensive documentation for all endpoints in the Game Telegram System. For additional help:

- 📖 Check the [Developer Guide](../developer-guide/)
- 🐛 Report issues on [GitHub](https://github.com/your-repo/issues)
- 💬 Join our [Developer Community](https://t.me/game_dev_community)
- 📧 Contact support: [api-support@game-system.com](mailto:api-support@game-system.com)

**Happy coding! 🚀**
