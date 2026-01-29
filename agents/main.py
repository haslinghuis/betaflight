from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from prompts import REVIEWER_PROMPT
from tools import BetaflightTools
import subprocess

# Configure the Local LLM connection
local_llm = ChatOpenAI(
    model='deepseek-coder-v2:lite', # High-performance coding model
    base_url="http://ollama:11434/v1",
    api_key="ollama" # Required field, but ignored by Ollama
)

# AGENT: The Functional Architect
functional_architect = Agent(
    role='Functional Architect',
    goal='Design new features for Betaflight based on user requirements',
    backstory='Expert in drone flight control systems and Betaflight architecture. Translates high-level ideas into technical specifications. Always searches the codebase for existing implementations.',
    tools=[BetaflightTools.search_codebase, BetaflightTools.read_file_content],
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

# Example Task: Discovery
discovery_task = Task(
    description="""
    1. Search for all instances of 'gpsRescue' in the codebase.
    2. Identify the primary header file defining the GPS Rescue state machine.
    3. Read the code to understand how it currently handles 'home distance'.
    """,
    expected_output="A summary of the current GPS Rescue logic and which files need modification.",
    agent=functional_architect
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
    tasks=[discovery_task, design_task, hardware_task, code_task, testing_task, review_task],
    process=Process.sequential
)

# Run the crew
if __name__ == "__main__":
    result = crew.kickoff()
    print(result)