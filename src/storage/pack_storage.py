"""
Хранилище игровых паков
"""
import json
import os
import uuid
from typing import Dict, List, Optional
from datetime import datetime
import logging

from src.models.game import GamePack
from src.settings import settings


class PackStorage:
    """Хранилище игровых паков"""
    
    def __init__(self):
        self.packs_dir = settings.game_packs_dir
        self.logger = logging.getLogger(__name__)
        
        # Создаем директории если не существуют
        os.makedirs(self.packs_dir, exist_ok=True)
        os.makedirs(os.path.join(self.packs_dir, "quiz"), exist_ok=True)
        # os.makedirs(os.path.join(self.packs_dir, "hundred_to_one"), exist_ok=True)
    
    async def save_pack(self, pack: GamePack) -> str:
        """
        Сохранение игрового пака
        
        Args:
            pack: Игровой пак для сохранения
            
        Returns:
            ID сохраненного пака
        """
        try:
            # Генерируем ID если не указан
            if not pack.id:
                pack.id = str(uuid.uuid4())
            
            # Определяем путь к файлу
            filename = f"{pack.id}.json"
            file_path = os.path.join(self.packs_dir, pack.type, filename)
            
            # Сохраняем в файл
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(pack.dict(), f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Игровой пак {pack.id} сохранен: {file_path}")
            return pack.id
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения игрового пака: {e}")
            raise
    
    async def load_pack(self, pack_id: str) -> Optional[GamePack]:
        """
        Загрузка игрового пака
        
        Args:
            pack_id: ID пака
            
        Returns:
            Игровой пак или None если не найден
        """
        try:
            # Ищем файл во всех поддиректориях
            for game_type in ["quiz"]:
                file_path = os.path.join(self.packs_dir, game_type, f"{pack_id}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    pack = GamePack(**data)
                    self.logger.info(f"Игровой пак {pack_id} загружен: {file_path}")
                    return pack
            
            self.logger.warning(f"Игровой пак {pack_id} не найден")
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки игрового пака {pack_id}: {e}")
            return None
    
    async def load_pack_by_name(self, name: str, game_type: Optional[str] = None) -> Optional[GamePack]:
        """
        Загрузка игрового пака по имени
        
        Args:
            name: Название пака
            game_type: Тип игры (опционально)
            
        Returns:
            Игровой пак или None если не найден
        """
        try:
            packs = await self.list_packs(game_type)
            for pack_info in packs:
                if pack_info["name"].lower() == name.lower():
                    return await self.load_pack(pack_info["id"])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска игрового пака по имени {name}: {e}")
            return None
    
    async def list_packs(self, game_type: Optional[str] = None) -> List[Dict]:
        """
        Получение списка игровых паков
        
        Args:
            game_type: Тип игры для фильтрации (опционально)
            
        Returns:
            Список информации о паках
        """
        packs = []
        
        try:
            # Определяем директории для поиска
            search_dirs = []
            if game_type:
                search_dirs = [game_type]
            else:
                search_dirs = ["quiz"]
            
            for dir_name in search_dirs:
                dir_path = os.path.join(self.packs_dir, dir_name)
                if not os.path.exists(dir_path):
                    continue
                
                for filename in os.listdir(dir_path):
                    if filename.endswith('.json'):
                        file_path = os.path.join(dir_path, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            pack_info = {
                                "id": data.get("id", filename[:-5]),  # Убираем .json
                                "name": data.get("name", "Без названия"),
                                "description": data.get("description", ""),
                                "type": data.get("type", dir_name),
                                "author": data.get("author"),
                                "difficulty": data.get("difficulty"),
                                "estimated_time": data.get("estimated_time"),
                                "created_at": data.get("created_at"),
                                "version": data.get("version", "1.0"),
                                "tags": data.get("tags", []),
                                "questions_count": len(data.get("questions", [])) if "questions" in data else None,
                                "rounds_count": len(data.get("rounds", [])) if "rounds" in data else None
                            }
                            
                            packs.append(pack_info)
                            
                        except Exception as e:
                            self.logger.error(f"Ошибка чтения файла {file_path}: {e}")
                            continue
            
            # Сортируем по дате создания (новые первыми)
            packs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return packs
            
        except Exception as e:
            self.logger.error(f"Ошибка получения списка игровых паков: {e}")
            return []
    
    async def delete_pack(self, pack_id: str) -> bool:
        """
        Удаление игрового пака
        
        Args:
            pack_id: ID пака
            
        Returns:
            True если пак удален
        """
        try:
            # Ищем файл во всех поддиректориях
            for game_type in ["quiz"]:
                file_path = os.path.join(self.packs_dir, game_type, f"{pack_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.info(f"Игровой пак {pack_id} удален: {file_path}")
                    return True
            
            self.logger.warning(f"Игровой пак {pack_id} не найден для удаления")
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления игрового пака {pack_id}: {e}")
            return False
    
    async def pack_exists(self, pack_id: str) -> bool:
        """
        Проверка существования пака
        
        Args:
            pack_id: ID пака
            
        Returns:
            True если пак существует
        """
        for game_type in ["quiz"]:
            file_path = os.path.join(self.packs_dir, game_type, f"{pack_id}.json")
            if os.path.exists(file_path):
                return True
        return False
    
    async def get_pack_info(self, pack_id: str) -> Optional[Dict]:
        """
        Получение краткой информации о паке
        
        Args:
            pack_id: ID пака
            
        Returns:
            Информация о паке или None
        """
        try:
            pack = await self.load_pack(pack_id)
            if not pack:
                return None
            
            return {
                "id": pack.id,
                "name": pack.name,
                "description": pack.description,
                "type": pack.type,
                "author": pack.author,
                "difficulty": pack.difficulty,
                "estimated_time": pack.estimated_time,
                "created_at": pack.created_at,
                "version": pack.version,
                "tags": pack.tags,
                "questions_count": len(pack.questions) if pack.questions else None,
                "rounds_count": len(pack.rounds) if pack.rounds else None
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о паке {pack_id}: {e}")
            return None
    
    async def search_packs(self, query: str, game_type: Optional[str] = None) -> List[Dict]:
        """
        Поиск игровых паков
        
        Args:
            query: Поисковый запрос
            game_type: Тип игры для фильтрации
            
        Returns:
            Список найденных паков
        """
        try:
            all_packs = await self.list_packs(game_type)
            query_lower = query.lower()
            
            found_packs = []
            for pack in all_packs:
                # Поиск в названии, описании и тегах
                if (query_lower in pack["name"].lower() or
                    query_lower in pack.get("description", "").lower() or
                    any(query_lower in tag.lower() for tag in pack.get("tags", []))):
                    found_packs.append(pack)
            
            return found_packs
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска игровых паков по запросу '{query}': {e}")
            return []
    
    async def get_stats(self) -> Dict:
        """
        Получение статистики по игровым пакам
        
        Returns:
            Статистика
        """
        try:
            all_packs = await self.list_packs()
            
            stats = {
                "total_packs": len(all_packs),
                "by_type": {},
                "by_difficulty": {},
                "total_questions": 0,
                "total_rounds": 0
            }
            
            for pack in all_packs:
                # По типам
                pack_type = pack.get("type", "unknown")
                stats["by_type"][pack_type] = stats["by_type"].get(pack_type, 0) + 1
                
                # По сложности
                difficulty = pack.get("difficulty", "unknown")
                stats["by_difficulty"][difficulty] = stats["by_difficulty"].get(difficulty, 0) + 1
                
                # Подсчет вопросов и раундов
                if pack.get("questions_count"):
                    stats["total_questions"] += pack["questions_count"]
                if pack.get("rounds_count"):
                    stats["total_rounds"] += pack["rounds_count"]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики игровых паков: {e}")
            return {}


# Глобальный экземпляр хранилища паков
pack_storage = PackStorage()