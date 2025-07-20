"""
File Handler for Admin Bot
Обработка загружаемых файлов (игровые паки, медиа)
"""

import json
import os
import tempfile
import aiofiles
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog
from ..config import settings

logger = structlog.get_logger()


class FileHandlerError(Exception):
    """Исключение для обработки файлов"""
    pass


class FileHandler:
    """Обработчик файлов для админ-бота"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "admin_bot_files"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def save_temp_file(self, file_content: bytes, filename: str) -> str:
        """Сохранить временный файл"""
        file_path = self.temp_dir / filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        logger.info(f"Temporary file saved: {file_path}")
        return str(file_path)
    
    def validate_file_type(self, filename: str) -> bool:
        """Проверить тип файла"""
        file_ext = Path(filename).suffix.lower()
        return file_ext in settings.ALLOWED_FILE_TYPES
    
    def validate_file_size(self, file_size: int) -> bool:
        """Проверить размер файла"""
        return file_size <= settings.MAX_FILE_SIZE
    
    async def parse_game_pack(self, file_path: str) -> Dict[str, Any]:
        """Парсинг игрового пака из JSON файла"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                game_pack = json.loads(content)
            
            # Валидация структуры игрового пака
            self._validate_game_pack_structure(game_pack)
            
            return game_pack
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in game pack: {e}")
            raise FileHandlerError(f"Неверный формат JSON: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing game pack: {e}")
            raise FileHandlerError(f"Ошибка обработки игрового пака: {e}")
    
    def _validate_game_pack_structure(self, game_pack: Dict[str, Any]) -> None:
        """Валидация структуры игрового пака"""
        required_fields = ["game_pack"]
        
        for field in required_fields:
            if field not in game_pack:
                raise FileHandlerError(f"Отсутствует обязательное поле: {field}")
        
        pack_data = game_pack["game_pack"]
        
        # Проверка метаданных
        if "meta" not in pack_data:
            raise FileHandlerError("Отсутствуют метаданные игры")
        
        meta = pack_data["meta"]
        required_meta_fields = ["title", "game_type"]
        
        for field in required_meta_fields:
            if field not in meta:
                raise FileHandlerError(f"Отсутствует поле в метаданных: {field}")
        
        # Проверка вопросов
        if "questions" not in pack_data:
            raise FileHandlerError("Отсутствуют вопросы в игровом паке")
        
        questions = pack_data["questions"]
        if not isinstance(questions, list) or len(questions) == 0:
            raise FileHandlerError("Игровой пак должен содержать хотя бы один вопрос")
        
        # Валидация каждого вопроса
        for i, question in enumerate(questions):
            self._validate_question_structure(question, i + 1)
    
    def _validate_question_structure(self, question: Dict[str, Any], question_num: int) -> None:
        """Валидация структуры вопроса"""
        required_fields = ["id", "type", "content", "correct_answers"]
        
        for field in required_fields:
            if field not in question:
                raise FileHandlerError(f"Вопрос {question_num}: отсутствует поле {field}")
        
        # Проверка типа вопроса
        valid_types = ["multiple_choice", "text_input", "true_false"]
        if question["type"] not in valid_types:
            raise FileHandlerError(f"Вопрос {question_num}: неверный тип вопроса")
        
        # Проверка контента
        content = question["content"]
        if not isinstance(content, dict) or "text" not in content:
            raise FileHandlerError(f"Вопрос {question_num}: неверная структура контента")
        
        # Проверка правильных ответов
        correct_answers = question["correct_answers"]
        if not isinstance(correct_answers, list) or len(correct_answers) == 0:
            raise FileHandlerError(f"Вопрос {question_num}: должен содержать правильные ответы")
        
        # Дополнительная проверка для multiple_choice
        if question["type"] == "multiple_choice":
            if "options" not in content:
                raise FileHandlerError(f"Вопрос {question_num}: отсутствуют варианты ответов")
            
            options = content["options"]
            if not isinstance(options, list) or len(options) < 2:
                raise FileHandlerError(f"Вопрос {question_num}: должно быть минимум 2 варианта ответа")
    
    def extract_game_data(self, game_pack: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечь данные игры из пака"""
        pack_data = game_pack["game_pack"]
        meta = pack_data["meta"]
        config = pack_data.get("config", {})
        questions = pack_data["questions"]
        
        return {
            "title": meta["title"],
            "description": meta.get("description", ""),
            "game_type": meta["game_type"],
            "config": config,
            "questions": questions,
            "version": meta.get("version", "1.0.0"),
            "author": meta.get("author", "Unknown")
        }
    
    async def cleanup_temp_file(self, file_path: str) -> None:
        """Удалить временный файл"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Получить информацию о файле"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileHandlerError("Файл не найден")
        
        stat = path.stat()
        
        return {
            "filename": path.name,
            "size": stat.st_size,
            "extension": path.suffix.lower(),
            "created": stat.st_ctime,
            "modified": stat.st_mtime
        }
    
    def format_file_size(self, size_bytes: int) -> str:
        """Форматировать размер файла"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    async def create_game_pack_template(self, game_type: str) -> str:
        """Создать шаблон игрового пака"""
        templates = {
            "quiz": {
                "game_pack": {
                    "meta": {
                        "title": "Новая викторина",
                        "description": "Описание викторины",
                        "version": "1.0.0",
                        "author": "Admin",
                        "game_type": "quiz",
                        "created_at": "2024-01-01T00:00:00Z"
                    },
                    "config": {
                        "time_limit": 30,
                        "points_per_question": 10,
                        "shuffle_options": True,
                        "allow_partial_credit": False,
                        "case_sensitive": False
                    },
                    "questions": [
                        {
                            "id": "q1",
                            "order": 1,
                            "type": "multiple_choice",
                            "content": {
                                "text": "Пример вопроса?",
                                "options": ["Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"]
                            },
                            "correct_answers": ["Вариант 1"],
                            "points": 10,
                            "time_limit": 30,
                            "requires_validation": False,
                            "explanation": "Объяснение правильного ответа"
                        }
                    ]
                }
            },
            "family_feud": {
                "game_pack": {
                    "meta": {
                        "title": "100 к одному",
                        "description": "Игра 100 к одному",
                        "version": "1.0.0",
                        "author": "Admin",
                        "game_type": "family_feud",
                        "created_at": "2024-01-01T00:00:00Z"
                    },
                    "config": {
                        "rounds": 3,
                        "answers_per_question": 6,
                        "time_limit": 60,
                        "strike_limit": 3
                    },
                    "questions": [
                        {
                            "id": "ff1",
                            "order": 1,
                            "type": "family_feud",
                            "content": {
                                "text": "Назовите популярные виды спорта"
                            },
                            "correct_answers": [
                                {"answer": "Футбол", "points": 40},
                                {"answer": "Баскетбол", "points": 25},
                                {"answer": "Теннис", "points": 15},
                                {"answer": "Хоккей", "points": 10},
                                {"answer": "Волейбол", "points": 7},
                                {"answer": "Плавание", "points": 3}
                            ],
                            "time_limit": 60,
                            "requires_validation": True
                        }
                    ]
                }
            }
        }
        
        template = templates.get(game_type)
        if not template:
            raise FileHandlerError(f"Неизвестный тип игры: {game_type}")
        
        # Сохранить шаблон во временный файл
        template_path = self.temp_dir / f"template_{game_type}.json"
        
        async with aiofiles.open(template_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(template, ensure_ascii=False, indent=2))
        
        return str(template_path)