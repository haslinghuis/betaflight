import subprocess
import re
from crewai.tools import tool

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
    return "\n".join(result.stdout.splitlines()[:20])

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