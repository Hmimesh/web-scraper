# AGENT Instructions

This repository is scraped automatically using Codex agents. Contributors must
follow these rules so that automated scrapers keep working correctly:

- **Run `pytest -q`** before every commit to ensure all tests pass.
- **Keep code in `src/`** so the import paths remain stable.
- **Follow PEP8** (e.g. via `black` or `flake8`) for consistent formatting.

These brief points tell Codex how to maintain code quality when updating the
project.
