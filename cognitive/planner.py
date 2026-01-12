from dataclasses import dataclass
from typing import List, Dict, Any
from core.llm_router import LLMRouter
import json
import time


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
    def __init__(self, model_name: str, temperature: float, provider: str = None):
        self.model = model_name
        self.temperature = temperature
        self.router = LLMRouter(provider=provider, model=model_name)

    def create_plan(self, task: str, context: Dict[str, Any] | None):
        system_prompt = (
            "You are a sophisticated planning agent. Break down the user's request into a structured execution plan.\n"
            "Return ONLY a valid JSON object with the following structure:\n"
            "{\n"
            "  \"subtasks\": [\n"
            "    {\n"
            "      \"id\": \"subtask_1\",\n"
            "      \"description\": \"Detailed description of what to do\",\n"
            "      \"type\": \"general\" | \"web_scrape\",\n"
            "      \"dependencies\": [\"previous_task_id\"]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Use 'web_scrape' type ONLY if the user explicitly asks to fetch data from a URL or if external info is obviously needed.\n"
            "Otherwise use 'general'."
        )

        response = self.router.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ],
            temperature=self.temperature,
            format="json"
        )

        try:
            plan_data = json.loads(response.content)
            subtasks = []
            order = []
            
            for item in plan_data.get("subtasks", []):
                subtasks.append(SubTask(
                    task_id=item["id"],
                    description=item["description"],
                    task_type=item.get("type", "general"),
                    dependencies=item.get("dependencies", []),
                    required_output="Result"
                ))
                order.append(item["id"])

            return ExecutionPlan(
                plan_id=f"plan_{int(time.time())}",
                subtasks=subtasks,
                execution_order=order
            )
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
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
