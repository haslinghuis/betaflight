from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from prompts import REVIEWER_PROMPT
import subprocess

# Configure the Local LLM connection
local_llm = ChatOpenAI(
    model='deepseek-coder-v2:lite', # High-performance coding model
    base_url="http://ollama:11434/v1",
    api_key="ollama" # Required field, but ignored by Ollama
)

# TOOL: Allows the Agent to search the codebase
@tool("grep_codebase")
def grep_codebase(query: str, file_pattern: str = "*.c"):
    """Searches the Betaflight codebase for relevant code snippets."""
    import os
    result = ""
    for root, dirs, files in os.walk("/workspace/src"):
        for file in files:
            if file.endswith(file_pattern.split("*")[-1]):
                try:
                    with open(os.path.join(root, file), 'r') as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            result += f"File: {os.path.join(root, file)}\nSnippet: {content[:500]}...\n\n"
                except:
                    pass
    return result[:2000]  # Limit output

# AGENT: The Functional Architect
functional_architect = Agent(
    role='Functional Architect',
    goal='Design new features for Betaflight based on user requirements',
    backstory='Expert in drone flight control systems and Betaflight architecture. Translates high-level ideas into technical specifications.',
    tools=[grep_codebase],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Technical Lead
tech_lead = Agent(
    role='Lead Firmware Engineer',
    goal='Write efficient C code for Betaflight targets',
    backstory='Expert in STM32 and Betaflight architecture. Obsessed with loop times.',
    tools=[build_betaflight],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Hardware Specialist
hardware_specialist = Agent(
    role='Hardware Specialist',
    goal='Provide expertise on flight controller hardware, pinouts, and target configurations',
    backstory='Expert in STM32 microcontrollers and Betaflight target definitions. Knows the specifics of each flight controller board and ensures code is compatible with hardware constraints.',
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Testing Agent
testing_agent = Agent(
    role='Testing Agent',
    goal='Create and run unit tests for Betaflight code changes',
    backstory='Focused on ensuring code quality through comprehensive testing. Generates test cases and validates functionality against Betaflight standards.',
    tools=[build_betaflight],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Safety Reviewer
safety_reviewer = Agent(
    role='Safety Reviewer',
    goal='Audit code for safety, performance, and Betaflight standards',
    backstory=REVIEWER_PROMPT,
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)
design_task = Task(
    description='Design a new GPS Rescue behavior for Betaflight',
    agent=functional_architect,
    expected_output='A Markdown specification document outlining the feature requirements and integration points.',
    human_input=True
)

# Example Task: Implement the code
code_task = Task(
    description='Implement the GPS Rescue behavior based on the design spec',
    agent=tech_lead,
    expected_output='C code files ready for compilation and testing.'
)

# Example Task: Hardware review
hardware_task = Task(
    description='Review the design for hardware compatibility and target-specific requirements',
    agent=hardware_specialist,
    expected_output='Hardware compatibility report and any necessary adjustments.'
)

# Example Task: Testing
testing_task = Task(
    description='Generate unit tests for the implemented code and validate functionality',
    agent=testing_agent,
    expected_output='Test files and validation results.'
)

# Create the Crew
crew = Crew(
    agents=[functional_architect, tech_lead, hardware_specialist, testing_agent, safety_reviewer],
    tasks=[design_task, hardware_task, code_task, testing_task, review_task],
    process=Process.sequential
)

# Run the crew
if __name__ == "__main__":
    result = crew.kickoff()
    print(result)