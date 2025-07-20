"""
Integration tests for all API endpoints across microservices.
"""
import pytest
import httpx
import json
from typing import Dict, Any
from unittest.mock import patch, AsyncMock


class TestGameEngineAPI:
    """Test Game Engine service API endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str]):
        """Test health check endpoint."""
        response = await http_client.get(f"{api_base_urls['game_engine']}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_create_game(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_game_data: Dict[str, Any]):
        """Test game creation endpoint."""
        with patch('services.game_engine.app.services.game_processor.GameProcessor.create_game') as mock_create:
            mock_create.return_value = sample_game_data
            
            response = await http_client.post(
                f"{api_base_urls['game_engine']}/api/v1/games",
                json=sample_game_data
            )
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == sample_game_data["id"]
            assert data["title"] == sample_game_data["title"]
    
    @pytest.mark.asyncio
    async def test_get_game(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_game_data: Dict[str, Any]):
        """Test get game endpoint."""
        game_id = sample_game_data["id"]
        
        with patch('services.game_engine.app.services.game_processor.GameProcessor.get_game') as mock_get:
            mock_get.return_value = sample_game_data
            
            response = await http_client.get(f"{api_base_urls['game_engine']}/api/v1/games/{game_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == game_id
    
    @pytest.mark.asyncio
    async def test_list_games(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_game_data: Dict[str, Any]):
        """Test list games endpoint."""
        with patch('services.game_engine.app.services.game_processor.GameProcessor.list_games') as mock_list:
            mock_list.return_value = [sample_game_data]
            
            response = await http_client.get(f"{api_base_urls['game_engine']}/api/v1/games")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == sample_game_data["id"]
    
    @pytest.mark.asyncio
    async def test_import_game_pack(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_game_data: Dict[str, Any]):
        """Test game pack import endpoint."""
        with patch('services.game_engine.app.services.game_importer.GameImporter.import_pack') as mock_import:
            mock_import.return_value = {"imported_games": 1, "games": [sample_game_data]}
            
            files = {"file": ("test_pack.json", json.dumps(sample_game_data), "application/json")}
            response = await http_client.post(
                f"{api_base_urls['game_engine']}/api/v1/import",
                files=files
            )
            assert response.status_code == 200
            data = response.json()
            assert data["imported_games"] == 1


class TestSessionManagerAPI:
    """Test Session Manager service API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_session_data: Dict[str, Any]):
        """Test session creation endpoint."""
        with patch('services.session_manager.app.services.redis_service.RedisService.create_session') as mock_create:
            mock_create.return_value = sample_session_data
            
            response = await http_client.post(
                f"{api_base_urls['session_manager']}/api/v1/sessions",
                json={
                    "game_id": sample_session_data["game_id"],
                    "admin_id": sample_session_data["admin_id"],
                    "settings": sample_session_data["settings"]
                }
            )
            assert response.status_code == 201
            data = response.json()
            assert data["session_id"] == sample_session_data["session_id"]
    
    @pytest.mark.asyncio
    async def test_join_session(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_session_data: Dict[str, Any], sample_player_data: Dict[str, Any]):
        """Test player joining session endpoint."""
        session_id = sample_session_data["session_id"]
        
        with patch('services.session_manager.app.services.redis_service.RedisService.add_player') as mock_join:
            mock_join.return_value = True
            
            response = await http_client.post(
                f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}/join",
                json={
                    "user_id": sample_player_data["user_id"],
                    "username": sample_player_data["username"],
                    "first_name": sample_player_data["first_name"]
                }
            )
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_session(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_session_data: Dict[str, Any]):
        """Test get session endpoint."""
        session_id = sample_session_data["session_id"]
        
        with patch('services.session_manager.app.services.redis_service.RedisService.get_session') as mock_get:
            mock_get.return_value = sample_session_data
            
            response = await http_client.get(f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
    
    @pytest.mark.asyncio
    async def test_start_session(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_session_data: Dict[str, Any]):
        """Test start session endpoint."""
        session_id = sample_session_data["session_id"]
        
        with patch('services.session_manager.app.services.redis_service.RedisService.start_session') as mock_start:
            mock_start.return_value = True
            
            response = await http_client.post(f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}/start")
            assert response.status_code == 200


class TestUserManagerAPI:
    """Test User Manager service API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_player_data: Dict[str, Any]):
        """Test user creation endpoint."""
        with patch('services.user_manager.app.services.user_service.UserService.create_user') as mock_create:
            mock_create.return_value = sample_player_data
            
            response = await http_client.post(
                f"{api_base_urls['user_manager']}/api/v1/users",
                json={
                    "user_id": sample_player_data["user_id"],
                    "username": sample_player_data["username"],
                    "first_name": sample_player_data["first_name"],
                    "last_name": sample_player_data["last_name"]
                }
            )
            assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_get_user(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_player_data: Dict[str, Any]):
        """Test get user endpoint."""
        user_id = sample_player_data["user_id"]
        
        with patch('services.user_manager.app.services.user_service.UserService.get_user') as mock_get:
            mock_get.return_value = sample_player_data
            
            response = await http_client.get(f"{api_base_urls['user_manager']}/api/v1/users/{user_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == user_id


class TestAnalyticsAPI:
    """Test Analytics service API endpoints."""
    
    @pytest.mark.asyncio
    async def test_record_game_result(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str]):
        """Test recording game result endpoint."""
        result_data = {
            "session_id": "test-session-123",
            "user_id": 987654321,
            "score": 85,
            "answers": [{"question_id": "q1", "answer": 1, "correct": True, "points": 10}],
            "completion_time": 120
        }
        
        with patch('services.analytics_service.app.services.results_service.ResultsService.record_result') as mock_record:
            mock_record.return_value = result_data
            
            response = await http_client.post(
                f"{api_base_urls['analytics']}/api/v1/results",
                json=result_data
            )
            assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_get_leaderboard(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str]):
        """Test get leaderboard endpoint."""
        leaderboard_data = [
            {"user_id": 987654321, "username": "player1", "score": 95, "rank": 1},
            {"user_id": 987654322, "username": "player2", "score": 85, "rank": 2}
        ]
        
        with patch('services.analytics_service.app.services.leaderboard_service.LeaderboardService.get_leaderboard') as mock_get:
            mock_get.return_value = leaderboard_data
            
            response = await http_client.get(f"{api_base_urls['analytics']}/api/v1/leaderboard/test-game-123")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["rank"] == 1
    
    @pytest.mark.asyncio
    async def test_get_analytics(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str]):
        """Test get analytics endpoint."""
        analytics_data = {
            "total_games": 10,
            "total_players": 50,
            "average_score": 75.5,
            "completion_rate": 0.85
        }
        
        with patch('services.analytics_service.app.services.analytics_service.AnalyticsService.get_analytics') as mock_get:
            mock_get.return_value = analytics_data
            
            response = await http_client.get(f"{api_base_urls['analytics']}/api/v1/analytics/test-game-123")
            assert response.status_code == 200
            data = response.json()
            assert data["total_games"] == 10


class TestNotificationAPI:
    """Test Notification service API endpoints."""
    
    @pytest.mark.asyncio
    async def test_send_notification(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str]):
        """Test send notification endpoint."""
        notification_data = {
            "type": "game_start",
            "session_id": "test-session-123",
            "message": "Game is starting!",
            "recipients": [987654321, 987654322]
        }
        
        with patch('services.notification_service.app.services.notification_manager.NotificationManager.send_notification') as mock_send:
            mock_send.return_value = True
            
            response = await http_client.post(
                f"{api_base_urls['notifications']}/api/v1/notifications",
                json=notification_data
            )
            assert response.status_code == 200


class TestCrossServiceIntegration:
    """Test integration between different services."""
    
    @pytest.mark.asyncio
    async def test_game_creation_to_session_flow(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_game_data: Dict[str, Any]):
        """Test creating a game and then a session for it."""
        # Create game
        with patch('services.game_engine.app.services.game_processor.GameProcessor.create_game') as mock_create_game:
            mock_create_game.return_value = sample_game_data
            
            game_response = await http_client.post(
                f"{api_base_urls['game_engine']}/api/v1/games",
                json=sample_game_data
            )
            assert game_response.status_code == 201
            game_data = game_response.json()
        
        # Create session for the game
        with patch('services.session_manager.app.services.redis_service.RedisService.create_session') as mock_create_session:
            session_data = {
                "session_id": "test-session-123",
                "game_id": game_data["id"],
                "admin_id": 123456789,
                "status": "waiting"
            }
            mock_create_session.return_value = session_data
            
            session_response = await http_client.post(
                f"{api_base_urls['session_manager']}/api/v1/sessions",
                json={
                    "game_id": game_data["id"],
                    "admin_id": 123456789,
                    "settings": {"max_players": 10}
                }
            )
            assert session_response.status_code == 201
            session_response_data = session_response.json()
            assert session_response_data["game_id"] == game_data["id"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str]):
        """Test error handling across services."""
        # Test 404 for non-existent game
        response = await http_client.get(f"{api_base_urls['game_engine']}/api/v1/games/non-existent")
        assert response.status_code == 404
        
        # Test 404 for non-existent session
        response = await http_client.get(f"{api_base_urls['session_manager']}/api/v1/sessions/non-existent")
        assert response.status_code == 404
        
        # Test validation error
        response = await http_client.post(
            f"{api_base_urls['game_engine']}/api/v1/games",
            json={"invalid": "data"}
        )
        assert response.status_code == 422


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    @pytest.mark.asyncio
    async def test_concurrent_game_creation(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str], sample_game_data: Dict[str, Any]):
        """Test concurrent game creation performance."""
        import asyncio
        
        async def create_game(game_id: str):
            game_data = sample_game_data.copy()
            game_data["id"] = game_id
            
            with patch('services.game_engine.app.services.game_processor.GameProcessor.create_game') as mock_create:
                mock_create.return_value = game_data
                
                response = await http_client.post(
                    f"{api_base_urls['game_engine']}/api/v1/games",
                    json=game_data
                )
                return response.status_code
        
        # Create 10 games concurrently
        tasks = [create_game(f"game-{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(status == 201 for status in results)
    
    @pytest.mark.asyncio
    async def test_session_join_performance(self, http_client: httpx.AsyncClient, api_base_urls: Dict[str, str]):
        """Test multiple players joining session performance."""
        import asyncio
        
        session_id = "test-session-123"
        
        async def join_session(user_id: int):
            with patch('services.session_manager.app.services.redis_service.RedisService.add_player') as mock_join:
                mock_join.return_value = True
                
                response = await http_client.post(
                    f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}/join",
                    json={
                        "user_id": user_id,
                        "username": f"player{user_id}",
                        "first_name": f"Player{user_id}"
                    }
                )
                return response.status_code
        
        # 20 players join concurrently
        tasks = [join_session(i) for i in range(1000000, 1000020)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(status == 200 for status in results)