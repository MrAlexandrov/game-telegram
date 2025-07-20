"""
Game Engine Service - Enhanced Module Loader
Loads and manages game modules with unified interface
"""

import os
import sys
import importlib.util
from typing import Dict, Any, List, Optional, Type, Union
import structlog
from pathlib import Path
import asyncio
import json
from datetime import datetime

from ..config import settings

logger = structlog.get_logger()


class ModuleLoadError(Exception):
    """Exception raised when module loading fails"""
    pass


class ModuleValidationError(Exception):
    """Exception raised when module validation fails"""
    pass


class GameModuleRegistry:
    """Registry for managing game modules"""
    
    def __init__(self):
        self.modules: Dict[str, Any] = {}
        self.module_metadata: Dict[str, Dict[str, Any]] = {}
        self.load_history: List[Dict[str, Any]] = []
    
    def register_module(self, game_type: str, module_instance: Any, metadata: Optional[Dict[str, Any]] = None):
        """Register a game module"""
        self.modules[game_type] = module_instance
        self.module_metadata[game_type] = metadata or {}
        
        self.load_history.append({
            "game_type": game_type,
            "module_name": getattr(module_instance, 'name', module_instance.__class__.__name__),
            "version": getattr(module_instance, 'version', '1.0.0'),
            "loaded_at": datetime.utcnow().isoformat(),
            "status": "registered"
        })
        
        logger.info("Module registered", game_type=game_type, 
                   module_name=getattr(module_instance, 'name', 'Unknown'))
    
    def get_module(self, game_type: str) -> Optional[Any]:
        """Get module by game type"""
        return self.modules.get(game_type)
    
    def get_all_modules(self) -> Dict[str, Any]:
        """Get all registered modules"""
        return self.modules.copy()
    
    def get_module_metadata(self, game_type: str) -> Optional[Dict[str, Any]]:
        """Get module metadata"""
        return self.module_metadata.get(game_type)
    
    def unregister_module(self, game_type: str) -> bool:
        """Unregister a module"""
        if game_type in self.modules:
            del self.modules[game_type]
            self.module_metadata.pop(game_type, None)
            
            self.load_history.append({
                "game_type": game_type,
                "loaded_at": datetime.utcnow().isoformat(),
                "status": "unregistered"
            })
            
            logger.info("Module unregistered", game_type=game_type)
            return True
        return False
    
    def list_modules(self) -> List[Dict[str, Any]]:
        """List all registered modules with their info"""
        modules_info = []
        for game_type, module in self.modules.items():
            info = {
                "game_type": game_type,
                "name": getattr(module, 'name', module.__class__.__name__),
                "version": getattr(module, 'version', '1.0.0'),
                "description": getattr(module, 'description', ''),
                "supported_question_types": getattr(module, 'get_supported_question_types', lambda: [])(),
                "metadata": self.module_metadata.get(game_type, {})
            }
            modules_info.append(info)
        return modules_info


class ModuleLoader:
    """Enhanced game module loader with unified interface support"""
    
    def __init__(self):
        self.registry = GameModuleRegistry()
        self.modules_path = Path(getattr(settings, 'GAME_MODULES_PATH', './game-modules'))
        self.builtin_modules_path = Path(__file__).parent
        self.load_errors: List[Dict[str, Any]] = []
    
    async def load_all_modules(self) -> Dict[str, Any]:
        """Load all available game modules"""
        logger.info("Starting module loading process", modules_path=str(self.modules_path))
        
        load_results = {
            "loaded": [],
            "failed": [],
            "total_attempted": 0,
            "load_time": datetime.utcnow().isoformat()
        }
        
        try:
            # Load built-in modules first
            builtin_results = await self._load_builtin_modules()
            load_results["loaded"].extend(builtin_results["loaded"])
            load_results["failed"].extend(builtin_results["failed"])
            load_results["total_attempted"] += builtin_results["total_attempted"]
            
            # Load external modules
            if self.modules_path.exists():
                external_results = await self._load_external_modules()
                load_results["loaded"].extend(external_results["loaded"])
                load_results["failed"].extend(external_results["failed"])
                load_results["total_attempted"] += external_results["total_attempted"]
            else:
                logger.warning("External modules path does not exist", path=str(self.modules_path))
            
            logger.info("Module loading completed", 
                       loaded_count=len(load_results["loaded"]),
                       failed_count=len(load_results["failed"]),
                       total_modules=len(self.registry.modules))
            
            return load_results
            
        except Exception as e:
            logger.error("Critical error during module loading", error=str(e))
            load_results["failed"].append({
                "module": "module_loader",
                "error": str(e),
                "error_type": "critical"
            })
            return load_results
    
    async def _load_builtin_modules(self) -> Dict[str, Any]:
        """Load built-in game modules"""
        results = {"loaded": [], "failed": [], "total_attempted": 0}
        
        builtin_modules = [
            {
                "name": "quiz",
                "import_path": "game_modules.quiz.quiz_module",
                "class_name": "QuizModule"
            },
            {
                "name": "family_feud", 
                "import_path": "services.game_engine.app.services.family_feud_module",
                "class_name": "FamilyFeudModule"
            }
        ]
        
        for module_config in builtin_modules:
            results["total_attempted"] += 1
            try:
                await self._load_builtin_module(module_config)
                results["loaded"].append(module_config["name"])
                logger.info("Built-in module loaded", name=module_config["name"])
            except Exception as e:
                error_info = {
                    "module": module_config["name"],
                    "error": str(e),
                    "error_type": "builtin_load_error"
                }
                results["failed"].append(error_info)
                self.load_errors.append(error_info)
                logger.error("Failed to load built-in module", 
                           name=module_config["name"], error=str(e))
        
        return results
    
    async def _load_builtin_module(self, module_config: Dict[str, Any]):
        """Load a specific built-in module"""
        try:
            # Try to import from the new location first
            if module_config["name"] == "quiz":
                try:
                    # Import from new quiz module location
                    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
                    from game_modules.quiz.quiz_module import QuizModule
                    module_instance = QuizModule()
                    self.registry.register_module("quiz", module_instance, {
                        "source": "new_implementation",
                        "location": "game-modules/quiz/"
                    })
                    return
                except ImportError:
                    # Fall back to old implementation
                    from .quiz_module import QuizModule as OldQuizModule
                    module_instance = OldQuizModule()
                    # Wrap old module to match new interface
                    module_instance = self._wrap_legacy_module(module_instance, "quiz")
                    self.registry.register_module("quiz", module_instance, {
                        "source": "legacy_implementation",
                        "location": "services/game-engine/app/services/"
                    })
            
            elif module_config["name"] == "family_feud":
                from .family_feud_module import FamilyFeudModule
                module_instance = FamilyFeudModule()
                # Wrap legacy module to match new interface
                module_instance = self._wrap_legacy_module(module_instance, "family_feud")
                self.registry.register_module("family_feud", module_instance, {
                    "source": "legacy_implementation", 
                    "location": "services/game-engine/app/services/"
                })
            
        except Exception as e:
            raise ModuleLoadError(f"Failed to load builtin module {module_config['name']}: {str(e)}")
    
    def _wrap_legacy_module(self, legacy_module: Any, game_type: str) -> Any:
        """Wrap legacy module to match new interface"""
        class LegacyModuleWrapper:
            def __init__(self, legacy_mod, g_type):
                self.legacy_module = legacy_mod
                self.game_type = g_type
                self.name = getattr(legacy_mod, 'name', legacy_mod.__class__.__name__)
                self.version = getattr(legacy_mod, 'version', '1.0.0')
                self.description = getattr(legacy_mod, 'description', f'Legacy {g_type} module')
            
            def get_supported_question_types(self):
                return getattr(self.legacy_module, 'get_supported_question_types', lambda: [])()
            
            def get_config_schema(self):
                return getattr(self.legacy_module, 'get_config_schema', lambda: {})()
            
            def get_default_config(self):
                return getattr(self.legacy_module, 'get_default_config', lambda: {})()
            
            def validate_question(self, question_data):
                return getattr(self.legacy_module, 'validate_question', lambda x: {"is_valid": True, "errors": [], "warnings": []})(question_data)
            
            async def process_question(self, question, session):
                # Convert to legacy format
                if hasattr(question, 'content'):
                    question_data = question.content.copy()
                    question_data.update({
                        "id": question.id,
                        "type": question.question_type,
                        "points": question.points,
                        "time_limit": question.time_limit
                    })
                else:
                    question_data = question
                
                session_data = session if isinstance(session, dict) else {
                    "session_id": getattr(session, 'id', ''),
                    "config": getattr(session, 'config', {})
                }
                
                if hasattr(self.legacy_module, 'process_question'):
                    return self.legacy_module.process_question(question_data, session_data)
                else:
                    return question_data
            
            async def validate_answer(self, answer, question, **kwargs):
                answer_text = answer if isinstance(answer, str) else getattr(answer, 'answer_text', '')
                question_data = question if isinstance(question, dict) else getattr(question, 'content', {})
                
                if hasattr(self.legacy_module, 'validate_answer'):
                    return self.legacy_module.validate_answer(answer_text, question_data)
                else:
                    return {"is_correct": False, "points_earned": 0}
            
            async def calculate_score(self, answers, question):
                if hasattr(self.legacy_module, 'calculate_score'):
                    answer_dicts = []
                    for answer in answers:
                        if hasattr(answer, 'user_id'):
                            answer_dicts.append({
                                "user_id": answer.user_id,
                                "points_earned": answer.points_earned,
                                "is_correct": answer.is_correct
                            })
                        else:
                            answer_dicts.append(answer)
                    
                    question_data = question if isinstance(question, dict) else getattr(question, 'content', {})
                    total_score = self.legacy_module.calculate_score(answer_dicts, question_data)
                    
                    # Convert to expected format
                    scores = {}
                    for answer in answers:
                        user_id = getattr(answer, 'user_id', '') if hasattr(answer, 'user_id') else answer.get('user_id', '')
                        scores[user_id] = getattr(answer, 'points_earned', 0) if hasattr(answer, 'points_earned') else answer.get('points_earned', 0)
                    
                    return scores
                else:
                    return {}
            
            async def get_results(self, session, all_answers):
                session_data = session if isinstance(session, dict) else {
                    "session_id": getattr(session, 'id', ''),
                    "players": getattr(session, 'players', []),
                    "answers": []
                }
                
                # Add answers to session data for legacy compatibility
                session_data["answers"] = []
                for answer in all_answers:
                    if hasattr(answer, 'user_id'):
                        session_data["answers"].append({
                            "user_id": answer.user_id,
                            "question_id": answer.question_id,
                            "is_correct": answer.is_correct,
                            "points_earned": answer.points_earned
                        })
                    else:
                        session_data["answers"].append(answer)
                
                if hasattr(self.legacy_module, 'get_results'):
                    return self.legacy_module.get_results(session_data)
                else:
                    return {"total_score": 0, "accuracy": 0}
        
        return LegacyModuleWrapper(legacy_module, game_type)
    
    async def _load_external_modules(self) -> Dict[str, Any]:
        """Load external game modules from filesystem"""
        results = {"loaded": [], "failed": [], "total_attempted": 0}
        
        try:
            for module_dir in self.modules_path.iterdir():
                if not module_dir.is_dir() or module_dir.name.startswith('.'):
                    continue
                
                results["total_attempted"] += 1
                try:
                    await self._load_external_module(module_dir)
                    results["loaded"].append(module_dir.name)
                except Exception as e:
                    error_info = {
                        "module": module_dir.name,
                        "error": str(e),
                        "error_type": "external_load_error",
                        "path": str(module_dir)
                    }
                    results["failed"].append(error_info)
                    self.load_errors.append(error_info)
                    logger.error("Failed to load external module", 
                               module=module_dir.name, error=str(e))
        
        except Exception as e:
            logger.error("Error scanning external modules directory", error=str(e))
        
        return results
    
    async def _load_external_module(self, module_dir: Path):
        """Load a single external module"""
        module_name = module_dir.name
        
        # Look for module file
        possible_files = [
            module_dir / f"{module_name}_module.py",
            module_dir / "module.py",
            module_dir / "__init__.py"
        ]
        
        module_file = None
        for file_path in possible_files:
            if file_path.exists():
                module_file = file_path
                break
        
        if not module_file:
            raise ModuleLoadError(f"No module file found in {module_dir}")
        
        # Load module spec
        spec = importlib.util.spec_from_file_location(f"external_{module_name}", module_file)
        if not spec or not spec.loader:
            raise ModuleLoadError(f"Cannot create module spec for {module_name}")
        
        # Load the module
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"external_{module_name}"] = module
        spec.loader.exec_module(module)
        
        # Find the game module class
        module_class = self._find_game_module_class(module, module_name)
        if not module_class:
            raise ModuleLoadError(f"No GameModule subclass found in {module_name}")
        
        # Instantiate and register
        try:
            module_instance = module_class()
            game_type = getattr(module_instance, 'game_type', module_name)
            
            self.registry.register_module(game_type, module_instance, {
                "source": "external",
                "location": str(module_dir),
                "file": str(module_file)
            })
            
        except Exception as e:
            raise ModuleLoadError(f"Failed to instantiate module {module_name}: {str(e)}")
    
    def _find_game_module_class(self, module: Any, module_name: str) -> Optional[Type]:
        """Find GameModule subclass in loaded module"""
        # Try to import the base GameModule class
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
            from game_modules.base.game_module import GameModule as BaseGameModule
        except ImportError:
            # Fallback to checking for common patterns
            BaseGameModule = None
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type):
                # Check if it's a GameModule subclass
                if BaseGameModule and issubclass(attr, BaseGameModule) and attr != BaseGameModule:
                    return attr
                # Check for common naming patterns
                elif (attr_name.endswith('Module') or 
                      attr_name.endswith('Game') or
                      attr_name.lower() == f"{module_name}module"):
                    # Basic duck typing check
                    required_methods = ['get_supported_question_types', 'process_question', 'validate_answer']
                    if all(hasattr(attr, method) for method in required_methods):
                        return attr
        
        return None
    
    def get_module(self, game_type: str) -> Optional[Any]:
        """Get module by game type"""
        return self.registry.get_module(game_type)
    
    def get_all_modules(self) -> Dict[str, Any]:
        """Get all loaded modules"""
        return self.registry.get_all_modules()
    
    def get_module_info(self, game_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed module information"""
        module = self.registry.get_module(game_type)
        if not module:
            return None
        
        info = {
            "game_type": game_type,
            "name": getattr(module, 'name', module.__class__.__name__),
            "version": getattr(module, 'version', '1.0.0'),
            "description": getattr(module, 'description', ''),
            "supported_question_types": [],
            "config_schema": {},
            "default_config": {},
            "metadata": self.registry.get_module_metadata(game_type)
        }
        
        # Safely get module capabilities
        try:
            if hasattr(module, 'get_supported_question_types'):
                info["supported_question_types"] = module.get_supported_question_types()
        except Exception as e:
            logger.warning("Error getting supported question types", game_type=game_type, error=str(e))
        
        try:
            if hasattr(module, 'get_config_schema'):
                info["config_schema"] = module.get_config_schema()
        except Exception as e:
            logger.warning("Error getting config schema", game_type=game_type, error=str(e))
        
        try:
            if hasattr(module, 'get_default_config'):
                info["default_config"] = module.get_default_config()
        except Exception as e:
            logger.warning("Error getting default config", game_type=game_type, error=str(e))
        
        return info
    
    def list_all_modules(self) -> List[Dict[str, Any]]:
        """List all loaded modules with their information"""
        return self.registry.list_modules()
    
    async def validate_game_pack(self, game_type: str, pack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate game pack data using appropriate module"""
        module = self.get_module(game_type)
        if not module:
            return {
                "is_valid": False,
                "errors": [f"Unknown game type: {game_type}"],
                "warnings": []
            }
        
        try:
            errors = []
            warnings = []
            
            # Basic pack structure validation
            if "questions" not in pack_data:
                errors.append("Missing 'questions' field in game pack")
            
            if "metadata" not in pack_data and "meta" not in pack_data:
                warnings.append("Missing metadata in game pack")
            
            # Validate questions using module
            if "questions" in pack_data:
                questions = pack_data["questions"]
                if not isinstance(questions, list):
                    errors.append("'questions' must be a list")
                else:
                    for i, question in enumerate(questions):
                        try:
                            if hasattr(module, 'validate_question'):
                                validation_result = module.validate_question(question)
                                if not validation_result.get("is_valid", True):
                                    question_errors = validation_result.get("errors", [])
                                    for error in question_errors:
                                        errors.append(f"Question {i+1}: {error}")
                                    
                                    question_warnings = validation_result.get("warnings", [])
                                    for warning in question_warnings:
                                        warnings.append(f"Question {i+1}: {warning}")
                        except Exception as e:
                            errors.append(f"Question {i+1}: Validation error - {str(e)}")
            
            # Validate config if present
            config = pack_data.get("config", {})
            if config and hasattr(module, 'validate_game_config'):
                try:
                    config_validation = module.validate_game_config(config)
                    if isinstance(config_validation, dict) and not config_validation.get("is_valid", True):
                        config_errors = config_validation.get("errors", [])
                        for error in config_errors:
                            errors.append(f"Config: {error}")
                except Exception as e:
                    warnings.append(f"Config validation error: {str(e)}")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "validated_questions": len(pack_data.get("questions", [])),
                "module_info": {
                    "name": getattr(module, 'name', 'Unknown'),
                    "version": getattr(module, 'version', '1.0.0')
                }
            }
            
        except Exception as e:
            logger.error("Error validating game pack", game_type=game_type, error=str(e))
            return {
                "is_valid": False,
                "errors": [f"Pack validation error: {str(e)}"],
                "warnings": []
            }
    
    async def reload_module(self, game_type: str) -> Dict[str, Any]:
        """Reload a specific module"""
        try:
            # Unregister current module
            if self.registry.unregister_module(game_type):
                logger.info("Module unregistered for reload", game_type=game_type)
            
            # Reload based on type
            if game_type in ["quiz", "family_feud"]:
                # Reload builtin module
                module_config = {
                    "name": game_type,
                    "import_path": f"services.game_engine.app.services.{game_type}_module",
                    "class_name": f"{game_type.title().replace('_', '')}Module"
                }
                await self._load_builtin_module(module_config)
            else:
                # Try to reload external module
                module_dir = self.modules_path / game_type
                if module_dir.exists():
                    await self._load_external_module(module_dir)
                else:
                    raise ModuleLoadError(f"Module directory not found: {module_dir}")
            
            return {
                "success": True,
                "game_type": game_type,
                "reloaded_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error reloading module", game_type=game_type, error=str(e))
            return {
                "success": False,
                "game_type": game_type,
                "error": str(e)
            }
    
    def get_load_status(self) -> Dict[str, Any]:
        """Get module loading status and statistics"""
        return {
            "total_modules": len(self.registry.modules),
            "loaded_modules": list(self.registry.modules.keys()),
            "load_errors": self.load_errors,
            "load_history": self.registry.load_history,
            "modules_path": str(self.modules_path),
            "builtin_modules_path": str(self.builtin_modules_path)
        }