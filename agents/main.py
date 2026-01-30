from crewai import Agent, Task, Crew, Process, LLM
from langchain.tools import tool
from prompts import REVIEWER_PROMPT, CYNIC_PROMPT
from tools import search_codebase, read_file_content, build_and_debug, run_sitl_test
from audit_tools import check_non_blocking_compliance, check_atomic_access
from harvester import harvester
import subprocess
import argparse

# Configure the Local LLM connection
local_llm = LLM(
    model='ollama/deepseek-coder-v2:lite',
    base_url="http://localhost:11434",
    api_key="ollama",  # Dummy key for Ollama
    provider="ollama"
)

# AGENT: The Functional Architect
functional_architect = Agent(
    role='Functional Architect',
    goal='Design new features for Betaflight based on user requirements',
    backstory='Expert in drone flight control systems and Betaflight architecture. Translates high-level ideas into technical specifications. Always searches the codebase for existing implementations.',
    tools=[search_codebase, read_file_content],
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
    tools=[build_and_debug, read_file_content],
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
    tools=[build_and_debug],
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
    tools=[check_non_blocking_compliance, check_atomic_access],
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
    tools=[search_codebase, read_file_content],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# AGENT: The Test Pilot (SITL Expert)
test_pilot = Agent(
    role='SITL Tester',
    goal='Run automated flight tests in the simulator',
    backstory='Compiles SITL target and runs virtual flight tests to validate functionality. Analyzes blackbox logs for stability.',
    tools=[build_and_debug, run_sitl_test],
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
    expected_output='A Markdown specification document outlining the feature requirements and integration points.'
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

# Example Task: Cynic Review
review_task = Task(
    description='Perform skeptical review of the code for safety violations, blocking calls, and atomic access issues',
    agent=cynic,
    expected_output='Safety audit report identifying any critical issues that need fixing.'
)

# Final Verification Task: SITL Test + Cynic Audit
verification_task = Task(
    description="""
    Perform final verification of the implemented code:
    1. Run SITL automated flight test to ensure no scheduler overruns
    2. Execute Cynic audit for safety and blocking code violations
    3. Only pass if both tests succeed
    """,
    expected_output='Flight-ready C implementation with 0 scheduler overruns and clean safety audit.',
    agent=test_pilot,  # Test Pilot handles SITL, but will delegate Cynic audit
    callback=harvester.save_learning  # Harvest successful corrections
)

# Create the Crew
crew = Crew(
    agents=[functional_architect, tech_lead, hardware_specialist, testing_agent, safety_reviewer, cynic, aero_physicist, librarian, test_pilot, research_agent],
    tasks=[discovery_task, design_task, hardware_task, code_task, testing_task, review_task, verification_task],
    process=Process.sequential
)

# Run the crew
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Betaflight AI Squad - Multi-agent system for Betaflight firmware development',
        epilog='Examples:\n'
               '  python main.py --task "Analyze PR #14620 motor telemetry refactoring"\n'
               '  python main.py --task "Implement GPS Rescue feature" --output gps_rescue.txt\n'
               '  python main.py --help'
    )
    parser.add_argument('--task', type=str,
                       default='Implement GPS Rescue feature for Betaflight',
                       help='Task description for the AI squad to perform. '
                            'Examples: "Analyze PR #1234", "Implement new feature", "Review code for safety"')
    parser.add_argument('--output', type=str,
                       default='ai_squad_output.txt',
                       help='Output file path where results will be saved (default: ai_squad_output.txt)')

    args = parser.parse_args()

    # Create dynamic analysis task based on input
    analysis_task = Task(
        description=f"""
        Analyze the following code changes and requirements: {args.task}

        1. Search the codebase for relevant existing implementations
        2. Identify potential safety and performance issues
        3. Check for compliance with Betaflight coding standards
        4. Verify hardware compatibility
        5. Ensure no blocking operations in flight control loops
        """,
        expected_output='Comprehensive code review with safety analysis and recommendations.',
        agent=functional_architect
    )

    # Create a crew with the analysis task
    analysis_crew = Crew(
        agents=[functional_architect],
        tasks=[analysis_task],
        process=Process.sequential,
        verbose=True
    )

    result = analysis_crew.kickoff()
    print("Analysis Result:")
    print(result)

    # Save output for GitHub Action
    with open(args.output, 'w') as f:
        f.write(str(result))