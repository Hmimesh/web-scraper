#!/bin/bash
# Run scraping, name translation and CSV/Excel conversion automatically

set -e

# Location of the scraped JSON
OUT="output/contacts.json"

# 1. Scrape all sites and apply ChatGPT translations
python3 ./src/database_func.py "$OUT"

# 2. Convert the JSON into CSV and Excel files
python3 ./src/all_contacts.py "$OUT"

# 3. Extract unique names from the logs
python3 ./src/name_pull.py
