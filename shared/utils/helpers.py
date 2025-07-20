"""
Shared Utility Functions
Common helper functions used across all services
"""

import random
import string
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import re


def generate_session_code(length: int = 6) -> str:
    """Generate a random session code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed


def sanitize_username(username: str) -> str:
    """Sanitize username by removing special characters"""
    if not username:
        return ""
    # Keep only alphanumeric characters, underscores, and hyphens
    return re.sub(r'[^a-zA-Z0-9_-]', '', username)


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s" if remaining_seconds else f"{minutes}m"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m" if remaining_minutes else f"{hours}h"


def calculate_score(base_points: int, time_taken: int, time_limit: int, bonus_multiplier: float = 1.0) -> int:
    """Calculate score based on points, time taken, and bonus multiplier"""
    if time_taken > time_limit:
        return 0
    
    # Time bonus: faster answers get more points
    time_bonus = max(0, (time_limit - time_taken) / time_limit * 0.5)
    final_score = int(base_points * (1 + time_bonus) * bonus_multiplier)
    
    return max(0, final_score)


def validate_telegram_data(data: Dict[str, Any], bot_token: str) -> bool:
    """Validate Telegram widget data"""
    # This is a simplified validation - in production, implement full Telegram validation
    required_fields = ['id', 'first_name', 'auth_date']
    return all(field in data for field in required_fields)


def clean_html(text: str) -> str:
    """Remove HTML tags from text"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_game_pack(json_data: str) -> Dict[str, Any]:
    """Parse and validate game pack JSON"""
    try:
        data = json.loads(json_data)
        if 'game_pack' not in data:
            raise ValueError("Invalid game pack format: missing 'game_pack' key")
        return data['game_pack']
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


def format_leaderboard(scores: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """Format leaderboard data"""
    sorted_scores = sorted(scores, key=lambda x: x.get('score', 0), reverse=True)
    
    leaderboard = []
    for i, player in enumerate(sorted_scores[:limit], 1):
        leaderboard.append({
            'rank': i,
            'user_id': player.get('user_id'),
            'username': player.get('username', 'Anonymous'),
            'score': player.get('score', 0),
            'correct_answers': player.get('correct_answers', 0),
            'total_answers': player.get('total_answers', 0)
        })
    
    return leaderboard


def is_valid_session_code(code: str) -> bool:
    """Validate session code format"""
    if not code or len(code) < 4 or len(code) > 10:
        return False
    return code.isalnum() and code.isupper()


def get_time_until_expiry(expires_at: datetime) -> Optional[int]:
    """Get seconds until expiry time"""
    if not expires_at:
        return None
    
    now = datetime.utcnow()
    if expires_at <= now:
        return 0
    
    return int((expires_at - now).total_seconds())


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only first few characters"""
    if len(data) <= visible_chars:
        return '*' * len(data)
    return data[:visible_chars] + '*' * (len(data) - visible_chars)