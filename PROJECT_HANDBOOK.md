# 📘 Multi-Agent Orchestration System - The Complete Handbook

## 1. System Philosophy & Vision

This project is not just a code generator; it is an **autonomous software engineering entity**. It mimics the workflow of a human engineering team:
1.  **Product Manager (Planner):** Breaks down vague requirements into actionable specs.
2.  **Architect (Graph Memory):** Remembers existing system constraints and dependencies.
3.  **UI/UX Specialist (Vision Agent):** analyzes visual inputs.
4.  **Engineer (Executor):** Writes the code, managing file structures and imports.
5.  **QA (Environment Manager):** Installs packages and fixes build errors.

The system is built on a **Modular Client-Server Architecture** using FastAPI, enabling it to be run headless or integrated into other tools.

---

## 2. High-Level Architecture

The system operates as a **State Machine** driven by the `OrchestratorEngine`.

### Data Flow Pipeline
1.  **Input:** User provides a Task String (and optional Images/Files).
2.  **Memory Retrieval (Pre-Computation):**
    *   System queries **Neo4j** for relevant knowledge graph context (e.g., "UserAuth class depends on Redis").
    *   System queries **Vision Agent** to analyze any input images.
3.  **Planning:** The `PlannerAgent` generates a list of Subtasks (JSON).
4.  **Execution Loop:**
    *   For each subtask, an `ExecutorAgent` is spawned.
    *   The Agent writes code to the `workspace/` directory using the `FileManager`.
    *   The `SecurityValidator` ensures no malicious commands are generated.
5.  **Self-Correction:**
    *   `EnvironmentManager` attempts `pip install` / `npm install`.
    *   If it fails, the error is fed back to the LLM for a patch fix.
6.  **Finalization:** The `FinalizerAgent` reviews all work and generates a Markdown report.

---

## 3. Deep Dive: Key Components

### 🧠 Core (`core/`)
This is the "Brain" of the operation.

#### `orchestrator_engine.py`
*   **Role:** The centralized controller. It acts as the glue between all other modules.
*   **Key Method:** `execute(task)`
    *   This is the entry point. It initializes all agents and manages the state.
    *   It handles the **Context Injection**: Combining user input + Graph Context + Vision Analysis into a single prompt for the agents.
*   **Key Method:** `_verify_and_heal()`
    *   This implements the **Self-Healing Loop**. It runs shell commands to install dependencies. If exit code != 0, it asks an LLM to rewrite the config file (`requirements.txt` / `package.json`).

#### `llm_router.py`
*   **Role:** The Universal Translator for LLMs.
*   **Logic:** It provides a unified `chat()` interface that abstracts away provider differences.
    *   **Ollama:** Uses the local API (great for privacy/free usage).
    *   **OpenAI/Groq/Gemini:** Adapts the request payload (headers, JSON structure) to match their specific APIs.
*   **Multi-Modal Handling:** It detects if `images` are present in the request and formats them correctly (e.g., converting to base64 for OpenAI or specific object types for Gemini).

### �️ Cognitive (`cognitive/`)
These are the specialized "lobes" of the brain.

#### `vision.py` (The Eyes)
*   **Function:** `analyze_ui(image_paths)`
*   **Process:**
    1.  The image is sent to a Vision-Language Model (like LLaVA or GPT-4o).
    2.  The prompt asks for a **structural breakdown**: "What components face the user? What is the layout? What colors are used?"
    3.  The text description is returned to the Orchestrator to "ground" the code generation in visual reality.

#### `graph_memory.py` (The Long-Term Memory)
*   **Technology:** Neo4j (Graph Database).
*   **Role:** Enables "Reasoning across files."
*   **Schema:**
    *   **Nodes:** Entities found in code (`Class`, `Function`, `File`, `Service`).
    *   **Edges:** Relationships (`IMPORTS`, `CALLS`, `EXTENDS`, `DEPENDS_ON`).
*   **Ingestion:** When `index_workspace()` is called, an LLM scans every file and outputs a JSON graph structure, which is then written to Neo4j.
*   **Retrieval:** Before writing new code, the system queries the graph: "What is related to 'Auth'?" It returns: "Auth uses RedisService". This prevents the agent from hallucinating a new Auth system when one exists.

#### `planner.py` (The Strategist)
*   **Role:** Prevents the system from getting lost in details.
*   **Logic:** Forces the LLM to output a **Structured JSON Plan** before writing a single line of code. This separates "Thinking" from "Doing."

### 🛡️ Admin & Tools

#### `admin/spawner.py`
*   **Role:** The Factory.
*   **Logic:** Instead of hardcoding "Use GPT-4", it enables dynamic selection. You can configure: "Use DeepSeek for Coding, but use Gemini for Vision."

#### `admin/security.py`
*   **Role:** The Safety Net.
*   **Logic:** Regex-based validation. It blocks commands like `rm -rf /`, `mkfs`, or access to sensitive directories (`/etc/shadow`).

---

## 4. Setup & Usage Guide

### 🐳 Option A: Docker (Production-Ready)
This is the most stable method as it isolates the environment and database.

**Prerequisites:**
*   Docker Desktop installed.
*   **Ollama Running Locally:** Run `ollama serve` in a dedicated terminal.

**Steps:**
1.  **Configuration:**
    *   Copy `.env.example` to `.env`.
    *   Add API keys if you want to use cloud models (Groq, OpenAI).
2.  **Build & Run:**
    ```bash
    docker-compose up --build
    ```
    *This starts two containers: `multiagent_core` (Python App) and `multiagent_graph` (Neo4j).*
3.  **Access:**
    *   API: `http://localhost:8000`
    *   Neo4j Browser: `http://localhost:7474` (User: `neo4j`, Pass: `password`)

### 🐍 Option B: Local Python (Development)
Use this if you are actively modifying the codebase.

**Prerequisites:**
*   Python 3.10+
*   Neo4j Database (You can run just the DB in Docker: `docker-compose up neo4j -d`)

**Steps:**
1.  **Virtual Env:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
2.  **Install Deps:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run Server:**
    ```bash
    ./run.sh
    ```
    *The app will listen on `0.0.0.0:8000`.*

---

## 5. Troubleshooting / Common Issues

### ❌ Docker: "Connection Refused"
*   **Cause:** The Python app uses `host.docker.internal` to talk to Ollama, but it might be trying to reach Neo4j before it's ready, or Neo4j crashed.
*   **Fix:**
    1.  Check Neo4j status: `docker ps`. If it's not there, run `docker-compose up neo4j`.
    2.  Ensure you are using the latest `Dockerfile` (which runs `uvicorn` directly, not via `run.sh`).

### ❌ Docker: "exec format error" in logs
*   **Cause:** The `run.sh` script has Windows line endings (CRLF) or missing permissions, and you are trying to run it in a Linux container.
*   **Fix:** The current `Dockerfile` bypasses `run.sh` to avoid this. If you revert to using the script, run `chmod +x run.sh` and ensure it is saved with LF line endings.

### ❌ "ModuleNotFoundError: cognitive"
*   **Cause:** Python path issue when running tests locally.
*   **Fix:** Run python with the current directory in the path:
    ```bash
    PYTHONPATH=. python3 tests/test_graph.py
    ```

### ❌ LLM Hallucinations / Bad Code
*   **Cause:** Small local models (like `llama3:8b`) struggle with complex constraints.
*   **Fix:**
    1.  Switch to a larger local model (`deepseek-coder:33b` or `llama3:70b` via Groq).
    2.  Edit `.env` and set `DEFAULT_PROVIDER=groq`.
