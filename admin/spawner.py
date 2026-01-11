from enum import Enum
from dataclasses import dataclass
import time
from config.settings import settings


class AgentType(Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    FINALIZER = "finalizer"
    VISION = "vision"


@dataclass
class AgentConfig:
    agent_id: str
    agent_type: AgentType
    model_name: str
    temperature: float
    provider: str


class AgentSpawner:
    """
    Spawns agent configurations using settings from config.
    """
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize spawner.
        
        Args:
            model: Override default model from settings
            provider: Override default provider from settings
        """
        self.model = model or settings.default_model
        self.provider = provider or settings.default_provider
    
    def spawn_agent(self, agent_type: AgentType, task: str) -> AgentConfig:
        """
        Create an agent configuration.
        
        Args:
            agent_type: Type of agent to spawn
            task: Task description (used for agent ID)
            
        Returns:
            AgentConfig with model and provider info
        """
        return AgentConfig(
            agent_id=f"{agent_type.value}_{int(time.time())}",
            agent_type=agent_type,
            model_name=self.model,
            temperature=0.7,
            provider=self.provider
        )
