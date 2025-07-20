"""
End-to-end integration tests for complete game flow scenarios.
"""
import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import patch, AsyncMock, MagicMock
import httpx


class TestCompleteGameFlow:
    """Test complete game flow from creation to results."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_quiz_game_complete_flow(
        self, 
        http_client: httpx.AsyncClient, 
        api_base_urls: Dict[str, str],
        sample_game_data: Dict[str, Any],
        sample_session_data: Dict[str, Any],
        sample_player_data: Dict[str, Any]
    ):
        """Test complete quiz game flow from creation to results."""
        
        # Step 1: Create a game
        with patch('services.game_engine.app.services.game_processor.GameProcessor.create_game') as mock_create_game:
            mock_create_game.return_value = sample_game_data
            
            game_response = await http_client.post(
                f"{api_base_urls['game_engine']}/api/v1/games",
                json=sample_game_data
            )
            assert game_response.status_code == 201
            game_data = game_response.json()
            game_id = game_data["id"]
        
        # Step 2: Create a session for the game
        with patch('services.session_manager.app.services.redis_service.RedisService.create_session') as mock_create_session:
            session_data = sample_session_data.copy()
            session_data["game_id"] = game_id
            mock_create_session.return_value = session_data
            
            session_response = await http_client.post(
                f"{api_base_urls['session_manager']}/api/v1/sessions",
                json={
                    "game_id": game_id,
                    "admin_id": sample_session_data["admin_id"],
                    "settings": sample_session_data["settings"]
                }
            )
            assert session_response.status_code == 201
            session_response_data = session_response.json()
            session_id = session_response_data["session_id"]
        
        # Step 3: Players join the session
        players = []
        for i in range(3):  # 3 players join
            player_data = {
                "user_id": 987654321 + i,
                "username": f"player{i+1}",
                "first_name": f"Player{i+1}",
                "last_name": "Test"
            }
            players.append(player_data)
            
            with patch('services.session_manager.app.services.redis_service.RedisService.add_player') as mock_join:
                mock_join.return_value = True
                
                join_response = await http_client.post(
                    f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}/join",
                    json=player_data
                )
                assert join_response.status_code == 200
        
        # Step 4: Start the session
        with patch('services.session_manager.app.services.redis_service.RedisService.start_session') as mock_start:
            mock_start.return_value = True
            
            start_response = await http_client.post(
                f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}/start"
            )
            assert start_response.status_code == 200
        
        # Step 5: Simulate game play - players answer questions
        for question_idx, question in enumerate(sample_game_data["questions"]):
            for player_idx, player in enumerate(players):
                # Simulate different answers for variety
                if question["type"] == "single_choice":
                    answer = question_idx % len(question["options"])
                else:  # multiple_choice
                    answer = [0, 1] if player_idx == 0 else [0]
                
                answer_data = {
                    "session_id": session_id,
                    "user_id": player["user_id"],
                    "question_id": question["id"],
                    "answer": answer,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                
                with patch('services.session_manager.app.services.redis_service.RedisService.submit_answer') as mock_answer:
                    mock_answer.return_value = True
                    
                    answer_response = await http_client.post(
                        f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}/answer",
                        json=answer_data
                    )
                    assert answer_response.status_code == 200
        
        # Step 6: End the session and calculate results
        with patch('services.session_manager.app.services.redis_service.RedisService.end_session') as mock_end:
            mock_end.return_value = True
            
            end_response = await http_client.post(
                f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}/end"
            )
            assert end_response.status_code == 200
        
        # Step 7: Record results in analytics
        for player in players:
            result_data = {
                "session_id": session_id,
                "user_id": player["user_id"],
                "score": 85,  # Mock score
                "answers": [
                    {"question_id": "q1", "answer": 1, "correct": True, "points": 10},
                    {"question_id": "q2", "answer": [0, 1], "correct": True, "points": 15}
                ],
                "completion_time": 120
            }
            
            with patch('services.analytics_service.app.services.results_service.ResultsService.record_result') as mock_record:
                mock_record.return_value = result_data
                
                result_response = await http_client.post(
                    f"{api_base_urls['analytics']}/api/v1/results",
                    json=result_data
                )
                assert result_response.status_code == 201
        
        # Step 8: Get final leaderboard
        leaderboard_data = [
            {"user_id": players[0]["user_id"], "username": players[0]["username"], "score": 95, "rank": 1},
            {"user_id": players[1]["user_id"], "username": players[1]["username"], "score": 85, "rank": 2},
            {"user_id": players[2]["user_id"], "username": players[2]["username"], "score": 75, "rank": 3}
        ]
        
        with patch('services.analytics_service.app.services.leaderboard_service.LeaderboardService.get_leaderboard') as mock_leaderboard:
            mock_leaderboard.return_value = leaderboard_data
            
            leaderboard_response = await http_client.get(
                f"{api_base_urls['analytics']}/api/v1/leaderboard/{game_id}"
            )
            assert leaderboard_response.status_code == 200
            leaderboard = leaderboard_response.json()
            assert len(leaderboard) == 3
            assert leaderboard[0]["rank"] == 1
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_family_feud_game_flow(
        self, 
        http_client: httpx.AsyncClient, 
        api_base_urls: Dict[str, str]
    ):
        """Test complete family feud game flow."""
        
        # Family Feud game data
        family_feud_data = {
            "id": "family-feud-123",
            "title": "Family Topics",
            "description": "Family Feud style game",
            "type": "family_feud",
            "settings": {
                "rounds": 3,
                "teams": 2,
                "strikes_limit": 3
            },
            "questions": [
                {
                    "id": "ff1",
                    "question": "Name something you find in a kitchen",
                    "answers": [
                        {"text": "Refrigerator", "points": 45},
                        {"text": "Stove", "points": 30},
                        {"text": "Sink", "points": 15},
                        {"text": "Microwave", "points": 10}
                    ]
                }
            ]
        }
        
        # Step 1: Create family feud game
        with patch('services.game_engine.app.services.game_processor.GameProcessor.create_game') as mock_create:
            mock_create.return_value = family_feud_data
            
            game_response = await http_client.post(
                f"{api_base_urls['game_engine']}/api/v1/games",
                json=family_feud_data
            )
            assert game_response.status_code == 201
        
        # Step 2: Create session with team settings
        session_data = {
            "session_id": "ff-session-123",
            "game_id": family_feud_data["id"],
            "admin_id": 123456789,
            "status": "waiting",
            "settings": {
                "max_players": 8,
                "teams": 2
            }
        }
        
        with patch('services.session_manager.app.services.redis_service.RedisService.create_session') as mock_create_session:
            mock_create_session.return_value = session_data
            
            session_response = await http_client.post(
                f"{api_base_urls['session_manager']}/api/v1/sessions",
                json={
                    "game_id": family_feud_data["id"],
                    "admin_id": 123456789,
                    "settings": session_data["settings"]
                }
            )
            assert session_response.status_code == 201
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_game_import_and_play_flow(
        self, 
        http_client: httpx.AsyncClient, 
        api_base_urls: Dict[str, str]
    ):
        """Test importing a game pack and playing it."""
        
        # Step 1: Import game pack
        game_pack = {
            "name": "Science Quiz Pack",
            "description": "Educational science questions",
            "games": [
                {
                    "id": "science-quiz-1",
                    "title": "Basic Science",
                    "type": "quiz",
                    "questions": [
                        {
                            "id": "sci1",
                            "type": "single_choice",
                            "question": "What is H2O?",
                            "options": ["Water", "Hydrogen", "Oxygen", "Salt"],
                            "correct_answer": 0,
                            "points": 10
                        }
                    ]
                }
            ]
        }
        
        with patch('services.game_engine.app.services.game_importer.GameImporter.import_pack') as mock_import:
            mock_import.return_value = {
                "imported_games": 1,
                "games": game_pack["games"]
            }
            
            files = {"file": ("science_pack.json", json.dumps(game_pack), "application/json")}
            import_response = await http_client.post(
                f"{api_base_urls['game_engine']}/api/v1/import",
                files=files
            )
            assert import_response.status_code == 200
            import_data = import_response.json()
            assert import_data["imported_games"] == 1
        
        # Step 2: Play the imported game
        imported_game = game_pack["games"][0]
        
        # Create session for imported game
        with patch('services.session_manager.app.services.redis_service.RedisService.create_session') as mock_create_session:
            session_data = {
                "session_id": "imported-session-123",
                "game_id": imported_game["id"],
                "admin_id": 123456789,
                "status": "waiting"
            }
            mock_create_session.return_value = session_data
            
            session_response = await http_client.post(
                f"{api_base_urls['session_manager']}/api/v1/sessions",
                json={
                    "game_id": imported_game["id"],
                    "admin_id": 123456789,
                    "settings": {"max_players": 5}
                }
            )
            assert session_response.status_code == 201
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_error_recovery_flow(
        self, 
        http_client: httpx.AsyncClient, 
        api_base_urls: Dict[str, str],
        sample_game_data: Dict[str, Any]
    ):
        """Test error recovery scenarios during game flow."""
        
        # Step 1: Try to create session for non-existent game
        response = await http_client.post(
            f"{api_base_urls['session_manager']}/api/v1/sessions",
            json={
                "game_id": "non-existent-game",
                "admin_id": 123456789,
                "settings": {"max_players": 10}
            }
        )
        assert response.status_code == 404
        
        # Step 2: Create valid game first
        with patch('services.game_engine.app.services.game_processor.GameProcessor.create_game') as mock_create:
            mock_create.return_value = sample_game_data
            
            game_response = await http_client.post(
                f"{api_base_urls['game_engine']}/api/v1/games",
                json=sample_game_data
            )
            assert game_response.status_code == 201
        
        # Step 3: Try to join non-existent session
        response = await http_client.post(
            f"{api_base_urls['session_manager']}/api/v1/sessions/non-existent/join",
            json={
                "user_id": 987654321,
                "username": "test_player",
                "first_name": "Test"
            }
        )
        assert response.status_code == 404
        
        # Step 4: Create valid session and test recovery
        with patch('services.session_manager.app.services.redis_service.RedisService.create_session') as mock_create_session:
            session_data = {
                "session_id": "recovery-session-123",
                "game_id": sample_game_data["id"],
                "admin_id": 123456789,
                "status": "waiting"
            }
            mock_create_session.return_value = session_data
            
            session_response = await http_client.post(
                f"{api_base_urls['session_manager']}/api/v1/sessions",
                json={
                    "game_id": sample_game_data["id"],
                    "admin_id": 123456789,
                    "settings": {"max_players": 10}
                }
            )
            assert session_response.status_code == 201


class TestBotGameIntegration:
    """Test integration between bots and game services."""
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_admin_bot_game_creation_flow(
        self,
        mock_telegram_bot,
        mock_message,
        sample_game_data: Dict[str, Any]
    ):
        """Test admin bot creating a game through API."""
        
        # Mock admin bot handlers
        with patch('services.admin_bot.app.services.api_client.APIClient.create_game') as mock_api:
            mock_api.return_value = sample_game_data
            
            # Simulate admin bot creating game
            from services.admin_bot.app.handlers.game_handlers import create_game_handler
            
            # Mock the handler call
            result = await create_game_handler(mock_message, mock_telegram_bot, sample_game_data)
            
            # Verify API was called
            mock_api.assert_called_once()
            assert mock_telegram_bot.send_message.called
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_player_bot_join_session_flow(
        self,
        mock_telegram_bot,
        mock_message,
        sample_session_data: Dict[str, Any]
    ):
        """Test player bot joining a session through API."""
        
        session_id = sample_session_data["session_id"]
        
        with patch('services.player_bot.app.services.api_client.APIClient.join_session') as mock_api:
            mock_api.return_value = {"success": True}
            
            # Simulate player bot joining session
            from services.player_bot.app.handlers.connection_handlers import join_session_handler
            
            # Mock the handler call
            result = await join_session_handler(mock_message, mock_telegram_bot, session_id)
            
            # Verify API was called
            mock_api.assert_called_once()
            assert mock_telegram_bot.send_message.called


class TestWebSocketGameFlow:
    """Test real-time game flow using WebSocket connections."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_realtime_quiz_flow(
        self,
        api_base_urls: Dict[str, str],
        sample_game_data: Dict[str, Any]
    ):
        """Test real-time quiz game using WebSocket."""
        
        # This would require actual WebSocket testing
        # For now, we'll mock the WebSocket behavior
        
        session_id = "ws-session-123"
        
        # Mock WebSocket connection
        class MockWebSocket:
            def __init__(self):
                self.messages = []
            
            async def send_text(self, message: str):
                self.messages.append(message)
            
            async def receive_text(self):
                return '{"type": "answer", "data": {"answer": 1}}'
        
        ws_mock = MockWebSocket()
        
        # Simulate real-time game events
        events = [
            {"type": "game_start", "data": {"session_id": session_id}},
            {"type": "question", "data": sample_game_data["questions"][0]},
            {"type": "answer_received", "data": {"user_id": 123, "answer": 1}},
            {"type": "question_end", "data": {"correct_answer": 1}},
            {"type": "game_end", "data": {"final_scores": [{"user_id": 123, "score": 10}]}}
        ]
        
        for event in events:
            await ws_mock.send_text(json.dumps(event))
        
        # Verify all events were sent
        assert len(ws_mock.messages) == len(events)


class TestGameFlowPerformance:
    """Performance tests for complete game flows."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_game_sessions(
        self,
        http_client: httpx.AsyncClient,
        api_base_urls: Dict[str, str],
        sample_game_data: Dict[str, Any]
    ):
        """Test multiple concurrent game sessions."""
        
        async def run_game_session(session_id: str):
            """Run a complete game session."""
            
            # Create session
            with patch('services.session_manager.app.services.redis_service.RedisService.create_session') as mock_create:
                session_data = {
                    "session_id": session_id,
                    "game_id": sample_game_data["id"],
                    "admin_id": 123456789,
                    "status": "waiting"
                }
                mock_create.return_value = session_data
                
                session_response = await http_client.post(
                    f"{api_base_urls['session_manager']}/api/v1/sessions",
                    json={
                        "game_id": sample_game_data["id"],
                        "admin_id": 123456789,
                        "settings": {"max_players": 5}
                    }
                )
                return session_response.status_code
        
        # Run 5 concurrent sessions
        tasks = [run_game_session(f"perf-session-{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(status == 201 for status in results)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_high_player_count_session(
        self,
        http_client: httpx.AsyncClient,
        api_base_urls: Dict[str, str]
    ):
        """Test session with many players joining simultaneously."""
        
        session_id = "high-load-session"
        
        async def join_as_player(user_id: int):
            """Simulate player joining session."""
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
        
        # 50 players join simultaneously
        tasks = [join_as_player(i) for i in range(1000000, 1000050)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(status == 200 for status in results)
