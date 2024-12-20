# Multi-Agent System Project
![image](https://github.com/user-attachments/assets/374003b2-31f8-43d5-be7c-432ab63a4edf)
```mermaid
graph TD
    A[User Interface Layer] --> B[Orchestration Layer]
    B --> C[Agent Management Layer]
    C --> D[Docker Container Layer]
    
    subgraph "User Interface Layer"
        A1[Agent Designer] --> A2[Workflow Monitor]
        A2 --> A3[Performance Metrics]
        A3 --> A4[Intervention Tools]
    end

    subgraph "Orchestration Layer"
        B1[Team Manager] --> B2[Task Decomposer]
        B2 --> B3[Progress Monitor]
        B3 --> B4[Intervention Handler]
    end

    subgraph "Agent Management Layer"
        C1[AutoGen Integration] --> C2[Agent Registry]
        C2 --> C3[Communication Bus]
        C3 --> C4[State Manager]
    end
```
### North Star Vision
The north star for this project is to create a robust multi-agent system that efficiently manages and executes complex tasks through a well-coordinated team of specialized agents. The system should provide a seamless user experience through an intuitive UI, allowing users to design, monitor, and optimize workflows in real time. The team orchestrator will play a crucial role in dynamically adapting to task requirements and agent capabilities, ensuring optimal performance and task completion.

Special thanks to GPT and Claude <3

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Overview

The multi-agent system is built using Python and Docker. It includes components for web searching, code execution, and user interaction through a conversational interface. The system is designed to be extensible, allowing for the integration of additional tools and functionalities.

## High-level overview:

1. Core Differentiators:
```python
class UnifiedTeamOrchestrator:
    """Combines:
    - Real-world management principles
    - Advanced task decomposition
    - Dynamic role assignment 
    - Real-time monitoring
    - Visual workflow tracking
    """
```

2. Key Innovations:
- Fact-based planning: Uses verified facts, facts to look up, and educated guesses
- Business-inspired workflow: Based on real management experience
- Visual monitoring: Real-time tracking and visualization
- Stall detection: Identifies and handles blocked progress
- Role optimization: Matches agent capabilities to tasks

3. Architecture Flow:
```mermaid
graph TD
    A[Initial Task] --> B[Fact Gathering]
    B --> C[Task Planning]
    C --> D[Role Assignment]
    D --> E[Execution]
    E --> F[Monitoring]
    F -->|Success| G[Complete]
    F -->|Stalled| H[Replan]
    H --> B
```

4. What Sets Us Apart:
- Business-driven design vs purely academic approaches
- Real-time visualization vs black box execution
- Practical management principles vs theoretical frameworks
- Focus on tracking and improvement vs just task completion

## Project Structure

- **src/**: Contains the main source code for the agents, configuration, and execution logic.
- **tools/**: Utilities for web searching and directory structure printing.
- **scripts/**: Batch scripts for setting up and managing the Docker environment.
- **docker/**: Docker configuration files for building and running the system.

## Overview

1. Architecture Overview:
- GUI Layer: Handles visualization and user interaction
- Core System: Manages workflows, tasks, and team configuration
- Specialized Agents: Different types of AI agents for specific tasks
- Docker Environment: Provides isolated execution environment

2. Key Features:
- Intuitive drag-and-drop workflow design
- Visual workflow monitoring with node editor
- Real-time metrics tracking
- Docker containerization for safe code execution
- Specialized agent roles (Research, Code, Viz, QA, PM)
- Task decomposition and dynamic team formation

3. Main Components:
- MultiAgentSystem: Main orchestrator class
- AgentMonitor: Handles UI and visualization
- WorkflowManager: Manages agent workflows
- TeamManager: Handles agent team composition
- DockerWorkspaceManager: Manages Docker containers and volumes

4. Workflow:
1. System initialization (configuration, Docker setup)
2. Monitor setup (UI components, message queue)
3. Workflow creation and team assignment
4. Real-time monitoring and visualization
5. Graceful shutdown and cleanup

## Setup

To set up the project, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/pattty847/Multi-Agent-Team.git
   cd Multi-Agent-Team
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Setup Script**:
   Execute the setup script to build and start the Docker containers.
   ```bash
   scripts/setup.bat
   ```

## Usage

1. **Access Jupyter Lab**:
   Use the Jupyter script to launch Jupyter Lab for interactive development.
   ```bash
   scripts/jupyter.bat
   ```

2. **Run Tasks**:
   The system can perform tasks such as web searches and code execution through the agents.

3. **Stop the System**:
   Use the stop script to stop the Docker containers when done.
   ```bash
   scripts/stop.bat
   ```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes. Ensure that your code adheres to the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
```
