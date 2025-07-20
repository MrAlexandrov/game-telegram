#!/usr/bin/env python3
"""
Script to create test users for the Game Telegram system.
"""

import asyncio
import argparse
import httpx
import random
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class TestUserCreator:
    """Create test users for development and testing."""
    
    def __init__(self, base_url: str = "http://localhost:8004", api_key: str = None):
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
    
    def generate_test_users(self, count: int) -> List[Dict[str, Any]]:
        """Generate test user data."""
        first_names = [
            "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Helen",
            "Ivan", "Julia", "Kevin", "Laura", "Michael", "Nina", "Oliver", "Paula",
            "Quinn", "Rachel", "Samuel", "Tina", "Ulrich", "Victoria", "William", "Xara",
            "Yuki", "Zoe", "Alex", "Beth", "Chris", "Dana", "Eric", "Faith", "Gary", "Hope"
        ]
        
        last_names = [
            "Anderson", "Brown", "Clark", "Davis", "Evans", "Fisher", "Garcia", "Harris",
            "Johnson", "King", "Lee", "Miller", "Nelson", "O'Connor", "Parker", "Quinn",
            "Roberts", "Smith", "Taylor", "Underwood", "Valdez", "Wilson", "Xavier", "Young", "Zhang"
        ]
        
        languages = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
        
        users = []
        used_ids = set()
        
        for i in range(count):
            # Generate unique user ID
            while True:
                user_id = random.randint(100000000, 999999999)
                if user_id not in used_ids:
                    used_ids.add(user_id)
                    break
            
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
            
            user = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "language_code": random.choice(languages),
                "is_bot": False,
                "is_premium": random.choice([True, False]) if random.random() < 0.2 else False,
                "settings": {
                    "notifications": random.choice([True, False]),
                    "theme": random.choice(["light", "dark", "auto"]),
                    "difficulty_preference": random.choice(["easy", "medium", "hard"]),
                    "favorite_categories": random.sample(
                        ["general", "science", "history", "sports", "entertainment", "geography"], 
                        random.randint(1, 3)
                    )
                }
            }
            
            users.append(user)
        
        return users
    
    async def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a single test user."""
        try:
            print(f"Creating user: {user_data['first_name']} {user_data['last_name']} (@{user_data['username']})")
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/users",
                json=user_data,
                headers=self.get_headers()
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Successfully created user: {user_data['username']}")
                return True
            else:
                print(f"❌ Failed to create user {user_data['username']}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating user {user_data['username']}: {str(e)}")
            return False
    
    async def create_admin_user(self) -> bool:
        """Create a demo admin user."""
        admin_user = {
            "user_id": 123456789,
            "username": "demo_admin",
            "first_name": "Demo",
            "last_name": "Admin",
            "language_code": "en",
            "is_bot": False,
            "is_premium": True,
            "is_admin": True,
            "settings": {
                "notifications": True,
                "theme": "dark",
                "admin_dashboard": True
            }
        }
        
        print("👑 Creating demo admin user...")
        return await self.create_user(admin_user)
    
    async def check_connection(self) -> bool:
        """Check if the user manager is accessible."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Create test users for Game Telegram system")
    parser.add_argument("--count", type=int, default=10, help="Number of test users to create")
    parser.add_argument("--admin", action="store_true", help="Create demo admin user")
    parser.add_argument("--url", default="http://localhost:8004", 
                       help="User Manager API URL (default: http://localhost:8004)")
    parser.add_argument("--api-key", help="API key for authentication")
    
    args = parser.parse_args()
    
    async with TestUserCreator(args.url, args.api_key) as creator:
        # Check connection
        print("🔍 Checking connection to User Manager...")
        if not await creator.check_connection():
            print(f"❌ Cannot connect to User Manager at {args.url}")
            print("Make sure the User Manager service is running")
            return 1
        
        print("✅ Connected to User Manager")
        
        created_count = 0
        
        # Create admin user if requested
        if args.admin:
            if await creator.create_admin_user():
                created_count += 1
        
        # Create regular test users
        if args.count > 0:
            print(f"👥 Generating {args.count} test users...")
            test_users = creator.generate_test_users(args.count)
            
            for user in test_users:
                if await creator.create_user(user):
                    created_count += 1
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.1)
        
        print(f"\n📊 Summary:")
        print(f"✅ Successfully created: {created_count} users")
        
        if args.admin and created_count > 0:
            print(f"\n👑 Demo admin user created:")
            print(f"   Username: demo_admin")
            print(f"   User ID: 123456789")
            print(f"   Use this for testing admin bot functionality")
        
        if created_count > 0:
            print(f"\n👥 Test users are now available in the system!")
            print(f"🌐 You can view them at: {args.url}/api/v1/users")
        
        return 0 if created_count > 0 else 1

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
