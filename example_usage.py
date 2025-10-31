"""
Example usage of the multi-agent system
Demonstrates automatic model selection based on task type
"""

from orchestrator import MultiAgentOrchestrator
from rich.console import Console

console = Console()


def example_coding_task():
    """Example: Coding task automatically uses qwen2.5-coder"""
    console.print("\n[bold cyan]═══ Example 1: Coding Task ═══[/bold cyan]\n")

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.execute_task(
        "Write a Python function that validates email addresses using regex"
    )

    if result['success']:
        console.print("\n[green]Task completed! Model automatically selected: qwen2.5-coder:7b[/green]")


def example_analysis_task():
    """Example: Analysis task uses llama3.1:8b"""
    console.print("\n[bold cyan]═══ Example 2: Analysis Task ═══[/bold cyan]\n")

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.execute_task(
        "Analyze the pros and cons of microservices architecture vs monolithic architecture"
    )

    if result['success']:
        console.print("\n[green]Task completed! Model automatically selected: llama3.1:8b[/green]")


def example_math_task():
    """Example: Math task uses deepseek-math or qwen2.5"""
    console.print("\n[bold cyan]═══ Example 3: Math Task ═══[/bold cyan]\n")

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.execute_task(
        "Calculate the compound interest for a $10,000 investment at 5% annual rate over 10 years"
    )

    if result['success']:
        console.print("\n[green]Task completed! Model automatically selected for math[/green]")


def example_creative_task():
    """Example: Creative task uses mistral or llama3.1"""
    console.print("\n[bold cyan]═══ Example 4: Creative Writing Task ═══[/bold cyan]\n")

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.execute_task(
        "Write a short story about an AI that learns to appreciate art"
    )

    if result['success']:
        console.print("\n[green]Task completed! Model automatically selected: mistral:7b[/green]")


def example_complex_task():
    """Example: Complex multi-step task uses multiple specialized models"""
    console.print("\n[bold cyan]═══ Example 5: Complex Multi-Step Task ═══[/bold cyan]\n")

    orchestrator = MultiAgentOrchestrator()

    result = orchestrator.execute_task(
        """
        Create a complete data analysis pipeline:
        1. Design the data structure for storing customer information
        2. Write Python code to load and validate the data
        3. Perform statistical analysis on the dataset
        4. Generate a summary report with key findings
        """
    )

    if result['success']:
        console.print("\n[green]Task completed! Multiple models used:[/green]")
        console.print("  • Planning: qwen2.5:14b")
        console.print("  • Code writing: qwen2.5-coder:7b")
        console.print("  • Analysis: llama3.1:8b")
        console.print("  • Report generation: mistral:7b")


def demonstrate_model_selection():
    """Demonstrate how different keywords trigger different models"""
    console.print("\n[bold cyan]═══ Model Selection Demonstration ═══[/bold cyan]\n")

    from admin.spawner import ModelSelector, AgentType

    test_cases = [
        ("Write a Python function to sort data", "CODING → qwen2.5-coder:7b"),
        ("Analyze customer feedback data", "ANALYSIS → llama3.1:8b"),
        ("Calculate the average of these numbers", "MATH → deepseek-math:7b"),
        ("Compose a blog post about AI", "CREATIVE → mistral:7b"),
        ("Debug this code and fix errors", "CODING → deepseek-coder:6.7b"),
        ("Plan the architecture for a web app", "PLANNING → qwen2.5:14b"),
        ("Explain why this approach is better", "REASONING → phi3:medium"),
    ]

    console.print("[bold]Task Description → Detected Category → Selected Model[/bold]\n")

    for task, expected in test_cases:
        model, category = ModelSelector.select_model(task, AgentType.EXECUTOR)
        console.print(f"[cyan]'{task[:40]}...'[/cyan]")
        console.print(f"  → Category: [yellow]{category.value}[/yellow]")
        console.print(f"  → Model: [green]{model}[/green]")
        console.print(f"  → Expected: [dim]{expected}[/dim]\n")


def show_system_capabilities():
    """Show what the system can do"""
    console.print("\n[bold cyan]═══ System Capabilities ═══[/bold cyan]\n")

    capabilities = {
        "Code Generation": [
            "Write functions, classes, and complete programs",
            "Debug and fix code issues",
            "Refactor and optimize code",
            "Add error handling and tests"
        ],
        "Data Analysis": [
            "Analyze datasets and find patterns",
            "Perform statistical computations",
            "Compare and contrast data",
            "Generate insights and recommendations"
        ],
        "Content Creation": [
            "Write articles, blogs, and stories",
            "Create documentation and reports",
            "Generate creative content",
            "Draft emails and communications"
        ],
        "Problem Solving": [
            "Break down complex problems",
            "Plan solution architectures",
            "Make logical decisions",
            "Optimize processes"
        ],
        "File Operations": [
            "Read and write files securely",
            "Process JSON, CSV, and text files",
            "Organize and manage files",
            "Track file operations"
        ]
    }

    for category, items in capabilities.items():
        console.print(f"[bold yellow]{category}:[/bold yellow]")
        for item in items:
            console.print(f"  ✓ {item}")
        console.print()


def interactive_demo():
    """Interactive demo mode - asks user for tasks"""
    console.print("\n[bold cyan]═══ Interactive Demo Mode ═══[/bold cyan]\n")
    console.print("Enter your tasks and the system will automatically select the best models.\n")
    console.print("[dim]Commands: 'stats' to see statistics, 'quit' to exit[/dim]\n")

    orchestrator = MultiAgentOrchestrator()

    while True:
        try:
            task = console.input("[bold green]Enter your task:[/bold green] ")

            if task.lower() in ['quit', 'exit', 'q']:
                console.print("\n[cyan]Goodbye![/cyan]")
                break

            if task.lower() == 'stats':
                orchestrator.display_stats()
                continue

            if not task.strip():
                console.print("[yellow]Please enter a valid task[/yellow]\n")
                continue

            # Execute the task
            result = orchestrator.execute_task(task)

            if result['success']:
                # Show which models were used
                console.print("\n[bold]Models Used:[/bold]")
                stats = orchestrator.spawner.get_stats()
                for model, count in stats['agents_by_model'].items():
                    console.print(f"  • {model}: {count} agent(s)")

                # Ask if user wants to save results
                save = console.input("\n[dim]Save results to file? (y/n):[/dim] ")
                if save.lower() == 'y':
                    filename = f"result_{result['report'].report_id}.json"
                    save_result = orchestrator.file_manager.write_json(filename, {
                        'task': task,
                        'summary': result['report'].summary,
                        'results': result['results'],
                        'validation': {
                            'is_valid': result['report'].validation.is_valid,
                            'quality_score': result['report'].validation.quality_score
                        }
                    })
                    if save_result['success']:
                        console.print(f"[green]✓ Saved to {filename}[/green]")

                console.print()  # Add spacing

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            break
        except Exception as e: