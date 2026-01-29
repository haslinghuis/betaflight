# Betaflight AI Dev Squad

This setup provides a multi-agent AI system for developing Betaflight firmware using CrewAI and Docker.

## Setup

1. Ensure you have Docker and Docker Compose installed.
2. Install NVIDIA Container Toolkit if you want GPU acceleration for Ollama.
3. Run `docker-compose up` to start the environment. This will automatically build the Betaflight dev container, start Ollama, and pull the DeepSeek-Coder-V2 Lite model.

## Agents

- **Foreman**: Supervisor coordinating all agents and managing human checkpoints
- **Functional Architect**: Designs features based on requirements
- **Hardware Specialist**: Provides expertise on flight controller hardware and target configurations
- **Technical Lead**: Implements C code for Betaflight
- **Testing Agent**: Creates and runs unit tests for code changes
- **Safety Reviewer**: Audits code for safety and standards
- **Cynic**: Skeptical reviewer looking for flaws and potential failures
- **Aero-Physicist**: Ensures alignment with flight physics and control theory
- **Librarian**: Hardware and documentation expert with RAG for datasheets
- **Test Pilot**: Runs SITL automated flight tests
- **Research Agent**: Keeps AI environment updated and optimized

## Features

- Hierarchical multi-agent collaboration with specialized roles
- Local LLM integration via Ollama
- Codebase search and read tools for context-aware development
- Human-in-the-loop checkpoints for critical decisions
- Safety auditing with Betaflight-specific rules
- Discovery phase to understand existing code before design
- Autonomous compilation and error fixing with GCC log parsing
- Cross-repository documentation synchronization
- SITL automated testing for flight validation
- Zero-trust skeptical auditing for architectural violations

## Requirements

- Docker and Docker Compose
- NVIDIA Container Toolkit (for GPU acceleration, optional)
- The system will automatically pull DeepSeek-Coder-V2 Lite model on first run