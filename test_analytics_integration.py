#!/usr/bin/env python3
"""
Comprehensive integration test for the analytics system
Tests all components: API endpoints, database operations, bot handlers
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
import httpx
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Test configuration
TEST_CONFIG = {
    "analytics_service_url": "http://localhost:8006",
    "database_url": "postgresql+asyncpg://postgres:password@localhost:5432/game_telegram_test",
    "redis_url": "redis://localhost:6379/1"
}

class AnalyticsIntegrationTest:
    """Integration test suite for analytics system"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=TEST_CONFIG["analytics_service_url"])
        self.test_data = {}
        
    async def setup(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")
        
        # Create test data
        self.test_data = {
            "session_id": str(uuid.uuid4()),
            "game_id": str(uuid.uuid4()),
            "player_id": str(uuid.uuid4()),
            "game_name": "Test Quiz Game",
            "game_type": "quiz",
            "player_name": "Test Player"
        }
        
        print(f"✅ Test data created: {self.test_data}")
        
    async def cleanup(self):
        """Cleanup test environment"""
        print("🧹 Cleaning up test environment...")
        await self.client.aclose()
        
    async def test_health_check(self) -> bool:
        """Test analytics service health"""
        print("\n📊 Testing analytics service health...")
        
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {health_data}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_record_game_result(self) -> bool:
        """Test recording game results"""
        print("\n🎮 Testing game result recording...")
        
        try:
            # Create test game result
            game_result = {
                "session_id": self.test_data["session_id"],
                "game_id": self.test_data["game_id"],
                "game_name": self.test_data["game_name"],
                "game_type": self.test_data["game_type"],
                "start_time": datetime.utcnow().isoformat(),
                "end_time": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "duration": 300,
                "total_players": 1,
                "completed_players": 1,
                "status": "completed"
            }
            
            # Record game result
            response = await self.client.post("/api/results/games", json=game_result)
            
            if response.status_code == 201:
                result_data = response.json()
                print(f"✅ Game result recorded: {result_data}")
                return True
            else:
                print(f"❌ Failed to record game result: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Game result recording error: {e}")
            return False
    
    async def test_record_player_result(self) -> bool:
        """Test recording player results"""
        print("\n👤 Testing player result recording...")
        
        try:
            # Create test player result
            player_result = {
                "session_id": self.test_data["session_id"],
                "player_id": self.test_data["player_id"],
                "player_name": self.test_data["player_name"],
                "total_score": 850,
                "correct_answers": 8,
                "total_questions": 10,
                "accuracy_percentage": 80.0,
                "time_taken": 240,
                "average_time_per_question": 24.0,
                "position": 1,
                "completed": True
            }
            
            # Record player result
            response = await self.client.post("/api/results/players", json=player_result)
            
            if response.status_code == 201:
                result_data = response.json()
                print(f"✅ Player result recorded: {result_data}")
                return True
            else:
                print(f"❌ Failed to record player result: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Player result recording error: {e}")
            return False
    
    async def test_get_player_stats(self) -> bool:
        """Test retrieving player statistics"""
        print("\n📈 Testing player statistics retrieval...")
        
        try:
            response = await self.client.get(f"/api/analytics/players/{self.test_data['player_id']}/stats")
            
            if response.status_code == 200:
                stats_data = response.json()
                print(f"✅ Player stats retrieved: {stats_data}")
                return True
            else:
                print(f"❌ Failed to get player stats: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Player stats retrieval error: {e}")
            return False
    
    async def test_get_leaderboard(self) -> bool:
        """Test leaderboard functionality"""
        print("\n🏆 Testing leaderboard...")
        
        try:
            response = await self.client.get("/api/leaderboard/global?limit=10")
            
            if response.status_code == 200:
                leaderboard_data = response.json()
                print(f"✅ Leaderboard retrieved: {leaderboard_data}")
                return True
            else:
                print(f"❌ Failed to get leaderboard: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Leaderboard retrieval error: {e}")
            return False
    
    async def test_achievements(self) -> bool:
        """Test achievements system"""
        print("\n🏅 Testing achievements system...")
        
        try:
            response = await self.client.get(f"/api/achievements/players/{self.test_data['player_id']}")
            
            if response.status_code == 200:
                achievements_data = response.json()
                print(f"✅ Achievements retrieved: {achievements_data}")
                return True
            else:
                print(f"❌ Failed to get achievements: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Achievements retrieval error: {e}")
            return False
    
    async def test_analytics_endpoints(self) -> bool:
        """Test analytics endpoints"""
        print("\n📊 Testing analytics endpoints...")
        
        endpoints_to_test = [
            "/api/analytics/system/metrics",
            "/api/analytics/games/popular?limit=5",
            "/api/analytics/trends/daily?days=7"
        ]
        
        success_count = 0
        
        for endpoint in endpoints_to_test:
            try:
                response = await self.client.get(endpoint)
                if response.status_code == 200:
                    print(f"✅ {endpoint}: OK")
                    success_count += 1
                else:
                    print(f"❌ {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint}: Error - {e}")
        
        return success_count == len(endpoints_to_test)
    
    async def test_export_functionality(self) -> bool:
        """Test data export functionality"""
        print("\n📋 Testing export functionality...")
        
        try:
            export_request = {
                "export_type": "results",
                "format": "json",
                "date_from": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "date_to": datetime.utcnow().isoformat()
            }
            
            response = await self.client.post("/api/export/data", json=export_request)
            
            if response.status_code == 200:
                export_data = response.json()
                print(f"✅ Export functionality working: {export_data}")
                return True
            else:
                print(f"❌ Export failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Export functionality error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("🚀 Starting Analytics System Integration Tests")
        print("=" * 60)
        
        await self.setup()
        
        test_results = {}
        
        # Run all tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Record Game Result", self.test_record_game_result),
            ("Record Player Result", self.test_record_player_result),
            ("Get Player Stats", self.test_get_player_stats),
            ("Get Leaderboard", self.test_get_leaderboard),
            ("Test Achievements", self.test_achievements),
            ("Analytics Endpoints", self.test_analytics_endpoints),
            ("Export Functionality", self.test_export_functionality)
        ]
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                test_results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                test_results[test_name] = False
        
        await self.cleanup()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! Analytics system is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the logs above.")
        
        return test_results


async def main():
    """Main test runner"""
    test_suite = AnalyticsIntegrationTest()
    results = await test_suite.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())