
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
from result_processor import ResultProcessor


class MultiAgentOrchestrator:
    """Main orchestrator for the multi-agent system"""

    def __init__(self, workspace: str = "./workspace"):
        self.console = Console()

        # Initialize components
        self.spawner = AgentSpawner()
        self.manager = AgentManager()
        self.security = SecurityValidator()
        self.file_manager = FileManager(workspace)
        self.result_processor = ResultProcessor(self.file_manager)

        # Initialize cognitive agents
        self.planner = None
        self.decision_engine = None
        self.finalizer = None

        self.console.print(Panel.fit(
            "[bold green]Multi-Agent System Initialized[/bold green]\n"
            "[dim]Ready to process complex tasks with automatic file generation[/dim]",
            title="System Status"
        ))

    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a complete task using multi-agent coordination

        Args:
            task_description: Description of the task to execute
            context: Optional context information

        Returns:
            Dictionary with execution results and created files
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

            # Step 3: Generate actual files from results
            self.console.print("\n[bold cyan]Generating files from results...[/bold cyan]")
            created_files = self.result_processor.create_complete_implementation(
                task_description, 
                results
            )

            # Display created files
            if created_files:
                self._display_created_files(created_files)
            else:
                self.console.print("[yellow]⚠ No files were generated. Extracting code manually...[/yellow]")
                # Fallback: manual extraction
                created_files = self._manual_code_extraction(results)
                if created_files:
                    self._display_created_files(created_files)

            # Step 4: Validate and finalize
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task(description="Finalizing results...", total=None)
                final_report = self._finalize_results(task_description, results)

            self.console.print(f"\n[green]✓[/green] Task completed successfully\n")
            self._display_report(final_report)

            return {
                'success': True,
                'task': task_description,
                'plan': plan,
                'results': results,
                'created_files': created_files,
                'report': final_report
            }

        except Exception as e:
            self.console.print(f"[red]✗ Error:[/red] {str(e)}\n")
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
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

            # Build enhanced prompt for better code generation
            enhanced_prompt = self._build_enhanced_prompt(subtask)

            # Execute using ollama
            response = ollama.chat(
                model=agent_config.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': self._get_system_prompt_for_task(agent_config.task_category.value)
                    },
                    {
                        'role': 'user',
                        'content': enhanced_prompt
                    }
                ],
                options={'temperature': agent_config.temperature}
            )

            return response['message']['content']

        except Exception as e:
            return f"Error executing subtask: {str(e)}"

    def _build_enhanced_prompt(self, subtask: Any) -> str:
        """Build enhanced prompt for better code generation"""
        prompt = f"{subtask.description}\n\n"
        prompt += f"Required output: {subtask.required_output}\n\n"
        prompt += "IMPORTANT: Provide complete, working code with:\n"
        prompt += "1. Proper imports at the top\n"
        prompt += "2. Clear docstrings and comments\n"
        prompt += "3. Error handling where appropriate\n"
        prompt += "4. Type hints for function parameters\n"
        prompt += "5. Example usage if applicable\n\n"
        prompt += "Format your code in markdown code blocks with language specification (```python)"
        
        return prompt

    def _get_system_prompt_for_task(self, category: str) -> str:
        """Get specialized system prompt based on task category"""
        base = "You are an expert software engineer. Provide production-quality code."
        
        prompts = {
            'coding': f"{base} Focus on clean, well-structured code with proper error handling.",
            'analysis': f"{base} Provide detailed analysis with statistical methods and clear explanations.",
            'math': f"{base} Show all calculations clearly with proper mathematical notation.",
            'testing': f"{base} Write comprehensive tests covering edge cases and error conditions.",
            'planning': f"{base} Create clear, actionable plans with proper dependency management.",
            'creative': f"{base} Be creative while maintaining code quality and functionality.",
        }
        
        return prompts.get(category, base)

    def _manual_code_extraction(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback method to manually extract and save code"""
        import re
        created_files = []

        for subtask_id, result in results.items():
            if not isinstance(result, str):
                continue

            # Extract code blocks
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', result, re.DOTALL)
            
            for i, (lang, code) in enumerate(code_blocks):
                if not code.strip():
                    continue
                    
                # Determine file extension
                ext = lang if lang else 'py'
                if ext not in ['py', 'js', 'java', 'cpp', 'go', 'rs']:
                    ext = 'py'
                
                # Generate filename
                clean_id = subtask_id.replace('subtask_', '')
                if 'test' in result.lower():
                    filename = f"test_{clean_id}.{ext}"
                elif 'example' in result.lower():
                    filename = f"example_{clean_id}.{ext}"
                elif 'cli' in result.lower() or 'interface' in result.lower():
                    filename = f"cli_interface.{ext}"
                else:
                    filename = f"module_{clean_id}.{ext}"
                
                # Write file
                file_result = self.file_manager.write_file(filename, code.strip())
                
                if file_result['success']:
                    created_files.append({
                        'filename': filename,
                        'type': 'code',
                        'language': ext,
                        'size': file_result['size']
                    })

        return created_files

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
            "Completeness - All required components implemented",
            "Quality - Code follows best practices",
            "Correctness - Logic is sound and accurate",
            "Clarity - Code is well-documented and readable",
            "Functionality - Solution works as intended"
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
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Description", style="white", width=50)
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Dependencies", style="dim", width=15)

        for subtask in plan.subtasks:
            deps = ", ".join(subtask.dependencies) if subtask.dependencies else "None"
            table.add_row(
                subtask.task_id,
                subtask.description[:47] + "..." if len(subtask.description) > 50 else subtask.description,
                subtask.task_type,
                deps
            )

        self.console.print(table)
        self.console.print()

    def _display_created_files(self, files: List[Dict[str, Any]]):
        """Display created files in a formatted table"""
        if not files:
            return

        table = Table(title="Created Files", show_header=True, header_style="bold magenta")
        table.add_column("Filename", style="cyan", width=30)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Size", style="green", width=10)

        for file_info in files:
            size_kb = file_info.get('size', 0) / 1024
            size_str = f"{size_kb:.2f} KB" if size_kb > 0 else "N/A"
            
            table.add_row(
                file_info['filename'],
                file_info.get('type', 'unknown'),
                size_str
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print(f"\n[green]✓ {len(files)} files created in workspace/[/green]\n")

    def _display_report(self, report: Any):
        """Display final report"""
        # Quality indicator
        quality = report.validation.quality_score
        if quality >= 0.8:
            quality_color = "green"
            quality_icon = "✓"
        elif quality >= 0.6:
            quality_color = "yellow"
            quality_icon = "⚠"
        else:
            quality_color = "red"
            quality_icon = "✗"

        self.console.print(Panel.fit(
            f"[bold]Summary:[/bold]\n{report.summary}\n\n"
            f"[bold]Quality Score:[/bold] [{quality_color}]{quality:.2%} {quality_icon}[/{quality_color}]\n"
            f"[bold]Status:[/bold] {'✓ Valid' if report.validation.is_valid else '✗ Issues Found'}\n"
            f"[bold]Subtasks Completed:[/bold] {report.metadata.get('subtask_count', 0)}",
            title="Final Report",
            border_style="green" if report.validation.is_valid else "yellow"
        ))

        if report.validation.issues:
            self.console.print("\n[bold yellow]Issues Found:[/bold yellow]")
            for i, issue in enumerate(report.validation.issues, 1):
                self.console.print(f"  {i}. {issue}")

        if report.recommendations:
            self.console.print("\n[bold cyan]Recommendations:[/bold cyan]")
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

        table = Table(title="System Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Metric", style="yellow", width=25)
        table.add_column("Value", style="green", width=15)

        # Spawner stats
        table.add_row("Spawner", "Total Spawned", str(stats['spawner']['total_spawned']))
        table.add_row("", "Currently Active", str(stats['spawner']['currently_active']))

        # Manager stats
        table.add_row("Manager", "Total Tasks", str(stats['manager']['total_tasks']))
        table.add_row("", "Messages", str(stats['manager']['total_messages']))

        # File manager stats
        table.add_row("File Manager", "Operations", str(stats['file_manager']['total_operations']))
        success_rate = (stats['file_manager']['successful_operations'] / 
                       max(stats['file_manager']['total_operations'], 1) * 100)
        table.add_row("", "Success Rate", f"{success_rate:.1f}%")

        self.console.print("\n")
        self.console.print(table)
        self.console.print()


def main():
    """Main entry point for the multi-agent system"""
    console = Console()

    console.print(Panel.fit(
        "[bold cyan]Multi-Agent System[/bold cyan]\n"
        "Intelligent task execution with automatic model selection\n"
        "[dim]Now with automatic file generation![/dim]",
        title="Welcome"
    ))

    orchestrator = MultiAgentOrchestrator()

    # Example tasks
    console.print("\n[bold]Suggested Complex Tasks:[/bold]")
    console.print("1. [cyan]Banking[/cyan]: Create a banking transaction analysis system with fraud detection")
    console.print("2. [cyan]Web Scraper[/cyan]: Build a web scraping and data processing pipeline")
    console.print("3. [cyan]Password Manager[/cyan]: Create a secure CLI password manager with encryption")
    console.print("4. [cyan]Data Quality[/cyan]: Build a data quality assessment tool for CSV files")
    console.print("5. [cyan]Portfolio[/cyan]: Create a stock portfolio tracker with analysis\n")

    # Interactive mode
    while True:
        try:
            console.print("[dim]Commands: 'stats', 'quit', or enter a task[/dim]")
            task = console.input("[bold green]Enter task:[/bold green] ")

            if task.lower() in ['quit', 'exit', 'q']:
                break

            if task.lower() == 'stats':
                orchestrator.display_stats()
                continue

            if not task.strip():
                continue

            # Execute task
            result = orchestrator.execute_task(task)

            # Optionally save full results
            if result.get('success'):
                save = console.input("\n[dim]Save full results to JSON? (y/n):[/dim] ")
                if save.lower() == 'y':
                    filename = f"full_result_{result['report'].report_id}.json"
                    save_data = {
                        'task': task,
                        'summary': result['report'].summary,
                        'created_files': result.get('created_files', []),
                        'quality_score': result['report'].validation.quality_score,
                        'is_valid': result['report'].validation.is_valid
                    }
                    orchestrator.file_manager.write_json(filename, save_data)
                    console.print(f"[green]✓[/green] Saved to {filename}\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}\n")

    console.print("\n[cyan]Goodbye![/cyan]")


if __name__ == "__main__":
    main()