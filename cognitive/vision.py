from typing import List, Dict, Any, Optional
from core.llm_router import LLMRouter
import os

class VisionAgent:
    """
    Specialized agent for computer vision tasks (UI/UX analysis, code from screenshot).
    """
    
    def __init__(self, model_name: str, provider: str = None):
        """
        Initialize the vision agent.
        
        Args:
            model_name: Name of the vision-capable model (e.g., llava, gpt-4o)
            provider: LLM provider (ollama, openai, etc.)
        """
        self.model = model_name
        self.provider = provider
        self.router = LLMRouter(provider=provider, model=model_name)

    def analyze_ui(self, image_paths: List[str]) -> str:
        """
        Analyze UI images and return a structural description.
        """
        system_prompt = (
            "You are an expert Frontend Architect and UI/UX Designer. "
            "Analyze the provided image(s) of a user interface. "
            "Describe the layout, components, colors, and functionality in technical detail. "
            "Focus on hierarchy: Header, Sidebar, Main Content, Footer."
        )
        
        response = self.router.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Analyze this UI design."}
            ],
            images=image_paths,
            temperature=0.2
        )
        
        return response.content

    def generate_code_from_image(self, image_paths: List[str], stack: str = "React/Tailwind") -> Dict[str, str]:
        """
        Generate code based on UI images.
        Returns a dict of filename -> code content.
        
        Note: This currently returns a single block or text. In a full implementation,
        we would parse the response into multiple files.
        """
        system_prompt = (
            f"You are an expert Full Stack Developer specializing in {stack}. "
            "Look at the provided design screenshot and turn it into clean, production-ready code. "
            "If multiple files are needed, separate them clearly with '### FILE: filename'.\n"
            "Include comments for complex logic."
        )
        
        response = self.router.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Turn this design into code."}
            ],
            images=image_paths,
            temperature=0.4
        )
        
        # Simple parser to extract files
        results = {}
        content = response.content
        
        if "### FILE:" in content:
            parts = content.split("### FILE:")
            for part in parts[1:]:  # Skip pre-text
                lines = part.strip().split("\n")
                filename = lines[0].strip()
                code = "\n".join(lines[1:]).strip()
                # Remove markdown code fences if present
                if code.startswith("```"):
                    code = code.split("\n", 1)[1]
                if code.endswith("```"):
                    code = code.rsplit("\n", 1)[0]
                
                results[filename] = code
        else:
            # Fallback for single file or raw text
            results["generated_view.js"] = content
            
        return results
