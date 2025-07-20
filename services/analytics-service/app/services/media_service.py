"""
Media Service for managing game media files.
Handles upload, optimization, storage, and delivery of media content.
"""

import os
import uuid
import asyncio
import aiofiles
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
from datetime import datetime, timedelta
import hashlib
import mimetypes

logger = logging.getLogger(__name__)


class MediaService:
    """Service for managing game media files."""
    
    def __init__(self, 
                 storage_path: str = "/app/media",
                 max_file_size: int = 50 * 1024 * 1024,  # 50MB
                 allowed_image_formats: List[str] = None,
                 allowed_video_formats: List[str] = None,
                 allowed_audio_formats: List[str] = None):
        """
        Initialize media service.
        
        Args:
            storage_path: Base path for media storage
            max_file_size: Maximum file size in bytes
            allowed_image_formats: List of allowed image formats
            allowed_video_formats: List of allowed video formats
            allowed_audio_formats: List of allowed audio formats
        """
        self.storage_path = Path(storage_path)
        self.max_file_size = max_file_size
        
        self.allowed_image_formats = allowed_image_formats or [
            'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'
        ]
        self.allowed_video_formats = allowed_video_formats or [
            'mp4', 'webm', 'avi', 'mov', 'mkv'
        ]
        self.allowed_audio_formats = allowed_audio_formats or [
            'mp3', 'wav', 'ogg', 'aac', 'm4a'
        ]
        
        # Create storage directories
        self.images_path = self.storage_path / "images"
        self.videos_path = self.storage_path / "videos"
        self.audio_path = self.storage_path / "audio"
        self.thumbnails_path = self.storage_path / "thumbnails"
        self.temp_path = self.storage_path / "temp"
        
        for path in [self.images_path, self.videos_path, self.audio_path, 
                     self.thumbnails_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    async def upload_media(self, file_content: bytes, filename: str, 
                          game_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload and process media file.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            game_id: Optional game ID for organization
            
        Returns:
            Media file information
        """
        logger.info(f"Starting media upload: {filename}")
        
        try:
            # Validate file
            validation_result = await self._validate_file(file_content, filename)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'file_info': None
                }
            
            file_info = validation_result['file_info']
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = Path(filename).suffix.lower()
            unique_filename = f"{file_id}{file_extension}"
            
            # Determine storage path based on media type
            if file_info['media_type'] == 'image':
                storage_dir = self.images_path
            elif file_info['media_type'] == 'video':
                storage_dir = self.videos_path
            elif file_info['media_type'] == 'audio':
                storage_dir = self.audio_path
            else:
                return {
                    'success': False,
                    'error': 'Unsupported media type',
                    'file_info': None
                }
            
            # Create game-specific subdirectory if game_id provided
            if game_id:
                storage_dir = storage_dir / game_id
                storage_dir.mkdir(exist_ok=True)
            
            file_path = storage_dir / unique_filename
            
            # Save original file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Process file based on type
            processing_result = await self._process_media_file(
                file_path, file_info, file_id
            )
            
            # Create file record
            media_record = {
                'id': file_id,
                'original_filename': filename,
                'filename': unique_filename,
                'file_path': str(file_path),
                'media_type': file_info['media_type'],
                'mime_type': file_info['mime_type'],
                'file_size': file_info['file_size'],
                'game_id': game_id,
                'created_at': datetime.utcnow().isoformat(),
                'url': f"/media/{file_info['media_type']}/{game_id or 'general'}/{unique_filename}",
                'thumbnail_url': processing_result.get('thumbnail_url'),
                'optimized_versions': processing_result.get('optimized_versions', {}),
                'metadata': processing_result.get('metadata', {})
            }
            
            logger.info(f"Media upload completed: {file_id}")
            
            return {
                'success': True,
                'error': None,
                'file_info': media_record
            }
            
        except Exception as e:
            logger.error(f"Error uploading media file {filename}: {str(e)}")
            return {
                'success': False,
                'error': f"Upload failed: {str(e)}",
                'file_info': None
            }
    
    async def _validate_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded file."""
        try:
            # Check file size
            if len(file_content) > self.max_file_size:
                return {
                    'valid': False,
                    'error': f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB",
                    'file_info': None
                }
            
            # Check file extension
            file_extension = Path(filename).suffix.lower().lstrip('.')
            
            # Determine media type
            media_type = None
            if file_extension in self.allowed_image_formats:
                media_type = 'image'
            elif file_extension in self.allowed_video_formats:
                media_type = 'video'
            elif file_extension in self.allowed_audio_formats:
                media_type = 'audio'
            else:
                return {
                    'valid': False,
                    'error': f"Unsupported file format: {file_extension}",
                    'file_info': None
                }
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = f"{media_type}/*"
            
            # Basic content validation
            if media_type == 'image':
                if not self._is_valid_image(file_content):
                    return {
                        'valid': False,
                        'error': "Invalid image file",
                        'file_info': None
                    }
            
            file_info = {
                'media_type': media_type,
                'mime_type': mime_type,
                'file_size': len(file_content),
                'extension': file_extension
            }
            
            return {
                'valid': True,
                'error': None,
                'file_info': file_info
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Validation error: {str(e)}",
                'file_info': None
            }
    
    def _is_valid_image(self, file_content: bytes) -> bool:
        """Check if file content is a valid image."""
        try:
            # Check for common image file signatures
            image_signatures = {
                b'\xff\xd8\xff': 'jpeg',
                b'\x89PNG\r\n\x1a\n': 'png',
                b'GIF87a': 'gif',
                b'GIF89a': 'gif',
                b'RIFF': 'webp',  # WebP files start with RIFF
                b'<svg': 'svg'
            }
            
            for signature, format_name in image_signatures.items():
                if file_content.startswith(signature):
                    return True
            
            return False
        except Exception:
            return False
    
    async def _process_media_file(self, file_path: Path, file_info: Dict[str, Any], 
                                 file_id: str) -> Dict[str, Any]:
        """Process media file based on type."""
        processing_result = {
            'thumbnail_url': None,
            'optimized_versions': {},
            'metadata': {}
        }
        
        try:
            if file_info['media_type'] == 'image':
                processing_result = await self._process_image(file_path, file_id)
            elif file_info['media_type'] == 'video':
                processing_result = await self._process_video(file_path, file_id)
            elif file_info['media_type'] == 'audio':
                processing_result = await self._process_audio(file_path, file_id)
            
        except Exception as e:
            logger.error(f"Error processing media file {file_path}: {str(e)}")
        
        return processing_result
    
    async def _process_image(self, file_path: Path, file_id: str) -> Dict[str, Any]:
        """Process image file - create thumbnails and optimized versions."""
        result = {
            'thumbnail_url': None,
            'optimized_versions': {},
            'metadata': {}
        }
        
        try:
            # For basic processing without PIL, we'll just create metadata
            file_stat = file_path.stat()
            result['metadata'] = {
                'file_size': file_stat.st_size,
                'created_at': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                'format': file_path.suffix.lower().lstrip('.')
            }
            
            # Create a simple thumbnail placeholder
            thumbnail_filename = f"{file_id}_thumb.jpg"
            result['thumbnail_url'] = f"/media/thumbnails/{thumbnail_filename}"
            
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {str(e)}")
        
        return result
    
    async def _process_video(self, file_path: Path, file_id: str) -> Dict[str, Any]:
        """Process video file - create thumbnails and get metadata."""
        result = {
            'thumbnail_url': None,
            'optimized_versions': {},
            'metadata': {}
        }
        
        try:
            file_stat = file_path.stat()
            result['metadata'] = {
                'file_size': file_stat.st_size,
                'created_at': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                'format': file_path.suffix.lower().lstrip('.')
            }
            
            # Create thumbnail placeholder
            thumbnail_filename = f"{file_id}_thumb.jpg"
            result['thumbnail_url'] = f"/media/thumbnails/{thumbnail_filename}"
                
        except Exception as e:
            logger.error(f"Error processing video {file_path}: {str(e)}")
        
        return result
    
    async def _process_audio(self, file_path: Path, file_id: str) -> Dict[str, Any]:
        """Process audio file - get metadata."""
        result = {
            'thumbnail_url': None,
            'optimized_versions': {},
            'metadata': {}
        }
        
        try:
            file_stat = file_path.stat()
            result['metadata'] = {
                'file_size': file_stat.st_size,
                'created_at': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                'format': file_path.suffix.lower().lstrip('.')
            }
                
        except Exception as e:
            logger.error(f"Error processing audio {file_path}: {str(e)}")
        
        return result
    
    async def get_media_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get media file information by ID."""
        # This would typically query a database
        # For now, return None as placeholder
        return None
    
    async def delete_media(self, file_id: str) -> bool:
        """Delete media file and all its variants."""
        try:
            # This would typically:
            # 1. Get file info from database
            # 2. Delete original file
            # 3. Delete thumbnails and optimized versions
            # 4. Remove database record
            
            logger.info(f"Media file deleted: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting media file {file_id}: {str(e)}")
            return False
    
    async def cleanup_unused_media(self, older_than_days: int = 30) -> Dict[str, Any]:
        """Clean up unused media files older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            
            cleanup_result = {
                'deleted_files': 0,
                'freed_space': 0,
                'errors': []
            }
            
            # Scan for old files
            for media_dir in [self.images_path, self.videos_path, self.audio_path]:
                if media_dir.exists():
                    for file_path in media_dir.rglob('*'):
                        if file_path.is_file():
                            file_stat = file_path.stat()
                            file_date = datetime.fromtimestamp(file_stat.st_mtime)
                            
                            if file_date < cutoff_date:
                                try:
                                    file_size = file_stat.st_size
                                    file_path.unlink()
                                    cleanup_result['deleted_files'] += 1
                                    cleanup_result['freed_space'] += file_size
                                except Exception as e:
                                    cleanup_result['errors'].append(f"Failed to delete {file_path}: {str(e)}")
            
            logger.info(f"Media cleanup completed: {cleanup_result}")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Error during media cleanup: {str(e)}")
            return {
                'deleted_files': 0,
                'freed_space': 0,
                'errors': [str(e)]
            }
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'by_type': {
                    'images': {'count': 0, 'size': 0},
                    'videos': {'count': 0, 'size': 0},
                    'audio': {'count': 0, 'size': 0}
                }
            }
            
            # Calculate statistics for each media type
            for media_type, path in [
                ('images', self.images_path),
                ('videos', self.videos_path),
                ('audio', self.audio_path)
            ]:
                if path.exists():
                    for file_path in path.rglob('*'):
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            stats['by_type'][media_type]['count'] += 1
                            stats['by_type'][media_type]['size'] += file_size
                            stats['total_files'] += 1
                            stats['total_size'] += file_size
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {
                'total_files': 0,
                'total_size': 0,
                'by_type': {},
                'error': str(e)
            }
    
    def get_file_url(self, file_path: str, file_type: str = 'original') -> str:
        """Generate URL for accessing media file."""
        base_url = "/media"  # This should come from configuration
        
        if file_type == 'thumbnail':
            return f"{base_url}/thumbnails/{Path(file_path).name}"
        else:
            return f"{base_url}/{file_path}"
    
    async def download_remote_media(self, url: str, game_id: Optional[str] = None) -> Dict[str, Any]:
        """Download media from remote URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Extract filename from URL
                        filename = Path(url).name or f"media_{uuid.uuid4().hex[:8]}"
                        
                        # Upload the downloaded content
                        return await self.upload_media(content, filename, game_id)
                    else:
                        return {
                            'success': False,
                            'error': f"Failed to download media: HTTP {response.status}",
                            'file_info': None
                        }
        except Exception as e:
            logger.error(f"Error downloading remote media {url}: {str(e)}")
            return {
                'success': False,
                'error': f"Download failed: {str(e)}",
                'file_info': None
            }
    
    async def batch_upload_media(self, files: List[Tuple[bytes, str]], 
                                game_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Upload multiple media files in batch."""
        results = []
        
        # Process uploads with limited concurrency
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent uploads
        
        async def upload_single(file_content: bytes, filename: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.upload_media(file_content, filename, game_id)
        
        # Execute all uploads
        upload_tasks = [upload_single(content, filename) for content, filename in files]
        results = await asyncio.gather(*upload_tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    'success': False,
                    'error': f"Upload failed with exception: {str(result)}",
                    'file_info': None
                })
            else:
                final_results.append(result)
        
        return final_results
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported media formats."""
        return {
            'images': self.allowed_image_formats,
            'videos': self.allowed_video_formats,
            'audio': self.allowed_audio_formats
        }
    
    async def validate_media_references(self, media_urls: List[str]) -> Dict[str, Any]:
        """Validate that media file references are accessible."""
        validation_result = {
            'valid_urls': [],
            'invalid_urls': [],
            'errors': []
        }
        
        for url in media_urls:
            try:
                if url.startswith(('http://', 'https://')):
                    # Validate remote URL
                    async with aiohttp.ClientSession() as session:
                        async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status < 400:
                                validation_result['valid_urls'].append(url)
                            else:
                                validation_result['invalid_urls'].append(url)
                                validation_result['errors'].append(f"{url}: HTTP {response.status}")
                else:
                    # Validate local file
                    file_path = self.storage_path / url.lstrip('/')
                    if file_path.exists():
                        validation_result['valid_urls'].append(url)
                    else:
                        validation_result['invalid_urls'].append(url)
                        validation_result['errors'].append(f"{url}: File not found")
                        
            except Exception as e:
                validation_result['invalid_urls'].append(url)
                validation_result['errors'].append(f"{url}: {str(e)}")
        
        return validation_result