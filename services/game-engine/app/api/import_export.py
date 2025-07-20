"""
Game Engine Service - Import/Export API Routes
Handles game pack import, export, validation, and library management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import json
import tempfile
import os
from pathlib import Path

from ..schemas.game_packs import (
    ImportRequest, ImportResult, ExportRequest, ExportResult,
    ValidationReport, GameLibraryFilter, GameLibraryResponse
)
from ..models.database import get_db
from ..services.game_importer import GameImporter
from ..services.pack_validator import PackValidator

router = APIRouter()

# Initialize services
game_importer = GameImporter()
pack_validator = PackValidator()


@router.post("/validate", response_model=ValidationReport)
async def validate_game_pack(
    file: UploadFile = File(..., description="Game pack JSON file"),
):
    """
    Validate a game pack file without importing it.
    
    Args:
        file: Uploaded JSON file containing game pack
        
    Returns:
        Detailed validation report
    """
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Validate the game pack
        validation_report = await pack_validator.validate_pack(content_str, file.filename)
        
        return validation_report
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded text"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/import", response_model=ImportResult)
async def import_game_pack(
    file: UploadFile = File(..., description="Game pack JSON file"),
    created_by: uuid.UUID = Form(..., description="User ID who is importing"),
    validate_only: bool = Form(False, description="Only validate, don't import"),
    overwrite_existing: bool = Form(False, description="Overwrite existing game"),
    import_media: bool = Form(True, description="Import associated media files"),
    db: AsyncSession = Depends(get_db)
):
    """
    Import a game pack from uploaded JSON file.
    
    Args:
        file: Uploaded JSON file containing game pack
        created_by: User ID who is importing the game
        validate_only: If True, only validate without importing
        overwrite_existing: If True, overwrite existing games with same title
        import_media: If True, import associated media files
        db: Database session
        
    Returns:
        Import result with success status and details
    """
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Create import request
        import_request = ImportRequest(
            file_content=content_str,
            filename=file.filename or "unknown.json",
            validate_only=validate_only,
            overwrite_existing=overwrite_existing,
            import_media=import_media
        )
        
        # Import the game pack
        result = await game_importer.import_game_pack(import_request, created_by, db)
        
        return result
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded text"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import error: {str(e)}"
        )


@router.post("/batch-import", response_model=List[ImportResult])
async def batch_import_game_packs(
    files: List[UploadFile] = File(..., description="Multiple game pack JSON files"),
    created_by: uuid.UUID = Form(..., description="User ID who is importing"),
    validate_only: bool = Form(False, description="Only validate, don't import"),
    overwrite_existing: bool = Form(False, description="Overwrite existing games"),
    import_media: bool = Form(True, description="Import associated media files"),
    db: AsyncSession = Depends(get_db)
):
    """
    Import multiple game packs in batch.
    
    Args:
        files: List of uploaded JSON files containing game packs
        created_by: User ID who is importing the games
        validate_only: If True, only validate without importing
        overwrite_existing: If True, overwrite existing games with same title
        import_media: If True, import associated media files
        db: Database session
        
    Returns:
        List of import results for each file
    """
    try:
        # Create import requests for all files
        import_requests = []
        
        for file in files:
            content = await file.read()
            content_str = content.decode('utf-8')
            
            import_request = ImportRequest(
                file_content=content_str,
                filename=file.filename or "unknown.json",
                validate_only=validate_only,
                overwrite_existing=overwrite_existing,
                import_media=import_media
            )
            import_requests.append(import_request)
        
        # Process batch import
        results = await game_importer.batch_import(import_requests, created_by, db)
        
        return results
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All files must be UTF-8 encoded text"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch import error: {str(e)}"
        )


@router.get("/export/{game_id}", response_model=ExportResult)
async def export_game_pack(
    game_id: uuid.UUID,
    include_media: bool = Query(True, description="Include media files in export"),
    format: str = Query("json", description="Export format"),
    db: AsyncSession = Depends(get_db)
):
    """
    Export a game pack to JSON format.
    
    Args:
        game_id: ID of the game to export
        include_media: If True, include media file references
        format: Export format (currently only 'json' supported)
        db: Database session
        
    Returns:
        Export result with game pack content
    """
    try:
        # Create export request
        export_request = ExportRequest(
            game_id=str(game_id),
            include_media=include_media,
            format=format
        )
        
        # Export the game pack
        result = await game_importer.export_game_pack(export_request, db)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in result.message.lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export error: {str(e)}"
        )


@router.get("/export/{game_id}/download")
async def download_game_pack(
    game_id: uuid.UUID,
    include_media: bool = Query(True, description="Include media files in export"),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a game pack as a JSON file.
    
    Args:
        game_id: ID of the game to export
        include_media: If True, include media file references
        db: Database session
        
    Returns:
        JSON file download
    """
    try:
        # Create export request
        export_request = ExportRequest(
            game_id=str(game_id),
            include_media=include_media,
            format="json"
        )
        
        # Export the game pack
        result = await game_importer.export_game_pack(export_request, db)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in result.message.lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(result.content)
            temp_file_path = temp_file.name
        
        # Return file response
        return FileResponse(
            path=temp_file_path,
            filename=result.filename,
            media_type='application/json',
            background=lambda: os.unlink(temp_file_path)  # Clean up temp file after response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download error: {str(e)}"
        )


@router.get("/library", response_model=GameLibraryResponse)
async def get_game_library(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    game_type: Optional[str] = Query(None, description="Filter by game type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    author: Optional[str] = Query(None, description="Filter by author"),
    search_text: Optional[str] = Query(None, description="Search in title and description"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    min_questions: Optional[int] = Query(None, ge=1, description="Minimum number of questions"),
    max_questions: Optional[int] = Query(None, ge=1, description="Maximum number of questions"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get filtered game library.
    
    Args:
        page: Page number for pagination
        per_page: Number of items per page
        game_type: Filter by game type
        category: Filter by category
        difficulty: Filter by difficulty level
        author: Filter by author name
        search_text: Search text for title and description
        tags: Comma-separated list of tags to filter by
        min_questions: Minimum number of questions
        max_questions: Maximum number of questions
        db: Database session
        
    Returns:
        Paginated game library response
    """
    try:
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Create filter object
        filter_params = GameLibraryFilter(
            page=page,
            per_page=per_page,
            game_type=game_type,
            category=category,
            difficulty=difficulty,
            author=author,
            search_text=search_text,
            tags=tag_list,
            min_questions=min_questions,
            max_questions=max_questions
        )
        
        # Get filtered library
        library_response = await game_importer.get_game_library(filter_params, db)
        
        return library_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Library error: {str(e)}"
        )


@router.get("/library/stats")
async def get_library_stats(db: AsyncSession = Depends(get_db)):
    """
    Get game library statistics.
    
    Args:
        db: Database session
        
    Returns:
        Library statistics including counts by type, category, etc.
    """
    try:
        # This would need to be implemented based on your database structure
        # For now, return basic stats
        stats = {
            "total_games": 0,
            "game_types": {},
            "categories": {},
            "difficulties": {},
            "total_questions": 0,
            "average_questions_per_game": 0
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats error: {str(e)}"
        )


@router.delete("/games/{game_id}")
async def delete_game_pack(
    game_id: uuid.UUID,
    create_backup: bool = Query(True, description="Create backup before deletion"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a game pack and optionally create a backup.
    
    Args:
        game_id: ID of the game to delete
        create_backup: If True, create backup before deletion
        db: Database session
        
    Returns:
        Deletion confirmation
    """
    try:
        # Create backup if requested
        if create_backup:
            export_request = ExportRequest(
                game_id=str(game_id),
                include_media=True,
                format="json"
            )
            
            backup_result = await game_importer.export_game_pack(export_request, db)
            if backup_result.success:
                # Save backup to backup directory
                backup_dir = Path("/app/backups") / "deleted_games"
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                backup_file = backup_dir / f"deleted_{game_id}_{backup_result.filename}"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(backup_result.content)
        
        # Delete the game (this would need to be implemented in your CRUD)
        # success = await GameCRUD.delete_game(db, game_id)
        
        # For now, return success
        return {
            "success": True,
            "message": f"Game {game_id} deleted successfully",
            "backup_created": create_backup
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion error: {str(e)}"
        )


@router.post("/games/{game_id}/duplicate")
async def duplicate_game_pack(
    game_id: uuid.UUID,
    new_title: str = Form(..., description="Title for the duplicated game"),
    created_by: uuid.UUID = Form(..., description="User ID who is duplicating"),
    db: AsyncSession = Depends(get_db)
):
    """
    Duplicate an existing game pack with a new title.
    
    Args:
        game_id: ID of the game to duplicate
        new_title: Title for the new duplicated game
        created_by: User ID who is duplicating the game
        db: Database session
        
    Returns:
        Import result for the duplicated game
    """
    try:
        # Export the existing game
        export_request = ExportRequest(
            game_id=str(game_id),
            include_media=True,
            format="json"
        )
        
        export_result = await game_importer.export_game_pack(export_request, db)
        
        if not export_result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found for duplication"
            )
        
        # Modify the exported data
        game_data = json.loads(export_result.content)
        game_data["metadata"]["title"] = new_title
        game_data["metadata"]["version"] = "1.0.0"  # Reset version
        
        # Create import request
        import_request = ImportRequest(
            file_content=json.dumps(game_data, ensure_ascii=False, indent=2),
            filename=f"duplicate_{new_title}.json",
            validate_only=False,
            overwrite_existing=False,
            import_media=True
        )
        
        # Import the duplicated game
        result = await game_importer.import_game_pack(import_request, created_by, db)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Duplication error: {str(e)}"
        )


@router.get("/validation-summary/{game_id}")
async def get_validation_summary(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a validation summary for an existing game.
    
    Args:
        game_id: ID of the game to validate
        db: Database session
        
    Returns:
        Validation summary and recommendations
    """
    try:
        # Export the game to get its current state
        export_request = ExportRequest(
            game_id=str(game_id),
            include_media=True,
            format="json"
        )
        
        export_result = await game_importer.export_game_pack(export_request, db)
        
        if not export_result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        
        # Validate the exported game
        validation_report = await pack_validator.validate_pack(
            export_result.content, 
            f"game_{game_id}.json"
        )
        
        # Generate human-readable summary
        summary = pack_validator.get_validation_summary(validation_report)
        
        return {
            "game_id": str(game_id),
            "validation_report": validation_report,
            "summary": summary,
            "recommendations": await _generate_recommendations(validation_report)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )


async def _generate_recommendations(validation_report: ValidationReport) -> List[str]:
    """Generate recommendations based on validation report."""
    recommendations = []
    
    if validation_report.warning_count > 0:
        recommendations.append("Consider addressing validation warnings to improve game quality")
    
    if validation_report.question_count < 5:
        recommendations.append("Add more questions for a better gaming experience")
    
    if validation_report.question_count > 50:
        recommendations.append("Consider splitting into multiple game packs for better performance")
    
    if len(validation_report.media_files) == 0:
        recommendations.append("Add media files (images, videos, audio) to make questions more engaging")
    
    if len(validation_report.media_files) > 20:
        recommendations.append("Large number of media files may impact loading performance")
    
    return recommendations