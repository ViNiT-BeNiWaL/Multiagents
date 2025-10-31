"""
Agent spawner for creating and managing agent instances
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import time
import re


class AgentType(Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    ANALYZER = "analyzer"
    FINALIZER = "finalizer"


class TaskCategory(Enum):
    CODING = "coding"
    REASONING = "reasoning"
    MATH = "math"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    GENERAL = "general"


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    agent_id: str
    agent_type: AgentType
    model_name: str
    task_category: TaskCategory
    max_iterations: int = 10
    timeout: int = 300
    temperature: float = 0.7


class ModelSelector:
    """Selects appropriate Ollama models based on task type"""

    # Model selection based on task type/category
    TASK_MODELS = {
        TaskCategory.CODING: [
            "qwen2.5-coder:7b",  # Best for code generation
            "deepseek-coder:6.7b",  # Excellent for code
            "codellama:7b",  # Specialized code model
            "qwen2.5:7b",  # Good general coding
        ],
        TaskCategory.REASONING: [
            "qwen2.5:14b",  # Strong reasoning
            "llama3.1:8b",  # Good logic
            "phi3:medium",  # Efficient reasoning
            "gemma2:9b",  # Solid reasoning
        ],
        TaskCategory.MATH: [
            "qwen2.5:14b",  # Excellent math
            "deepseek-math:7b",  # Math specialist
            "llama3.1:8b",  # Good math capabilities
            "phi3:medium",  # Decent math
        ],
        TaskCategory.CREATIVE: [
            "llama3.1:8b",  # Creative writing
            "mistral:7b",  # Good creativity
            "gemma2:9b",  # Creative tasks
            "neural-chat:7b",  # Conversational/creative
        ],
        TaskCategory.ANALYSIS: [
            "llama3.1:8b",  # Data analysis
            "qwen2.5:14b",  # Deep analysis
            "mistral:7b",  # Good analytical
            "gemma2:9b",  # Analysis tasks
        ],
        TaskCategory.PLANNING: [
            "qwen2.5:14b",  # Strategic planning
            "llama3.1:8b",  # Task planning
            "mixtral:8x7b",  # Complex planning
            "gemma2:9b",  # Planning tasks
        ],
        TaskCategory.GENERAL: [
            "llama3.2:3b",  # Fast general tasks
            "phi3:mini",  # Efficient general
            "gemma2:2b",  # Quick responses
            "mistral:7b",  # Versatile
        ]
    }

    # Keywords to identify task type
    TASK_KEYWORDS = {
        TaskCategory.CODING: [
            'code', 'program', 'function', 'class', 'debug', 'implement',
            'script', 'algorithm', 'python', 'javascript', 'java', 'api',
            'refactor', 'optimize code', 'fix bug', 'write code'
        ],
        TaskCategory.REASONING: [
            'reason', 'logic', 'deduce', 'infer', 'conclude', 'prove',
            'argue', 'justify', 'explain why', 'figure out', 'solve problem'
        ],
        TaskCategory.MATH: [
            'calculate', 'compute', 'solve', 'equation', 'formula', 'math',
            'arithmetic', 'algebra', 'geometry', 'statistics', 'probability',
            'number', 'sum', 'multiply', 'divide'
        ],
        TaskCategory.CREATIVE: [
            'write', 'create', 'story', 'poem', 'article', 'blog', 'creative',
            'generate', 'compose', 'draft', 'imagine', 'design content'
        ],
        TaskCategory.ANALYSIS: [
            'analyze', 'examine', 'evaluate', 'assess', 'review', 'study',
            'investigate', 'research', 'compare', 'contrast', 'interpret'
        ],
        TaskCategory.PLANNING: [
            'plan', 'strategy', 'roadmap', 'schedule', 'organize', 'structure',
            'architecture', 'design system', 'workflow', 'pipeline', 'framework'
        ]
    }

    @classmethod
    def select_model(cls, task_description: str, agent_type: AgentType) -> tuple[str, TaskCategory]:
        """
        Select appropriate model based on task type

        Args:
            task_description: Description of the task
            agent_type: Type of agent

        Returns:
            Tuple of (model_name, task_category)
        """
        # Determine task category from description
        category = cls._identify_task_category(task_description, agent_type)

        # Get model for task category
        available_models = cls.TASK_MODELS[category]
        selected_model = available_models[0]  # Use first/best model for category

        return selected_model, category

    @classmethod
    def _identify_task_category(cls, task_description: str, agent_type: AgentType) -> TaskCategory:
        """Identify task category from description"""
        task_lower = task_description.lower()

        # Score each category based on keyword matches
        category_scores = {category: 0 for category in TaskCategory}

        for category, keywords in cls.TASK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    category_scores[category] += 1

        # Get category with highest score
        max_score = max(category_scores.values())

        if max_score > 0:
            for category, score in category_scores.items():
                if score == max_score:
                    return category

        # Fallback based on agent type
        if agent_type == AgentType.PLANNER:
            return TaskCategory.PLANNING
        elif agent_type == AgentType.EXECUTOR:
            return TaskCategory.CODING
        elif agent_type == AgentType.ANALYZER:
            return TaskCategory.ANALYSIS
        else:
            return TaskCategory.GENERAL

    @classmethod
    def get_model_for_category(cls, category: TaskCategory, preference: int = 0) -> str:
        """
        Get a specific model for a category

        Args:
            category: Task category
            preference: Index of model preference (0 = best, 1 = second best, etc.)

        Returns:
            Model name
        """
        models = cls.TASK_MODELS[category]
        if preference < len(models):
            return models[preference]
        return models[0]


class AgentSpawner:
    """Manages agent lifecycle and spawning"""

    def __init__(self):
        self.active_agents: Dict[str, AgentConfig] = {}
        self.agent_counter = 0
        self.model_selector = ModelSelector()

    def spawn_agent(
            self,
            agent_type: AgentType,
            task_description: str,
            custom_model: Optional[str] = None,
            **kwargs
    ) -> AgentConfig:
        """
        Spawn a new agent with appropriate model selection based on task type

        Args:
            agent_type: Type of agent to spawn
            task_description: Description of the task
            custom_model: Optional custom model override
            **kwargs: Additional configuration parameters

        Returns:
            AgentConfig for the spawned agent
        """
        self.agent_counter += 1
        agent_id = f"{agent_type.value}_{self.agent_counter}_{int(time.time())}"

        # Select model if not custom
        if custom_model:
            model_name = custom_model
            category = TaskCategory.GENERAL
        else:
            model_name, category = self.model_selector.select_model(
                task_description, agent_type
            )

        # Create agent configuration
        config = AgentConfig(
            agent_id=agent_id,
            agent_type=agent_type,
            model_name=model_name,
            task_category=category,
            max_iterations=kwargs.get('max_iterations', 10),
            timeout=kwargs.get('timeout', 300),
            temperature=kwargs.get('temperature', 0.7)
        )

        self.active_agents[agent_id] = config
        return config

    def terminate_agent(self, agent_id: str) -> bool:
        """
        Terminate an agent

        Args:
            agent_id: ID of agent to terminate

        Returns:
            True if terminated, False if not found
        """
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            return True
        return False

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get configuration for an agent"""
        return self.active_agents.get(agent_id)

    def list_active_agents(self) -> List[AgentConfig]:
        """List all active agents"""
        return list(self.active_agents.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get spawner statistics"""
        return {
            'total_spawned': self.agent_counter,
            'currently_active': len(self.active_agents),
            'agents_by_type': self._count_by_type(),
            'agents_by_category': self._count_by_category(),
            'agents_by_model': self._count_by_model()
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count agents by type"""
        counts = {}
        for config in self.active_agents.values():
            agent_type = config.agent_type.value
            counts[agent_type] = counts.get(agent_type, 0) + 1
        return counts

    def _count_by_category(self) -> Dict[str, int]:
        """Count agents by task category"""
        counts = {}
        for config in self.active_agents.values():
            category = config.task_category.value
            counts[category] = counts.get(category, 0) + 1
        return counts

    def _count_by_model(self) -> Dict[str, int]:
        """Count agents by model"""
        counts = {}
        for config in self.active_agents.values():
            model = config.model_name
            counts[model] = counts.get(model, 0) + 1
        return counts