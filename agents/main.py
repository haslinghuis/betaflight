from crewai import Agent, Task, Crew, Process, LLM
from langchain.tools import tool
from prompts import REVIEWER_PROMPT, CYNIC_PROMPT
from tools import search_codebase, read_file_content, build_and_debug, run_sitl_test, fetch_github_pr
from audit_tools import check_non_blocking_compliance, check_atomic_access
from harvester import harvester
import subprocess
import argparse
import os

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
    tools=[search_codebase, read_file_content, fetch_github_pr],
    llm=local_llm,
    allow_delegation=False,
    verbose=False  # Will be set dynamically
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
    verbose=False  # Will be set dynamically
)

# AGENT: The Hardware Specialist
hardware_specialist = Agent(
    role='Hardware Specialist',
    goal='Provide expertise on flight controller hardware, pinouts, and target configurations',
    backstory='Expert in STM32 microcontrollers and Betaflight target definitions. Knows the specifics of each flight controller board and ensures code is compatible with hardware constraints.',
    llm=local_llm,
    allow_delegation=False,
    verbose=False  # Will be set dynamically
)

# AGENT: The Testing Agent
testing_agent = Agent(
    role='Testing Agent',
    goal='Create and run unit tests for Betaflight code changes',
    backstory='Focused on ensuring code quality through comprehensive testing. Generates test cases and validates functionality against Betaflight standards.',
    tools=[build_and_debug],
    llm=local_llm,
    allow_delegation=False,
    verbose=False  # Will be set dynamically
)

# AGENT: The Safety Reviewer
safety_reviewer = Agent(
    role='Safety Reviewer',
    goal='Audit code for safety, performance, and Betaflight standards',
    backstory=REVIEWER_PROMPT,
    llm=local_llm,
    allow_delegation=False,
    verbose=False  # Will be set dynamically
)

# AGENT: The Cynic (Skeptic)
cynic = Agent(
    role='Lead Skeptic',
    goal='Find flaws and potential failures in proposed code',
    backstory=CYNIC_PROMPT,
    tools=[check_non_blocking_compliance, check_atomic_access],
    llm=local_llm,
    allow_delegation=False,
    verbose=False  # Will be set dynamically
)

# AGENT: The Aero-Physicist
aero_physicist = Agent(
    role='Aerospace Engineer',
    goal='Ensure code changes align with flight physics and control theory',
    backstory='Expert in PID control theory, vibrations, and thrust-to-weight dynamics. Prevents flyaways from poor filtering or control logic.',
    llm=local_llm,
    allow_delegation=False,
    verbose=False  # Will be set dynamically
)

# AGENT: The Librarian (Hardware/Docs Expert)
librarian = Agent(
    role='Hardware and Documentation Expert',
    goal='Provide accurate hardware information and update documentation',
    backstory='RAG-enabled expert for STM32/AT32 datasheets and betaflight.com updates. Ensures register addresses and DMA assignments are correct.',
    tools=[search_codebase, read_file_content],
    llm=local_llm,
    allow_delegation=False,
    verbose=False  # Will be set dynamically
)

# AGENT: The Test Pilot (SITL Expert)
test_pilot = Agent(
    role='SITL Tester',
    goal='Run automated flight tests in the simulator',
    backstory='Compiles SITL target and runs virtual flight tests to validate functionality. Analyzes blackbox logs for stability.',
    tools=[build_and_debug, run_sitl_test],
    llm=local_llm,
    allow_delegation=False,
    verbose=False  # Will be set dynamically
)

# AGENT: The Research Agent (DevOps for AI)
research_agent = Agent(
    role='Research and Infrastructure Specialist',
    goal='Keep the AI environment updated and optimized',
    backstory='Audits Docker infrastructure, tests new models, and ensures the development environment stays current.',
    llm=local_llm,
    allow_delegation=False,
    verbose=False  # Will be set dynamically
)

# AGENT: The Foreman (Supervisor)
foreman = Agent(
    role='Foreman',
    goal='Coordinate all agents and manage human-in-the-loop checkpoints',
    backstory='Meticulous project manager who values flight safety above all else. Ensures quality and cross-agent collaboration.',
    allow_delegation=True,
    llm=local_llm,
    verbose=False  # Will be set dynamically
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

# Crew will be created dynamically in main based on task type

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
                       default='agents/output/ai_squad_output.txt',
                       help='Output file path where results will be saved (default: agents/output/ai_squad_output.txt)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output with detailed agent reasoning and intermediate steps')
    parser.add_argument('--quiet-tools', '-q', action='store_true',
                       help='Show only tool errors, suppress successful tool output (reduces verbosity)')

    args = parser.parse_args()

    # Set verbosity for all agents dynamically
    verbose_agents = args.verbose
    functional_architect.verbose = verbose_agents
    tech_lead.verbose = verbose_agents
    hardware_specialist.verbose = verbose_agents
    testing_agent.verbose = verbose_agents
    safety_reviewer.verbose = verbose_agents
    cynic.verbose = verbose_agents
    aero_physicist.verbose = verbose_agents
    librarian.verbose = verbose_agents
    test_pilot.verbose = verbose_agents
    research_agent.verbose = verbose_agents
    foreman.verbose = verbose_agents

    # Set quiet tools mode in environment for tools to check
    if args.quiet_tools:
        os.environ['QUIET_TOOLS'] = '1'
    else:
        os.environ.pop('QUIET_TOOLS', None)

    # Create dynamic analysis tasks based on input
    if "PR" in args.task or "pull request" in args.task.lower():
        # PR Analysis Crew - Multi-agent approach
        pr_analysis_task = Task(
            description=f"""
            Analyze the PR changes: {args.task}
            
            1. First, fetch the PR details and diff using the fetch_github_pr tool
            2. Search the local codebase for related motor telemetry implementations
            3. Read the relevant local files to understand the current implementation
            4. Identify the key files and functions being modified
            5. Summarize the architectural changes and benefits
            """,
            expected_output='Technical summary of PR changes, fetched PR data, and architectural impact.',
            agent=functional_architect
        )
        
        safety_review_task = Task(
            description="""
            Review the PR changes for safety and performance:
            1. Check for blocking operations in flight control loops
            2. Verify atomic access patterns for shared data
            3. Ensure no memory safety violations
            4. Validate scheduler compliance
            """,
            expected_output='Safety audit report with any critical issues identified.',
            agent=safety_reviewer,
            context=[pr_analysis_task]
        )
        
        hardware_compat_task = Task(
            description="""
            Assess hardware compatibility of the PR changes:
            1. Check target-specific requirements
            2. Verify DMA and peripheral usage
            3. Ensure register access is correct
            4. Validate pinout and sensor interface compatibility
            """,
            expected_output='Hardware compatibility assessment and any required adjustments.',
            agent=hardware_specialist,
            context=[pr_analysis_task]
        )
        
        cynic_review_task = Task(
            description="""
            Perform skeptical analysis of the PR changes:
            1. Identify potential race conditions or timing issues
            2. Check for interrupt conflicts or priority inversions
            3. Look for memory corruption risks
            4. Find any watchdog timeout scenarios
            """,
            expected_output='Critical failure analysis and risk assessment.',
            agent=cynic,
            context=[pr_analysis_task, safety_review_task]
        )
        
        final_assessment_task = Task(
            description=f"""
            Provide final assessment of PR {args.task}:
            1. Summarize all findings from the analysis
            2. Rate the quality and safety of the changes
            3. Recommend approval, rejection, or modifications
            4. Suggest any additional testing requirements
            """,
            expected_output="""
            # PR Assessment Summary

            ## Executive Summary
            [Brief overview of the PR's impact and overall assessment]

            ## Key Findings
            - [Major finding 1]
            - [Major finding 2]
            - [Major finding 3]

            ## Quality Rating
            [Rate the code quality on a scale of 1-5, with justification]

            ## Safety Assessment
            [Rate the safety impact on a scale of 1-5, with justification]

            ## Recommendation
            [APPROVE/REJECT/MODIFY] - [Clear reasoning]

            ## Required Actions
            - [Action 1]
            - [Action 2]
            - [Action 3]

            ## Testing Requirements
            - [Test requirement 1]
            - [Test requirement 2]
            """,
            agent=foreman,
            context=[pr_analysis_task, safety_review_task, hardware_compat_task, cynic_review_task]
        )
        
        # Create PR analysis crew
        analysis_crew = Crew(
            agents=[functional_architect, safety_reviewer, hardware_specialist, cynic, foreman],
            tasks=[pr_analysis_task, safety_review_task, hardware_compat_task, cynic_review_task, final_assessment_task],
            process=Process.sequential,
            verbose=args.verbose
        )
    else:
        # Generic analysis with single agent
        analysis_task = Task(
            description=f"""
            Analyze the following request: {args.task}

            1. Search the codebase for relevant existing implementations
            2. Identify potential safety and performance issues
            3. Check for compliance with Betaflight coding standards
            4. Verify hardware compatibility
            5. Ensure no blocking operations in flight control loops
            """,
            expected_output='Comprehensive analysis with safety review and recommendations.',
            agent=functional_architect
        )
        
        analysis_crew = Crew(
            agents=[functional_architect],
            tasks=[analysis_task],
            process=Process.sequential,
            verbose=args.verbose
        )

    result = analysis_crew.kickoff()
    print("Analysis Result:")
    print(result)

    # Save output for GitHub Action - ensure it's human readable
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Convert result to string if it's not already, and ensure it's readable
    if hasattr(result, 'raw'):
        output_content = str(result.raw)
    else:
        output_content = str(result)

    # Clean up any JSON artifacts and ensure readable format
    if output_content.startswith('{') and output_content.endswith('}'):
        # If it looks like JSON, try to extract the readable content
        try:
            import json
            data = json.loads(output_content)
            if 'final_answer' in data:
                output_content = data['final_answer']
            elif 'output' in data:
                output_content = data['output']
            elif 'Action' in data:
                # This is an agent action, not a final answer
                output_content = f"Agent Action: {data.get('Action', 'Unknown')}\nDetails: {json.dumps(data, indent=2)}"
        except:
            pass  # Keep original if JSON parsing fails

    # Remove markdown code blocks that might contain JSON
    import re
    # Remove ```json ... ``` blocks
    output_content = re.sub(r'```json\s*\{.*?\}\s*```', '', output_content, flags=re.DOTALL)
    # Remove any remaining ``` blocks
    output_content = re.sub(r'```\w*\s*', '', output_content)

    # Clean up extra whitespace
    output_content = re.sub(r'\n\s*\n\s*\n', '\n\n', output_content)

    with open(args.output, 'w') as f:
        f.write(output_content)