"""
Code Generation Service for Session Manager
Generates unique game codes, manages expiration, and handles validation
"""

import random
import string
import hashlib
import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
import json

from ..services.redis_service import redis_service
from ..config import settings

logger = structlog.get_logger()


class CodeGeneratorService:
    """Service for generating and managing game codes"""
    
    # Code generation settings
    DEFAULT_CODE_LENGTH = 6
    MIN_CODE_LENGTH = 4
    MAX_CODE_LENGTH = 10
    DEFAULT_EXPIRY_MINUTES = 60
    MAX_EXPIRY_MINUTES = 1440  # 24 hours
    
    # Character sets for code generation
    ALPHANUMERIC = string.ascii_uppercase + string.digits
    CONSONANTS = "BCDFGHJKLMNPQRSTVWXYZ"
    VOWELS = "AEIOU"
    NUMBERS = "23456789"  # Exclude 0, 1 to avoid confusion
    
    # Excluded patterns to avoid offensive words
    EXCLUDED_PATTERNS = [
        "FUCK", "SHIT", "DAMN", "HELL", "NAZI", "KILL", "DIE", "SEX", "ASS"
    ]
    
    def __init__(self):
        self.redis = redis_service
    
    async def generate_session_code(
        self,
        session_id: uuid.UUID,
        length: int = DEFAULT_CODE_LENGTH,
        expires_in_minutes: int = DEFAULT_EXPIRY_MINUTES,
        max_uses: Optional[int] = None,
        description: Optional[str] = None,
        readable: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a unique session code
        
        Args:
            session_id: Session UUID
            length: Code length (4-10 characters)
            expires_in_minutes: Expiration time in minutes
            max_uses: Maximum number of uses (None for unlimited)
            description: Optional description
            readable: Use readable character set (avoid confusing characters)
            
        Returns:
            Dict with code information
        """
        # Validate parameters
        length = max(self.MIN_CODE_LENGTH, min(self.MAX_CODE_LENGTH, length))
        expires_in_minutes = min(self.MAX_EXPIRY_MINUTES, max(5, expires_in_minutes))
        
        # Generate unique code
        code = await self._generate_unique_code(length, readable)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        # Create code data
        code_data = {
            "code": code,
            "session_id": str(session_id),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "max_uses": max_uses,
            "current_uses": 0,
            "description": description,
            "generation_method": "readable" if readable else "alphanumeric"
        }
        
        # Store in Redis
        await self._store_code(code, code_data, expires_in_minutes)
        
        # Store reverse mapping (session_id -> codes)
        await self._add_session_code_mapping(session_id, code)
        
        logger.info(
            "Generated session code",
            code=code,
            session_id=str(session_id),
            expires_at=expires_at.isoformat()
        )
        
        return code_data
    
    async def _generate_unique_code(self, length: int, readable: bool = True) -> str:
        """Generate a unique code that doesn't exist in Redis"""
        max_attempts = 100
        
        for attempt in range(max_attempts):
            if readable:
                code = self._generate_readable_code(length)
            else:
                code = self._generate_alphanumeric_code(length)
            
            # Check if code contains excluded patterns
            if any(pattern in code for pattern in self.EXCLUDED_PATTERNS):
                continue
            
            # Check if code already exists
            if not await self._code_exists(code):
                return code
        
        # Fallback to UUID-based code if all attempts failed
        logger.warning(f"Failed to generate unique code after {max_attempts} attempts, using UUID fallback")
        return self._generate_uuid_based_code(length)
    
    def _generate_readable_code(self, length: int) -> str:
        """Generate a readable code using consonants, vowels, and numbers"""
        code = ""
        
        # Pattern: consonant-vowel-consonant-number for better readability
        for i in range(length):
            if i % 4 == 0:  # Consonant
                code += random.choice(self.CONSONANTS)
            elif i % 4 == 1:  # Vowel
                code += random.choice(self.VOWELS)
            elif i % 4 == 2:  # Consonant
                code += random.choice(self.CONSONANTS)
            else:  # Number
                code += random.choice(self.NUMBERS)
        
        return code
    
    def _generate_alphanumeric_code(self, length: int) -> str:
        """Generate a standard alphanumeric code"""
        return ''.join(random.choices(self.ALPHANUMERIC, k=length))
    
    def _generate_uuid_based_code(self, length: int) -> str:
        """Generate a code based on UUID (fallback method)"""
        uuid_str = str(uuid.uuid4()).replace('-', '').upper()
        return uuid_str[:length]
    
    async def _code_exists(self, code: str) -> bool:
        """Check if code already exists in Redis"""
        try:
            key = f"game_code:{code}"
            return await self.redis.redis_client.exists(key)
        except Exception as e:
            logger.error("Error checking code existence", code=code, error=str(e))
            return True  # Assume exists to be safe
    
    async def _store_code(self, code: str, code_data: Dict[str, Any], expires_in_minutes: int):
        """Store code data in Redis"""
        try:
            key = f"game_code:{code}"
            
            # Store code data
            await self.redis.redis_client.hset(key, mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in code_data.items()
            })
            
            # Set expiration
            await self.redis.redis_client.expire(key, expires_in_minutes * 60)
            
        except Exception as e:
            logger.error("Error storing code", code=code, error=str(e))
            raise
    
    async def _add_session_code_mapping(self, session_id: uuid.UUID, code: str):
        """Add code to session's code list"""
        try:
            key = f"session_codes:{session_id}"
            await self.redis.redis_client.sadd(key, code)
            await self.redis.redis_client.expire(key, self.MAX_EXPIRY_MINUTES * 60)
        except Exception as e:
            logger.error("Error adding session code mapping", session_id=str(session_id), code=code, error=str(e))
    
    async def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate a game code
        
        Args:
            code: Game code to validate
            
        Returns:
            Dict with validation result and code data
        """
        code = code.strip().upper()
        
        try:
            key = f"game_code:{code}"
            code_data = await self.redis.redis_client.hgetall(key)
            
            if not code_data:
                return {
                    "valid": False,
                    "error_code": "CODE_NOT_FOUND",
                    "error_message": "Game code not found"
                }
            
            # Parse code data
            parsed_data = {}
            for k, v in code_data.items():
                try:
                    parsed_data[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    parsed_data[k] = v
            
            # Check status
            if parsed_data.get("status") != "active":
                return {
                    "valid": False,
                    "error_code": "CODE_DISABLED",
                    "error_message": "Game code has been disabled"
                }
            
            # Check expiration
            expires_at_str = parsed_data.get("expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.utcnow() > expires_at:
                    # Mark as expired
                    await self._update_code_status(code, "expired")
                    return {
                        "valid": False,
                        "error_code": "CODE_EXPIRED",
                        "error_message": "Game code has expired"
                    }
            
            # Check usage limits
            max_uses = parsed_data.get("max_uses")
            current_uses = int(parsed_data.get("current_uses", 0))
            
            if max_uses is not None and current_uses >= max_uses:
                return {
                    "valid": False,
                    "error_code": "CODE_MAX_USES",
                    "error_message": "Game code has reached maximum uses"
                }
            
            return {
                "valid": True,
                "code_data": parsed_data
            }
            
        except Exception as e:
            logger.error("Error validating code", code=code, error=str(e))
            return {
                "valid": False,
                "error_code": "SYSTEM_ERROR",
                "error_message": "System error during validation"
            }
    
    async def use_code(self, code: str, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Use a game code (increment usage counter)
        
        Args:
            code: Game code to use
            user_id: User ID using the code
            
        Returns:
            Dict with usage result
        """
        code = code.strip().upper()
        
        try:
            # First validate the code
            validation_result = await self.validate_code(code)
            
            if not validation_result["valid"]:
                return validation_result
            
            # Increment usage counter
            key = f"game_code:{code}"
            current_uses = await self.redis.redis_client.hincrby(key, "current_uses", 1)
            
            # Log usage
            await self._log_code_usage(code, user_id, "used")
            
            logger.info(
                "Code used",
                code=code,
                user_id=str(user_id),
                current_uses=current_uses
            )
            
            return {
                "success": True,
                "current_uses": current_uses,
                "code_data": validation_result["code_data"]
            }
            
        except Exception as e:
            logger.error("Error using code", code=code, user_id=str(user_id), error=str(e))
            return {
                "success": False,
                "error_code": "SYSTEM_ERROR",
                "error_message": "System error during code usage"
            }
    
    async def _update_code_status(self, code: str, status: str):
        """Update code status"""
        try:
            key = f"game_code:{code}"
            await self.redis.redis_client.hset(key, "status", status)
        except Exception as e:
            logger.error("Error updating code status", code=code, status=status, error=str(e))
    
    async def _log_code_usage(self, code: str, user_id: uuid.UUID, action: str):
        """Log code usage for analytics"""
        try:
            log_key = f"code_usage_log:{code}"
            log_entry = {
                "user_id": str(user_id),
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis.redis_client.lpush(log_key, json.dumps(log_entry))
            await self.redis.redis_client.ltrim(log_key, 0, 99)  # Keep last 100 entries
            await self.redis.redis_client.expire(log_key, 86400 * 7)  # 7 days
            
        except Exception as e:
            logger.error("Error logging code usage", code=code, error=str(e))
    
    async def get_session_codes(self, session_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all codes for a session"""
        try:
            key = f"session_codes:{session_id}"
            codes = await self.redis.redis_client.smembers(key)
            
            code_list = []
            for code in codes:
                validation_result = await self.validate_code(code)
                if validation_result["valid"]:
                    code_list.append(validation_result["code_data"])
            
            return code_list
            
        except Exception as e:
            logger.error("Error getting session codes", session_id=str(session_id), error=str(e))
            return []
    
    async def deactivate_code(self, code: str) -> bool:
        """Deactivate a game code"""
        try:
            await self._update_code_status(code, "disabled")
            logger.info("Code deactivated", code=code)
            return True
        except Exception as e:
            logger.error("Error deactivating code", code=code, error=str(e))
            return False
    
    async def get_code_stats(self, code: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a code"""
        try:
            validation_result = await self.validate_code(code)
            if not validation_result["valid"]:
                return None
            
            code_data = validation_result["code_data"]
            
            # Get usage log
            log_key = f"code_usage_log:{code}"
            usage_log = await self.redis.redis_client.lrange(log_key, 0, -1)
            
            usage_entries = []
            for entry in usage_log:
                try:
                    usage_entries.append(json.loads(entry))
                except json.JSONDecodeError:
                    continue
            
            return {
                "code": code,
                "code_data": code_data,
                "usage_history": usage_entries,
                "total_uses": len(usage_entries)
            }
            
        except Exception as e:
            logger.error("Error getting code stats", code=code, error=str(e))
            return None
    
    async def cleanup_expired_codes(self) -> int:
        """Clean up expired codes (maintenance task)"""
        try:
            # This would typically be run as a background task
            # Redis TTL will handle most cleanup automatically
            # This method can be used for additional cleanup logic
            
            pattern = "game_code:*"
            keys = await self.redis.redis_client.keys(pattern)
            
            expired_count = 0
            for key in keys:
                ttl = await self.redis.redis_client.ttl(key)
                if ttl == -1:  # No expiration set
                    # Check if code is expired based on expires_at field
                    code_data = await self.redis.redis_client.hgetall(key)
                    if code_data and "expires_at" in code_data:
                        try:
                            expires_at = datetime.fromisoformat(code_data["expires_at"])
                            if datetime.utcnow() > expires_at:
                                await self.redis.redis_client.delete(key)
                                expired_count += 1
                        except (ValueError, TypeError):
                            continue
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired codes")
            
            return expired_count
            
        except Exception as e:
            logger.error("Error during code cleanup", error=str(e))
            return 0


# Global code generator service instance
code_generator = CodeGeneratorService()