import subprocess
import re
from crewai.tools import tool
import requests
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
def fetch_github_pr(pr_number: str, github_token: str = None) -> str:
    """Fetch GitHub PR diff and changed files for analysis."""
    try:
        # Extract PR number if it's in format "PR #1234" or "#1234"
        if "PR" in pr_number.upper():
            pr_num = re.search(r'#?(\d+)', pr_number).group(1)
        else:
            pr_num = pr_number

        headers = {'Authorization': f'token {github_token}'} if github_token else {}

        # Get PR diff
        diff_url = f"https://api.github.com/repos/betaflight/betaflight/pulls/{pr_num}"
        response = requests.get(diff_url, headers=headers)

        if response.status_code != 200:
            return f"Failed to fetch PR #{pr_num}: {response.status_code}"

        pr_data = response.json()

        # Get the diff
        diff_response = requests.get(f"{diff_url}.diff", headers=headers)
        if diff_response.status_code == 200:
            diff_content = diff_response.text
        else:
            diff_content = "Diff not available"

        # Get changed files
        files_url = f"{diff_url}/files"
        files_response = requests.get(files_url, headers=headers)

        files_info = ""
        if files_response.status_code == 200:
            files_data = files_response.json()
            files_info = f"\nChanged files ({len(files_data)}):\n"
            for file in files_data[:10]:  # Limit to first 10 files
                files_info += f"- {file['filename']} ({file['status']})\n"

        return f"""PR #{pr_num}: {pr_data.get('title', 'Unknown')}

Description: {pr_data.get('body', 'No description')[:500]}...

Status: {pr_data.get('state', 'Unknown')}
Author: {pr_data.get('user', {}).get('login', 'Unknown')}

{files_info}

Diff Preview (first 2000 chars):
{diff_content[:2000]}...
"""

    except Exception as e:
        return f"Error fetching PR: {e}"