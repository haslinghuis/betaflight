#!/bin/bash
# Package Betaflight AI Squad Training Data

echo "Packaging Betaflight AI Squad training data..."

# Create package directory
mkdir -p package
cd package

# Copy and filter gold dataset (only human-approved entries)
if [ -f "../agents/betaflight_gold_dataset.jsonl" ]; then
    # Filter only human-approved entries
    python3 -c "
import json
import sys

approved_entries = []
try:
    with open('../agents/betaflight_gold_dataset.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                if entry.get('human_approved', False):
                    approved_entries.append(entry)
    
    with open('betaflight_gold_dataset.jsonl', 'w', encoding='utf-8') as f:
        for entry in approved_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f'Filtered {len(approved_entries)} approved entries')
except Exception as e:
    print(f'Error filtering entries: {e}')
    # Fallback: copy all entries
    cp ../agents/betaflight_gold_dataset.jsonl .
else
    echo 'No training data found' > betaflight_gold_dataset.jsonl
fi

# Create vector store placeholder (will be populated by agents)
mkdir -p vector_db
echo "Vector store will be populated during agent runs" > vector_db/README.txt

# Create metadata
cat > metadata.json << EOF
{
  "name": "Betaflight AI Squad Training Data",
  "version": "0.1.0",
  "description": "Shared intelligence for Betaflight firmware development",
  "created": "$(date -Iseconds)",
  "source": "betaflight/betaflight",
  "license": "GPL-3.0",
  "agents": [
    "Foreman", "Functional Architect", "Technical Lead", "Hardware Specialist",
    "Safety Reviewer", "Cynic", "Aero Physicist", "Librarian", "Test Pilot", "Research Agent"
  ],
  "tools": [
    "search_codebase", "read_file_content", "build_and_debug", "scan_for_violations", "run_sitl_test"
  ]
}
EOF

# Create zip file
zip -r ../betaflight_ai_training_data.zip .

cd ..
echo "Package created: betaflight_ai_training_data.zip"
echo "Upload this to GitHub releases for community sharing"