from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Copy .env.example to .env and configure your API keys.
    """
    
    # LLM Provider API Keys
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    
    # Provider Configuration
    default_provider: str = "ollama"  # ollama | groq | gemini | openai
    ollama_base_url: str = "http://localhost:11434"
    
    # Model Configuration
    default_model: str = "deepseek-v3.1:671b-cloud"

    # Graph Database (Neo4j)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Application Settings
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def get_available_providers(self) -> list:
        """Returns list of providers that have API keys configured."""
        available = ["ollama"]  # Ollama is always available (local)
        
        if self.groq_api_key:
            available.append("groq")
        if self.gemini_api_key:
            available.append("gemini")
        if self.openai_api_key:
            available.append("openai")
            
        return available


# Global settings instance
settings = Settings()
