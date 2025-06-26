#!/bin/bash
# Run scraping, name translation and CSV/Excel conversion automatically

set -e

# Prompt user for output filename or generate timestamped one
echo "Enter output filename (or press Enter for timestamped filename):"
read -r USER_INPUT

if [ -z "$USER_INPUT" ]; then
    # Generate timestamped filename
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    OUT="output/contacts_${TIMESTAMP}.json"
    echo "Using timestamped filename: $OUT"
else
    # Use user input, ensure it has .json extension
    if [[ "$USER_INPUT" != *.json ]]; then
        USER_INPUT="${USER_INPUT}.json"
    fi
    # Add output/ prefix if not already there
    if [[ "$USER_INPUT" != output/* ]] && [[ "$USER_INPUT" != /* ]]; then
        OUT="output/$USER_INPUT"
    else
        OUT="$USER_INPUT"
    fi
    echo "Using filename: $OUT"
fi

# Create output directory if it doesn't exist
mkdir -p output

# 1. Scrape all sites and apply ChatGPT translations
echo "Starting scraping process..."
python3 ./src/database_func.py "$OUT"

# 2. Convert the JSON into CSV and Excel files
echo "Converting to CSV and Excel..."
python3 ./src/all_contacts.py "$OUT"

# 3. Extract unique names from the logs
echo "Extracting unique names..."
python3 ./src/name_pull.py

echo "✅ Process completed! Files saved:"
echo "   JSON: $OUT"
echo "   CSV: all_contacts.csv"
echo "   Excel: all_contacts.xlsx"
