"""
Session Manager API - Sessions Endpoints
Handles session management, player connections, and game codes
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional, Dict, Any
import structlog
import uuid
from datetime import datetime

from ..models.database import get_db
from ..models import GameSession, SessionParticipant, PlayerAnswer, SessionEvent
from ..schemas import (
    SessionCreate, SessionResponse, SessionUpdate, ParticipantJoin,
    ParticipantResponse, SessionJoinResponse, SessionStatusResponse,
    AnswerSubmit, AnswerResponse, SessionEventCreate, SessionEventResponse
)
from ..services.code_generator import code_generator
from ..services.redis_service import redis_service
from ..game_schemas.connection import (
    ConnectionRequest, ConnectionResponse, ConnectionValidation,
    ConnectionValidationResponse, SessionInfoResponse, GameCodeCreate,
    GameCodeResponse, QRCodeRequest, QRCodeResponse, DeepLinkData,
    CONNECTION_ERROR_CODES
)

logger = structlog.get_logger()
router = APIRouter()


# Dependency to get current request info
async def get_request_info(request: Request) -> Dict[str, Any]:
    """Extract request information for logging and security"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "referer": request.headers.get("referer")
    }


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new game session"""
    try:
        # Generate unique session code
        code_data = await code_generator.generate_session_code(
            session_id=uuid.uuid4(),  # Temporary ID for code generation
            length=6,
            expires_in_minutes=1440,  # 24 hours
            description=f"Session: {session_data.title}"
        )
        
        # Create session in database
        session = GameSession(
            game_id=session_data.game_id,
            admin_id=session_data.admin_id,
            session_code=code_data["code"],
            title=session_data.title,
            description=session_data.description,
            max_players=session_data.max_players,
            allow_late_join=session_data.allow_late_join,
            question_time_limit=session_data.question_time_limit
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        # Update code with actual session ID
        await code_generator._store_code(
            code_data["code"],
            {**code_data, "session_id": str(session.id)},
            1440
        )
        
        # Store session in Redis for fast access
        await redis_service.create_session(str(session.id), {
            "session_code": session.session_code,
            "title": session.title,
            "status": session.status,
            "max_players": session.max_players,
            "current_players": 0
        })
        
        logger.info("Session created", session_id=str(session.id), code=session.session_code)
        return session
        
    except Exception as e:
        logger.error("Error creating session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get session by ID"""
    try:
        result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting session", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session"
        )


@router.get("/by-code/{game_code}", response_model=SessionInfoResponse)
async def get_session_by_code(
    game_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get session information by game code"""
    try:
        # Validate code first
        validation_result = await code_generator.validate_code(game_code)
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=validation_result.get("error_message", "Invalid game code")
            )
        
        # Get session from database
        session_id = uuid.UUID(validation_result["code_data"]["session_id"])
        result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get current player count
        participants_result = await db.execute(
            select(func.count(SessionParticipant.id))
            .where(and_(
                SessionParticipant.session_id == session.id,
                SessionParticipant.is_active == True
            ))
        )
        current_players = participants_result.scalar() or 0
        
        return SessionInfoResponse(
            session_id=session.id,
            session_code=session.session_code,
            title=session.title,
            description=session.description,
            game_type="quiz",  # TODO: Get from game service
            game_title=session.title,
            status=session.status,
            max_players=session.max_players,
            current_players=current_players,
            allow_late_join=session.allow_late_join,
            question_time_limit=session.question_time_limit,
            created_at=session.created_at,
            started_at=session.started_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting session by code", game_code=game_code, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session"
        )


@router.post("/{session_id}/join", response_model=ConnectionResponse)
async def join_session(
    session_id: uuid.UUID,
    connection_request: ConnectionRequest,
    request_info: Dict[str, Any] = Depends(get_request_info),
    db: AsyncSession = Depends(get_db)
):
    """Join a session using game code"""
    try:
        # Validate the game code
        validation_result = await code_generator.validate_code(connection_request.game_code)
        
        if not validation_result["valid"]:
            return ConnectionResponse(
                success=False,
                error_code=validation_result.get("error_code", "INVALID_CODE"),
                error_message=validation_result.get("error_message", "Invalid game code")
            )
        
        # Verify session ID matches code
        code_session_id = uuid.UUID(validation_result["code_data"]["session_id"])
        if code_session_id != session_id:
            return ConnectionResponse(
                success=False,
                error_code="SESSION_MISMATCH",
                error_message="Session ID does not match game code"
            )
        
        # Get session
        result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return ConnectionResponse(
                success=False,
                error_code="SESSION_NOT_FOUND",
                error_message="Session not found"
            )
        
        # Check session status
        if session.status not in ["waiting", "in_progress"]:
            error_codes = {
                "completed": "SESSION_ENDED",
                "cancelled": "SESSION_ENDED",
                "paused": "SESSION_NOT_STARTED"
            }
            return ConnectionResponse(
                success=False,
                error_code=error_codes.get(session.status, "SESSION_NOT_AVAILABLE"),
                error_message=f"Session is {session.status}"
            )
        
        # Check if user already joined
        existing_participant = await db.execute(
            select(SessionParticipant).where(and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.user_id == connection_request.user_id,
                SessionParticipant.is_active == True
            ))
        )
        
        if existing_participant.scalar_one_or_none():
            return ConnectionResponse(
                success=False,
                error_code="ALREADY_CONNECTED",
                error_message="User is already connected to this session"
            )
        
        # Check session capacity
        participants_count = await db.execute(
            select(func.count(SessionParticipant.id))
            .where(and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.is_active == True
            ))
        )
        current_players = participants_count.scalar() or 0
        
        if current_players >= session.max_players:
            return ConnectionResponse(
                success=False,
                error_code="SESSION_FULL",
                error_message="Session is full"
            )
        
        # Check late join policy
        if session.status == "in_progress" and not session.allow_late_join:
            return ConnectionResponse(
                success=False,
                error_code="LATE_JOIN_DISABLED",
                error_message="Late joining is disabled for this session"
            )
        
        # Create participant
        participant = SessionParticipant(
            session_id=session_id,
            user_id=connection_request.user_id,
            display_name=connection_request.display_name,
            is_connected=True
        )
        
        db.add(participant)
        await db.commit()
        await db.refresh(participant)
        
        # Use the code (increment usage counter)
        await code_generator.use_code(connection_request.game_code, connection_request.user_id)
        
        # Add participant to Redis
        await redis_service.add_participant(str(session_id), str(participant.id), {
            "user_id": str(connection_request.user_id),
            "display_name": connection_request.display_name,
            "score": 0,
            "is_connected": True
        })
        
        # Update session player count in Redis
        await redis_service.update_session(str(session_id), {
            "current_players": current_players + 1
        })
        
        # Log connection event
        event = SessionEvent(
            session_id=session_id,
            event_type="player_joined",
            event_data={
                "user_id": str(connection_request.user_id),
                "display_name": connection_request.display_name,
                "connection_method": connection_request.connection_method,
                "ip_address": request_info.get("ip_address"),
                "user_agent": request_info.get("user_agent")
            },
            actor_id=connection_request.user_id,
            actor_type="player"
        )
        db.add(event)
        await db.commit()
        
        # Publish real-time update
        await redis_service.publish_update(f"session:{session_id}", {
            "type": "player_joined",
            "data": {
                "participant_id": str(participant.id),
                "display_name": connection_request.display_name,
                "total_players": current_players + 1
            }
        })
        
        logger.info(
            "Player joined session",
            session_id=str(session_id),
            user_id=str(connection_request.user_id),
            participant_id=str(participant.id)
        )
        
        return ConnectionResponse(
            success=True,
            session_id=session_id,
            participant_id=participant.id,
            session_info={
                "title": session.title,
                "status": session.status,
                "game_type": "quiz"  # TODO: Get from game service
            },
            player_number=current_players + 1,
            total_players=current_players + 1
        )
        
    except Exception as e:
        logger.error("Error joining session", session_id=str(session_id), error=str(e))
        return ConnectionResponse(
            success=False,
            error_code="SYSTEM_ERROR",
            error_message="System error during connection"
        )


@router.post("/{session_id}/generate-code", response_model=GameCodeResponse)
async def generate_session_code(
    session_id: uuid.UUID,
    code_request: GameCodeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Generate a new game code for session"""
    try:
        # Verify session exists
        result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Generate new code
        code_data = await code_generator.generate_session_code(
            session_id=session_id,
            length=code_request.code_length,
            expires_in_minutes=code_request.expires_in_minutes,
            max_uses=code_request.max_uses,
            description=code_request.description
        )
        
        # Create deep link
        from ...admin_bot.app.services.qr_generator import QRGenerator
        qr_gen = QRGenerator("your_player_bot")  # TODO: Get from config
        deep_link = qr_gen.generate_session_link(code_data["code"])
        
        return GameCodeResponse(
            code=code_data["code"],
            session_id=session_id,
            deep_link=deep_link,
            expires_at=datetime.fromisoformat(code_data["expires_at"]),
            max_uses=code_data["max_uses"],
            current_uses=code_data["current_uses"],
            status=code_data["status"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating code", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate code"
        )


@router.delete("/{session_id}/codes/{code}")
async def deactivate_code(
    session_id: uuid.UUID,
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a game code"""
    try:
        # Verify session exists
        result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Deactivate code
        success = await code_generator.deactivate_code(code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Code not found"
            )
        
        return {"message": "Code deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deactivating code", session_id=str(session_id), code=code, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate code"
        )


@router.post("/validate-code", response_model=ConnectionValidationResponse)
async def validate_connection_code(
    validation_request: ConnectionValidation,
    db: AsyncSession = Depends(get_db)
):
    """Validate a game code for connection"""
    try:
        # Validate code
        validation_result = await code_generator.validate_code(validation_request.game_code)
        
        if not validation_result["valid"]:
            return ConnectionValidationResponse(
                valid=False,
                error_code=validation_result.get("error_code"),
                error_message=validation_result.get("error_message"),
                can_join=False
            )
        
        # Get session info
        session_id = uuid.UUID(validation_result["code_data"]["session_id"])
        result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return ConnectionValidationResponse(
                valid=False,
                error_code="SESSION_NOT_FOUND",
                error_message="Session not found",
                can_join=False
            )
        
        # Check if user can join
        can_join = True
        reason = None
        
        # Check session status
        if session.status not in ["waiting", "in_progress"]:
            can_join = False
            reason = f"Session is {session.status}"
        
        # Check capacity
        if can_join:
            participants_count = await db.execute(
                select(func.count(SessionParticipant.id))
                .where(and_(
                    SessionParticipant.session_id == session_id,
                    SessionParticipant.is_active == True
                ))
            )
            current_players = participants_count.scalar() or 0
            
            if current_players >= session.max_players:
                can_join = False
                reason = "Session is full"
        
        # Check late join policy
        if can_join and session.status == "in_progress" and not session.allow_late_join:
            can_join = False
            reason = "Late joining is disabled"
        
        # Check if user already joined
        if can_join and validation_request.user_id:
            existing_participant = await db.execute(
                select(SessionParticipant).where(and_(
                    SessionParticipant.session_id == session_id,
                    SessionParticipant.user_id == validation_request.user_id,
                    SessionParticipant.is_active == True
                ))
            )
            
            if existing_participant.scalar_one_or_none():
                can_join = False
                reason = "Already connected to this session"
        
        # Create session info
        session_info = SessionInfoResponse(
            session_id=session.id,
            session_code=session.session_code,
            title=session.title,
            description=session.description,
            game_type="quiz",  # TODO: Get from game service
            game_title=session.title,
            status=session.status,
            max_players=session.max_players,
            current_players=current_players,
            allow_late_join=session.allow_late_join,
            question_time_limit=session.question_time_limit,
            created_at=session.created_at,
            started_at=session.started_at
        )
        
        return ConnectionValidationResponse(
            valid=True,
            session_info=session_info,
            can_join=can_join,
            reason=reason
        )
        
    except Exception as e:
        logger.error("Error validating code", code=validation_request.game_code, error=str(e))
        return ConnectionValidationResponse(
            valid=False,
            error_code="SYSTEM_ERROR",
            error_message="System error during validation",
            can_join=False
        )


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed session status"""
    try:
        # Get session
        result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get participants
        participants_result = await db.execute(
            select(SessionParticipant)
            .where(and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.is_active == True
            ))
            .order_by(SessionParticipant.score.desc())
        )
        participants = participants_result.scalars().all()
        
        # Create leaderboard
        leaderboard = []
        for i, participant in enumerate(participants, 1):
            leaderboard.append({
                "rank": i,
                "display_name": participant.display_name,
                "score": participant.score,
                "is_connected": participant.is_connected
            })
        
        return SessionStatusResponse(
            session=session,
            participants=participants,
            current_question=None,  # TODO: Get current question
            leaderboard=leaderboard
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting session status", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session status"
        )


@router.post("/{session_id}/leave")
async def leave_session(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Leave a session"""
    try:
        # Find participant
        result = await db.execute(
            select(SessionParticipant).where(and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.user_id == user_id,
                SessionParticipant.is_active == True
            ))
        )
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found"
            )
        
        # Mark as inactive
        participant.is_active = False
        participant.is_connected = False
        await db.commit()
        
        # Remove from Redis
        await redis_service.remove_participant(str(session_id), str(participant.id))
        
        # Update session player count
        participants_count = await db.execute(
            select(func.count(SessionParticipant.id))
            .where(and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.is_active == True
            ))
        )
        current_players = participants_count.scalar() or 0
        
        await redis_service.update_session(str(session_id), {
            "current_players": current_players
        })
        
        # Log event
        event = SessionEvent(
            session_id=session_id,
            event_type="player_left",
            event_data={
                "user_id": str(user_id),
                "display_name": participant.display_name
            },
            actor_id=user_id,
            actor_type="player"
        )
        db.add(event)
        await db.commit()
        
        # Publish update
        await redis_service.publish_update(f"session:{session_id}", {
            "type": "player_left",
            "data": {
                "participant_id": str(participant.id),
                "display_name": participant.display_name,
                "total_players": current_players
            }
        })
        
        logger.info("Player left session", session_id=str(session_id), user_id=str(user_id))
        
        return {"message": "Left session successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error leaving session", session_id=str(session_id), user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave session"
        )

