"""
Unit tests for LLM Router and multi-provider integration.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.llm_router import LLMRouter, ChatResponse


class TestLLMRouter(unittest.TestCase):
    """Tests for LLMRouter provider implementations."""
    
    @patch('ollama.chat')
    def test_ollama_chat(self, mock_ollama_chat):
        """Test Ollama provider chat."""
        mock_ollama_chat.return_value = {
            "message": {"content": "Hello from Ollama!"},
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        
        router = LLMRouter(provider="ollama", model="test-model")
        response = router.chat(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7
        )
        
        self.assertEqual(response.content, "Hello from Ollama!")
        self.assertEqual(response.provider, "ollama")
        self.assertEqual(response.model, "test-model")
        mock_ollama_chat.assert_called_once()
        print("✓ Ollama adapter works correctly")

    @patch('core.llm_router.settings')
    def test_groq_missing_api_key(self, mock_settings):
        """Test Groq raises error when API key is missing."""
        mock_settings.groq_api_key = ""
        mock_settings.default_provider = "groq"
        mock_settings.default_model = "test"
        
        router = LLMRouter(provider="groq")
        
        with self.assertRaises(ValueError) as ctx:
            router.chat(messages=[{"role": "user", "content": "test"}])
        
        self.assertIn("GROQ_API_KEY", str(ctx.exception))
        print("✓ Groq API key validation works")

    @patch('core.llm_router.settings')
    def test_openai_missing_api_key(self, mock_settings):
        """Test OpenAI raises error when API key is missing."""
        mock_settings.openai_api_key = ""
        mock_settings.default_provider = "openai"
        mock_settings.default_model = "test"
        
        router = LLMRouter(provider="openai")
        
        with self.assertRaises(ValueError) as ctx:
            router.chat(messages=[{"role": "user", "content": "test"}])
        
        self.assertIn("OPENAI_API_KEY", str(ctx.exception))
        print("✓ OpenAI API key validation works")

    @patch('core.llm_router.settings')
    def test_gemini_missing_api_key(self, mock_settings):
        """Test Gemini raises error when API key is missing."""
        mock_settings.gemini_api_key = ""
        mock_settings.default_provider = "gemini"
        mock_settings.default_model = "test"
        
        router = LLMRouter(provider="gemini")
        
        with self.assertRaises(ValueError) as ctx:
            router.chat(messages=[{"role": "user", "content": "test"}])
        
        self.assertIn("GEMINI_API_KEY", str(ctx.exception))
        print("✓ Gemini API key validation works")

    def test_unknown_provider(self):
        """Test unknown provider raises error."""
        router = LLMRouter(provider="unknown_provider")
        
        with self.assertRaises(ValueError) as ctx:
            router.chat(messages=[{"role": "user", "content": "test"}])
        
        self.assertIn("Unknown provider", str(ctx.exception))
        print("✓ Unknown provider validation works")


class TestSettingsIntegration(unittest.TestCase):
    """Tests for settings and configuration."""
    
    def test_settings_load(self):
        """Test settings loads without errors."""
        from config.settings import settings
        
        # Should have default values
        self.assertEqual(settings.default_provider, "ollama")
        self.assertTrue(hasattr(settings, 'groq_api_key'))
        self.assertTrue(hasattr(settings, 'gemini_api_key'))
        self.assertTrue(hasattr(settings, 'openai_api_key'))
        print("✓ Settings load correctly")

    def test_available_providers(self):
        """Test get_available_providers method."""
        from config.settings import Settings
        
        # Create settings with some API keys
        test_settings = Settings(
            groq_api_key="test-key",
            gemini_api_key="",
            openai_api_key="test-key"
        )
        
        available = test_settings.get_available_providers()
        
        self.assertIn("ollama", available)  # Always available
        self.assertIn("groq", available)
        self.assertIn("openai", available)
        self.assertNotIn("gemini", available)  # No key
        print("✓ Available providers detection works")


if __name__ == '__main__':
    print("\n=== Running LLM Router Tests ===\n")
    unittest.main(verbosity=2)
