import subprocess
from langchain.tools import tool

class BetaflightTools:

    @tool("search_codebase")
    def search_codebase(query: str):
        """Searches the Betaflight /src directory for a specific string or regex.
        Returns filenames and line numbers."""
        # Using grep to find the pattern in the src directory
        cmd = ["grep", "-rn", "--exclude-dir=obj", query, "/workspace/src"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if not result.stdout:
            return f"No results found for '{query}'."
        # Limit output to first 20 results to avoid context window overflow
        return "\n".join(result.stdout.splitlines()[:20])

    @tool("read_file_content")
    def read_file_content(file_path: str):
        """Reads the full content of a specific file. Use this after finding a file via search_codebase."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"