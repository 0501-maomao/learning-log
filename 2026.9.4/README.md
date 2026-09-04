# Data Cleaning Project

This folder contains a small, reusable Python data-cleaning project.

## What It Does

- Reads CSV, JSON, JSONL, XLS, and XLSX files.
- Normalizes column names.
- Trims messy whitespace.
- Removes exact duplicate rows.
- Standardizes email, phone, city, status, date, and amount fields.
- Handles missing and invalid values with explicit rules.
- Writes a cleaned CSV file.
- Writes a data-quality report as JSON.
- Writes logs for each run.
- Optionally writes an Excel file when `openpyxl` is installed.

## Folder Layout

```text
2026.9.4/
  data/
    raw/
      dirty_customers.csv
    processed/
  logs/
  reports/
  src/
    data_cleaning/
      cleaner.py
      cli.py
      config.py
      io.py
      logging_utils.py
  tests/
    test_cleaner.py
  pyproject.toml
  requirements.txt
```

## Quick Start

```bash
cd 2026.9.4
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m data_cleaning.cli --input data/raw/dirty_customers.csv
```

Expected outputs:

```text
data/processed/cleaned_customers.csv
data/processed/cleaned_customers.xlsx
reports/quality_report.json
logs/data_cleaning.log
```

If `openpyxl` is not installed, the Excel output is skipped and the CSV/report are still created.

## Run Tests

```bash
pytest
```

## Notes

This project is intentionally not uploaded or pushed anywhere. It only creates local files under this folder.
