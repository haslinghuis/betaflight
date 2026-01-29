import json
import os
from datetime import datetime
from typing import Dict, Any

class BetaflightHarvester:
    """
    Data Harvester for Betaflight AI Squad

    Captures successful 'Cynic-to-Tech-Lead' corrections and saves them
    in a format suitable for fine-tuning local models like DeepSeek or Llama.
    """

    def __init__(self, file_path="betaflight_gold_dataset.jsonl"):
        self.file_path = file_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def save_learning(self, task_output: Any) -> None:
        """
        Captured after the 'SITL Test' and 'Cynic Audit' both return PASS.

        Args:
            task_output: The task output from CrewAI containing the final verified solution
        """
        try:
            # Extract the components from the task output
            entry = self._extract_training_entry(task_output)

            # Save to JSONL file
            with open(self.file_path, "a", encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            print(f"✅ Knowledge harvested: {entry.get('task', 'Unknown task')[:50]}...")

        except Exception as e:
            print(f"❌ Failed to harvest knowledge: {e}")

    def _extract_training_entry(self, task_output: Any) -> Dict[str, Any]:
        """
        Extract the training entry from the task output.

        This parses the CrewAI task output to extract:
        - The original task/instruction
        - The critique (Cynic's feedback)
        - The final solution (Tech Lead's corrected code)
        """
        # Get the raw output - this contains the inter-agent conversation
        raw_output = getattr(task_output, 'raw', '') or str(task_output)

        # Extract components using heuristics
        instruction = self._extract_instruction(raw_output)
        critique = self._extract_critique(raw_output)
        solution = self._extract_solution(raw_output)

        entry = {
            "instruction": instruction,
            "critique": critique,
            "solution": solution,
            "context": "Betaflight Firmware v4.6-dev - STM32 flight controller",
            "timestamp": datetime.now().isoformat(),
            "source": "betaflight_ai_squad",
            "verified": True,  # Only called after SITL + Cynic pass
            "agent_interactions": raw_output[:2000]  # Truncate for storage
        }

        return entry

    def _extract_instruction(self, raw_output: str) -> str:
        """Extract the original task instruction."""
        # Look for task descriptions or requirements
        lines = raw_output.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['implement', 'create', 'add', 'fix', 'task:']):
                return line.strip()
        return "Implement Betaflight firmware feature"

    def _extract_critique(self, raw_output: str) -> str:
        """Extract the Cynic's critique/feedback."""
        # Look for Cynic's feedback or rejection reasons
        if 'cynic' in raw_output.lower():
            # Find the section with Cynic's analysis
            start = raw_output.lower().find('cynic')
            if start != -1:
                end = raw_output.find('\n\n', start)
                if end == -1:
                    end = len(raw_output)
                return raw_output[start:end].strip()

        # Fallback: look for common critique patterns
        critique_patterns = [
            'blocking', 'hang', 'scheduler', 'interrupt', 'atomic',
            'race condition', 'deadlock', 'memory leak', 'unsafe'
        ]

        for pattern in critique_patterns:
            if pattern in raw_output.lower():
                # Extract surrounding context
                idx = raw_output.lower().find(pattern)
                start = max(0, idx - 100)
                end = min(len(raw_output), idx + 200)
                return f"Found {pattern} issue: {raw_output[start:end].strip()}"

        return "Code passed Cynic audit with no blocking violations"

    def _extract_solution(self, raw_output: str) -> str:
        """Extract the final corrected solution."""
        # Look for code blocks or final implementation
        if '```c' in raw_output:
            # Extract C code blocks
            start = raw_output.find('```c')
            end = raw_output.find('```', start + 3)
            if end != -1:
                return raw_output[start:end + 3].strip()

        # Look for final code or solution sections
        lines = raw_output.split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            if line.strip().startswith('//') or '#include' in line or 'void ' in line or 'int ' in line:
                in_code = True
                code_lines.append(line)
            elif in_code and line.strip() == '':
                continue
            elif in_code and not line.strip().startswith(' ') and not line.strip().startswith('\t'):
                break

        if code_lines:
            return '\n'.join(code_lines)

        # Fallback: return the last part of the output
        return raw_output[-500:].strip()

    def mark_human_approved(self, entry_index: int = -1) -> None:
        """
        Mark the most recent entry (or specific index) as human-approved.
        Only human-approved entries should be used for fine-tuning.
        """
        try:
            # Read all entries
            entries = []
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))

            # Mark the specified entry as human-approved
            if entries and 0 <= entry_index < len(entries):
                entries[entry_index]['human_approved'] = True
            elif entries and entry_index == -1:
                entries[-1]['human_approved'] = True

            # Rewrite the file
            with open(self.file_path, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')

            print(f"✅ Entry {entry_index} marked as human-approved")

        except Exception as e:
            print(f"❌ Failed to mark human approval: {e}")

# Global harvester instance
harvester = BetaflightHarvester()