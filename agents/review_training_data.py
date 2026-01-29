#!/usr/bin/env python3
"""
Human Approval Tool for Betaflight AI Training Data

This script allows maintainers to review and approve harvested training data
before it's used for fine-tuning AI models.
"""

import json
import os
from harvester import BetaflightHarvester

def review_entries():
    """Display all harvested entries for review."""
    harvester = BetaflightHarvester()

    if not os.path.exists(harvester.file_path):
        print("No training data found.")
        return []

    entries = []
    with open(harvester.file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.strip():
                entry = json.loads(line)
                entries.append((i, entry))

    return entries

def display_entry(index, entry):
    """Display a single entry for review."""
    print(f"\n{'='*80}")
    print(f"Entry #{index}")
    print(f"Timestamp: {entry.get('timestamp', 'Unknown')}")
    print(f"Human Approved: {entry.get('human_approved', False)}")
    print(f"{'='*80}")

    print(f"\n📝 INSTRUCTION:")
    print(entry.get('instruction', 'No instruction'))

    print(f"\n🔍 CRITIQUE:")
    print(entry.get('critique', 'No critique'))

    print(f"\n✅ SOLUTION:")
    solution = entry.get('solution', 'No solution')
    if len(solution) > 500:
        print(solution[:500] + "...")
    else:
        print(solution)

    print(f"\n💬 AGENT INTERACTIONS (truncated):")
    interactions = entry.get('agent_interactions', 'No interactions')
    if len(interactions) > 300:
        print(interactions[:300] + "...")
    else:
        print(interactions)

def main():
    print("🤖 Betaflight AI Training Data Review Tool")
    print("=" * 50)

    entries = review_entries()

    if not entries:
        print("No entries to review.")
        return

    print(f"Found {len(entries)} entries to review.")

    for index, entry in entries:
        display_entry(index, entry)

        if not entry.get('human_approved', False):
            response = input(f"\nApprove entry #{index} for training? (y/n): ").lower().strip()
            if response == 'y':
                harvester = BetaflightHarvester()
                harvester.mark_human_approved(index)
                print(f"✅ Entry #{index} approved!")
            else:
                print(f"⏭️  Entry #{index} skipped.")
        else:
            print(f"✅ Entry #{index} already approved.")

    print("
📊 Summary:"    approved = sum(1 for _, entry in entries if entry.get('human_approved', False))
    print(f"Total entries: {len(entries)}")
    print(f"Approved for training: {approved}")
    print(f"Pending approval: {len(entries) - approved}")

if __name__ == "__main__":
    main()