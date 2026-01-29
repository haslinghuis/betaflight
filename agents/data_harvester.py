#!/usr/bin/env python3
"""
Data Harvester for Betaflight AI Squad

This script captures successful 'Cynic-to-Tech-Lead' corrections
and saves them in a format suitable for fine-tuning local models.
"""

import json
import os
from datetime import datetime

class DataHarvester:
    def __init__(self, output_file="gold_dataset.jsonl"):
        self.output_file = output_file
        self.entries = []

    def add_entry(self, input_prompt, corrected_code, context=""):
        """Add a new training entry."""
        entry = {
            "input": input_prompt,
            "output": corrected_code,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "source": "betaflight_ai_squad"
        }
        self.entries.append(entry)

    def save(self):
        """Save all entries to the JSONL file."""
        with open(self.output_file, 'a') as f:
            for entry in self.entries:
                f.write(json.dumps(entry) + '\n')
        print(f"Saved {len(self.entries)} entries to {self.output_file}")
        self.entries = []  # Clear for next batch

# Example usage (integrate into main.py after successful correction)
if __name__ == "__main__":
    harvester = DataHarvester()

    # Example entry
    harvester.add_entry(
        input_prompt="Write a DMA-based SPI driver for the OSD.",
        corrected_code="#include <stdint.h>\n// Corrected DMA SPI implementation\n...",
        context="Fixed race condition in ISR"
    )

    harvester.save()