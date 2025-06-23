#!/bin/bash
# Post-processing after running main.sh
set -e

INPUT="all_contacts.csv"
OUTPUT="extracted_contacts_fillter.csv"

if [ -f "$INPUT" ]; then
    python3 ./src/extraction.py "$INPUT" "$OUTPUT"
else
    echo "Missing $INPUT - run main.sh first" >&2
    exit 1
fi
