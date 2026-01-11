import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cognitive.vision import VisionAgent
from core.llm_router import ChatResponse

class TestVisionAgent(unittest.TestCase):
    
    @patch('core.llm_router.LLMRouter.chat')
    def test_analyze_ui(self, mock_chat):
        """Test UI analysis prompt and image handling."""
        mock_chat.return_value = ChatResponse(
            content="Header: Navigation bar with logo.",
            model="llava",
            provider="ollama"
        )
        
        agent = VisionAgent(model_name="llava", provider="ollama")
        result = agent.analyze_ui(["/path/to/image.png"])
        
        self.assertIn("Header", result)
        
        # Verify call args
        args, kwargs = mock_chat.call_args
        self.assertIn("images", kwargs)
        self.assertEqual(kwargs["images"], ["/path/to/image.png"])
        self.assertEqual(kwargs["temperature"], 0.2)
        print("✓ Vision analysis uses correct parameters")

    @patch('core.llm_router.LLMRouter.chat')
    def test_generate_code_parsing(self, mock_chat):
        """Test extraction of code files from vision response."""
        mock_response = """
        Here is the code:
        ### FILE: src/App.js
        ```javascript
        import React from 'react';
        function App() { return <div>Hello</div>; }
        ```
        ### FILE: src/styles.css
        body { color: red; }
        """
        
        mock_chat.return_value = ChatResponse(
            content=mock_response,
            model="gpt-4o",
            provider="openai"
        )
        
        agent = VisionAgent(model_name="gpt-4o", provider="openai")
        files = agent.generate_code_from_image(["/path/to/mockup.png"])
        
        self.assertIn("src/App.js", files)
        self.assertIn("src/styles.css", files)
        self.assertIn("import React", files["src/App.js"])
        # Check stripping of markdown blocks
        self.assertFalse(files["src/App.js"].startswith("```"))
        print("✓ Code parsing from vision response works")

if __name__ == '__main__':
    unittest.main()
