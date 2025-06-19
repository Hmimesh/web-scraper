# Web Scraper

This project scrapes municipal contact information from Israeli websites. It extracts phone numbers, emails and names, then normalizes the data so it can be saved in JSON, CSV or Excel format.

## Features

- Crawls contact pages listed in `data/cities_links.csv` using Playwright
- Parses free text with heuristics to find personal names, emails and phone numbers
- Transliterates English names to Hebrew using names fetched from data.gov.il
- Optional ChatGPT integration for guessing Hebrew names when heuristics fail
- Produces logs and incremental JSON files under `logs/` and `data/incremental_results`

## Requirements

- Python 3.11+
- [Playwright](https://playwright.dev/python/) for browser automation
- `pandas` for data handling
- `beautifulsoup4` and `requests` for page parsing
- `openpyxl` to export Excel files
- `nameparser` for name parsing helpers
- `openai` (optional) if using ChatGPT

Install dependencies with:

```bash
pip install pandas playwright beautifulsoup4 requests openpyxl nameparser openai
playwright install
```

## Usage

Run the main scraper which fetches contact pages and stores results:

```bash
python src/database_func.py
```

After scraping, create consolidated output files:

```bash
python src/all_contacts.py
```

Unique names can be extracted from the logs with:

```bash
python src/name_pull.py
```

## ChatGPT Integration

Set the `OPENAI_API_KEY` environment variable to allow the scraper to query ChatGPT when it cannot determine a Hebrew name. This step is optional; without the variable the code falls back to built‑in heuristics.

## Testing

Run the unit tests with:

```bash
pytest -q
```

