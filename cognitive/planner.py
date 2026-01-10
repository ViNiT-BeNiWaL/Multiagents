from dataclasses import dataclass
from typing import List, Dict, Any
import ollama, json, time

@dataclass
class SubTask:
    task_id: str
    description: str
    task_type: str
    dependencies: List[str]
    required_output: str

@dataclass
class ExecutionPlan:
    plan_id: str
    subtasks: List[SubTask]
    execution_order: List[str]

class PlannerAgent:
    def __init__(self, model_name: str, temperature: float):
        self.model = model_name
        self.temperature = temperature

    def create_plan(self, task: str, context: Dict[str, Any] | None):
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": f"Break this into subtasks:\n{task}"}],
            options={"temperature": self.temperature}
        )

        return ExecutionPlan(
            plan_id=f"plan_{int(time.time())}",
            subtasks=[
                SubTask(
                    task_id="subtask_1",
                    description=task,
                    task_type="general",
                    dependencies=[],
                    required_output="Task completed"
                )
            ],
            execution_order=["subtask_1"]
        )
