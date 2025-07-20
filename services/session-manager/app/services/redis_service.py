"""
Session Manager Service - Redis Service
"""

import redis.asyncio as redis
import json
import structlog
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta

from ..config import settings

logger = structlog.get_logger()


class RedisService:
    """Redis service for session management"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            if not self.redis_client:
                return False
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    # Session Management
    async def create_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Create a new session in Redis"""
        try:
            key = f"session:{session_id}"
            data = {
                **session_data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.hset(key, mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in data.items()
            })
            
            # Set expiration
            await self.redis_client.expire(key, settings.SESSION_EXPIRE_SECONDS)
            
            logger.info("Session created in Redis", session_id=session_id)
            return True
        
        except Exception as e:
            logger.error("Failed to create session in Redis", session_id=session_id, error=str(e))
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        try:
            key = f"session:{session_id}"
            data = await self.redis_client.hgetall(key)
            
            if not data:
                return None
            
            # Parse JSON fields
            parsed_data = {}
            for k, v in data.items():
                try:
                    parsed_data[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    parsed_data[k] = v
            
            return parsed_data
        
        except Exception as e:
            logger.error("Failed to get session from Redis", session_id=session_id, error=str(e))
            return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data in Redis"""
        try:
            key = f"session:{session_id}"
            
            # Check if session exists
            if not await self.redis_client.exists(key):
                return False
            
            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            # Update fields
            await self.redis_client.hset(key, mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in updates.items()
            })
            
            logger.info("Session updated in Redis", session_id=session_id)
            return True
        
        except Exception as e:
            logger.error("Failed to update session in Redis", session_id=session_id, error=str(e))
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        try:
            key = f"session:{session_id}"
            result = await self.redis_client.delete(key)
            
            if result:
                logger.info("Session deleted from Redis", session_id=session_id)
            
            return bool(result)
        
        except Exception as e:
            logger.error("Failed to delete session from Redis", session_id=session_id, error=str(e))
            return False
    
    # Participant Management
    async def add_participant(self, session_id: str, participant_id: str, participant_data: Dict[str, Any]) -> bool:
        """Add participant to session"""
        try:
            key = f"session:{session_id}:participants"
            data = {
                **participant_data,
                "joined_at": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.hset(key, participant_id, json.dumps(data))
            await self.redis_client.expire(key, settings.SESSION_EXPIRE_SECONDS)
            
            logger.info("Participant added to session", session_id=session_id, participant_id=participant_id)
            return True
        
        except Exception as e:
            logger.error("Failed to add participant", session_id=session_id, participant_id=participant_id, error=str(e))
            return False
    
    async def get_participants(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all participants for a session"""
        try:
            key = f"session:{session_id}:participants"
            data = await self.redis_client.hgetall(key)
            
            participants = {}
            for participant_id, participant_data in data.items():
                try:
                    participants[participant_id] = json.loads(participant_data)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse participant data", participant_id=participant_id)
            
            return participants
        
        except Exception as e:
            logger.error("Failed to get participants", session_id=session_id, error=str(e))
            return {}
    
    async def update_participant(self, session_id: str, participant_id: str, updates: Dict[str, Any]) -> bool:
        """Update participant data"""
        try:
            key = f"session:{session_id}:participants"
            
            # Get current data
            current_data = await self.redis_client.hget(key, participant_id)
            if not current_data:
                return False
            
            participant_data = json.loads(current_data)
            participant_data.update(updates)
            participant_data["last_seen"] = datetime.utcnow().isoformat()
            
            await self.redis_client.hset(key, participant_id, json.dumps(participant_data))
            
            return True
        
        except Exception as e:
            logger.error("Failed to update participant", session_id=session_id, participant_id=participant_id, error=str(e))
            return False
    
    async def remove_participant(self, session_id: str, participant_id: str) -> bool:
        """Remove participant from session"""
        try:
            key = f"session:{session_id}:participants"
            result = await self.redis_client.hdel(key, participant_id)
            
            if result:
                logger.info("Participant removed from session", session_id=session_id, participant_id=participant_id)
            
            return bool(result)
        
        except Exception as e:
            logger.error("Failed to remove participant", session_id=session_id, participant_id=participant_id, error=str(e))
            return False
    
    # Real-time Updates
    async def publish_update(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish real-time update"""
        try:
            await self.redis_client.publish(channel, json.dumps(message))
            return True
        
        except Exception as e:
            logger.error("Failed to publish update", channel=channel, error=str(e))
            return False
    
    async def subscribe_to_updates(self, channels: List[str]):
        """Subscribe to real-time updates"""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(*channels)
            return pubsub
        
        except Exception as e:
            logger.error("Failed to subscribe to updates", channels=channels, error=str(e))
            return None
    
    # Statistics
    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        try:
            keys = await self.redis_client.keys("session:*")
            # Filter out participant keys
            session_keys = [k for k in keys if not k.endswith(":participants")]
            return len(session_keys)
        
        except Exception as e:
            logger.error("Failed to get active sessions count", error=str(e))
            return 0
    
    async def get_connected_players_count(self) -> int:
        """Get count of connected players"""
        try:
            count = 0
            participant_keys = await self.redis_client.keys("session:*:participants")
            
            for key in participant_keys:
                participants = await self.redis_client.hgetall(key)
                for participant_data in participants.values():
                    try:
                        data = json.loads(participant_data)
                        if data.get("is_connected", False):
                            count += 1
                    except json.JSONDecodeError:
                        continue
            
            return count
        
        except Exception as e:
            logger.error("Failed to get connected players count", error=str(e))
            return 0


# Global Redis service instance
redis_service = RedisService()