from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from prompts import REVIEWER_PROMPT, CYNIC_PROMPT
from tools import BetaflightTools, build_and_debug, scan_for_violations
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
    goal='Generate and compile error-free Betaflight code.',
    backstory="""You are an expert C developer. If a build fails, 
    you use the 'read_file_content' tool to look at the line numbers 
    reported by the compiler and fix your mistakes immediately.""",
    tools=[build_and_debug, BetaflightTools.read_file_content],
    llm=local_llm,
    max_iter=3, # Allow the agent to try fixing its code 3 times before asking for help
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

# AGENT: The Cynic (Skeptic)
cynic = Agent(
    role='Lead Skeptic',
    goal='Find flaws and potential failures in proposed code',
    backstory=CYNIC_PROMPT,
    tools=[scan_for_violations],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Aero-Physicist
aero_physicist = Agent(
    role='Aerospace Engineer',
    goal='Ensure code changes align with flight physics and control theory',
    backstory='Expert in PID control theory, vibrations, and thrust-to-weight dynamics. Prevents flyaways from poor filtering or control logic.',
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Librarian (Hardware/Docs Expert)
librarian = Agent(
    role='Hardware and Documentation Expert',
    goal='Provide accurate hardware information and update documentation',
    backstory='RAG-enabled expert for STM32/AT32 datasheets and betaflight.com updates. Ensures register addresses and DMA assignments are correct.',
    tools=[BetaflightTools.search_codebase, BetaflightTools.read_file_content],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Test Pilot (SITL Expert)
test_pilot = Agent(
    role='SITL Tester',
    goal='Run automated flight tests in the simulator',
    backstory='Compiles SITL target and runs virtual flight tests to validate functionality. Analyzes blackbox logs for stability.',
    tools=[build_and_debug],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Research Agent (DevOps for AI)
research_agent = Agent(
    role='Research and Infrastructure Specialist',
    goal='Keep the AI environment updated and optimized',
    backstory='Audits Docker infrastructure, tests new models, and ensures the development environment stays current.',
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Foreman (Supervisor)
foreman = Agent(
    role='Foreman',
    goal='Coordinate all agents and manage human-in-the-loop checkpoints',
    backstory='Meticulous project manager who values flight safety above all else. Ensures quality and cross-agent collaboration.',
    allow_delegation=True,
    llm=local_llm,
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
    agents=[functional_architect, tech_lead, hardware_specialist, testing_agent, safety_reviewer, cynic, aero_physicist, librarian, test_pilot, research_agent],
    tasks=[discovery_task, design_task, hardware_task, code_task, testing_task, review_task],
    process=Process.hierarchical,
    manager_agent=foreman
)

# Run the crew
if __name__ == "__main__":
    result = crew.kickoff()
    print(result)