#!/usr/bin/env python3
"""
API Examples: Game Management

This script demonstrates how to use the Game Engine API for:
- Creating games
- Retrieving games
- Updating games
- Managing game content
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List

class GameAPIExample:
    """Examples for Game Engine API usage."""
    
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
    
    async def create_quiz_game(self) -> str:
        """Example: Create a new quiz game."""
        print("📝 Creating a new quiz game...")
        
        game_data = {
            "title": "Python Programming Quiz",
            "description": "Test your Python programming knowledge",
            "type": "quiz",
            "category": "programming",
            "tags": ["python", "programming", "coding"],
            "settings": {
                "time_limit": 30,
                "randomize_questions": True,
                "show_correct_answer": True,
                "max_players": 100
            },
            "questions": [
                {
                    "text": "What is the output of print(2 ** 3)?",
                    "type": "single_choice",
                    "options": ["6", "8", "9", "16"],
                    "correct_answer": 1,
                    "explanation": "2 ** 3 means 2 to the power of 3, which equals 8",
                    "points": 10
                },
                {
                    "text": "Which of these are Python data types?",
                    "type": "multiple_choice",
                    "options": ["list", "dict", "tuple", "array", "set"],
                    "correct_answers": [0, 1, 2, 4],
                    "explanation": "list, dict, tuple, and set are built-in Python data types. array is from numpy.",
                    "points": 15
                },
                {
                    "text": "Python is case-sensitive",
                    "type": "true_false",
                    "correct_answer": True,
                    "explanation": "Python is case-sensitive, meaning 'Variable' and 'variable' are different.",
                    "points": 5
                }
            ]
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/games",
            json=game_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            game_id = result["data"]["id"]
            print(f"✅ Game created successfully! ID: {game_id}")
            return game_id
        else:
            print(f"❌ Failed to create game: {response.status_code} - {response.text}")
            return None
    
    async def get_game(self, game_id: str) -> Dict[str, Any]:
        """Example: Retrieve a game by ID."""
        print(f"🔍 Retrieving game: {game_id}")
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/games/{game_id}",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            game = result["data"]
            print(f"✅ Retrieved game: {game['title']}")
            print(f"   Type: {game['type']}")
            print(f"   Questions: {len(game['questions'])}")
            return game
        else:
            print(f"❌ Failed to retrieve game: {response.status_code} - {response.text}")
            return None
    
    async def list_games(self, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Example: List games with optional filtering."""
        print(f"📋 Listing games (limit: {limit})")
        
        params = {"limit": limit}
        if category:
            params["category"] = category
            print(f"   Category filter: {category}")
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/games",
            params=params,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            games = result["data"]
            print(f"✅ Found {len(games)} games")
            
            for game in games:
                print(f"   - {game['title']} ({game['type']}) - {len(game.get('questions', []))} questions")
            
            return games
        else:
            print(f"❌ Failed to list games: {response.status_code} - {response.text}")
            return []
    
    async def update_game(self, game_id: str) -> bool:
        """Example: Update a game."""
        print(f"✏️ Updating game: {game_id}")
        
        update_data = {
            "description": "Updated: Test your Python programming knowledge with advanced questions",
            "tags": ["python", "programming", "coding", "advanced"],
            "settings": {
                "time_limit": 45,  # Increased time limit
                "difficulty": "hard"
            }
        }
        
        response = await self.client.patch(
            f"{self.base_url}/api/v1/games/{game_id}",
            json=update_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Game updated successfully")
            print(f"   New description: {result['data']['description']}")
            return True
        else:
            print(f"❌ Failed to update game: {response.status_code} - {response.text}")
            return False
    
    async def delete_game(self, game_id: str) -> bool:
        """Example: Delete a game."""
        print(f"🗑️ Deleting game: {game_id}")
        
        response = await self.client.delete(
            f"{self.base_url}/api/v1/games/{game_id}",
            headers=self.get_headers()
        )
        
        if response.status_code == 204:
            print(f"✅ Game deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete game: {response.status_code} - {response.text}")
            return False

async def run_examples():
    """Run all API examples."""
    print("🚀 Game Management API Examples")
    print("=" * 50)
    
    async with GameAPIExample() as api:
        # Create a new game
        game_id = await api.create_quiz_game()
        if not game_id:
            print("❌ Cannot continue without a game ID")
            return
        
        print("\n" + "-" * 30)
        
        # Retrieve the created game
        game = await api.get_game(game_id)
        
        print("\n" + "-" * 30)
        
        # List all games
        await api.list_games(limit=5)
        
        print("\n" + "-" * 30)
        
        # Update the game
        await api.update_game(game_id)
        
        print("\n" + "-" * 30)
        
        # Clean up - delete the test game
        await api.delete_game(game_id)
        
        print("\n✅ All examples completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_examples())