#!/bin/bash
# Post-processing after running main.sh
set -e

INPUT="contacts_attpeIMPROVED_EXTRACTION_contacts.csv"
OUTPUT="extracted_contacts_attpeIMPROVED_EXTRACTION_contacts.csv"

if [ -f "$INPUT" ]; then
    python3 ./src/extraction.py "$INPUT" "$OUTPUT"
else
    echo "Missing $INPUT - run main.sh first" >&2
    exit 1
fi
