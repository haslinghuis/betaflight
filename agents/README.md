# Betaflight AI Dev Squad

This setup provides a multi-agent AI system for developing Betaflight firmware using CrewAI and Docker.

## Setup

1. Ensure you have Docker and Docker Compose installed.
2. Install NVIDIA Container Toolkit if you want GPU acceleration for Ollama.
3. Run `docker-compose up` to start the environment. This will automatically build the Betaflight dev container, start Ollama, and pull the DeepSeek-Coder-V2 Lite model.

## Usage

The AI squad can be run directly using the `main.py` script with Docker.

### Basic Command
```bash
docker build -t ai-agents:latest ./agents && \
docker run --rm --network host \
  -v $(pwd):/workspace/src \
  -v $(pwd)/betaflight-com:/workspace/docs \
  -v $(pwd)/agents:/workspace/agents \
  -e OPENAI_API_BASE=http://localhost:11434/v1 \
  ai-agents:latest python /workspace/agents/main.py --task "Your task description here"
```

### Command Line Options

- `--task`: **Required**. Description of the task for the AI squad to perform
  - Examples:
    - `"Analyze PR #14620 motor telemetry refactoring for safety, performance, and Betaflight standards compliance"`
    - `"Implement GPS Rescue feature for Betaflight"`
    - `"Review code changes in src/main/fc/rc.c for potential race conditions"`

- `--output`: **Optional**. Output file for results (default: `agents/output/ai_squad_output.txt`)
  - The analysis results will be saved to this file
  - Can be used for integration with CI/CD pipelines

- `--verbose`, `-v`: **Optional**. Enable verbose output with detailed agent reasoning and intermediate steps
  - When enabled, shows detailed thinking process of each agent
  - Useful for debugging and understanding agent decision-making
  - Default: disabled (quiet mode for cleaner output)

- `--help`, `-h`: **Optional**. Show help message and exit
  - Displays usage information and available options

### Examples

#### Analyze a Pull Request
```bash
docker build -t ai-agents:latest ./agents && \
docker run --rm --network host \
  -v $(pwd):/workspace/src \
  -v $(pwd)/betaflight-com:/workspace/docs \
  -v $(pwd)/agents:/workspace/agents \
  -e OPENAI_API_BASE=http://localhost:11434/v1 \
  ai-agents:latest /bin/bash -c "cd /workspace/agents && python main.py \
  --task 'Analyze PR #14620 motor telemetry refactoring for safety, performance, and Betaflight standards compliance' \
  --output output/pr_14620_analysis.txt"
```

#### Implement a New Feature
```bash
docker build -t ai-agents:latest ./agents && \
docker run --rm --network host \
  -v $(pwd):/workspace/src \
  -v $(pwd)/betaflight-com:/workspace/docs \
  -v $(pwd)/agents:/workspace/agents \
  -e OPENAI_API_BASE=http://localhost:11434/v1 \
  ai-agents:latest /bin/bash -c "cd /workspace/agents && python main.py \
  --task 'Implement a new LED control feature for Betaflight with support for WS2812B strips'"
```

#### Analyze with Verbose Output
```bash
docker build -t ai-agents:latest ./agents && \
docker run --rm --network host \
  -v $(pwd):/workspace/src \
  -v $(pwd)/betaflight-com:/workspace/docs \
  -v $(pwd)/agents:/workspace/agents \
  -e OPENAI_API_BASE=http://localhost:11434/v1 \
  ai-agents:latest /bin/bash -c "cd /workspace/agents && python main.py \
  --task 'Analyze PR #14620 motor telemetry refactoring' \
  --verbose \
  --output output/verbose_analysis.txt"
```

### Prerequisites

- **Ollama must be running** with DeepSeek-Coder-V2 Lite model:
  ```bash
  ollama serve  # Start Ollama service
  ollama pull deepseek-coder-v2:lite  # Pull the model
  ```

- **Docker volumes mounted** for access to:
  - `/workspace/src`: Betaflight source code
  - `/workspace/docs`: Documentation repository
  - `/workspace/agents`: AI agents code

### Output

The AI squad will:
1. Search the codebase for relevant existing implementations
2. Identify potential safety and performance issues
3. Check compliance with Betaflight coding standards
4. Verify hardware compatibility
5. Ensure no blocking operations in flight control loops
6. Provide comprehensive analysis and recommendations

Results are displayed in the terminal and saved to the `agents/output/` directory by default.
All AI-generated output files are automatically ignored by git.

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
- Zero-trust skeptical auditing with static analysis tools
- **Shared Intelligence**: Community-shared vector stores and gold datasets for consistent AI behavior across teams

## Shared Intelligence

The AI squad supports sharing "training data" (vector stores, gold datasets, and persona libraries) across the Betaflight community for decentralized expert systems.

### How It Works
- Agents automatically harvest successful corrections from Cynic-to-Tech-Lead interactions
- Data is stored in a shared volume accessible to all team members
- Community can share vector stores via GitHub releases
- Knowledge-sync service downloads latest shared intelligence on startup

### Creating Training Data
Run the packaging script to create shareable training data:
```bash
./package_training_data.sh
```

This creates `betaflight_ai_training_data.zip` containing:
- Gold dataset of successful corrections (JSONL format)
- Vector store for RAG retrieval
- Metadata about agents and tools

### Sharing with Community
1. Upload the zip file to GitHub releases
2. Other teams can download it via the knowledge-sync service
3. Ensures consistent AI behavior across different Betaflight development teams

## Data Harvester

The **Data Harvester** captures successful bug fixes and agent interactions to create training data for fine-tuning local models.

### How It Works
- Triggers only after both **Cynic Audit** and **SITL Test** pass
- Extracts instruction, critique, and solution from agent conversations
- Saves in JSONL format suitable for fine-tuning DeepSeek/Llama models
- Includes human approval workflow to ensure data quality

### Training Data Format
Each entry contains:
```json
{
  "instruction": "Task description",
  "critique": "Cynic's feedback on issues found",
  "solution": "Final corrected implementation",
  "context": "Betaflight v4.6-dev",
  "verified": true,
  "human_approved": false
}
```

### Human Approval
Only human-approved entries are used for fine-tuning:
```python
from harvester import harvester
harvester.mark_human_approved()  # Mark latest entry as approved
```

## GitHub Actions Integration

The AI squad can automatically review code changes on pull requests.

### Setup
1. The workflow file is located at `.github/workflows/ai-squad-review.yml`
2. Triggers on PRs that modify source code (excluding tests and docs)
3. Runs the full AI squad analysis pipeline

### What It Does
- Builds the development environment
- Analyzes changed files for safety violations
- Runs Cynic audit for blocking code patterns
- Comments on the PR with findings
- Harvests training data from successful reviews
- Uploads training data as artifacts

### Benefits
- **Automated Code Review**: Catches safety issues before merge
- **Continuous Learning**: Each review improves the AI models
- **Community Knowledge**: Training data is shared across teams
- **Quality Assurance**: Ensures Betaflight coding standards are maintained

## Installation

### Docker and Docker Compose

#### Ubuntu
1. Update your package index:
   ```
   sudo apt update
   ```
2. Install Docker:
   ```
   sudo apt install docker.io
   ```
3. Start and enable Docker:
   ```
   sudo systemctl start docker
   sudo systemctl enable docker
   ```
4. Add your user to the docker group (optional, to run without sudo):
   ```
   sudo usermod -aG docker $USER
   ```
   Log out and back in for changes to take effect.
5. Install Docker Compose:
   ```
   sudo apt install docker-compose
   ```

#### Windows
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop).
2. Run the installer and follow the setup wizard.
3. Docker Compose is included with Docker Desktop.

#### macOS
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop).
2. Open the downloaded .dmg file and drag Docker to Applications.
3. Launch Docker Desktop from Applications.
4. Docker Compose is included with Docker Desktop.

### NVIDIA Container Toolkit (for GPU acceleration, optional)

#### Ubuntu
1. Install NVIDIA drivers (if not already installed).
2. Add the NVIDIA package repository:
   ```
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   ```
3. Install nvidia-docker2:
   ```
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   ```
4. Restart Docker:
   ```
   sudo systemctl restart docker
   ```

#### Windows/macOS
NVIDIA Container Toolkit is not required for Docker Desktop on Windows/macOS; GPU acceleration is handled automatically if NVIDIA drivers are installed.

## Requirements

- Docker and Docker Compose
- NVIDIA Container Toolkit (for GPU acceleration, optional)
- The system will automatically pull DeepSeek-Coder-V2 Lite model on first run