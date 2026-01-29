# Betaflight AI Dev Squad

This setup provides a multi-agent AI system for developing Betaflight firmware using CrewAI and Docker.

## Setup

1. Ensure you have Docker and Docker Compose installed.
2. Install NVIDIA Container Toolkit if you want GPU acceleration for Ollama.
3. Run `docker-compose up` to start the environment. This will automatically build the Betaflight dev container, start Ollama, and pull the DeepSeek-Coder-V2 Lite model.

## Agents

- **Functional Architect**: Designs features based on requirements.
- **Hardware Specialist**: Provides expertise on flight controller hardware and target configurations.
- **Technical Lead**: Implements C code for Betaflight.
- **Testing Agent**: Creates and runs unit tests for code changes.
- **Safety Reviewer**: Audits code for safety and standards.

## Usage

Modify the tasks in `main.py` to define your development goals. The agents will collaborate to design, implement, and review code changes.

## Requirements

- Docker and Docker Compose
- NVIDIA Container Toolkit (for GPU acceleration, optional)
- The system will automatically pull DeepSeek-Coder-V2 Lite model on first run