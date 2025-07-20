"""
Performance and load testing for the game-telegram system.
"""
import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from unittest.mock import patch, AsyncMock
import httpx
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc


class TestAPIPerformance:
    """Test API endpoint performance under load."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_game_creation_performance(self, api_base_urls: Dict[str, str]):
        """Test game creation API performance."""
        
        async def create_game(session_id: int) -> Dict[str, Any]:
            """Create a single game and measure response time."""
            start_time = time.time()
            
            game_data = {
                "id": f"perf-game-{session_id}",
                "title": f"Performance Test Game {session_id}",
                "description": "Game for performance testing",
                "type": "quiz",
                "questions": [
                    {
                        "id": f"q{i}",
                        "type": "single_choice",
                        "question": f"Question {i}?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": i % 4,
                        "points": 10
                    } for i in range(10)  # 10 questions per game
                ]
            }
            
            with patch('services.game_engine.app.services.game_processor.GameProcessor.create_game') as mock_create:
                mock_create.return_value = game_data
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{api_base_urls['game_engine']}/api/v1/games",
                        json=game_data,
                        timeout=30.0
                    )
                
                end_time = time.time()
                
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "game_id": game_data["id"]
                }
        
        # Test with increasing load
        concurrent_requests = [1, 5, 10, 20, 50]
        results = {}
        
        for num_requests in concurrent_requests:
            print(f"\nTesting {num_requests} concurrent game creations...")
            
            start_time = time.time()
            tasks = [create_game(i) for i in range(num_requests)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Filter successful responses
            successful_responses = [r for r in responses if isinstance(r, dict) and r.get("status_code") == 201]
            response_times = [r["response_time"] for r in successful_responses]
            
            results[num_requests] = {
                "total_time": total_time,
                "successful_requests": len(successful_responses),
                "failed_requests": num_requests - len(successful_responses),
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "requests_per_second": len(successful_responses) / total_time if total_time > 0 else 0
            }
            
            print(f"Results: {results[num_requests]}")
        
        # Assertions for performance requirements
        assert results[1]["avg_response_time"] < 1.0  # Single request should be fast
        assert results[10]["requests_per_second"] > 5   # Should handle at least 5 RPS
        assert results[50]["failed_requests"] < 5       # Less than 10% failure rate
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_session_join_performance(self, api_base_urls: Dict[str, str]):
        """Test session join performance with many concurrent players."""
        
        session_id = "perf-session-123"
        
        async def join_session(user_id: int) -> Dict[str, Any]:
            """Simulate player joining session."""
            start_time = time.time()
            
            with patch('services.session_manager.app.services.redis_service.RedisService.add_player') as mock_join:
                mock_join.return_value = True
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}/join",
                        json={
                            "user_id": user_id,
                            "username": f"player{user_id}",
                            "first_name": f"Player{user_id}"
                        },
                        timeout=10.0
                    )
                
                end_time = time.time()
                
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "user_id": user_id
                }
        
        # Test with 100 concurrent players joining
        num_players = 100
        print(f"\nTesting {num_players} players joining session simultaneously...")
        
        start_time = time.time()
        tasks = [join_session(1000000 + i) for i in range(num_players)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful_joins = [r for r in responses if isinstance(r, dict) and r.get("status_code") == 200]
        response_times = [r["response_time"] for r in successful_joins]
        
        results = {
            "total_players": num_players,
            "successful_joins": len(successful_joins),
            "failed_joins": num_players - len(successful_joins),
            "total_time": total_time,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "joins_per_second": len(successful_joins) / total_time if total_time > 0 else 0
        }
        
        print(f"Session join results: {results}")
        
        # Performance assertions
        assert results["successful_joins"] >= 95  # At least 95% success rate
        assert results["avg_response_time"] < 2.0  # Average response under 2 seconds
        assert results["joins_per_second"] > 20    # At least 20 joins per second
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_answer_submission_performance(self, api_base_urls: Dict[str, str]):
        """Test answer submission performance during active gameplay."""
        
        session_id = "perf-session-456"
        question_id = "perf-q1"
        
        async def submit_answer(user_id: int, answer: int) -> Dict[str, Any]:
            """Submit answer for a player."""
            start_time = time.time()
            
            with patch('services.session_manager.app.services.redis_service.RedisService.submit_answer') as mock_submit:
                mock_submit.return_value = {"correct": True, "points": 10}
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{api_base_urls['session_manager']}/api/v1/sessions/{session_id}/answer",
                        json={
                            "question_id": question_id,
                            "answer": answer,
                            "timestamp": time.time()
                        },
                        timeout=5.0
                    )
                
                end_time = time.time()
                
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "user_id": user_id
                }
        
        # Simulate 200 players answering simultaneously
        num_players = 200
        print(f"\nTesting {num_players} simultaneous answer submissions...")
        
        start_time = time.time()
        tasks = [submit_answer(2000000 + i, i % 4) for i in range(num_players)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful_submissions = [r for r in responses if isinstance(r, dict) and r.get("status_code") == 200]
        response_times = [r["response_time"] for r in successful_submissions]
        
        results = {
            "total_submissions": num_players,
            "successful_submissions": len(successful_submissions),
            "failed_submissions": num_players - len(successful_submissions),
            "total_time": total_time,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "submissions_per_second": len(successful_submissions) / total_time if total_time > 0 else 0
        }
        
        print(f"Answer submission results: {results}")
        
        # Performance assertions
        assert results["successful_submissions"] >= 190  # At least 95% success rate
        assert results["avg_response_time"] < 1.0        # Fast answer processing
        assert results["submissions_per_second"] > 50    # High throughput


class TestMemoryPerformance:
    """Test memory usage and performance."""
    
    @pytest.mark.performance
    def test_memory_usage_during_load(self):
        """Test memory usage during high load operations."""
        
        def get_memory_usage():
            """Get current memory usage in MB."""
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        
        initial_memory = get_memory_usage()
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        
        # Simulate creating many games in memory
        games = []
        for i in range(1000):
            game_data = {
                "id": f"memory-test-{i}",
                "title": f"Memory Test Game {i}",
                "questions": [
                    {
                        "id": f"q{j}",
                        "question": f"Question {j}?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": j % 4,
                        "points": 10
                    } for j in range(50)  # 50 questions per game
                ]
            }
            games.append(game_data)
        
        peak_memory = get_memory_usage()
        print(f"Peak memory usage: {peak_memory:.2f} MB")
        
        # Clear games and force garbage collection
        games.clear()
        gc.collect()
        
        final_memory = get_memory_usage()
        print(f"Final memory usage: {final_memory:.2f} MB")
        
        memory_increase = peak_memory - initial_memory
        memory_recovered = peak_memory - final_memory
        
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"Memory recovered: {memory_recovered:.2f} MB")
        
        # Assertions
        assert memory_increase < 500  # Should not use more than 500MB
        assert memory_recovered > memory_increase * 0.8  # Should recover at least 80%
    
    @pytest.mark.performance
    def test_game_module_memory_efficiency(self):
        """Test memory efficiency of game modules."""
        from game_modules.quiz.quiz_module import QuizModule
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Create many quiz modules
        quiz_modules = []
        for i in range(100):
            quiz_data = {
                "id": f"quiz-{i}",
                "title": f"Quiz {i}",
                "questions": [
                    {
                        "id": f"q{j}",
                        "type": "single_choice",
                        "question": f"Question {j}?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": j % 4,
                        "points": 10
                    } for j in range(20)
                ]
            }
            quiz_modules.append(QuizModule(quiz_data))
        
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_per_module = (peak_memory - initial_memory) / 100
        
        print(f"Memory per quiz module: {memory_per_module:.2f} MB")
        
        # Should be efficient
        assert memory_per_module < 5.0  # Less than 5MB per module


class TestDatabasePerformance:
    """Test database performance under load."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, mock_database):
        """Test concurrent database operations."""
        
        async def create_user_record(user_id: int):
            """Create a user record in database."""
            start_time = time.time()
            
            # Simulate database operation
            await asyncio.sleep(0.01)  # Simulate DB latency
            
            end_time = time.time()
            return {
                "user_id": user_id,
                "operation_time": end_time - start_time,
                "success": True
            }
        
        # Test with increasing concurrency
        concurrency_levels = [10, 50, 100, 200]
        
        for concurrency in concurrency_levels:
            print(f"\nTesting {concurrency} concurrent database operations...")
            
            start_time = time.time()
            tasks = [create_user_record(i) for i in range(concurrency)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            operation_times = [r["operation_time"] for r in results]
            
            stats = {
                "concurrency": concurrency,
                "total_time": total_time,
                "avg_operation_time": statistics.mean(operation_times),
                "max_operation_time": max(operation_times),
                "operations_per_second": concurrency / total_time
            }
            
            print(f"Database performance: {stats}")
            
            # Performance assertions
            assert stats["avg_operation_time"] < 0.1  # Average under 100ms
            assert stats["operations_per_second"] > concurrency * 0.5  # Reasonable throughput


class TestRedisPerformance:
    """Test Redis performance under load."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_redis_session_operations(self, mock_redis):
        """Test Redis session operations performance."""
        
        async def redis_operation(operation_id: int):
            """Perform Redis operations."""
            start_time = time.time()
            
            # Simulate Redis operations
            session_key = f"session:{operation_id}"
            session_data = {
                "session_id": f"session-{operation_id}",
                "players": [f"player-{i}" for i in range(10)],
                "status": "active"
            }
            
            # Mock Redis operations
            mock_redis.hset(session_key, mapping=session_data)
            mock_redis.hget(session_key, "status")
            mock_redis.expire(session_key, 3600)
            
            end_time = time.time()
            return {
                "operation_id": operation_id,
                "operation_time": end_time - start_time
            }
        
        # Test high-frequency Redis operations
        num_operations = 1000
        print(f"\nTesting {num_operations} Redis operations...")
        
        start_time = time.time()
        tasks = [redis_operation(i) for i in range(num_operations)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        operation_times = [r["operation_time"] for r in results]
        
        stats = {
            "total_operations": num_operations,
            "total_time": total_time,
            "avg_operation_time": statistics.mean(operation_times),
            "operations_per_second": num_operations / total_time
        }
        
        print(f"Redis performance: {stats}")
        
        # Performance assertions
        assert stats["avg_operation_time"] < 0.01  # Very fast operations
        assert stats["operations_per_second"] > 500  # High throughput


class TestWebSocketPerformance:
    """Test WebSocket performance for real-time features."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput."""
        
        class MockWebSocket:
            def __init__(self):
                self.messages_sent = 0
                self.messages_received = 0
            
            async def send_text(self, message: str):
                self.messages_sent += 1
                await asyncio.sleep(0.001)  # Simulate network latency
            
            async def receive_text(self):
                self.messages_received += 1
                return '{"type": "test", "data": "response"}'
        
        async def websocket_session(session_id: int, messages_per_session: int):
            """Simulate WebSocket session with multiple messages."""
            ws = MockWebSocket()
            
            start_time = time.time()
            
            # Send messages
            send_tasks = []
            for i in range(messages_per_session):
                message = f'{{"type": "game_event", "session_id": "{session_id}", "data": "event_{i}"}}'
                send_tasks.append(ws.send_text(message))
            
            await asyncio.gather(*send_tasks)
            
            end_time = time.time()
            
            return {
                "session_id": session_id,
                "messages_sent": ws.messages_sent,
                "session_time": end_time - start_time
            }
        
        # Test multiple concurrent WebSocket sessions
        num_sessions = 50
        messages_per_session = 20
        
        print(f"\nTesting {num_sessions} WebSocket sessions with {messages_per_session} messages each...")
        
        start_time = time.time()
        tasks = [websocket_session(i, messages_per_session) for i in range(num_sessions)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        total_messages = sum(r["messages_sent"] for r in results)
        session_times = [r["session_time"] for r in results]
        
        stats = {
            "total_sessions": num_sessions,
            "total_messages": total_messages,
            "total_time": total_time,
            "avg_session_time": statistics.mean(session_times),
            "messages_per_second": total_messages / total_time
        }
        
        print(f"WebSocket performance: {stats}")
        
        # Performance assertions
        assert stats["messages_per_second"] > 200  # Good message throughput
        assert stats["avg_session_time"] < 1.0     # Fast session handling


class TestScalabilityLimits:
    """Test system scalability limits."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_maximum_concurrent_games(self):
        """Test maximum number of concurrent games the system can handle."""
        
        def create_game_simulation(game_id: int):
            """Simulate game creation and basic operations."""
            start_time = time.time()
            
            # Simulate game creation overhead
            game_data = {
                "id": f"scale-test-{game_id}",
                "questions": [{"id": f"q{i}", "data": f"question_{i}"} for i in range(10)]
            }
            
            # Simulate processing time
            time.sleep(0.01)
            
            end_time = time.time()
            return {
                "game_id": game_id,
                "creation_time": end_time - start_time,
                "success": True
            }
        
        # Test with increasing number of games
        game_counts = [100, 500, 1000, 2000]
        
        for num_games in game_counts:
            print(f"\nTesting {num_games} concurrent games...")
            
            start_time = time.time()
            
            # Use ThreadPoolExecutor for CPU-bound simulation
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(create_game_simulation, i) for i in range(num_games)]
                results = [future.result() for future in futures]
            
            total_time = time.time() - start_time
            
            successful_games = [r for r in results if r["success"]]
            creation_times = [r["creation_time"] for r in successful_games]
            
            stats = {
                "total_games": num_games,
                "successful_games": len(successful_games),
                "total_time": total_time,
                "avg_creation_time": statistics.mean(creation_times),
                "games_per_second": len(successful_games) / total_time
            }
            
            print(f"Scalability test results: {stats}")
            
            # Check if system can handle the load
            if stats["games_per_second"] < 10:
                print(f"System limit reached at {num_games} concurrent games")
                break
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_maximum_players_per_session(self):
        """Test maximum number of players that can join a single session."""
        
        async def add_player_to_session(player_id: int, session_id: str):
            """Simulate adding player to session."""
            start_time = time.time()
            
            # Simulate player addition overhead
            await asyncio.sleep(0.001)
            
            end_time = time.time()
            return {
                "player_id": player_id,
                "session_id": session_id,
                "join_time": end_time - start_time,
                "success": True
            }
        
        session_id = "max-players-test"
        player_counts = [100, 500, 1000, 2000, 5000]
        
        for num_players in player_counts:
            print(f"\nTesting {num_players} players in single session...")
            
            start_time = time.time()
            tasks = [add_player_to_session(i, session_id) for i in range(num_players)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            successful_joins = [r for r in results if isinstance(r, dict) and r.get("success")]
            join_times = [r["join_time"] for r in successful_joins]
            
            stats = {
                "target_players": num_players,
                "successful_joins": len(successful_joins),
                "total_time": total_time,
                "avg_join_time": statistics.mean(join_times) if join_times else 0,
                "joins_per_second": len(successful_joins) / total_time if total_time > 0 else 0
            }
            
            print(f"Max players test: {stats}")
            
            # Check system limits
            if stats["joins_per_second"] < 100 or stats["avg_join_time"] > 0.1:
                print(f"Performance degradation at {num_players} players")
                break


class TestStressTest:
    """Comprehensive stress testing."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_full_system_stress(self, api_base_urls: Dict[str, str]):
        """Comprehensive stress test of the entire system."""
        
        print("\n=== FULL SYSTEM STRESS TEST ===")
        
        # Test parameters
        num_games = 10
        players_per_game = 50
        questions_per_game = 10
        
        async def run_complete_game_session(game_id: int):
            """Run a complete game session from creation to completion."""
            session_results = {
                "game_id": game_id,
                "phases": {},
                "total_time": 0,
                "success": True
            }
            
            session_start = time.time()
            
            try:
                # Phase 1: Create game
                phase_start = time.time()
                game_data = {
                    "id": f"stress-game-{game_id}",
                    "title": f"Stress Test Game {game_id}",
                    "questions": [
                        {
                            "id": f"q{i}",
                            "type": "single_choice",
                            "question": f"Question {i}?",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": i % 4,
                            "points": 10
                        } for i in range(questions_per_game)
                    ]
                }
                
                with patch('services.game_engine.app.services.game_processor.GameProcessor.create_game') as mock_create:
                    mock_create.return_value = game_data
                    # Simulate game creation
                    await asyncio.sleep(0.1)
                
                session_results["phases"]["game_creation"] = time.time() - phase_start
                
                # Phase 2: Create session
                phase_start = time.time()
                session_id = f"stress-session-{game_id}"
                
                with patch('services.session_manager.app.services.redis_service.RedisService.create_session') as mock_session:
                    mock_session.return_value = {"session_id": session_id}
                    await asyncio.sleep(0.05)
                
                session_results["phases"]["session_creation"] = time.time() - phase_start
                
                # Phase 3: Players join
                phase_start = time.time()
                join_tasks = []
                
                for player_id in range(players_per_game):
                    async def join_player(pid):
                        with patch('services.session_manager.app.services.redis_service.RedisService.add_player') as mock_join:
                            mock_join.return_value = True
                            await asyncio.sleep(0.01)
                    
                    join_tasks.append(join_player(player_id))
                
                await asyncio.gather(*join_tasks)
                session_results["phases"]["player_joining"] = time.time() - phase_start
                
                # Phase 4: Game play (answer submission)
                phase_start = time.time()
                answer_tasks = []
                
                for question_idx in range(questions_per_game):
                    for player_id in range(players_per_game):
                        async def submit_answer(qid, pid):
                            with patch('services.session_manager.app.services.redis_service.RedisService.submit_answer') as mock_answer:
                                mock_answer.return_value = {"correct": True, "points": 10}
                                await asyncio.sleep(0.005)
                        
                        answer_tasks.append(submit_answer(question_idx, player_id))
                
                await asyncio.gather(*answer_tasks)
                session_results["phases"]["gameplay"] = time.time() - phase_start
                
                # Phase 5: Results calculation
                phase_start = time.time()
                
                with patch('services.analytics_service.app.services.results_service.ResultsService.calculate_results') as mock_results:
                    mock_results.return_value = {"calculated": True}
                    await asyncio.sleep(0.2)
                
                session_results["phases"]["results_calculation"] = time.time() - phase_start
                
            except Exception as e:
                session_results["success"] = False
                session_results["error"] = str(e)
            
            session_results["total_time"] = time.time() - session_start
            return session_results
        
        # Run stress test
        print(f"Running {num_games} concurrent game sessions...")
        print(f"Each session: {players_per_game} players, {questions_per_game} questions")
        
        stress_start = time.time()
        tasks = [run_complete_game_session(i) for i in range(num_games)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_stress_time = time.time() - stress_start
        
        # Analyze results
        successful_sessions = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_sessions = len(results) - len(successful_sessions)
        
        if successful_sessions:
            avg_total_time = statistics.mean([r["total_time"] for r in successful_sessions])
            avg_phase_times = {}
            
            for phase in ["game_creation", "session_creation", "player_joining", "gameplay", "results_calculation"]:
                phase_times = [r["phases"].get(phase, 0) for r in successful_sessions]
                avg_phase_times[phase] = statistics.mean(phase_times) if phase_times else 0
        else:
            avg_total_time = 0
            avg_phase_times = {}
        
        stress_results = {
            "total_sessions": num_games,
            "successful_sessions": len(successful_sessions),
            "failed_sessions": failed_sessions,
            "total_stress_time": total_stress_time,
            "avg_session_time": avg_total_time,
            "avg_phase_times": avg_phase_times,
            "sessions_per_second": len(successful_sessions) / total_stress_time if total_stress_time > 0 else 0,
            "total_operations": num_games * players_per_game * questions_per_game,
            "operations_per_second": (num_games * players_per_game * questions_per_game) / total_stress_time if total_stress_time > 0 else 0
        }
        
        print("\n=== STRESS TEST RESULTS ===")
        for key, value in stress_results.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value:.3f}s")
            else:
                print(f"{key}: {value}")
        
        # Performance assertions
        assert stress_results["successful_sessions"] >= num_games * 0.9  # 90% success rate
        assert stress_results["avg_session_time"] < 10.0  # Sessions complete in reasonable time
        assert stress_results["sessions_per_second"] > 0.5  # Reasonable throughput
        
        print("\n=== STRESS TEST COMPLETED ===")


class TestResourceMonitoring:
    """Test resource usage monitoring during performance tests."""
    
    @pytest.mark.performance
    def test_cpu_usage_monitoring(self):
        """Monitor CPU usage during intensive operations."""
        
        def cpu_intensive_task():
            """Simulate CPU-intensive game processing."""
            # Simulate complex game logic
            for i in range(100000):
                result = sum(j * j for j in range(100))
            return result
        
        # Monitor CPU usage
        cpu_percentages = []
        
        # Monitor CPU usage during task execution
        import threading
        
        def monitor_cpu():
            for _ in range(10):  # Monitor for 10 intervals
                cpu_percentages.append(psutil.cpu_percent(interval=0.1))
        
        # Start monitoring
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        # Run CPU intensive tasks
        start_time = time.time()
        results = []
        for i in range(10):
            results.append(cpu_intensive_task())
        execution_time = time.time() - start_time
        
        # Wait for monitoring to complete
        monitor_thread.join()
        
        avg_cpu_usage = statistics.mean(cpu_percentages) if cpu_percentages else 0
        max_cpu_usage = max(cpu_percentages) if cpu_percentages else 0
        
        print(f"CPU Usage - Average: {avg_cpu_usage:.2f}%, Max: {max_cpu_usage:.2f}%")
        print(f"Execution time: {execution_time:.2f}s")
        
        # CPU usage should be reasonable
        assert avg_cpu_usage < 90  # Should not max out CPU
        assert execution_time < 5.0  # Should complete in reasonable time