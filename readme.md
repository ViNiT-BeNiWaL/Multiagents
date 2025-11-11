# Multi-Agent System 🤖

An intelligent multi-agent orchestration system that automatically decomposes complex tasks, selects optimal AI models, and generates complete implementations with working code files.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## ✨ Features

- **🧠 Intelligent Task Decomposition**: Automatically breaks down complex tasks into manageable subtasks
- **🎯 Smart Model Selection**: Chooses the best AI model for each subtask based on task type (coding, analysis, math, creative, etc.)
- **📁 Automatic File Generation**: Creates actual working files from task results
- **🔒 Security First**: Built-in security validation for safe operations
- **📊 Comprehensive Reporting**: Detailed execution reports with quality scores
- **🎨 Rich CLI Interface**: Beautiful terminal output with progress tracking

## 🏗️ Architecture

The system consists of four main layers:

### 1. **Admin Layer** (`admin/`)
- **Spawner**: Creates and manages agent instances with automatic model selection
- **Manager**: Coordinates task execution and inter-agent communication
- **Security**: Validates operations to prevent harmful commands

### 2. **Cognitive Layer** (`cognitive/`)
- **Planner**: Breaks down complex tasks into subtasks
- **Decision Engine**: Makes intelligent routing and prioritization decisions

### 3. **Action Layer** (`action/`)
- **File Manager**: Handles secure file operations in workspace
- **Finalizer**: Validates and consolidates results

### 4. **Orchestrator** (`orchestrator.py`)
Central coordinator that manages the entire execution pipeline

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Ollama installed and running
- 8GB+ RAM recommended

### Installation

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd Multiagents
```

2. **Run automated setup**:
```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Install Python dependencies
- Install Ollama (if not present)
- Download required AI models
- Set up workspace directory

3. **Or manual setup**:
```bash
# Install dependencies
pip install -r requirements.txt

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull required models
ollama pull deepseek-v3.1:671b-cloud
ollama pull qwen3-coder:480b-cloud

# Create workspace
mkdir -p workspace
```

### Usage

**Interactive Mode**:
```bash
python orchestrator.py
```

**Example Usage**:
```python
from orchestrator import MultiAgentOrchestrator

# Initialize orchestrator
orchestrator = MultiAgentOrchestrator()

# Execute a task
result = orchestrator.execute_task(
    "Create a Python password manager with encryption"
)

# Results include created files
print(f"Created {len(result['created_files'])} files")
```

## 🎯 Model Selection

The system automatically selects models based on task type:

| Task Type | Primary Model | Use Case |
|-----------|---------------|----------|
| **Coding** | deepseek-v3.1:671b-cloud | Writing functions, classes, algorithms |
| **Planning** | qwen3-coder:480b-cloud | Task decomposition, architecture design |
| **Analysis** | deepseek-v3.1:671b-cloud | Data analysis, evaluations |
| **Math** | deepseek-v3.1:671b-cloud | Calculations, equations, statistics |
| **Creative** | deepseek-v3.1:671b-cloud | Content generation, creative writing |
| **Reasoning** | deepseek-v3.1:671b-cloud | Logic, deduction, problem-solving |

### Model Selection Keywords

The system detects task types using keywords:

- **Coding**: code, program, function, implement, debug, refactor
- **Analysis**: analyze, evaluate, compare, review, study
- **Math**: calculate, compute, equation, formula, statistics
- **Planning**: plan, strategy, architecture, design, structure
- **Creative**: write, create, story, compose, generate

## 📋 Example Tasks

### 1. Banking System
```python
orchestrator.execute_task(
    "Create a banking transaction analysis system with fraud detection"
)
```
**Output**: Complete banking system with transaction processing, fraud detection algorithms, and test files

### 2. Web Scraper
```python
orchestrator.execute_task(
    "Build a web scraping and data processing pipeline"
)
```
**Output**: Scraper implementation, data processors, and usage examples

### 3. Password Manager
```python
orchestrator.execute_task(
    "Create a secure CLI password manager with encryption"
)
```
**Output**: Encrypted storage, CLI interface, security utilities

### 4. Data Analysis Tool
```python
orchestrator.execute_task(
    "Build a data quality assessment tool for CSV files"
)
```
**Output**: CSV parser, quality metrics, reporting module

## 🗂️ Project Structure

```
Multiagents/
├── admin/                  # Agent management
│   ├── spawner.py         # Agent creation & model selection
│   ├── manager.py         # Task coordination
│   └── security.py        # Security validation
├── cognitive/             # Planning & decision making
│   ├── planner.py        # Task decomposition
│   └── decision_engine.py # Intelligent routing
├── action/               # Execution & file operations
│   ├── file_manager.py   # File operations
│   └── finalizer.py      # Result validation
├── orchestrator.py       # Main coordinator
├── result_processor.py   # File generation from results
├── workspace/           # Generated files
└── requirements.txt     # Dependencies
```

## 🔧 Configuration

### Custom Model Selection

Override automatic model selection:

```python
orchestrator = MultiAgentOrchestrator()

# Use custom model
config = orchestrator.spawner.spawn_agent(
    agent_type=AgentType.EXECUTOR,
    task_description="your task",
    custom_model="your-preferred-model"
)
```

### Workspace Configuration

Change workspace directory:

```python
orchestrator = MultiAgentOrchestrator(workspace="./custom_workspace")
```

### Security Levels

Adjust security validation:

```python
from admin.security import SecurityLevel

# Available levels: LOW, MEDIUM, HIGH, CRITICAL
orchestrator.security.validate_command(command, SecurityLevel.HIGH)
```

## 📊 System Statistics

View comprehensive statistics:

```python
# Get stats
stats = orchestrator.get_system_stats()

# Display in terminal
orchestrator.display_stats()
```

Metrics include:
- Total agents spawned
- Active agents by type
- Task completion rates
- File operation statistics
- Model usage distribution

## 🔒 Security Features

- **Path Traversal Prevention**: Restricts file operations to workspace
- **Command Validation**: Blocks dangerous shell commands
- **Input Sanitization**: Removes control characters and null bytes
- **Pattern Matching**: Detects forbidden operations (rm -rf, fork bombs, etc.)
- **Audit Logging**: Tracks all security events

## 🐛 Troubleshooting

### 401 Unauthorized Error

**Problem**: `unauthorized (status code: 401)`

**Solutions**:
1. **Cloud models require authentication**:
   ```bash
   export OLLAMA_API_KEY="your-api-key"
   ```

2. **Use local models instead**:
   ```bash
   ollama pull deepseek-v3.1:671b  # Remove :cloud suffix
   ```

3. **Check available models**:
   ```bash
   ollama list
   ```

### Models Not Found

**Problem**: Model not available

**Solution**:
```bash
# Pull the model
ollama pull deepseek-v3.1:671b-cloud

# Or use alternative
ollama pull llama3.2
```

### Memory Issues

**Problem**: Out of memory

**Solution**:
- Use smaller models (7B instead of 671B)
- Close other applications
- Increase system swap space

### No Files Generated

**Problem**: Task completes but no files created

**Solution**:
- Check workspace/ directory permissions
- Review result_processor logs
- Use manual code extraction fallback

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Ollama](https://ollama.ai/) for local LLM inference
- Uses [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Models by DeepSeek, Qwen, and other open-source contributors

## 📧 Support

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: See `/docs` for detailed guides

## 🗺️ Roadmap

- [ ] Support for more AI models (GPT-4, Claude)
- [ ] Web interface for task submission
- [ ] Collaborative multi-agent conversations
- [ ] Plugin system for custom agents
- [ ] Cloud deployment support
- [ ] Real-time progress streaming
- [ ] Task templates library

---

**Built with ❤️ using AI-powered multi-agent orchestration**