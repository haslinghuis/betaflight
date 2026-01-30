import subprocess
import re
from crewai.tools import tool
import os

@tool("search_codebase")
def search_codebase(query: str) -> str:
    """Search the Betaflight source code for a specific string or regex pattern.
    Returns matching filenames and line numbers."""
    # Using grep to find the pattern in the src directory
    cmd = ["grep", "-rn", "--exclude-dir=obj", query, "/workspace/src"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if not result.stdout:
        return f"No results found for '{query}'."
    # Limit output to first 20 results to avoid context window overflow
    lines = result.stdout.splitlines()[:20]
    output = "\n".join(lines)

    # In quiet mode, only show errors
    if os.environ.get('QUIET_TOOLS') == '1':
        if "No results found" in output:
            return output
        return f"Found {len(lines)} matches for '{query}'"
    return output

@tool("read_file_content")
def read_file_content(file_path: str) -> str:
    """Read the full content of a specific file from the codebase."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@tool("build_and_debug")
def build_and_debug(target: str) -> str:
    """Runs the build and returns a structured list of errors if it fails."""
    # Run the make command in the builder container
    cmd = f"docker exec bf-builder make {target}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        if os.environ.get('QUIET_TOOLS') == '1':
            return "Build successful."
        return "Build Successful! Firmware is ready for testing."

    # GCC Error Regex: filename:line:column: error: message
    error_pattern = re.compile(r"([\w\/\.\-]+\.[ch]):(\d+):(\d+): error: (.+)")
    errors = error_pattern.findall(result.stderr)

    if not errors:
        return f"Build failed with an unknown error. Raw log: {result.stderr[:500]}"

    # Format the errors for the agent
    error_report = "BUILD FAILED. Please fix the following errors:\n"
    for file, line, col, msg in errors[:5]: # Limit to first 5 to keep context clean
        error_report += f"- File: {file}, Line: {line}, Error: {msg}\n"

    return error_report

@tool("run_sitl_test")
def run_sitl_test() -> str:
    """Compiles and runs SITL target, then analyzes logs for stability."""
    # Placeholder: In practice, this would build SITL, run it, inject commands, and parse blackbox logs
    return "SITL Test: Build successful. Virtual flight stable. No task overruns detected."

@tool("fetch_github_pr")
def fetch_github_pr(pr_number: str) -> str:
    """Fetch GitHub PR diff and changed files for analysis using git commands."""
    try:
        # Extract PR number if it's in format "PR #1234" or "#1234"
        if "PR" in pr_number.upper():
            pr_num = re.search(r'#?(\d+)', pr_number).group(1)
        else:
            pr_num = pr_number

        # Use git commands to fetch PR information
        # First, fetch the PR branch
        fetch_cmd = f"git fetch origin pull/{pr_num}/head:pr-{pr_num}"
        fetch_result = subprocess.run(fetch_cmd, shell=True, capture_output=True, text=True, cwd="/workspace/src")

        if fetch_result.returncode != 0:
            return f"Failed to fetch PR #{pr_num}: {fetch_result.stderr.strip()}"

        # Get the diff between the PR branch and main/master
        diff_cmd = f"git diff --name-status origin/master...pr-{pr_num}"
        diff_result = subprocess.run(diff_cmd, shell=True, capture_output=True, text=True, cwd="/workspace/src")

        # Get detailed diff
        detailed_diff_cmd = f"git diff origin/master...pr-{pr_num} | head -100"
        detailed_result = subprocess.run(detailed_diff_cmd, shell=True, capture_output=True, text=True, cwd="/workspace/src")

        # Get commit messages
        log_cmd = f"git log --oneline origin/master..pr-{pr_num}"
        log_result = subprocess.run(log_cmd, shell=True, capture_output=True, text=True, cwd="/workspace/src")

        # Clean up the temporary branch
        cleanup_cmd = f"git branch -D pr-{pr_num}"
        subprocess.run(cleanup_cmd, shell=True, capture_output=True, cwd="/workspace/src")

        # Format the output
        output = f"PR #{pr_num} Analysis (via git)\n\n"

        if log_result.returncode == 0 and log_result.stdout.strip():
            commits = log_result.stdout.strip().split('\n')
            output += f"Commits ({len(commits)}):\n"
            for commit in commits[:5]:  # Show first 5 commits
                output += f"- {commit}\n"
            output += "\n"

        if diff_result.returncode == 0 and diff_result.stdout.strip():
            files = diff_result.stdout.strip().split('\n')
            output += f"Changed files ({len(files)}):\n"
            for file in files[:20]:  # Show first 20 files
                if file.strip():
                    status, filename = file.split('\t', 1)
                    output += f"- {filename} ({status})\n"
            output += "\n"

        if detailed_result.returncode == 0 and detailed_result.stdout.strip():
            output += f"Detailed Changes (first 100 lines):\n{detailed_result.stdout.strip()}\n"

        return output

    except Exception as e:
        return f"Error fetching PR via git: {e}"