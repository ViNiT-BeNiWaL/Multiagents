from enum import Enum
from dataclasses import dataclass
import time

class AgentType(Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    FINALIZER = "finalizer"

@dataclass
class AgentConfig:
    agent_id: str
    agent_type: AgentType
    model_name: str
    temperature: float

class AgentSpawner:
    def spawn_agent(self, agent_type: AgentType, task: str):
        return AgentConfig(
            agent_id=f"{agent_type.value}_{int(time.time())}",
            agent_type=agent_type,
            model_name="deepseek-v3.1:671b-cloud",
            temperature=0.7
        )
