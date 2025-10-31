"""
Main orchestrator for coordinating multi-agent system
"""
import sys
import ollama
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from admin.spawner import AgentSpawner, AgentType
from admin.manager import AgentManager, TaskStatus
from admin.security import SecurityValidator, SecurityLevel
from cognitive.planner import PlannerAgent
from cognitive.decision_engine import DecisionEngine
from action.file_manager import FileManager
from action.finalizer import FinalizerAgent


class MultiAgentOrchestrator:
    """Main orchestrator for the multi-agent system"""

    def __init__(self, workspace: str = "./workspace"):
        self.console = Console()

        # Initialize components
        self.spawner = AgentSpawner()
        self.manager = AgentManager()
        self.security = SecurityValidator()
        self.file_manager = FileManager(workspace)

        # Initialize cognitive agents
        self.planner = None
        self.decision_engine = None
        self.finalizer = None

        self.console.print(Panel.fit(
            "[bold green]Multi-Agent System Initialized[/bold green]",
            title="System Status"
        ))

    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a complete task using multi-agent coordination

        Args:
            task_description: Description of the task to execute
            context: Optional context information

        Returns:
            Dictionary with execution results
        """
        self.console.print(f"\n[bold cyan]Starting Task:[/bold cyan] {task_description}\n")

        try:
            # Step 1: Create execution plan
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task(description="Planning task execution...", total=None)
                plan = self._create_plan(task_description, context)

            self.console.print(f"[green]✓[/green] Created plan with {len(plan.subtasks)} subtasks\n")

            # Step 2: Execute subtasks
            results = self._execute_plan(plan)

            # Step 3: Validate and finalize
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task(description="Finalizing results...", total=None)
                final_report = self._finalize_results(task_description, results)

            self.console.print(f"[green]✓[/green] Task completed successfully\n")
            self._display_report(final_report)

            return {
                'success': True,
                'task': task_description,
                'plan': plan,
                'results': results,
                'report': final_report
            }

        except Exception as e:
            self.console.print(f"[red]✗ Error:[/red] {str(e)}\n")
            return {
                'success': False,
                'error': str(e),
                'task': task_description
            }

    def _create_plan(self, task_description: str, context: Optional[Dict[str, Any]]) -> Any:
        """Create execution plan using planner agent"""
        # Spawn planner if not exists
        if not self.planner:
            planner_config = self.spawner.spawn_agent(
                agent_type=AgentType.PLANNER,
                task_description="planning and task decomposition",
                temperature=0.7
            )
            self.planner = PlannerAgent(
                model_name=planner_config.model_name,
                temperature=planner_config.temperature
            )
            self.console.print(f"[dim]Using {planner_config.model_name} for planning[/dim]")

        # Create plan
        plan = self.planner.create_plan(task_description, context)

        # Display plan
        self._display_plan(plan)

        return plan

    def _execute_plan(self, plan: Any) -> Dict[str, Any]:
        """Execute all subtasks in the plan"""
        results = {}

        for subtask in plan.subtasks:
            self.console.print(f"\n[cyan]Executing:[/cyan] {subtask.description}")

            # Create task in manager
            task = self.manager.create_task(
                description=subtask.description,
                dependencies=subtask.dependencies,
                task_type=subtask.task_type
            )

            # Spawn appropriate agent for subtask
            agent_config = self.spawner.spawn_agent(
                agent_type=AgentType.EXECUTOR,
                task_description=subtask.description
            )

            self.console.print(f"[dim]→ Using {agent_config.model_name} ({agent_config.task_category.value})[/dim]")

            # Assign and execute task
            self.manager.assign_task(task.task_id, agent_config.agent_id)

            # Execute with appropriate model
            result = self._execute_subtask(subtask, agent_config)

            # Store result
            self.manager.complete_task(task.task_id, result)
            results[subtask.task_id] = result

            # Terminate agent after task
            self.spawner.terminate_agent(agent_config.agent_id)

            self.console.print(f"[green]✓[/green] Completed: {subtask.task_id}")

        return results

    def _execute_subtask(self, subtask: Any, agent_config: Any) -> str:
        """Execute a single subtask using appropriate model"""
        try:
            # Validate with security
            is_valid, reason = self.security.validate_command(
                subtask.description,
                SecurityLevel.MEDIUM
            )

            if not is_valid:
                return f"Task blocked by security: {reason}"

            # Execute using ollama
            response = ollama.chat(
                model=agent_config.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': f'You are an expert at {agent_config.task_category.value} tasks. Provide detailed, high-quality output.'
                    },
                    {
                        'role': 'user',
                        'content': f"{subtask.description}\n\nRequired output: {subtask.required_output}"
                    }
                ],
                options={'temperature': agent_config.temperature}
            )

            return response['message']['content']

        except Exception as e:
            return f"Error executing subtask: {str(e)}"

    def _finalize_results(self, task_description: str, results: Dict[str, Any]) -> Any:
        """Finalize and validate results"""
        # Spawn finalizer if not exists
        if not self.finalizer:
            finalizer_config = self.spawner.spawn_agent(
                agent_type=AgentType.FINALIZER,
                task_description="result validation and consolidation",
                temperature=0.5
            )
            self.finalizer = FinalizerAgent(
                model_name=finalizer_config.model_name,
                temperature=finalizer_config.temperature
            )

        # Consolidate results
        validation_criteria = [
            "Completeness",
            "Quality",
            "Correctness",
            "Clarity"
        ]

        report = self.finalizer.consolidate_results(
            task_description,
            results,
            validation_criteria
        )

        return report

    def _display_plan(self, plan: Any):
        """Display execution plan in a table"""
        table = Table(title="Execution Plan")
        table.add_column("ID", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Dependencies", style="dim")

        for subtask in plan.subtasks:
            deps = ", ".join(subtask.dependencies) if subtask.dependencies else "None"
            table.add_row(
                subtask.task_id,
                subtask.description[:50] + "..." if len(subtask.description) > 50 else subtask.description,
                subtask.task_type,
                deps
            )

        self.console.print(table)
        self.console.print()

    def _display_report(self, report: Any):
        """Display final report"""
        self.console.print(Panel.fit(
            f"[bold]Summary:[/bold]\n{report.summary}\n\n"
            f"[bold]Quality Score:[/bold] {report.validation.quality_score:.2f}\n"
            f"[bold]Status:[/bold] {'✓ Valid' if report.validation.is_valid else '✗ Issues Found'}",
            title="Final Report",
            border_style="green" if report.validation.is_valid else "yellow"
        ))

        if report.recommendations:
            self.console.print("\n[bold]Recommendations:[/bold]")
            for i, rec in enumerate(report.recommendations, 1):
                self.console.print(f"  {i}. {rec}")

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            'spawner': self.spawner.get_stats(),
            'manager': self.manager.get_stats(),
            'security': {
                'total_events': len(self.security.get_security_report())
            },
            'file_manager': self.file_manager.get_stats()
        }

    def display_stats(self):
        """Display system statistics"""
        stats = self.get_system_stats()

        table = Table(title="System Statistics")
        table.add_column("Component", style="cyan")
        table.add_column("Metric", style="yellow")
        table.add_column("Value", style="green")

        # Spawner stats
        table.add_row("Spawner", "Total Spawned", str(stats['spawner']['total_spawned']))
        table.add_row("", "Currently Active", str(stats['spawner']['currently_active']))

        # Manager stats
        table.add_row("Manager", "Total Tasks", str(stats['manager']['total_tasks']))
        table.add_row("", "Messages", str(stats['manager']['total_messages']))

        # File manager stats
        table.add_row("File Manager", "Operations", str(stats['file_manager']['total_operations']))
        table.add_row("", "Success Rate",
                      f"{stats['file_manager']['successful_operations']}/{stats['file_manager']['total_operations']}")

        self.console.print(table)


def main():
    """Main entry point for the multi-agent system"""
    console = Console()

    console.print(Panel.fit(
        "[bold cyan]Multi-Agent System[/bold cyan]\n"
        "Intelligent task execution with automatic model selection",
        title="Welcome"
    ))

    orchestrator = MultiAgentOrchestrator()

    # Example usage
    console.print("\n[bold]Example Tasks:[/bold]")
    console.print("1. Write a Python function to process CSV files")
    console.print("2. Analyze data and create visualizations")
    console.print("3. Design a REST API architecture")
    console.print("4. Debug and optimize existing code")
    console.print("5. Write creative content for a blog\n")

    # Interactive mode
    while True:
        try:
            task = console.input("[bold green]Enter task (or 'quit' to exit):[/bold green] ")

            if task.lower() in ['quit', 'exit', 'q']:
                break

            if task.lower() == 'stats':
                orchestrator.display_stats()
                continue

            if not task.strip():
                continue

            # Execute task
            result = orchestrator.execute_task(task)

            # Optionally save results
            if result.get('success'):
                save = console.input("\n[dim]Save results to file? (y/n):[/dim] ")
                if save.lower() == 'y':
                    filename = f"result_{int(result['report'].report_id.split('_')[1])}.json"
                    orchestrator.file_manager.write_json(filename, result)
                    console.print(f"[green]✓[/green] Saved to {filename}\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}\n")

    console.print("\n[cyan]Goodbye![/cyan]")


if __name__ == "__main__":
    main()