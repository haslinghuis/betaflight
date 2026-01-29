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

## Features

- Multi-agent collaboration with specialized roles
- Local LLM integration via Ollama
- Codebase search and read tools for context-aware development
- Human-in-the-loop checkpoints for critical decisions
- Safety auditing with Betaflight-specific rules
- Discovery phase to understand existing code before design

## Requirements

- Docker and Docker Compose
- NVIDIA Container Toolkit (for GPU acceleration, optional)
- The system will automatically pull DeepSeek-Coder-V2 Lite model on first run