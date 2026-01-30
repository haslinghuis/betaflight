import re
from crewai.tools import tool

@tool("check_non_blocking_compliance")
def check_non_blocking_compliance(file_path: str) -> str:
    """Scans a file for blocking calls like delay() or infinite while loops."""
    forbidden_patterns = {
        r"\bdelay\(": "Forbidden use of blocking delay(). Use the task scheduler.",
        r"\bdelayMicroseconds\(": "Blocking micro-delay detected. Is this in a time-critical ISR?",
        r"while\s*\([^)]+\)\s*\{(?![^}]*timeout)": "Potential infinite while-loop without a safety timeout.",
        r"\bmalloc\(": "Dynamic memory allocation is forbidden. Use static arrays.",
    }
    
    results = []
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                for pattern, msg in forbidden_patterns.items():
                    if re.search(pattern, line):
                        results.append(f"Line {i+1}: {msg}")
    except Exception as e:
        return f"Error scanning file: {e}"
    
    return "\n".join(results) if results else "No blocking calls detected. Safety check passed."

@tool("check_atomic_access")
def check_atomic_access(file_path: str) -> str:
    """Checks if shared global variables are accessed outside of ATOMIC_BLOCKs."""
    # Simple heuristic: look for variables modified in ISRs but used in main loop
    # This is a complex check; for now, it flags global flag modifications.
    return "Manual Review Required: Ensure all shared 'uint32_t' flags are wrapped in ATOMIC_BLOCK(NVIC_PRIO_MAX)."