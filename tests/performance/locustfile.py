"""
Locust load testing configuration for the game-telegram system.
Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between, events
import json
import random
import time
from typing import Dict, Any


class GameEngineUser(HttpUser):
    """Simulate users interacting with the Game Engine service."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize user session."""
        self.game_id = None
        self.session_id = None
        self.user_id = random.randint(1000000, 9999999)
        
        # Create a game first
        self.create_game()
    
    def create_game(self):
        """Create a test game."""
        game_data = {
            "title": f"Load Test Game {self.user_id}",
            "description": "Game created for load testing",
            "type": "quiz",
            "settings": {
                "time_limit": 30,
                "max_players": 10,
                "show_correct_answers": True
            },
            "questions": [
                {
                    "id": f"q{i}",
                    "type": "single_choice",
                    "question": f"Load test question {i}?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": i % 4,
                    "points": 10,
                    "time_limit": 15
                } for i in range(5)
            ]
        }
        
        with self.client.post(
            "/api/v1/games",
            json=game_data,
            catch_response=True,
            name="Create Game"
        ) as response:
            if response.status_code == 201:
                self.game_id = response.json().get("id")
                response.success()
            else:
                response.failure(f"Failed to create game: {response.status_code}")
    
    @task(3)
    def get_game_list(self):
        """Get list of available games."""
        with self.client.get("/api/v1/games", name="List Games") as response:
            if response.status_code != 200:
                response.failure(f"Failed to get games: {response.status_code}")
    
    @task(2)
    def get_game_details(self):
        """Get details of a specific game."""
        if self.game_id:
            with self.client.get(f"/api/v1/games/{self.game_id}", name="Get Game Details") as response:
                if response.status_code != 200:
                    response.failure(f"Failed to get game details: {response.status_code}")
    
    @task(1)
    def import_game_pack(self):
        """Test game pack import."""
        game_pack = {
            "name": f"Load Test Pack {self.user_id}",
            "description": "Pack for load testing",
            "games": [
                {
                    "id": f"imported-game-{self.user_id}",
                    "title": "Imported Game",
                    "type": "quiz",
                    "questions": [
                        {
                            "id": "iq1",
                            "type": "single_choice",
                            "question": "Imported question?",
                            "options": ["A", "B"],
                            "correct_answer": 0,
                            "points": 5
                        }
                    ]
                }
            ]
        }
        
        files = {
            "file": ("test_pack.json", json.dumps(game_pack), "application/json")
        }
        
        with self.client.post(
            "/api/v1/import",
            files=files,
            name="Import Game Pack"
        ) as response:
            if response.status_code not in [200, 201]:
                response.failure(f"Failed to import pack: {response.status_code}")


class SessionManagerUser(HttpUser):
    """Simulate users interacting with the Session Manager service."""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Initialize session user."""
        self.session_id = None
        self.user_id = random.randint(1000000, 9999999)
        self.game_id = f"test-game-{random.randint(1, 100)}"
        
        # Create a session
        self.create_session()
    
    def create_session(self):
        """Create a test session."""
        session_data = {
            "game_id": self.game_id,
            "admin_id": self.user_id,
            "settings": {
                "max_players": 20,
                "auto_start": False,
                "allow_late_join": True
            }
        }
        
        with self.client.post(
            "/api/v1/sessions",
            json=session_data,
            catch_response=True,
            name="Create Session"
        ) as response:
            if response.status_code == 201:
                self.session_id = response.json().get("session_id")
                response.success()
            else:
                response.failure(f"Failed to create session: {response.status_code}")
    
    @task(5)
    def join_session(self):
        """Simulate player joining session."""
        if self.session_id:
            player_data = {
                "user_id": random.randint(2000000, 2999999),
                "username": f"player_{random.randint(1, 1000)}",
                "first_name": f"Player{random.randint(1, 1000)}"
            }
            
            with self.client.post(
                f"/api/v1/sessions/{self.session_id}/join",
                json=player_data,
                name="Join Session"
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Failed to join session: {response.status_code}")
    
    @task(3)
    def get_session_status(self):
        """Get session status."""
        if self.session_id:
            with self.client.get(
                f"/api/v1/sessions/{self.session_id}",
                name="Get Session Status"
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Failed to get session: {response.status_code}")
    
    @task(2)
    def submit_answer(self):
        """Submit answer to question."""
        if self.session_id:
            answer_data = {
                "question_id": f"q{random.randint(1, 5)}",
                "answer": random.randint(0, 3),
                "timestamp": time.time()
            }
            
            with self.client.post(
                f"/api/v1/sessions/{self.session_id}/answer",
                json=answer_data,
                name="Submit Answer"
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Failed to submit answer: {response.status_code}")
    
    @task(1)
    def start_session(self):
        """Start the session."""
        if self.session_id:
            with self.client.post(
                f"/api/v1/sessions/{self.session_id}/start",
                name="Start Session"
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Failed to start session: {response.status_code}")


class AnalyticsUser(HttpUser):
    """Simulate users interacting with the Analytics service."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Initialize analytics user."""
        self.user_id = random.randint(1000000, 9999999)
        self.game_id = f"analytics-game-{random.randint(1, 50)}"
        self.session_id = f"analytics-session-{random.randint(1, 100)}"
    
    @task(4)
    def record_game_result(self):
        """Record a game result."""
        result_data = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "game_id": self.game_id,
            "score": random.randint(0, 100),
            "max_score": 100,
            "correct_answers": random.randint(0, 10),
            "total_questions": 10,
            "completion_time": random.randint(60, 300),
            "answers": [
                {
                    "question_id": f"q{i}",
                    "answer": random.randint(0, 3),
                    "correct": random.choice([True, False]),
                    "points": random.randint(0, 10),
                    "time_taken": random.randint(5, 30)
                } for i in range(5)
            ]
        }
        
        with self.client.post(
            "/api/v1/results",
            json=result_data,
            name="Record Result"
        ) as response:
            if response.status_code not in [200, 201]:
                response.failure(f"Failed to record result: {response.status_code}")
    
    @task(3)
    def get_leaderboard(self):
        """Get game leaderboard."""
        with self.client.get(
            f"/api/v1/leaderboard/{self.game_id}",
            name="Get Leaderboard"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get leaderboard: {response.status_code}")
    
    @task(2)
    def get_analytics(self):
        """Get game analytics."""
        with self.client.get(
            f"/api/v1/analytics/{self.game_id}",
            name="Get Analytics"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get analytics: {response.status_code}")
    
    @task(1)
    def get_player_stats(self):
        """Get player statistics."""
        with self.client.get(
            f"/api/v1/players/{self.user_id}/stats",
            name="Get Player Stats"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get player stats: {response.status_code}")


class MixedWorkloadUser(HttpUser):
    """Simulate mixed workload across all services."""
    
    wait_time = between(1, 4)
    
    def on_start(self):
        """Initialize mixed workload user."""
        self.user_id = random.randint(1000000, 9999999)
        self.game_id = None
        self.session_id = None
        
        # Randomly choose user behavior
        self.behavior = random.choice(["creator", "player", "observer"])
        
        if self.behavior == "creator":
            self.setup_creator()
        elif self.behavior == "player":
            self.setup_player()
    
    def setup_creator(self):
        """Setup for game creator behavior."""
        # Create a game
        game_data = {
            "title": f"Mixed Load Game {self.user_id}",
            "type": "quiz",
            "questions": [
                {
                    "id": f"q{i}",
                    "type": "single_choice",
                    "question": f"Question {i}?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": i % 4,
                    "points": 10
                } for i in range(3)
            ]
        }
        
        response = self.client.post("/api/v1/games", json=game_data)
        if response.status_code == 201:
            self.game_id = response.json().get("id")
    
    def setup_player(self):
        """Setup for player behavior."""
        # Join an existing session
        self.session_id = f"existing-session-{random.randint(1, 20)}"
    
    @task
    def mixed_activity(self):
        """Perform mixed activities based on user behavior."""
        if self.behavior == "creator":
            self.creator_activity()
        elif self.behavior == "player":
            self.player_activity()
        else:
            self.observer_activity()
    
    def creator_activity(self):
        """Activities for game creators."""
        activities = [
            self.check_game_status,
            self.create_session,
            self.monitor_session,
            self.view_analytics
        ]
        
        activity = random.choice(activities)
        activity()
    
    def player_activity(self):
        """Activities for players."""
        activities = [
            self.join_random_session,
            self.submit_random_answer,
            self.check_leaderboard
        ]
        
        activity = random.choice(activities)
        activity()
    
    def observer_activity(self):
        """Activities for observers."""
        activities = [
            self.browse_games,
            self.view_public_leaderboards,
            self.check_system_stats
        ]
        
        activity = random.choice(activities)
        activity()
    
    def check_game_status(self):
        """Check game status."""
        if self.game_id:
            self.client.get(f"/api/v1/games/{self.game_id}", name="Check Game Status")
    
    def create_session(self):
        """Create a new session."""
        if self.game_id:
            session_data = {
                "game_id": self.game_id,
                "admin_id": self.user_id,
                "settings": {"max_players": 10}
            }
            response = self.client.post("/api/v1/sessions", json=session_data, name="Create Session")
            if response.status_code == 201:
                self.session_id = response.json().get("session_id")
    
    def monitor_session(self):
        """Monitor session status."""
        if self.session_id:
            self.client.get(f"/api/v1/sessions/{self.session_id}", name="Monitor Session")
    
    def view_analytics(self):
        """View game analytics."""
        if self.game_id:
            self.client.get(f"/api/v1/analytics/{self.game_id}", name="View Analytics")
    
    def join_random_session(self):
        """Join a random session."""
        session_id = f"public-session-{random.randint(1, 10)}"
        player_data = {
            "user_id": self.user_id,
            "username": f"player_{self.user_id}",
            "first_name": f"Player{self.user_id}"
        }
        self.client.post(f"/api/v1/sessions/{session_id}/join", json=player_data, name="Join Random Session")
    
    def submit_random_answer(self):
        """Submit a random answer."""
        if self.session_id:
            answer_data = {
                "question_id": f"q{random.randint(1, 5)}",
                "answer": random.randint(0, 3),
                "timestamp": time.time()
            }
            self.client.post(f"/api/v1/sessions/{self.session_id}/answer", json=answer_data, name="Submit Answer")
    
    def check_leaderboard(self):
        """Check leaderboard."""
        game_id = f"popular-game-{random.randint(1, 5)}"
        self.client.get(f"/api/v1/leaderboard/{game_id}", name="Check Leaderboard")
    
    def browse_games(self):
        """Browse available games."""
        self.client.get("/api/v1/games", name="Browse Games")
    
    def view_public_leaderboards(self):
        """View public leaderboards."""
        game_id = f"featured-game-{random.randint(1, 3)}"
        self.client.get(f"/api/v1/leaderboard/{game_id}", name="View Public Leaderboard")
    
    def check_system_stats(self):
        """Check system statistics."""
        self.client.get("/api/v1/stats/system", name="Check System Stats")


# Event handlers for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Handle request events for custom metrics."""
    if exception:
        print(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Handle test start event."""
    print("Load test starting...")
    print(f"Target host: {environment.host}")
    print(f"Number of users: {environment.runner.target_user_count}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Handle test stop event."""
    print("Load test completed!")
    
    # Print summary statistics
    stats = environment.runner.stats
    print(f"\nSummary:")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.current_rps:.2f}")
    
    # Print per-endpoint statistics
    print(f"\nPer-endpoint statistics:")
    for name, entry in stats.entries.items():
        if entry.num_requests > 0:
            print(f"{name}: {entry.num_requests} requests, "
                  f"{entry.avg_response_time:.2f}ms avg, "
                  f"{entry.num_failures} failures")


# Custom user classes for different load patterns
class BurstLoadUser(HttpUser):
    """Simulate burst load patterns."""
    
    wait_time = between(0.1, 0.5)  # Very short wait times for burst
    
    @task
    def burst_requests(self):
        """Make rapid requests to simulate burst load."""
        endpoints = [
            "/api/v1/games",
            "/api/v1/sessions",
            "/health"
        ]
        
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name=f"Burst - {endpoint}")


class SteadyLoadUser(HttpUser):
    """Simulate steady, consistent load."""
    
    wait_time = between(5, 10)  # Longer wait times for steady load
    
    @task
    def steady_requests(self):
        """Make consistent requests."""
        self.client.get("/api/v1/games", name="Steady - List Games")
        time.sleep(1)
        self.client.get("/health", name="Steady - Health Check")


# Load test scenarios
class GameCreationScenario(HttpUser):
    """Focused scenario for testing game creation under load."""
    
    wait_time = between(2, 5)
    
    @task
    def create_and_manage_game(self):
        """Complete game creation and management workflow."""
        
        # Step 1: Create game
        game_data = {
            "title": f"Scenario Game {random.randint(1, 1000)}",
            "type": "quiz",
            "questions": [
                {
                    "id": f"q{i}",
                    "type": "single_choice",
                    "question": f"Scenario question {i}?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": i % 4,
                    "points": 10
                } for i in range(random.randint(5, 15))
            ]
        }
        
        response = self.client.post("/api/v1/games", json=game_data, name="Scenario - Create Game")
        
        if response.status_code == 201:
            game_id = response.json().get("id")
            
            # Step 2: Create session
            session_data = {
                "game_id": game_id,
                "admin_id": random.randint(1000000, 9999999),
                "settings": {"max_players": random.randint(5, 20)}
            }
            
            session_response = self.client.post("/api/v1/sessions", json=session_data, name="Scenario - Create Session")
            
            if session_response.status_code == 201:
                session_id = session_response.json().get("session_id")
                
                # Step 3: Simulate players joining
                for i in range(random.randint(2, 5)):
                    player_data = {
                        "user_id": random.randint(2000000, 2999999),
                        "username": f"scenario_player_{i}",
                        "first_name": f"Player{i}"
                    }
                    
                    self.client.post(
                        f"/api/v1/sessions/{session_id}/join",
                        json=player_data,
                        name="Scenario - Player Join"
                    )
                
                # Step 4: Start session
                self.client.post(f"/api/v1/sessions/{session_id}/start", name="Scenario - Start Session")