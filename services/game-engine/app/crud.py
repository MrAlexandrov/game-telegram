"""
Game Engine Service - CRUD Operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from typing import Optional, List
import uuid
from datetime import datetime

from .models import Game, Question, GamePack, MediaFile
from .schemas import GameCreate, GameUpdate, QuestionCreate, QuestionUpdate, GamePackCreate, MediaFileCreate


class GameCRUD:
    """CRUD operations for Game model"""
    
    @staticmethod
    async def create_game(db: AsyncSession, game_data: GameCreate) -> Game:
        """Create a new game"""
        game = Game(
            title=game_data.title,
            description=game_data.description,
            game_type=game_data.game_type,
            config=game_data.config,
            created_by=game_data.created_by
        )
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game
    
    @staticmethod
    async def get_game_by_id(db: AsyncSession, game_id: uuid.UUID) -> Optional[Game]:
        """Get game by ID"""
        result = await db.execute(
            select(Game)
            .options(selectinload(Game.questions))
            .where(Game.id == game_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_games(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        game_type: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None
    ) -> List[Game]:
        """Get list of games"""
        query = select(Game).offset(skip).limit(limit).order_by(Game.created_at.desc())
        
        if game_type:
            query = query.where(Game.game_type == game_type)
        if created_by:
            query = query.where(Game.created_by == created_by)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_game(db: AsyncSession, game_id: uuid.UUID, game_data: GameUpdate) -> Optional[Game]:
        """Update game"""
        update_data = game_data.model_dump(exclude_unset=True)
        if not update_data:
            return await GameCRUD.get_game_by_id(db, game_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        await db.execute(
            update(Game)
            .where(Game.id == game_id)
            .values(**update_data)
        )
        await db.commit()
        return await GameCRUD.get_game_by_id(db, game_id)
    
    @staticmethod
    async def delete_game(db: AsyncSession, game_id: uuid.UUID) -> bool:
        """Delete game"""
        result = await db.execute(delete(Game).where(Game.id == game_id))
        await db.commit()
        return result.rowcount > 0


class QuestionCRUD:
    """CRUD operations for Question model"""
    
    @staticmethod
    async def create_question(db: AsyncSession, question_data: QuestionCreate) -> Question:
        """Create a new question"""
        question = Question(
            game_id=question_data.game_id,
            order_index=question_data.order_index,
            question_type=question_data.question_type,
            content=question_data.content,
            media_url=question_data.media_url,
            correct_answers=question_data.correct_answers,
            points=question_data.points,
            time_limit=question_data.time_limit
        )
        db.add(question)
        await db.commit()
        await db.refresh(question)
        return question
    
    @staticmethod
    async def get_question_by_id(db: AsyncSession, question_id: uuid.UUID) -> Optional[Question]:
        """Get question by ID"""
        result = await db.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_questions_by_game(db: AsyncSession, game_id: uuid.UUID) -> List[Question]:
        """Get questions by game ID"""
        result = await db.execute(
            select(Question)
            .where(Question.game_id == game_id)
            .order_by(Question.order_index)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_question(db: AsyncSession, question_id: uuid.UUID, question_data: QuestionUpdate) -> Optional[Question]:
        """Update question"""
        update_data = question_data.model_dump(exclude_unset=True)
        if not update_data:
            return await QuestionCRUD.get_question_by_id(db, question_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        await db.execute(
            update(Question)
            .where(Question.id == question_id)
            .values(**update_data)
        )
        await db.commit()
        return await QuestionCRUD.get_question_by_id(db, question_id)
    
    @staticmethod
    async def delete_question(db: AsyncSession, question_id: uuid.UUID) -> bool:
        """Delete question"""
        result = await db.execute(delete(Question).where(Question.id == question_id))
        await db.commit()
        return result.rowcount > 0


class GamePackCRUD:
    """CRUD operations for GamePack model"""
    
    @staticmethod
    async def create_game_pack(db: AsyncSession, pack_data: GamePackCreate) -> GamePack:
        """Create a new game pack"""
        pack = GamePack(
            name=pack_data.name,
            version=pack_data.version,
            description=pack_data.description,
            game_type=pack_data.game_type,
            pack_data=pack_data.pack_data,
            file_path=pack_data.file_path,
            uploaded_by=pack_data.uploaded_by
        )
        db.add(pack)
        await db.commit()
        await db.refresh(pack)
        return pack
    
    @staticmethod
    async def get_game_pack_by_id(db: AsyncSession, pack_id: uuid.UUID) -> Optional[GamePack]:
        """Get game pack by ID"""
        result = await db.execute(select(GamePack).where(GamePack.id == pack_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_game_packs(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        game_type: Optional[str] = None,
        uploaded_by: Optional[uuid.UUID] = None
    ) -> List[GamePack]:
        """Get list of game packs"""
        query = select(GamePack).offset(skip).limit(limit).order_by(GamePack.created_at.desc())
        
        if game_type:
            query = query.where(GamePack.game_type == game_type)
        if uploaded_by:
            query = query.where(GamePack.uploaded_by == uploaded_by)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_validation_status(
        db: AsyncSession, 
        pack_id: uuid.UUID, 
        is_validated: bool, 
        validation_errors: Optional[dict] = None
    ) -> Optional[GamePack]:
        """Update game pack validation status"""
        await db.execute(
            update(GamePack)
            .where(GamePack.id == pack_id)
            .values(
                is_validated=is_validated,
                validation_errors=validation_errors,
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
        return await GamePackCRUD.get_game_pack_by_id(db, pack_id)


class MediaFileCRUD:
    """CRUD operations for MediaFile model"""
    
    @staticmethod
    async def create_media_file(db: AsyncSession, file_data: MediaFileCreate) -> MediaFile:
        """Create a new media file"""
        media_file = MediaFile(
            filename=file_data.filename,
            original_name=file_data.original_name,
            file_path=file_data.file_path,
            file_size=file_data.file_size,
            mime_type=file_data.mime_type,
            game_id=file_data.game_id,
            uploaded_by=file_data.uploaded_by
        )
        db.add(media_file)
        await db.commit()
        await db.refresh(media_file)
        return media_file
    
    @staticmethod
    async def get_media_file_by_id(db: AsyncSession, file_id: uuid.UUID) -> Optional[MediaFile]:
        """Get media file by ID"""
        result = await db.execute(select(MediaFile).where(MediaFile.id == file_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_media_files_by_game(db: AsyncSession, game_id: uuid.UUID) -> List[MediaFile]:
        """Get media files by game ID"""
        result = await db.execute(
            select(MediaFile)
            .where(MediaFile.game_id == game_id)
            .order_by(MediaFile.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def delete_media_file(db: AsyncSession, file_id: uuid.UUID) -> bool:
        """Delete media file"""
        result = await db.execute(delete(MediaFile).where(MediaFile.id == file_id))
        await db.commit()
        return result.rowcount > 0