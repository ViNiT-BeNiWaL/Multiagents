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
        images: Optional[List[str]] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Send a chat request to the configured LLM provider.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Override model for this request
            temperature: Sampling temperature
            format: Response format (e.g., "json")
            images: List of image paths or base64 strings (for vision models)
            **kwargs: Additional provider-specific options
            
        Returns:
            ChatResponse with the model's reply
        """
        target_model = model or self.model
        
        if self.provider == "ollama":
            return self._ollama_chat(messages, target_model, temperature, format, images)
        elif self.provider == "groq":
            return self._groq_chat(messages, target_model, temperature, format)
        elif self.provider == "gemini":
            return self._gemini_chat(messages, target_model, temperature, images)
        elif self.provider == "openai":
            return self._openai_chat(messages, target_model, temperature, format, images)
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
        format: Optional[str],
        images: Optional[List[str]] = None
    ) -> ChatResponse:
        """Ollama (local) chat implementation."""
        import ollama
        
        options = {"temperature": temperature}
        
        # Ollama expects images in the message object for the USER role
        # We need to inject images into the last user message if present
        final_messages = messages.copy()
        if images and final_messages:
            # Find last user message
            for i in range(len(final_messages) - 1, -1, -1):
                if final_messages[i]["role"] == "user":
                    final_messages[i]["images"] = images
                    break
        
        kwargs = {"model": model, "messages": final_messages, "options": options}
        
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
        temperature: float,
        images: Optional[List[str]] = None
    ) -> ChatResponse:
        """Google Gemini chat implementation."""
        import google.generativeai as genai
        from pathlib import Path
        import PIL.Image
        
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured in .env")
        
        genai.configure(api_key=settings.gemini_api_key)
        
        # Convert messages to Gemini format
        gemini_model = genai.GenerativeModel(model)
        
        # Prepare image objects
        image_parts = []
        if images:
            for img_path in images:
                if Path(img_path).exists():
                     image_parts.append(PIL.Image.open(img_path))
        
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
        last_text = conversation[-1]["parts"][0] if conversation else ""
        if system_prompt:
            last_text = f"{system_prompt}\n\n{last_text}"
            
        # Construct content for the final message (text + images)
        content_parts = [last_text] + image_parts
        
        response = chat.send_message(
            content_parts,
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
        format: Optional[str],
        images: Optional[List[str]] = None
    ) -> ChatResponse:
        """OpenAI chat implementation."""
        from openai import OpenAI
        import base64
        import mimetypes
        
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured in .env")
        
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Transform messages for vision if images exist
        if images:
            # We need to construct a robust content block for the user message
            # Assuming the last message is the user message to attach images to
            final_messages = []
            
            for i, msg in enumerate(messages):
                if i == len(messages) - 1 and msg["role"] == "user":
                    content_list = [{"type": "text", "text": msg["content"]}]
                    
                    for img_path in images:
                        # Simple check for URL vs local file
                        if img_path.startswith("http"):
                            content_list.append({
                                "type": "image_url",
                                "image_url": {"url": img_path}
                            })
                        else:
                            # Read local file and encode
                            with open(img_path, "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                                mime_type, _ = mimetypes.guess_type(img_path)
                                mime_type = mime_type or "image/jpeg"
                                content_list.append({
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{mime_type};base64,{encoded_string}"}
                                })
                    
                    final_messages.append({"role": "user", "content": content_list})
                else:
                    final_messages.append(msg)
        else:
            final_messages = messages
        
        kwargs = {
            "model": model,
            "messages": final_messages,
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
