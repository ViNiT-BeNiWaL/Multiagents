from typing import Dict, Any, List
from cognitive.planner import PlannerAgent
from admin.manager import AgentManager
from admin.spawner import AgentSpawner, AgentType
from admin.security import SecurityValidator, SecurityLevel
from processing.result_processor import ResultProcessor
from action.finalizer import FinalizerAgent
from action.file_manager import FileManager

from core.llm_router import LLMRouter
from cognitive.vision import VisionAgent


class OrchestratorEngine:
    """
    Core orchestration engine (NO UI, NO API)
    Supports multiple LLM providers via LLMRouter.
    """

    def __init__(self, workspace: str = "./workspace"):
        self.spawner = AgentSpawner()
        self.manager = AgentManager()
        self.security = SecurityValidator()
        self.base_workspace = workspace
        
        # Default global (legacy support)
        self.file_manager = FileManager(workspace)
        self.result_processor = ResultProcessor(self.file_manager)

        self.planner = None
        self.finalizer = None
        self.vision = None

    def execute(self, task: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        import uuid
        project_id = f"project_{uuid.uuid4().hex[:8]}"
        project_path = f"{self.base_workspace}/{project_id}"
        
        # Scoped instances for this task
        scoped_fm = FileManager(project_path)
        scoped_rp = ResultProcessor(scoped_fm)
        
        plan = self._plan(task, context)
        results = self._execute_plan(plan)
        
        # Use scoped processor
        files = scoped_rp.create_complete_implementation(task, results)
        
        # Auto-heal dependencies using scoped instances
        healing_report = self._verify_and_heal(scoped_fm, scoped_rp)
        
        report = self._finalize(task, results)

        return {
            "task": task,
            "project_id": project_id,
            "project_path": project_path,
            "plan": plan,
            "results": results,
            "files": files,
            "healing": healing_report,
            "report": report
        }

    def execute_with_images(self, task: str, images: List[str], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Execute a task that involves visual input (screenshots/mockups).
        """
        if not self.vision:
             cfg = self.spawner.spawn_agent(AgentType.VISION, "Vision Analysis")
             self.vision = VisionAgent(cfg.model_name, cfg.provider)
        
        # 1. Analyze the images to get technical requirements
        print(f"Analyzing {len(images)} images...")
        analysis = self.vision.analyze_ui(images)
        
        # 2. Enrich the task with visual analysis
        enriched_task = (
            f"Original Task: {task}\n\n"
            f"Visual Analysis of UI/UX Requirements:\n{analysis}\n\n"
            "Based on the visual analysis above, implement the solution."
        )
        
        # 3. Proceed with standard execution flow
        return self.execute(enriched_task, context)

    def _verify_and_heal(self, file_manager: FileManager, result_processor: ResultProcessor, max_retries: int = 3):
        from action.environment_manager import EnvironmentManager
        env_manager = EnvironmentManager(file_manager.base)
        
        history = []

        for attempt in range(max_retries):
            failures = env_manager.install_dependencies()
            if not failures:
                history.append(f"Attempt {attempt+1}: Success")
                return history

            # Fix failures
            for fail in failures:
                error_msg = fail["error"]
                file_path = fail["file"]
                
                print(f"Fixing {file_path} (Attempt {attempt+1})...")
                
                cfg = self.spawner.spawn_agent(AgentType.EXECUTOR, "Fix Dependencies")
                router = LLMRouter(provider=cfg.provider, model=cfg.model_name)
                
                fix_prompt = (
                    f"Dependency installation failed for {file_path}.\n"
                    f"Error log:\n{error_msg}\n\n"
                    f"Please provide the corrected content for {file_path}. "
                    "Use the standard file protocol:\n"
                    f"### FILE: {file_path}\n..."
                )
                
                response = router.chat(
                    messages=[{"role": "user", "content": fix_prompt}]
                )
                
                # Apply fix using scoped processor
                result_processor.create_complete_implementation(
                    "Fix", 
                    {"fix": response.content}
                )
                
            history.append(f"Attempt {attempt+1}: Failed with {len(failures)} errors. Retrying...")

        return history

    def _plan(self, task: str, context: Dict[str, Any] | None):
        if not self.planner:
            cfg = self.spawner.spawn_agent(AgentType.PLANNER, task)
            self.planner = PlannerAgent(cfg.model_name, cfg.temperature, cfg.provider)

        return self.planner.create_plan(task, context)

    def _execute_plan(self, plan):
        from action.web_scraper import WebScraper
        
        results = {}
        scraper = WebScraper()

        for subtask in plan.subtasks:
            # Handle Web Scraping Task
            if subtask.task_type == "web_scrape":
                print(f"Executing Scraping Task: {subtask.description}")
                import re
                urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', subtask.description)
                if urls:
                    scraped_content = scraper.scrape(urls[0])
                    results[subtask.task_id] = f"Scraped content from {urls[0]}:\n{scraped_content[:2000]}..."
                else:
                    results[subtask.task_id] = "Error: No URL found in task description."
                continue

            # Handle General Task
            ok, reason = self.security.validate_command(
                subtask.description, SecurityLevel.MEDIUM
            )
            if not ok:
                results[subtask.task_id] = f"Blocked: {reason}"
                continue

            cfg = self.spawner.spawn_agent(
                AgentType.EXECUTOR, subtask.description
            )
            
            # Use LLMRouter instead of direct ollama calls
            router = LLMRouter(provider=cfg.provider, model=cfg.model_name)
            
            system_prompt = (
                "You are an expert software engineer. "
                "When generating code which should be saved to a file, you MUST precede every code block "
                "with its filepath using the format:\n"
                "### FILE: path/to/file.ext\n"
                "```language\n"
                "code...\n"
                "```\n"
                "For complex projects (like MERN), ensure you organize files into folders "
                "(e.g., server/index.js, client/src/App.js)."
            )

            response = router.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": subtask.description}
                ]
            )

            results[subtask.task_id] = response.content

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
