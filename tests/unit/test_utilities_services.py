"""
Unit tests for utility functions and service classes.
"""
import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
import json
import tempfile
import os


class TestFileHandlers:
    """Test file handling utilities."""
    
    def test_json_file_operations(self):
        """Test JSON file read/write operations."""
        from shared.utils.file_utils import JSONFileHandler
        
        handler = JSONFileHandler()
        test_data = {
            "test": "data",
            "number": 42,
            "list": [1, 2, 3]
        }
        
        # Test writing to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Write data
            handler.write_json(tmp_path, test_data)
            
            # Read data back
            loaded_data = handler.read_json(tmp_path)
            
            assert loaded_data == test_data
            assert loaded_data["test"] == "data"
            assert loaded_data["number"] == 42
            
        finally:
            os.unlink(tmp_path)
    
    def test_json_validation(self):
        """Test JSON file validation."""
        from shared.utils.file_utils import JSONFileHandler
        
        handler = JSONFileHandler()
        
        # Valid JSON
        valid_json = '{"valid": true, "data": [1, 2, 3]}'
        assert handler.validate_json(valid_json) == True
        
        # Invalid JSON
        invalid_json = '{"invalid": true, "missing_quote: "value"}'
        assert handler.validate_json(invalid_json) == False
        
        # Empty string
        assert handler.validate_json("") == False
        
        # None
        assert handler.validate_json(None) == False
    
    def test_game_pack_validation(self):
        """Test game pack file validation."""
        from shared.utils.game_pack_validator import GamePackValidator
        
        validator = GamePackValidator()
        
        # Valid game pack
        valid_pack = {
            "name": "Test Pack",
            "description": "Test game pack",
            "version": "1.0.0",
            "games": [
                {
                    "id": "test-game",
                    "title": "Test Game",
                    "type": "quiz",
                    "questions": [
                        {
                            "id": "q1",
                            "type": "single_choice",
                            "question": "Test?",
                            "options": ["A", "B"],
                            "correct_answer": 0,
                            "points": 10
                        }
                    ]
                }
            ]
        }
        
        result = validator.validate_pack(valid_pack)
        assert result.is_valid == True
        assert len(result.errors) == 0
        
        # Invalid game pack - missing required fields
        invalid_pack = {
            "name": "Test Pack"
            # Missing games array
        }
        
        result = validator.validate_pack(invalid_pack)
        assert result.is_valid == False
        assert len(result.errors) > 0
    
    def test_file_size_validation(self):
        """Test file size validation."""
        from shared.utils.file_utils import validate_file_size
        
        # Create temporary file with known size
        test_content = "x" * 1000  # 1KB
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_path = tmp_file.name
        
        try:
            # Test size validation
            assert validate_file_size(tmp_path, max_size_mb=1) == True  # 1MB limit
            assert validate_file_size(tmp_path, max_size_mb=0.001) == False  # 1KB limit
            
        finally:
            os.unlink(tmp_path)


class TestQRCodeGenerator:
    """Test QR code generation utilities."""
    
    def test_qr_code_generation(self):
        """Test QR code generation."""
        from shared.utils.qr_generator import QRCodeGenerator
        
        generator = QRCodeGenerator()
        
        # Test basic QR code generation
        qr_data = generator.generate_qr_code("https://t.me/testbot?start=join_session123")
        
        assert qr_data is not None
        assert isinstance(qr_data, bytes)
        assert len(qr_data) > 0
    
    def test_qr_code_with_logo(self):
        """Test QR code generation with logo."""
        from shared.utils.qr_generator import QRCodeGenerator
        
        generator = QRCodeGenerator()
        
        # Create a simple test logo (1x1 pixel PNG)
        logo_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xd2\x00\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as logo_file:
            logo_file.write(logo_data)
            logo_path = logo_file.name
        
        try:
            qr_data = generator.generate_qr_code(
                "https://example.com",
                logo_path=logo_path
            )
            
            assert qr_data is not None
            assert isinstance(qr_data, bytes)
            
        finally:
            os.unlink(logo_path)
    
    def test_qr_code_customization(self):
        """Test QR code customization options."""
        from shared.utils.qr_generator import QRCodeGenerator
        
        generator = QRCodeGenerator()
        
        # Test with custom colors and size
        qr_data = generator.generate_qr_code(
            "test data",
            fill_color="blue",
            back_color="white",
            box_size=15,
            border=2
        )
        
        assert qr_data is not None
        assert isinstance(qr_data, bytes)


class TestSessionCodeGenerator:
    """Test session code generation utilities."""
    
    def test_code_generation(self):
        """Test session code generation."""
        from shared.utils.code_generator import SessionCodeGenerator
        
        generator = SessionCodeGenerator()
        
        # Generate multiple codes
        codes = [generator.generate_code() for _ in range(100)]
        
        # All codes should be unique
        assert len(set(codes)) == 100
        
        # All codes should match expected format
        for code in codes:
            assert len(code) == 6
            assert code.isalnum()
            assert code.isupper()
    
    def test_code_collision_avoidance(self):
        """Test code collision avoidance."""
        from shared.utils.code_generator import SessionCodeGenerator
        
        generator = SessionCodeGenerator()
        
        # Mock existing codes
        existing_codes = {"ABC123", "XYZ789", "DEF456"}
        
        # Generate new code avoiding collisions
        new_code = generator.generate_unique_code(existing_codes)
        
        assert new_code not in existing_codes
        assert len(new_code) == 6
    
    def test_code_expiration(self):
        """Test code expiration logic."""
        from shared.utils.code_generator import SessionCodeGenerator
        
        generator = SessionCodeGenerator()
        
        # Test if code is expired
        old_timestamp = datetime.now() - timedelta(hours=2)
        recent_timestamp = datetime.now() - timedelta(minutes=5)
        
        assert generator.is_code_expired(old_timestamp, expiry_hours=1) == True
        assert generator.is_code_expired(recent_timestamp, expiry_hours=1) == False


class TestCryptographyUtils:
    """Test cryptography utilities."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        from shared.utils.crypto_utils import PasswordHasher
        
        hasher = PasswordHasher()
        password = "test_password_123"
        
        # Hash password
        hashed = hasher.hash_password(password)
        
        assert hashed != password  # Should be different from original
        assert len(hashed) > 0
        
        # Verify correct password
        assert hasher.verify_password(password, hashed) == True
        
        # Verify incorrect password
        assert hasher.verify_password("wrong_password", hashed) == False
    
    def test_token_generation(self):
        """Test secure token generation."""
        from shared.utils.crypto_utils import TokenGenerator
        
        generator = TokenGenerator()
        
        # Generate tokens
        token1 = generator.generate_token(32)
        token2 = generator.generate_token(32)
        
        assert token1 != token2  # Should be unique
        assert len(token1) == 64  # 32 bytes = 64 hex chars
        assert len(token2) == 64
        
        # Test different lengths
        short_token = generator.generate_token(16)
        assert len(short_token) == 32  # 16 bytes = 32 hex chars
    
    def test_data_encryption(self):
        """Test data encryption and decryption."""
        from shared.utils.crypto_utils import DataEncryptor
        
        encryptor = DataEncryptor("test_secret_key_32_characters_long")
        test_data = "sensitive information"
        
        # Encrypt data
        encrypted = encryptor.encrypt(test_data)
        assert encrypted != test_data
        
        # Decrypt data
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == test_data


class TestDateTimeUtils:
    """Test date and time utilities."""
    
    def test_timezone_conversion(self):
        """Test timezone conversion utilities."""
        from shared.utils.datetime_utils import TimezoneConverter
        
        converter = TimezoneConverter()
        
        # Test UTC to Moscow conversion
        utc_time = datetime(2024, 1, 1, 12, 0, 0)
        moscow_time = converter.utc_to_timezone(utc_time, "Europe/Moscow")
        
        assert moscow_time.hour == 15  # UTC+3
        
        # Test Moscow to UTC conversion
        moscow_time = datetime(2024, 1, 1, 15, 0, 0)
        utc_time = converter.timezone_to_utc(moscow_time, "Europe/Moscow")
        
        assert utc_time.hour == 12
    
    def test_duration_formatting(self):
        """Test duration formatting."""
        from shared.utils.datetime_utils import format_duration
        
        # Test various durations
        assert format_duration(30) == "30 seconds"
        assert format_duration(90) == "1 minute 30 seconds"
        assert format_duration(3661) == "1 hour 1 minute 1 second"
        assert format_duration(7200) == "2 hours"
    
    def test_relative_time(self):
        """Test relative time formatting."""
        from shared.utils.datetime_utils import get_relative_time
        
        now = datetime.now()
        
        # Test past times
        past_time = now - timedelta(minutes=5)
        assert "5 minutes ago" in get_relative_time(past_time)
        
        past_time = now - timedelta(hours=2)
        assert "2 hours ago" in get_relative_time(past_time)
        
        # Test future times
        future_time = now + timedelta(minutes=10)
        assert "in 10 minutes" in get_relative_time(future_time)


class TestValidationUtils:
    """Test validation utilities."""
    
    def test_input_sanitization(self):
        """Test input sanitization."""
        from shared.utils.validation_utils import sanitize_input
        
        # Test HTML sanitization
        dirty_input = "<script>alert('xss')</script>Hello World"
        clean_input = sanitize_input(dirty_input)
        
        assert "<script>" not in clean_input
        assert "Hello World" in clean_input
        
        # Test SQL injection prevention
        sql_input = "'; DROP TABLE users; --"
        clean_sql = sanitize_input(sql_input)
        
        assert "DROP TABLE" not in clean_sql
    
    def test_profanity_filter(self):
        """Test profanity filtering."""
        from shared.utils.validation_utils import ProfanityFilter
        
        filter = ProfanityFilter()
        
        # Test clean text
        clean_text = "This is a nice message"
        assert filter.is_clean(clean_text) == True
        
        # Test profanity detection (using mild examples)
        profane_text = "This is a damn message"
        assert filter.is_clean(profane_text) == False
        
        # Test profanity replacement
        filtered_text = filter.filter_text(profane_text)
        assert "damn" not in filtered_text
        assert "*" in filtered_text or "***" in filtered_text
    
    def test_rate_limiting(self):
        """Test rate limiting utilities."""
        from shared.utils.validation_utils import RateLimiter
        
        limiter = RateLimiter(max_requests=5, time_window=60)  # 5 requests per minute
        
        user_id = "test_user"
        
        # First 5 requests should be allowed
        for i in range(5):
            assert limiter.is_allowed(user_id) == True
        
        # 6th request should be blocked
        assert limiter.is_allowed(user_id) == False
        
        # Test different user
        assert limiter.is_allowed("other_user") == True


class TestCacheUtils:
    """Test caching utilities."""
    
    def test_memory_cache(self):
        """Test in-memory caching."""
        from shared.utils.cache_utils import MemoryCache
        
        cache = MemoryCache(max_size=100, ttl=60)
        
        # Test basic operations
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test non-existent key
        assert cache.get("non_existent") is None
        
        # Test cache size limit
        for i in range(150):
            cache.set(f"key{i}", f"value{i}")
        
        # Should not exceed max_size
        assert len(cache._cache) <= 100
    
    def test_cache_expiration(self):
        """Test cache expiration."""
        from shared.utils.cache_utils import MemoryCache
        import time
        
        cache = MemoryCache(ttl=1)  # 1 second TTL
        
        cache.set("temp_key", "temp_value")
        assert cache.get("temp_key") == "temp_value"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("temp_key") is None
    
    @pytest.mark.asyncio
    async def test_async_cache_decorator(self):
        """Test async cache decorator."""
        from shared.utils.cache_utils import async_cache
        
        call_count = 0
        
        @async_cache(ttl=60)
        async def expensive_operation(x):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x * 2
        
        # First call
        result1 = await expensive_operation(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call with same argument (should use cache)
        result2 = await expensive_operation(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
        
        # Call with different argument
        result3 = await expensive_operation(10)
        assert result3 == 20
        assert call_count == 2


class TestAPIClientUtils:
    """Test API client utilities."""
    
    @pytest.mark.asyncio
    async def test_http_client_wrapper(self):
        """Test HTTP client wrapper."""
        from shared.utils.http_client import HTTPClient
        
        client = HTTPClient(base_url="https://httpbin.org", timeout=10)
        
        # Test GET request
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_get.return_value = mock_response
            
            response = await client.get("/get")
            assert response["success"] == True
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test HTTP client retry mechanism."""
        from shared.utils.http_client import HTTPClient
        
        client = HTTPClient(base_url="https://example.com", max_retries=3)
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # First two calls fail, third succeeds
            mock_get.side_effect = [
                Exception("Network error"),
                Exception("Timeout"),
                MagicMock(status_code=200, json=lambda: {"success": True})
            ]
            
            response = await client.get("/test")
            assert response["success"] == True
            assert mock_get.call_count == 3
    
    @pytest.mark.asyncio
    async def test_request_logging(self):
        """Test HTTP request logging."""
        from shared.utils.http_client import HTTPClient
        
        client = HTTPClient(base_url="https://example.com", log_requests=True)
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"created": True}
            mock_post.return_value = mock_response
            
            with patch('shared.utils.http_client.logger') as mock_logger:
                await client.post("/create", json={"data": "test"})
                
                # Should log request and response
                assert mock_logger.info.called
                assert mock_logger.debug.called


class TestMessageFormatting:
    """Test message formatting utilities."""
    
    def test_telegram_message_formatting(self):
        """Test Telegram message formatting."""
        from shared.utils.message_formatter import TelegramFormatter
        
        formatter = TelegramFormatter()
        
        # Test basic formatting
        text = formatter.bold("Bold text")
        assert text == "*Bold text*"
        
        text = formatter.italic("Italic text")
        assert text == "_Italic text_"
        
        text = formatter.code("code snippet")
        assert text == "`code snippet`"
        
        # Test escaping
        text = formatter.escape("Text with * special _ chars")
        assert "*" not in text or "\\*" in text
    
    def test_game_result_formatting(self):
        """Test game result message formatting."""
        from shared.utils.message_formatter import GameResultFormatter
        
        formatter = GameResultFormatter()
        
        result_data = {
            "player_name": "TestPlayer",
            "score": 85,
            "max_score": 100,
            "rank": 2,
            "total_players": 10,
            "correct_answers": 8,
            "total_questions": 10
        }
        
        message = formatter.format_result(result_data)
        
        assert "TestPlayer" in message
        assert "85" in message
        assert "2" in message  # rank
        assert "8/10" in message  # correct answers
    
    def test_leaderboard_formatting(self):
        """Test leaderboard formatting."""
        from shared.utils.message_formatter import LeaderboardFormatter
        
        formatter = LeaderboardFormatter()
        
        leaderboard_data = [
            {"rank": 1, "name": "Player1", "score": 95},
            {"rank": 2, "name": "Player2", "score": 85},
            {"rank": 3, "name": "Player3", "score": 75}
        ]
        
        message = formatter.format_leaderboard(leaderboard_data)
        
        assert "🥇" in message  # Gold medal for 1st place
        assert "🥈" in message  # Silver medal for 2nd place
        assert "🥉" in message  # Bronze medal for 3rd place
        assert "Player1" in message
        assert "95" in message


class TestUtilityPerformance:
    """Test utility performance characteristics."""
    
    @pytest.mark.performance
    def test_large_data_processing(self):
        """Test processing large amounts of data."""
        from shared.utils.data_processor import DataProcessor
        import time
        
        processor = DataProcessor()
        
        # Generate large dataset
        large_data = [{"id": i, "value": f"data_{i}"} for i in range(10000)]
        
        # Test processing time
        start_time = time.time()
        processed_data = processor.process_batch(large_data)
        processing_time = time.time() - start_time
        
        assert processing_time < 1.0  # Should process in less than 1 second
        assert len(processed_data) == len(large_data)
    
    @pytest.mark.performance
    def test_concurrent_operations(self):
        """Test concurrent utility operations."""
        from shared.utils.concurrent_processor import ConcurrentProcessor
        import asyncio
        
        processor = ConcurrentProcessor(max_workers=5)
        
        async def test_concurrent():
            tasks = []
            for i in range(100):
                task = processor.process_item(f"item_{i}")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results
        
        results = asyncio.run(test_concurrent())
        assert len(results) == 100
        assert all(result is not None for result in results)


class TestErrorHandlingUtils:
    """Test error handling utilities."""
    
    def test_exception_handler_decorator(self):
        """Test exception handler decorator."""
        from shared.utils.error_handlers import handle_exceptions
        
        @handle_exceptions(default_return="error")
        def risky_function(should_fail=False):
            if should_fail:
                raise ValueError("Something went wrong")
            return "success"
        
        # Test normal operation
        result = risky_function(should_fail=False)
        assert result == "success"
        
        # Test exception handling
        result = risky_function(should_fail=True)
        assert result == "error"
    
    @pytest.mark.asyncio
    async def test_async_exception_handler(self):
        """Test async exception handler."""
        from shared.utils.error_handlers import async_handle_exceptions
        
        @async_handle_exceptions(default_return=None)
        async def async_risky_function(should_fail=False):
            if should_fail:
                raise ConnectionError("Network error")
            return "async_success"
        
        # Test normal operation
        result = await async_risky_function(should_fail=False)
        assert result == "async_success"
        
        # Test exception handling
        result = await async_risky_function(should_fail=True)
        assert result is None
    
    def test_error_reporting(self):
        """Test error reporting utilities."""
        from shared.utils.error_handlers import ErrorReporter
        
        reporter = ErrorReporter()
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            error_id = reporter.report_error(e, context={"user_id": 123})
            
            assert error_id is not None
            assert len(error_id) > 0
            
            # Test error retrieval
            error_info = reporter.get_error(error_id)
            assert error_info is not None
            assert "ValueError" in error_info["type"]