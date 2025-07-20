"""
Shared Exceptions Package
Common exceptions used across all services
"""

class GameSystemException(Exception):
    """Base exception for the game system"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class UserNotFoundException(GameSystemException):
    """User not found exception"""
    def __init__(self, user_id: str):
        super().__init__(f"User with ID {user_id} not found", "USER_NOT_FOUND")


class SessionNotFoundException(GameSystemException):
    """Session not found exception"""
    def __init__(self, session_id: str):
        super().__init__(f"Session with ID {session_id} not found", "SESSION_NOT_FOUND")


class GameNotFoundException(GameSystemException):
    """Game not found exception"""
    def __init__(self, game_id: str):
        super().__init__(f"Game with ID {game_id} not found", "GAME_NOT_FOUND")


class InvalidGameStateException(GameSystemException):
    """Invalid game state exception"""
    def __init__(self, current_state: str, expected_state: str):
        super().__init__(
            f"Invalid game state. Current: {current_state}, Expected: {expected_state}",
            "INVALID_GAME_STATE"
        )


class PlayerNotInSessionException(GameSystemException):
    """Player not in session exception"""
    def __init__(self, user_id: str, session_id: str):
        super().__init__(
            f"Player {user_id} is not in session {session_id}",
            "PLAYER_NOT_IN_SESSION"
        )


class SessionFullException(GameSystemException):
    """Session is full exception"""
    def __init__(self, session_id: str, max_players: int):
        super().__init__(
            f"Session {session_id} is full (max {max_players} players)",
            "SESSION_FULL"
        )


class UnauthorizedException(GameSystemException):
    """Unauthorized access exception"""
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, "UNAUTHORIZED")


class ValidationException(GameSystemException):
    """Data validation exception"""
    def __init__(self, field: str, message: str):
        super().__init__(f"Validation error for {field}: {message}", "VALIDATION_ERROR")


class ServiceUnavailableException(GameSystemException):
    """Service unavailable exception"""
    def __init__(self, service_name: str):
        super().__init__(f"Service {service_name} is unavailable", "SERVICE_UNAVAILABLE")