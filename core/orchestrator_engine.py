from typing import Dict, Any
from cognitive.planner import PlannerAgent
from admin.manager import AgentManager
from admin.spawner import AgentSpawner, AgentType
from admin.security import SecurityValidator, SecurityLevel
from processing.result_processor import ResultProcessor
from action.finalizer import FinalizerAgent
from action.file_manager import FileManager


class OrchestratorEngine:
    """
    Core orchestration engine (NO UI, NO API)
    """

    def __init__(self, workspace: str = "./workspace"):
        self.spawner = AgentSpawner()
        self.manager = AgentManager()
        self.security = SecurityValidator()
        self.file_manager = FileManager(workspace)
        self.result_processor = ResultProcessor(self.file_manager)

        self.planner = None
        self.finalizer = None

    def execute(self, task: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        plan = self._plan(task, context)
        results = self._execute_plan(plan)
        files = self.result_processor.create_complete_implementation(task, results)
        report = self._finalize(task, results)

        return {
            "task": task,
            "plan": plan,
            "results": results,
            "files": files,
            "report": report
        }

    def _plan(self, task: str, context: Dict[str, Any] | None):
        if not self.planner:
            cfg = self.spawner.spawn_agent(AgentType.PLANNER, task)
            self.planner = PlannerAgent(cfg.model_name, cfg.temperature)

        return self.planner.create_plan(task, context)

    def _execute_plan(self, plan):
        results = {}

        for subtask in plan.subtasks:
            ok, reason = self.security.validate_command(
                subtask.description, SecurityLevel.MEDIUM
            )
            if not ok:
                results[subtask.task_id] = f"Blocked: {reason}"
                continue

            cfg = self.spawner.spawn_agent(
                AgentType.EXECUTOR, subtask.description
            )

            # Simple execution
            import ollama
            response = ollama.chat(
                model=cfg.model_name,
                messages=[{"role": "user", "content": subtask.description}]
            )

            results[subtask.task_id] = response["message"]["content"]

        return results

    def _finalize(self, task: str, results: Dict[str, Any]):
        if not self.finalizer:
            cfg = self.spawner.spawn_agent(AgentType.FINALIZER, task)
            self.finalizer = FinalizerAgent(cfg.model_name, cfg.temperature)

        return self.finalizer.consolidate_results(
            task,
            results,
            validation_criteria=[
                "Correctness",
                "Completeness",
                "Clarity",
                "Production readiness"
            ]
        )
