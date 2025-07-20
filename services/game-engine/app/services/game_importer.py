"""
Game importer service with async file processing.
Handles importing games from JSON packs with media files and validation.
"""

import json
import asyncio
import aiofiles
import uuid
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
import shutil
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.game_packs import (
    ImportRequest, ImportResult, ExportRequest, ExportResult,
    ValidationReport, GamePack, QuizGamePack, FamilyFeudGamePack,
    GameLibraryEntry, GameLibraryFilter, GameLibraryResponse
)
from .pack_validator import PackValidator
from ..models.database import get_db
from ..crud import GameCRUD, QuestionCRUD
from ..schemas import GameCreate, QuestionCreate

logger = logging.getLogger(__name__)


class GameImporter:
    """Game importer with async file processing and validation."""
    
    def __init__(self, media_base_path: str = "/app/media", backup_path: str = "/app/backups"):
        """Initialize game importer."""
        self.media_base_path = Path(media_base_path)
        self.backup_path = Path(backup_path)
        self.validator = PackValidator(str(self.media_base_path))
        
        # Ensure directories exist
        self.media_base_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)
    
    async def import_game_pack(self, request: ImportRequest, created_by: uuid.UUID, db: AsyncSession) -> ImportResult:
        """
        Import a game pack from JSON content.
        
        Args:
            request: Import request with game pack data
            created_by: User ID who is importing the game
            db: Database session
            
        Returns:
            Import result with success status and details
        """
        logger.info(f"Starting import of game pack: {request.filename}")
        
        # Validate the game pack first
        validation_report = await self.validator.validate_pack(request.file_content, request.filename)
        
        if request.validate_only:
            return ImportResult(
                success=validation_report.is_valid,
                validation_report=validation_report,
                message="Validation completed" if validation_report.is_valid else "Validation failed"
            )
        
        if not validation_report.is_valid:
            return ImportResult(
                success=False,
                validation_report=validation_report,
                message="Cannot import invalid game pack"
            )
        
        try:
            # Parse and normalize game pack
            data = json.loads(request.file_content)
            game_type, normalized_data = self.validator._detect_and_normalize_game_type(data)
            
            # Create game pack object
            if game_type == "quiz":
                game_pack = QuizGamePack(**normalized_data)
            elif game_type == "family_feud":
                game_pack = FamilyFeudGamePack(**normalized_data)
            else:
                return ImportResult(
                    success=False,
                    validation_report=validation_report,
                    message=f"Unsupported game type: {game_type}"
                )
            
            # Check for existing game
            existing_game = await self._check_existing_game(game_pack, db)
            if existing_game and not request.overwrite_existing:
                return ImportResult(
                    success=False,
                    validation_report=validation_report,
                    message=f"Game '{game_pack.metadata.title}' already exists. Use overwrite_existing=True to replace it."
                )
            
            # Import media files if requested
            imported_files = []
            failed_files = []
            if request.import_media and validation_report.media_files:
                imported_files, failed_files = await self._import_media_files(
                    validation_report.media_files, game_pack.metadata.title
                )
            
            # Create or update game in database
            game_id = await self._create_game_in_db(game_pack, created_by, db, existing_game)
            
            # Create backup
            await self._create_backup(game_pack, game_id)
            
            logger.info(f"Successfully imported game pack: {request.filename} -> {game_id}")
            
            return ImportResult(
                success=True,
                game_id=str(game_id),
                validation_report=validation_report,
                imported_files=imported_files,
                failed_files=failed_files,
                message=f"Successfully imported game '{game_pack.metadata.title}'"
            )
            
        except Exception as e:
            logger.error(f"Error importing game pack {request.filename}: {str(e)}")
            return ImportResult(
                success=False,
                validation_report=validation_report,
                message=f"Import failed: {str(e)}"
            )
    
    async def export_game_pack(self, request: ExportRequest, db: AsyncSession) -> ExportResult:
        """
        Export a game pack to JSON format.
        
        Args:
            request: Export request with game ID and options
            db: Database session
            
        Returns:
            Export result with game pack content
        """
        logger.info(f"Starting export of game: {request.game_id}")
        
        try:
            # Get game from database
            game_id = uuid.UUID(request.game_id)
            game = await GameCRUD.get_game_by_id(db, game_id)
            
            if not game:
                return ExportResult(
                    success=False,
                    filename="",
                    message="Game not found"
                )
            
            # Get questions
            questions = await QuestionCRUD.get_questions_by_game(db, game_id)
            
            # Convert to game pack format
            game_pack_data = await self._convert_db_to_pack(game, questions)
            
            # Generate filename
            safe_title = "".join(c for c in game.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}_{game.game_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Serialize to JSON
            content = json.dumps(game_pack_data, ensure_ascii=False, indent=2)
            
            # Collect media files if requested
            media_files = []
            if request.include_media:
                media_files = await self._collect_media_files(game_pack_data)
            
            logger.info(f"Successfully exported game: {request.game_id} -> {filename}")
            
            return ExportResult(
                success=True,
                content=content,
                filename=filename,
                media_files=media_files,
                message=f"Successfully exported game '{game.title}'"
            )
            
        except Exception as e:
            logger.error(f"Error exporting game {request.game_id}: {str(e)}")
            return ExportResult(
                success=False,
                filename="",
                message=f"Export failed: {str(e)}"
            )
    
    async def batch_import(self, requests: List[ImportRequest], created_by: uuid.UUID, db: AsyncSession) -> List[ImportResult]:
        """
        Import multiple game packs in batch.
        
        Args:
            requests: List of import requests
            created_by: User ID who is importing the games
            db: Database session
            
        Returns:
            List of import results
        """
        logger.info(f"Starting batch import of {len(requests)} game packs")
        
        results = []
        
        # Process imports concurrently with limited concurrency
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent imports
        
        async def import_single(request: ImportRequest) -> ImportResult:
            async with semaphore:
                return await self.import_game_pack(request, created_by, db)
        
        # Execute all imports
        import_tasks = [import_single(request) for request in requests]
        results = await asyncio.gather(*import_tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(ImportResult(
                    success=False,
                    validation_report=ValidationReport(is_valid=False, errors=[], warnings=[]),
                    message=f"Import failed with exception: {str(result)}"
                ))
            else:
                final_results.append(result)
        
        successful_imports = sum(1 for r in final_results if r.success)
        logger.info(f"Batch import completed: {successful_imports}/{len(requests)} successful")
        
        return final_results
    
    async def get_game_library(self, filter_params: GameLibraryFilter, db: AsyncSession) -> GameLibraryResponse:
        """
        Get filtered game library.
        
        Args:
            filter_params: Filter parameters
            db: Database session
            
        Returns:
            Filtered game library response
        """
        logger.info("Fetching game library")
        
        try:
            # Get games from database with filters
            games = await GameCRUD.get_games(
                db,
                skip=(filter_params.page - 1) * filter_params.per_page,
                limit=filter_params.per_page,
                game_type=filter_params.game_type,
                # Add more filters as needed
            )
            
            # Convert to library entries
            library_entries = []
            for game in games:
                questions = await QuestionCRUD.get_questions_by_game(db, game.id)
                
                entry = GameLibraryEntry(
                    id=str(game.id),
                    title=game.title,
                    type=game.game_type,
                    category=game.config.get("category", "General"),
                    difficulty=game.config.get("difficulty"),
                    question_count=len(questions),
                    author=game.config.get("author", "Unknown"),
                    version=game.config.get("version", "1.0.0"),
                    created_at=game.created_at,
                    tags=game.config.get("tags", []),
                    estimated_duration=game.config.get("estimated_duration")
                )
                library_entries.append(entry)
            
            # Apply additional filters
            filtered_entries = await self._apply_library_filters(library_entries, filter_params)
            
            # Calculate pagination
            total_count = len(filtered_entries)
            total_pages = (total_count + filter_params.per_page - 1) // filter_params.per_page
            
            # Apply pagination
            start_idx = (filter_params.page - 1) * filter_params.per_page
            end_idx = start_idx + filter_params.per_page
            paginated_entries = filtered_entries[start_idx:end_idx]
            
            return GameLibraryResponse(
                games=paginated_entries,
                total_count=total_count,
                page=filter_params.page,
                per_page=filter_params.per_page,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error fetching game library: {str(e)}")
            return GameLibraryResponse(
                games=[],
                total_count=0,
                page=filter_params.page,
                per_page=filter_params.per_page,
                total_pages=0
            )
    
    async def _check_existing_game(self, game_pack, db: AsyncSession) -> Optional[Any]:
        """Check if a game with the same title already exists."""
        # This would need to be implemented based on your GameCRUD methods
        # For now, return None (no existing game)
        return None
    
    async def _import_media_files(self, media_urls: List[str], game_title: str) -> Tuple[List[str], List[str]]:
        """Import media files from URLs or local paths."""
        imported_files = []
        failed_files = []
        
        # Create game-specific media directory
        game_media_dir = self.media_base_path / "games" / self._sanitize_filename(game_title)
        game_media_dir.mkdir(parents=True, exist_ok=True)
        
        for media_url in media_urls:
            try:
                if media_url.startswith(('http://', 'https://')):
                    # Download remote file
                    success = await self._download_media_file(media_url, game_media_dir)
                    if success:
                        imported_files.append(media_url)
                    else:
                        failed_files.append(media_url)
                else:
                    # Copy local file
                    success = await self._copy_local_media_file(media_url, game_media_dir)
                    if success:
                        imported_files.append(media_url)
                    else:
                        failed_files.append(media_url)
                        
            except Exception as e:
                logger.error(f"Error importing media file {media_url}: {str(e)}")
                failed_files.append(media_url)
        
        return imported_files, failed_files
    
    async def _download_media_file(self, url: str, target_dir: Path) -> bool:
        """Download a media file from URL."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Extract filename from URL
                        filename = Path(url).name or f"media_{uuid.uuid4().hex[:8]}"
                        target_path = target_dir / filename
                        
                        # Write file
                        async with aiofiles.open(target_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        logger.info(f"Downloaded media file: {url} -> {target_path}")
                        return True
                    else:
                        logger.error(f"Failed to download media file {url}: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error downloading media file {url}: {str(e)}")
            return False
    
    async def _copy_local_media_file(self, source_path: str, target_dir: Path) -> bool:
        """Copy a local media file."""
        try:
            source = Path(source_path)
            if not source.exists():
                logger.error(f"Source media file not found: {source_path}")
                return False
            
            target = target_dir / source.name
            shutil.copy2(source, target)
            
            logger.info(f"Copied media file: {source_path} -> {target}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying media file {source_path}: {str(e)}")
            return False
    
    async def _create_game_in_db(self, game_pack, created_by: uuid.UUID, db: AsyncSession, existing_game=None) -> uuid.UUID:
        """Create or update game in database."""
        # Convert game pack to database format
        game_data = GameCreate(
            title=game_pack.metadata.title,
            description=game_pack.metadata.description or "",
            game_type=game_pack.metadata.game_type,
            config={
                "metadata": game_pack.metadata.dict(),
                "settings": game_pack.settings.dict() if game_pack.settings else {}
            },
            created_by=created_by
        )
        
        if existing_game:
            # Update existing game
            game = await GameCRUD.update_game(db, existing_game.id, game_data)
            game_id = existing_game.id
        else:
            # Create new game
            game = await GameCRUD.create_game(db, game_data)
            game_id = game.id
        
        # Create questions
        for i, question in enumerate(game_pack.questions):
            question_data = QuestionCreate(
                game_id=game_id,
                order_index=i + 1,
                question_type=question.type,
                content=self._convert_question_content(question),
                correct_answers=question.correct_answers,
                points=question.points,
                time_limit=question.time_limit
            )
            
            await QuestionCRUD.create_question(db, question_data)
        
        return game_id
    
    def _convert_question_content(self, question) -> Dict[str, Any]:
        """Convert question to database content format."""
        content = {
            "text": question.text,
            "id": question.id,
            "type": question.type
        }
        
        if hasattr(question, 'options') and question.options:
            content["options"] = [
                opt.text if isinstance(opt, str) else opt.dict()
                for opt in question.options
            ]
        
        if hasattr(question, 'explanation') and question.explanation:
            content["explanation"] = question.explanation
        
        if hasattr(question, 'media') and question.media:
            content["media"] = question.media.dict()
        
        if hasattr(question, 'media_content') and question.media_content:
            content["media_content"] = question.media_content
        
        # Add Family Feud specific content
        if hasattr(question, 'answers') and question.answers:
            content["answers"] = [answer.dict() for answer in question.answers]
        
        return content
    
    async def _create_backup(self, game_pack, game_id: uuid.UUID):
        """Create backup of imported game pack."""
        try:
            backup_dir = self.backup_path / str(game_id)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_file = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            backup_data = {
                "game_id": str(game_id),
                "imported_at": datetime.now().isoformat(),
                "game_pack": game_pack.dict()
            }
            
            async with aiofiles.open(backup_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(backup_data, ensure_ascii=False, indent=2))
            
            logger.info(f"Created backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"Error creating backup for game {game_id}: {str(e)}")
    
    async def _convert_db_to_pack(self, game, questions) -> Dict[str, Any]:
        """Convert database game to game pack format."""
        # Extract metadata from config
        metadata = game.config.get("metadata", {})
        settings = game.config.get("settings", {})
        
        # Convert questions
        converted_questions = []
        for question in questions:
            q_data = {
                "id": question.content.get("id", f"q_{question.order_index}"),
                "type": question.question_type,
                "text": question.content.get("text", ""),
                "correct_answers": question.correct_answers or [],
                "points": question.points,
                "time_limit": question.time_limit,
                "order": question.order_index
            }
            
            # Add question-specific fields
            if "options" in question.content:
                q_data["options"] = question.content["options"]
            
            if "explanation" in question.content:
                q_data["explanation"] = question.content["explanation"]
            
            if "media" in question.content:
                q_data["media"] = question.content["media"]
            
            if "answers" in question.content:
                q_data["answers"] = question.content["answers"]
            
            converted_questions.append(q_data)
        
        # Create game pack structure
        game_pack = {
            "type": game.game_type,
            "metadata": {
                "title": game.title,
                "description": game.description,
                "game_type": game.game_type,
                "version": metadata.get("version", "1.0.0"),
                "author": metadata.get("author", "Unknown"),
                "created_at": game.created_at.isoformat(),
                **metadata
            },
            "settings": settings,
            "questions": converted_questions
        }
        
        return game_pack
    
    async def _collect_media_files(self, game_pack_data: Dict[str, Any]) -> List[str]:
        """Collect media file references from game pack data."""
        media_files = []
        
        questions = game_pack_data.get("questions", [])
        for question in questions:
            # Check for media in question
            if "media" in question:
                media = question["media"]
                if isinstance(media, dict) and "url" in media:
                    media_files.append(media["url"])
            
            # Check for media_content
            if "media_content" in question:
                media_content = question["media_content"]
                if isinstance(media_content, dict):
                    if "media_url" in media_content:
                        media_files.append(media_content["media_url"])
                    if "thumbnail_url" in media_content:
                        media_files.append(media_content["thumbnail_url"])
            
            # Check options for media
            if "options" in question:
                for option in question["options"]:
                    if isinstance(option, dict) and "media" in option:
                        media = option["media"]
                        if isinstance(media, dict) and "url" in media:
                            media_files.append(media["url"])
        
        return list(set(media_files))  # Remove duplicates
    
    async def _apply_library_filters(self, entries: List[GameLibraryEntry], filters: GameLibraryFilter) -> List[GameLibraryEntry]:
        """Apply additional filters to library entries."""
        filtered = entries
        
        # Filter by category
        if filters.category:
            filtered = [e for e in filtered if e.category and filters.category.lower() in e.category.lower()]
        
        # Filter by difficulty
        if filters.difficulty:
            filtered = [e for e in filtered if e.difficulty == filters.difficulty]
        
        # Filter by author
        if filters.author:
            filtered = [e for e in filtered if filters.author.lower() in e.author.lower()]
        
        # Filter by tags
        if filters.tags:
            filtered = [e for e in filtered if all(tag in e.tags for tag in filters.tags)]
        
        # Filter by search text
        if filters.search_text:
            search_lower = filters.search_text.lower()
            filtered = [e for e in filtered if 
                       search_lower in e.title.lower() or 
                       (e.category and search_lower in e.category.lower())]
        
        # Filter by question count
        if filters.min_questions:
            filtered = [e for e in filtered if e.question_count >= filters.min_questions]
        
        if filters.max_questions:
            filtered = [e for e in filtered if e.question_count <= filters.max_questions]
        
        # Filter by date range
        if filters.created_after:
            filtered = [e for e in filtered if e.created_at >= filters.created_after]
        
        if filters.created_before:
            filtered = [e for e in filtered if e.created_at <= filters.created_before]
        
        return filtered
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem use."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        return filename[:100].strip()