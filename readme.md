# Multi-Agent System

This project is a sophisticated multi-agent system designed to execute complex tasks by leveraging the power of large language models (LLMs). It intelligently breaks down tasks, assigns them to specialized AI agents, and generates the necessary files and reports. The system is built to be extensible, allowing for the easy addition of new agents and capabilities.

## Features

- **Intelligent Task Decomposition:** The system can take a high-level task and break it down into smaller, manageable subtasks.
- **Automatic Model Selection:** Based on the nature of a subtask, the system automatically selects the most appropriate AI model for the job (e.g., a coding model for a programming task, a creative model for writing tasks).
- **Web Search Capability:** The system can access the web to answer questions and incorporate real-time information into its responses.
- **File Generation:** The system can generate files, such as code, reports, and other documents, based on the results of the tasks.
- **Interactive Demo Mode:** An interactive command-line interface allows you to give tasks to the system and see it in action.
- **Extensible Architecture:** The project is designed to be easily extended with new agents, models, and capabilities.

## System Architecture

The system is composed of several key components that work together to execute tasks:

- **`MultiAgentOrchestrator`**: The central coordinator of the entire system. It manages the overall task execution flow.
- **`AgentSpawner`**: Responsible for dynamically selecting and spawning the best AI model for a given subtask.
- **`PlannerAgent`**: Creates a step-by-step execution plan for a given task.
- **`FileManager`**: Manages all file-related operations, such as reading, writing, and creating files.
- **`ResultProcessor`**: Takes the outputs from the AI models and creates the final implementation files.
- **`FinalizerAgent`**: Assesses the quality of the results and provides a concluding report.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.ai/) installed and running

### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/your-username/multi-agent-system.git
    cd multi-agent-system
    ```

2.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

3.  Make sure the Ollama server is running. You can start it by running the `ollama serve` command in your terminal.

### Usage

To start the interactive demo mode, run the following command:

```bash
python orchestrator.py
```

You can then enter tasks at the prompt. For example:

```
Enter your task: Write a Python function that validates email addresses using regex
```

The system will then execute the task and generate the necessary files.

## Agent Roles

The system uses different types of agents, each with a specialized role:

- **`PlannerAgent`**: Responsible for breaking down a complex task into a series of smaller, more manageable subtasks.
- **`ExecutorAgent`**: Executes a specific subtask, such as writing code or analyzing data.
- **`AnalyzerAgent`**: Analyzes the results of a task and provides insights.
- **`FinalizerAgent`**: Consolidates the results of all the subtasks and generates a final report.

By using specialized agents, the system can handle a wide range of tasks with a high degree of accuracy and efficiency.
