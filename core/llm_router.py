"""
LLM Router - Unified interface for multiple LLM providers.
Supports: Ollama (local), Groq, Google Gemini, and OpenAI.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from config.settings import settings


@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass 
class ChatResponse:
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None


class LLMRouter:
    """
    Routes LLM requests to the configured provider.
    """
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the router.
        
        Args:
            provider: Override default provider (ollama|groq|gemini|openai)
            model: Override default model
        """
        self.provider = provider or settings.default_provider
        self.model = model or settings.default_model
        
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        format: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Send a chat request to the configured LLM provider.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Override model for this request
            temperature: Sampling temperature
            format: Response format (e.g., "json")
            **kwargs: Additional provider-specific options
            
        Returns:
            ChatResponse with the model's reply
        """
        target_model = model or self.model
        
        if self.provider == "ollama":
            return self._ollama_chat(messages, target_model, temperature, format)
        elif self.provider == "groq":
            return self._groq_chat(messages, target_model, temperature, format)
        elif self.provider == "gemini":
            return self._gemini_chat(messages, target_model, temperature)
        elif self.provider == "openai":
            return self._openai_chat(messages, target_model, temperature, format)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    # =========================================================================
    # Provider Implementations
    # =========================================================================
    
    def _ollama_chat(
        self, 
        messages: List[Dict], 
        model: str, 
        temperature: float,
        format: Optional[str]
    ) -> ChatResponse:
        """Ollama (local) chat implementation."""
        import ollama
        
        options = {"temperature": temperature}
        kwargs = {"model": model, "messages": messages, "options": options}
        
        if format:
            kwargs["format"] = format
            
        response = ollama.chat(**kwargs)
        
        return ChatResponse(
            content=response["message"]["content"],
            model=model,
            provider="ollama",
            usage=response.get("usage")
        )
    
    def _groq_chat(
        self, 
        messages: List[Dict], 
        model: str, 
        temperature: float,
        format: Optional[str]
    ) -> ChatResponse:
        """Groq cloud chat implementation."""
        from groq import Groq
        
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not configured in .env")
        
        client = Groq(api_key=settings.groq_api_key)
        
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**kwargs)
        
        return ChatResponse(
            content=response.choices[0].message.content,
            model=model,
            provider="groq",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            } if response.usage else None
        )
    
    def _gemini_chat(
        self, 
        messages: List[Dict], 
        model: str, 
        temperature: float
    ) -> ChatResponse:
        """Google Gemini chat implementation."""
        import google.generativeai as genai
        
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured in .env")
        
        genai.configure(api_key=settings.gemini_api_key)
        
        # Convert messages to Gemini format
        gemini_model = genai.GenerativeModel(model)
        
        # Gemini uses a different format - combine system + user messages
        system_prompt = ""
        conversation = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                conversation.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                conversation.append({"role": "model", "parts": [msg["content"]]})
        
        # Start chat with history
        chat = gemini_model.start_chat(history=conversation[:-1] if len(conversation) > 1 else [])
        
        # Get the last user message
        last_message = conversation[-1]["parts"][0] if conversation else ""
        if system_prompt:
            last_message = f"{system_prompt}\n\n{last_message}"
        
        response = chat.send_message(
            last_message,
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )
        
        return ChatResponse(
            content=response.text,
            model=model,
            provider="gemini"
        )
    
    def _openai_chat(
        self, 
        messages: List[Dict], 
        model: str, 
        temperature: float,
        format: Optional[str]
    ) -> ChatResponse:
        """OpenAI chat implementation."""
        from openai import OpenAI
        
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured in .env")
        
        client = OpenAI(api_key=settings.openai_api_key)
        
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**kwargs)
        
        return ChatResponse(
            content=response.choices[0].message.content,
            model=model,
            provider="openai",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            } if response.usage else None
        )


# Convenience function for quick usage
def chat(messages: List[Dict[str, str]], **kwargs) -> str:
    """Quick chat function using default settings."""
    router = LLMRouter()
    response = router.chat(messages, **kwargs)
    return response.content
