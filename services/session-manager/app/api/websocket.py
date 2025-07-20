"""
Session Manager API - WebSocket Endpoints
Real-time communication for game sessions
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set, Optional
import structlog
import json
import uuid
from datetime import datetime

from ..services.redis_service import redis_service

logger = structlog.get_logger()
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Active connections: session_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Connection metadata: websocket -> connection info
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: Optional[str] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Add to session connections
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        
        # Store connection metadata
        self.connection_info[websocket] = {
            "session_id": session_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        logger.info(
            "WebSocket connected",
            session_id=session_id,
            user_id=user_id,
            total_connections=len(self.active_connections.get(session_id, set()))
        )
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_info:
            session_id = self.connection_info[websocket]["session_id"]
            user_id = self.connection_info[websocket].get("user_id")
            
            # Remove from session connections
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
            
            # Remove metadata
            del self.connection_info[websocket]
            
            logger.info(
                "WebSocket disconnected",
                session_id=session_id,
                user_id=user_id,
                remaining_connections=len(self.active_connections.get(session_id, set()))
            )
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("Error sending personal message", error=str(e))
            self.disconnect(websocket)
    
    async def broadcast_to_session(self, message: dict, session_id: str, exclude: Optional[WebSocket] = None):
        """Broadcast a message to all connections in a session"""
        if session_id not in self.active_connections:
            return
        
        disconnected = set()
        for websocket in self.active_connections[session_id]:
            if websocket == exclude:
                continue
            
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error("Error broadcasting message", error=str(e))
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def send_to_user(self, message: dict, session_id: str, user_id: str):
        """Send a message to a specific user in a session"""
        if session_id not in self.active_connections:
            return
        
        for websocket in self.active_connections[session_id]:
            if websocket in self.connection_info:
                if self.connection_info[websocket].get("user_id") == user_id:
                    await self.send_personal_message(message, websocket)
    
    def get_session_connections_count(self, session_id: str) -> int:
        """Get number of active connections for a session"""
        return len(self.active_connections.get(session_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())


# Global connection manager
manager = ConnectionManager()


@router.websocket("/session/{session_id}")
async def websocket_session_endpoint(
    websocket: WebSocket,
    session_id: str,
    user_id: Optional[str] = Query(None),
    participant_id: Optional[str] = Query(None)
):
    """WebSocket endpoint for session real-time updates"""
    await manager.connect(websocket, session_id, user_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection_established",
            "data": {
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, websocket)
        
        # Subscribe to Redis updates for this session
        pubsub = await redis_service.subscribe_to_updates([f"session:{session_id}"])
        
        if pubsub:
            # Start listening for Redis messages in background
            import asyncio
            
            async def redis_listener():
                """Listen for Redis pub/sub messages"""
                try:
                    async for message in pubsub.listen():
                        if message["type"] == "message":
                            try:
                                data = json.loads(message["data"])
                                await manager.broadcast_to_session(data, session_id)
                            except json.JSONDecodeError:
                                logger.error("Invalid JSON in Redis message", data=message["data"])
                except Exception as e:
                    logger.error("Error in Redis listener", error=str(e))
            
            # Start Redis listener task
            redis_task = asyncio.create_task(redis_listener())
        
        # Handle incoming WebSocket messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_websocket_message(websocket, session_id, user_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }, websocket)
            except Exception as e:
                logger.error("Error handling WebSocket message", error=str(e))
                await manager.send_personal_message({
                    "type": "error",
                    "data": {"message": "Internal server error"}
                }, websocket)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket error", session_id=session_id, user_id=user_id, error=str(e))
    finally:
        manager.disconnect(websocket)
        
        # Clean up Redis subscription
        if 'pubsub' in locals() and pubsub:
            await pubsub.unsubscribe(f"session:{session_id}")
            await pubsub.close()
        
        # Cancel Redis listener task
        if 'redis_task' in locals():
            redis_task.cancel()


async def handle_websocket_message(
    websocket: WebSocket,
    session_id: str,
    user_id: Optional[str],
    message: dict
):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Handle ping/pong for connection health
        await manager.send_personal_message({
            "type": "pong",
            "data": {"timestamp": datetime.utcnow().isoformat()}
        }, websocket)
        
        # Update last ping time
        if websocket in manager.connection_info:
            manager.connection_info[websocket]["last_ping"] = datetime.utcnow()
    
    elif message_type == "join_session":
        # Handle session join notification
        data = message.get("data", {})
        await manager.broadcast_to_session({
            "type": "player_joined",
            "data": {
                "user_id": user_id,
                "display_name": data.get("display_name"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }, session_id, exclude=websocket)
    
    elif message_type == "leave_session":
        # Handle session leave notification
        data = message.get("data", {})
        await manager.broadcast_to_session({
            "type": "player_left",
            "data": {
                "user_id": user_id,
                "display_name": data.get("display_name"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }, session_id, exclude=websocket)
    
    elif message_type == "answer_submitted":
        # Handle answer submission notification
        data = message.get("data", {})
        await manager.broadcast_to_session({
            "type": "answer_submitted",
            "data": {
                "user_id": user_id,
                "question_id": data.get("question_id"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }, session_id, exclude=websocket)
    
    elif message_type == "typing":
        # Handle typing indicator
        data = message.get("data", {})
        await manager.broadcast_to_session({
            "type": "user_typing",
            "data": {
                "user_id": user_id,
                "display_name": data.get("display_name"),
                "is_typing": data.get("is_typing", True),
                "timestamp": datetime.utcnow().isoformat()
            }
        }, session_id, exclude=websocket)
    
    elif message_type == "request_session_status":
        # Handle session status request
        try:
            # Get session data from Redis
            session_data = await redis_service.get_session(session_id)
            participants = await redis_service.get_participants(session_id)
            
            await manager.send_personal_message({
                "type": "session_status",
                "data": {
                    "session": session_data,
                    "participants": participants,
                    "connections_count": manager.get_session_connections_count(session_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }, websocket)
        except Exception as e:
            logger.error("Error getting session status", error=str(e))
            await manager.send_personal_message({
                "type": "error",
                "data": {"message": "Failed to get session status"}
            }, websocket)
    
    else:
        # Unknown message type
        await manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Unknown message type: {message_type}"}
        }, websocket)


@router.get("/connections/stats")
async def get_connection_stats():
    """Get WebSocket connection statistics"""
    return {
        "total_connections": manager.get_total_connections(),
        "active_sessions": len(manager.active_connections),
        "sessions": {
            session_id: len(connections)
            for session_id, connections in manager.active_connections.items()
        }
    }


# Utility function to send updates via WebSocket
async def broadcast_session_update(session_id: str, update_type: str, data: dict):
    """Utility function to broadcast updates to a session"""
    message = {
        "type": update_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Broadcast via WebSocket
    await manager.broadcast_to_session(message, session_id)
    
    # Also publish to Redis for other instances
    await redis_service.publish_update(f"session:{session_id}", message)