# Multi-Agent Orchestration System

This project is a sophisticated **FastAPI-based** multi-agent system designed to execute complex tasks by leveraging the power of local Large Language Models (LLMs) via Ollama. It intelligently breaks down tasks, assigns them to specialized AI agents, and generates the necessary files and reports.

## Key Features

- **Full Stack Project Generation:** Capable of generating complex directory structures (e.g., MERN stack with `client/` and `server/`) using a robust file protocol.
- **Self-Healing Dependency Management:** Automatically runs `npm install` or `pip install`. If installation fails, the system **self-corrects** by asking the AI to fix the configuration files (e.g., `package.json`) and retries.
- **Intelligent Task Decomposition:** The system takes a high-level task and breaks it down into actionable subtasks.
- **Dynamic Agent Spawning:** Automatically spawns specialized agents (Planner, Executor, Finalizer) based on the task needs.
- **Security Validation:** Commands are validated against security levels before execution to prevent unsafe operations.
- **Local Privacy:** Built on top of [Ollama](https://ollama.ai/), ensuring all model inference happens locally.
- **REST API:** Fully functional FastAPI backend for easy integration.

## System Architecture

The system is built on a modular architecture:

- **`OrchestratorEngine`**: The core brain (no UI/API) that coordinates the entire lifecycle.
- **`EnvironmentManager`**: Handles automated dependency installation and environment setup.
- **`AgentSpawner`**: Dynamically configures and spawns the appropriate LLM contexts.
- **`PlannerAgent`**: Breaks down the initial prompt into a structured plan.
- **`ExecutorAgent`**: Executes individual subtasks using the selected LLM with support for deep file structures.
- **`SecurityValidator`**: Enforces security policies (e.g., blocking dangerous shell commands).
- **`ResultProcessor`**: Parses agent output and handles file creation (including recursive directories).
- **`FinalizerAgent`**: Reviews the work and generates a final report.
- **`FileManager`**: Handles workspace file operations.

## Capabilities

### Complex Project Structures
Unlike simple code generators, this system supports creating deep directory trees.
- **Example**: "Create a MERN stack app"
- **Result**:
  - `workspace/server/package.json`
  - `workspace/server/routes/auth.js`
  - `workspace/client/src/App.js`

### Auto-Install & Repair
The system attempts to make the generated code **runnable out of the box**.
1.  It detects `package.json` or `requirements.txt`.
2.  Run the install command (`npm install`, etc).
3.  **Self-Correction**: If the install fails (e.g. invalid version), it feeds the error back to the AI, patches the file, and retries automatically.

## Getting Started

### Prerequisites

- **Mac/Linux** (Recommended)
- **Python 3.10+**
- **Ollama** installed and running

### Installation

The project includes an automated setup script to install dependencies and pull the required Ollama models.

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/multi-agent-system.git
    cd multi-agent-system
    ```

2.  Run the setup script:
    ```bash
    ./setup.sh
    ```
    This will:
    - Check for Python and Ollama.
    - Install Python dependencies from `requirements.txt`.
    - Pull the default models (e.g., `deepseek-v3.1`).
    - Create the necessary workspace directories.

### Usage

1.  **Start the Server:**
    Use the provided run script to start the FastAPI server with hot-reload enabled.
    ```bash
    ./run.sh
    ```
    The server will start at `http://127.0.0.1:8000`.

2.  **Access the API:**
    - **Swagger UI:** Navigate to `http://127.0.0.1:8000/docs` to interact with the API visually.
    - **ReDoc:** Navigate to `http://127.0.0.1:8000/redoc`.

3.  **Execute a Task:**
    Send a POST request to `/tasks/execute`:

    ```bash
    curl -X POST "http://127.0.0.1:8000/tasks/execute" \
         -H "Content-Type: application/json" \
         -d '{
               "task": "Create a MERN stack application for a car dealership",
               "context": {}
             }'
    ```

## Docker Support 🐳

You can run the entire system in a Docker container.

1.  **Build and Run:**
    ```bash
    docker-compose up --build
    ```

2.  **Access:**
    The API will be available at `http://localhost:8000`.

3.  **Note on Ollama:**
    The container is configured to talk to your *host machine's* Ollama instance via `host.docker.internal`. Ensure Ollama is running on your machine (`ollama serve`).

## Development

- **`app/`**: Contains the FastAPI application and routes.
- **`core/`**: Contains the core logic (`OrchestratorEngine`).
- **`action/`**: Contains execution tools including `EnvironmentManager`.
- **`workspace/`**: The default location where generated files are saved.
