"""
Manager for coordinating agents and handling communication
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Message:
    """Message passed between agents"""
    sender_id: str
    receiver_id: str
    content: Any
    message_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Task to be executed by agents"""
    task_id: str
    description: str
    status: TaskStatus
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentManager:
    """Manages agent coordination and communication"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.messages: List[Message] = []
        self.task_counter = 0
        self.agent_outputs: Dict[str, List[Any]] = {}

    def create_task(
            self,
            description: str,
            dependencies: Optional[List[str]] = None,
            **metadata
    ) -> Task:
        """
        Create a new task

        Args:
            description: Task description
            dependencies: List of task IDs this task depends on
            **metadata: Additional metadata

        Returns:
            Created task
        """
        self.task_counter += 1
        task_id = f"task_{self.task_counter}_{int(datetime.now().timestamp())}"

        task = Task(
            task_id=task_id,
            description=description,
            status=TaskStatus.PENDING,
            dependencies=dependencies or [],
            metadata=metadata
        )

        self.tasks[task_id] = task
        return task

    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """
        Assign a task to an agent

        Args:
            task_id: Task ID
            agent_id: Agent ID

        Returns:
            True if assigned successfully
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        # Check if dependencies are met
        if not self._dependencies_met(task):
            task.status = TaskStatus.BLOCKED
            return False

        task.assigned_agent = agent_id
        task.status = TaskStatus.IN_PROGRESS
        return True

    def complete_task(self, task_id: str, result: Any) -> bool:
        """
        Mark a task as completed

        Args:
            task_id: Task ID
            result: Task result

        Returns:
            True if completed successfully
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now()

        # Store agent output
        if task.assigned_agent:
            if task.assigned_agent not in self.agent_outputs:
                self.agent_outputs[task.assigned_agent] = []
            self.agent_outputs[task.assigned_agent].append(result)

        return True

    def fail_task(self, task_id: str, error: str) -> bool:
        """
        Mark a task as failed

        Args:
            task_id: Task ID
            error: Error message

        Returns:
            True if marked as failed
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.result = {"error": error}
        task.completed_at = datetime.now()
        return True

    def send_message(
            self,
            sender_id: str,
            receiver_id: str,
            content: Any,
            message_type: str = "general",
            **metadata
    ) -> Message:
        """
        Send a message between agents

        Args:
            sender_id: Sender agent ID
            receiver_id: Receiver agent ID
            content: Message content
            message_type: Type of message
            **metadata: Additional metadata

        Returns:
            Created message
        """
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            metadata=metadata
        )

        self.messages.append(message)
        return message

    def get_messages_for_agent(self, agent_id: str) -> List[Message]:
        """Get all messages for an agent"""
        return [msg for msg in self.messages if msg.receiver_id == agent_id]

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks with met dependencies"""
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING and self._dependencies_met(task)
        ]

    def get_agent_tasks(self, agent_id: str) -> List[Task]:
        """Get all tasks assigned to an agent"""
        return [
            task for task in self.tasks.values()
            if task.assigned_agent == agent_id
        ]

    def get_task_chain(self, task_id: str) -> List[Task]:
        """Get the dependency chain for a task"""
        if task_id not in self.tasks:
            return []

        chain = []
        task = self.tasks[task_id]

        # Add dependencies recursively
        for dep_id in task.dependencies:
            chain.extend(self.get_task_chain(dep_id))

        chain.append(task)
        return chain

    def _dependencies_met(self, task: Task) -> bool:
        """Check if all task dependencies are met"""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        status_counts = {}
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            'total_tasks': len(self.tasks),
            'total_messages': len(self.messages),
            'tasks_by_status': status_counts,
            'active_agents': len(self.agent_outputs)
        }