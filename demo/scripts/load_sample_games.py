#!/usr/bin/env python3
"""
Script to load sample games into the Game Telegram system.
"""

import json
import os
import sys
import argparse
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class GameLoader:
    """Load sample games into the system."""
    
    def __init__(self, base_url: str = "http://localhost:8002", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def load_game(self, game_data: Dict[str, Any]) -> bool:
        """Load a single game into the system."""
        try:
            print(f"Loading game: {game_data['title']}")
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/games",
                json=game_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ Successfully loaded: {game_data['title']} (ID: {result['data']['id']})")
                return True
            else:
                print(f"❌ Failed to load {game_data['title']}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error loading {game_data['title']}: {str(e)}")
            return False
    
    async def load_games_from_directory(self, directory: Path, game_type: str = None) -> int:
        """Load all games from a directory."""
        loaded_count = 0
        
        if not directory.exists():
            print(f"❌ Directory not found: {directory}")
            return 0
        
        for file_path in directory.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                
                # Filter by game type if specified
                if game_type and game_data.get('type') != game_type:
                    continue
                
                if await self.load_game(game_data):
                    loaded_count += 1
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in {file_path}: {str(e)}")
            except Exception as e:
                print(f"❌ Error processing {file_path}: {str(e)}")
        
        return loaded_count
    
    async def check_connection(self) -> bool:
        """Check if the game engine is accessible."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

def get_sample_games_directory() -> Path:
    """Get the sample games directory path."""
    script_dir = Path(__file__).parent
    return script_dir.parent / "sample-games"

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Load sample games into Game Telegram system")
    parser.add_argument("--type", choices=["quiz", "family_feud", "word_game"], 
                       help="Load only games of specific type")
    parser.add_argument("--all", action="store_true", help="Load all sample games")
    parser.add_argument("--url", default="http://localhost:8002", 
                       help="Game Engine API URL (default: http://localhost:8002)")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--file", help="Load specific game file")
    
    args = parser.parse_args()
    
    # Determine what to load
    if not any([args.type, args.all, args.file]):
        print("❌ Please specify --type, --all, or --file")
        return 1
    
    async with GameLoader(args.url, args.api_key) as loader:
        # Check connection
        print("🔍 Checking connection to Game Engine...")
        if not await loader.check_connection():
            print(f"❌ Cannot connect to Game Engine at {args.url}")
            print("Make sure the Game Engine service is running")
            return 1
        
        print("✅ Connected to Game Engine")
        
        loaded_count = 0
        
        if args.file:
            # Load specific file
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                return 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                
                if await loader.load_game(game_data):
                    loaded_count = 1
                    
            except Exception as e:
                print(f"❌ Error loading file {file_path}: {str(e)}")
                return 1
        
        else:
            # Load from directory
            games_dir = get_sample_games_directory()
            game_type = args.type if not args.all else None
            
            print(f"📁 Loading games from: {games_dir}")
            if game_type:
                print(f"🎮 Game type filter: {game_type}")
            
            loaded_count = await loader.load_games_from_directory(games_dir, game_type)
        
        print(f"\n📊 Summary:")
        print(f"✅ Successfully loaded: {loaded_count} games")
        
        if loaded_count > 0:
            print(f"\n🎮 Games are now available in the system!")
            print(f"🌐 You can view them at: {args.url}/api/v1/games")
        
        return 0 if loaded_count > 0 else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)