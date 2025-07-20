"""
Integration tests for Telegram bot workflows and handlers.
"""
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import patch, AsyncMock, MagicMock
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, User, Chat


class TestAdminBotWorkflows:
    """Test admin bot workflow scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_game_creation_workflow(
        self,
        mock_telegram_bot,
        sample_game_data: Dict[str, Any]
    ):
        """Test complete game creation workflow through admin bot."""
        
        # Mock message from admin
        admin_message = MagicMock()
        admin_message.from_user.id = 123456789
        admin_message.chat.id = 123456789
        admin_message.text = "/create_game"
        
        # Mock API client responses
        with patch('services.admin_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.create_game.return_value = sample_game_data
            
            # Import and test the handler
            from services.admin_bot.app.handlers.game_handlers import GameHandlers
            handler = GameHandlers()
            
            # Test game creation start
            await handler.start_game_creation(admin_message, mock_telegram_bot)
            
            # Verify bot sent response
            mock_telegram_bot.send_message.assert_called()
            call_args = mock_telegram_bot.send_message.call_args
            assert "game creation" in call_args[1]["text"].lower()
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_session_management_workflow(
        self,
        mock_telegram_bot,
        sample_session_data: Dict[str, Any]
    ):
        """Test session creation and management workflow."""
        
        admin_message = MagicMock()
        admin_message.from_user.id = 123456789
        admin_message.chat.id = 123456789
        admin_message.text = "/create_session"
        
        with patch('services.admin_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.create_session.return_value = sample_session_data
            api_instance.get_games.return_value = [{"id": "game1", "title": "Test Game"}]
            
            from services.admin_bot.app.handlers.session_handlers import SessionHandlers
            handler = SessionHandlers()
            
            # Test session creation
            await handler.create_session(admin_message, mock_telegram_bot)
            
            # Verify response
            mock_telegram_bot.send_message.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_qr_code_generation_workflow(
        self,
        mock_telegram_bot,
        mock_qr_generator,
        sample_session_data: Dict[str, Any]
    ):
        """Test QR code generation for session joining."""
        
        callback_query = MagicMock()
        callback_query.from_user.id = 123456789
        callback_query.data = f"generate_qr:{sample_session_data['session_id']}"
        callback_query.message.chat.id = 123456789
        
        with patch('services.admin_bot.app.services.qr_generator.QRGenerator') as mock_qr_class:
            mock_qr_class.return_value = mock_qr_generator
            
            from services.admin_bot.app.handlers.qr_handlers import QRHandlers
            handler = QRHandlers()
            
            await handler.generate_qr_code(callback_query, mock_telegram_bot)
            
            # Verify QR code was generated and sent
            mock_qr_generator.generate_qr_code.assert_called()
            mock_telegram_bot.send_photo.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_game_pack_import_workflow(
        self,
        mock_telegram_bot,
        mock_file_handler
    ):
        """Test game pack import workflow."""
        
        # Mock message with document
        message = MagicMock()
        message.from_user.id = 123456789
        message.chat.id = 123456789
        message.document = MagicMock()
        message.document.file_name = "game_pack.json"
        message.document.file_id = "test_file_id"
        
        with patch('services.admin_bot.app.services.file_handler.FileHandler') as mock_file_class:
            mock_file_class.return_value = mock_file_handler
            
            with patch('services.admin_bot.app.services.api_client.APIClient') as mock_api_client:
                api_instance = mock_api_client.return_value
                api_instance.import_game_pack.return_value = {"imported_games": 5}
                
                from services.admin_bot.app.handlers.game_handlers import GameHandlers
                handler = GameHandlers()
                
                await handler.import_game_pack(message, mock_telegram_bot)
                
                # Verify file was processed and games imported
                mock_file_handler.save_file.assert_called()
                api_instance.import_game_pack.assert_called()
                mock_telegram_bot.send_message.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_analytics_workflow(
        self,
        mock_telegram_bot
    ):
        """Test analytics viewing workflow."""
        
        callback_query = MagicMock()
        callback_query.from_user.id = 123456789
        callback_query.data = "analytics:game-123"
        callback_query.message.chat.id = 123456789
        
        analytics_data = {
            "total_games": 10,
            "total_players": 50,
            "average_score": 75.5,
            "completion_rate": 0.85
        }
        
        with patch('services.admin_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.get_analytics.return_value = analytics_data
            
            from services.admin_bot.app.handlers.analytics_handlers import AnalyticsHandlers
            handler = AnalyticsHandlers()
            
            await handler.show_analytics(callback_query, mock_telegram_bot)
            
            # Verify analytics were fetched and displayed
            api_instance.get_analytics.assert_called()
            mock_telegram_bot.send_message.assert_called()


class TestPlayerBotWorkflows:
    """Test player bot workflow scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_session_join_workflow(
        self,
        mock_telegram_bot,
        sample_session_data: Dict[str, Any]
    ):
        """Test player joining session workflow."""
        
        # Test joining by session code
        message = MagicMock()
        message.from_user.id = 987654321
        message.from_user.username = "test_player"
        message.from_user.first_name = "Test"
        message.from_user.last_name = "Player"
        message.chat.id = 987654321
        message.text = "ABC123"  # Session code
        
        with patch('services.player_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.join_session_by_code.return_value = {
                "success": True,
                "session_id": sample_session_data["session_id"]
            }
            api_instance.get_session.return_value = sample_session_data
            
            from services.player_bot.app.handlers.connection_handlers import ConnectionHandlers
            handler = ConnectionHandlers()
            
            await handler.join_by_code(message, mock_telegram_bot)
            
            # Verify player joined session
            api_instance.join_session_by_code.assert_called()
            mock_telegram_bot.send_message.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_deep_link_join_workflow(
        self,
        mock_telegram_bot,
        sample_session_data: Dict[str, Any]
    ):
        """Test joining session via deep link."""
        
        # Deep link message
        message = MagicMock()
        message.from_user.id = 987654321
        message.from_user.username = "test_player"
        message.chat.id = 987654321
        message.text = f"/start join_{sample_session_data['session_id']}"
        
        with patch('services.player_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.join_session.return_value = {"success": True}
            api_instance.get_session.return_value = sample_session_data
            
            from services.player_bot.app.handlers.connection_handlers import ConnectionHandlers
            handler = ConnectionHandlers()
            
            await handler.handle_deep_link(message, mock_telegram_bot)
            
            # Verify deep link was processed
            api_instance.join_session.assert_called()
            mock_telegram_bot.send_message.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_quiz_gameplay_workflow(
        self,
        mock_telegram_bot,
        sample_game_data: Dict[str, Any]
    ):
        """Test quiz gameplay workflow."""
        
        # Player answers question
        callback_query = MagicMock()
        callback_query.from_user.id = 987654321
        callback_query.data = "answer:q1:1"  # question_id:answer_index
        callback_query.message.chat.id = 987654321
        
        with patch('services.player_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.submit_answer.return_value = {
                "correct": True,
                "points": 10,
                "total_score": 10
            }
            
            from services.player_bot.app.handlers.question_handlers import QuestionHandlers
            handler = QuestionHandlers()
            
            await handler.submit_answer(callback_query, mock_telegram_bot)
            
            # Verify answer was submitted
            api_instance.submit_answer.assert_called()
            mock_telegram_bot.edit_message_text.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_results_viewing_workflow(
        self,
        mock_telegram_bot
    ):
        """Test viewing game results workflow."""
        
        callback_query = MagicMock()
        callback_query.from_user.id = 987654321
        callback_query.data = "results:session-123"
        callback_query.message.chat.id = 987654321
        
        results_data = {
            "final_score": 85,
            "rank": 2,
            "total_players": 5,
            "correct_answers": 8,
            "total_questions": 10
        }
        
        with patch('services.player_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.get_player_results.return_value = results_data
            
            from services.player_bot.app.handlers.results_handlers import ResultsHandlers
            handler = ResultsHandlers()
            
            await handler.show_results(callback_query, mock_telegram_bot)
            
            # Verify results were displayed
            api_instance.get_player_results.assert_called()
            mock_telegram_bot.send_message.assert_called()


class TestBotErrorHandling:
    """Test bot error handling scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_api_error_handling(
        self,
        mock_telegram_bot
    ):
        """Test handling of API errors in bot workflows."""
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.chat.id = 123456789
        message.text = "/create_game"
        
        # Mock API error
        with patch('services.admin_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.create_game.side_effect = Exception("API Error")
            
            from services.admin_bot.app.handlers.game_handlers import GameHandlers
            handler = GameHandlers()
            
            # Should handle error gracefully
            await handler.start_game_creation(message, mock_telegram_bot)
            
            # Verify error message was sent
            mock_telegram_bot.send_message.assert_called()
            call_args = mock_telegram_bot.send_message.call_args
            assert "error" in call_args[1]["text"].lower()
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_invalid_session_code_handling(
        self,
        mock_telegram_bot
    ):
        """Test handling of invalid session codes."""
        
        message = MagicMock()
        message.from_user.id = 987654321
        message.chat.id = 987654321
        message.text = "INVALID"
        
        with patch('services.player_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.join_session_by_code.return_value = {
                "success": False,
                "error": "Invalid session code"
            }
            
            from services.player_bot.app.handlers.connection_handlers import ConnectionHandlers
            handler = ConnectionHandlers()
            
            await handler.join_by_code(message, mock_telegram_bot)
            
            # Verify error was handled
            mock_telegram_bot.send_message.assert_called()
            call_args = mock_telegram_bot.send_message.call_args
            assert "invalid" in call_args[1]["text"].lower()
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_session_full_handling(
        self,
        mock_telegram_bot
    ):
        """Test handling when session is full."""
        
        message = MagicMock()
        message.from_user.id = 987654321
        message.chat.id = 987654321
        message.text = "ABC123"
        
        with patch('services.player_bot.app.services.api_client.APIClient') as mock_api_client:
            api_instance = mock_api_client.return_value
            api_instance.join_session_by_code.return_value = {
                "success": False,
                "error": "Session is full"
            }
            
            from services.player_bot.app.handlers.connection_handlers import ConnectionHandlers
            handler = ConnectionHandlers()
            
            await handler.join_by_code(message, mock_telegram_bot)
            
            # Verify appropriate message was sent
            mock_telegram_bot.send_message.assert_called()
            call_args = mock_telegram_bot.send_message.call_args
            assert "full" in call_args[1]["text"].lower()


class TestBotMiddlewares:
    """Test bot middleware functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_logging_middleware(
        self,
        mock_telegram_bot
    ):
        """Test logging middleware captures bot interactions."""
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.chat.id = 123456789
        message.text = "/start"
        
        with patch('services.admin_bot.app.middlewares.logging_middleware.logger') as mock_logger:
            from services.admin_bot.app.middlewares.logging_middleware import LoggingMiddleware
            middleware = LoggingMiddleware()
            
            # Mock handler
            async def mock_handler(message, bot):
                await bot.send_message(message.chat.id, "Response")
            
            await middleware.pre_process(message, {})
            await mock_handler(message, mock_telegram_bot)
            await middleware.post_process(message, {}, None)
            
            # Verify logging occurred
            assert mock_logger.info.called
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_error_handling_middleware(
        self,
        mock_telegram_bot
    ):
        """Test error handling middleware catches exceptions."""
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.chat.id = 123456789
        message.text = "/error"
        
        from services.admin_bot.app.middlewares.error_handler import ErrorHandlerMiddleware
        middleware = ErrorHandlerMiddleware()
        
        # Mock handler that raises exception
        async def failing_handler(message, bot):
            raise Exception("Test error")
        
        # Should handle error gracefully
        result = await middleware.process_error(message, Exception("Test error"))
        
        # Verify error was handled
        assert result is True


class TestBotStates:
    """Test bot state management."""
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_game_creation_states(
        self,
        mock_telegram_bot
    ):
        """Test state transitions during game creation."""
        
        from services.admin_bot.app.states import GameCreationStates
        
        # Test state transitions
        assert GameCreationStates.WAITING_TITLE != GameCreationStates.WAITING_DESCRIPTION
        assert GameCreationStates.WAITING_QUESTIONS != GameCreationStates.WAITING_CONFIRMATION
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    async def test_player_states(
        self,
        mock_telegram_bot
    ):
        """Test player state management."""
        
        from services.player_bot.app.states import PlayerStates
        
        # Test state transitions
        assert PlayerStates.WAITING_SESSION_CODE != PlayerStates.IN_GAME
        assert PlayerStates.ANSWERING_QUESTION != PlayerStates.VIEWING_RESULTS


class TestBotKeyboards:
    """Test bot keyboard generation."""
    
    @pytest.mark.bot
    def test_main_menu_keyboard(self):
        """Test main menu keyboard generation."""
        
        from services.admin_bot.app.keyboards.main_menu import get_main_menu_keyboard
        
        keyboard = get_main_menu_keyboard()
        
        # Verify keyboard structure
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0
    
    @pytest.mark.bot
    def test_game_management_keyboard(self):
        """Test game management keyboard."""
        
        from services.admin_bot.app.keyboards.game_management import get_game_management_keyboard
        
        games = [
            {"id": "game1", "title": "Test Game 1"},
            {"id": "game2", "title": "Test Game 2"}
        ]
        
        keyboard = get_game_management_keyboard(games)
        
        # Verify keyboard contains games
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) >= len(games)
    
    @pytest.mark.bot
    def test_question_keyboard(self):
        """Test question answer keyboard."""
        
        from services.player_bot.app.keyboards.questions import get_question_keyboard
        
        question = {
            "id": "q1",
            "type": "single_choice",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"]
        }
        
        keyboard = get_question_keyboard(question)
        
        # Verify keyboard has options
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == len(question["options"])


class TestBotIntegrationFlow:
    """Test complete bot integration scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.bot
    @pytest.mark.e2e
    async def test_complete_admin_to_player_flow(
        self,
        mock_telegram_bot,
        sample_game_data: Dict[str, Any],
        sample_session_data: Dict[str, Any]
    ):
        """Test complete flow from admin creating game to players joining."""
        
        # Step 1: Admin creates game
        admin_message = MagicMock()
        admin_message.from_user.id = 123456789
        admin_message.chat.id = 123456789
        
        with patch('services.admin_bot.app.services.api_client.APIClient') as mock_admin_api:
            admin_api = mock_admin_api.return_value
            admin_api.create_game.return_value = sample_game_data
            admin_api.create_session.return_value = sample_session_data
            
            # Create game
            from services.admin_bot.app.handlers.game_handlers import GameHandlers
            game_handler = GameHandlers()
            await game_handler.start_game_creation(admin_message, mock_telegram_bot)
            
            # Create session
            from services.admin_bot.app.handlers.session_handlers import SessionHandlers
            session_handler = SessionHandlers()
            await session_handler.create_session(admin_message, mock_telegram_bot)
        
        # Step 2: Player joins session
        player_message = MagicMock()
        player_message.from_user.id = 987654321
        player_message.chat.id = 987654321
        player_message.text = "ABC123"
        
        with patch('services.player_bot.app.services.api_client.APIClient') as mock_player_api:
            player_api = mock_player_api.return_value
            player_api.join_session_by_code.return_value = {"success": True}
            
            from services.player_bot.app.handlers.connection_handlers import ConnectionHandlers
            connection_handler = ConnectionHandlers()
            await connection_handler.join_by_code(player_message, mock_telegram_bot)
        
        # Verify both admin and player interactions
        assert mock_telegram_bot.send_message.call_count >= 2