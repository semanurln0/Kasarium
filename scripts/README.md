# Phase 1 Data Pipeline

This is the documentation for the Phase 1 data preparation scripts. The pipeline reads `products.xlsx` and `expiration.csv` from the repository root, normalises barcodes and dates, merges the two datasets, and writes clean CSVs ready for database import.

## Scripts Overview

- **`__init__.py`**: Makes `scripts/` a Python package.
- **`validate_inputs.py`**: Checks that both input files exist and have the expected structure before processing begins.
- **`merge_products_expiration.py`**: Normalises barcodes, parses / repairs expiration dates, and produces the output files.
- **`run_phase1.py`**: Orchestrates the full pipeline; run as `python -m scripts.run_phase1` from the repository root.

## Running the Pipeline

```bash
# Install dependencies (once)
pip install -r requirements.txt

# Run Phase 1
python -m scripts.run_phase1
```

## Input Files

| File | Required columns / structure |
|---|---|
| `products.xlsx` | `Barcode`, `Name`, `Sales Price`, `Sales Description`, `Description for the website`, `Origin`, `Website Product Category` |
| `expiration.csv` | Row 0: description (skipped). Row 1: header (`Brūkšninis kodas`, `Galiojimo Pabaigos Data`). Row 2+: data. |

## Output Files (`data/`)

| File | Description |
|---|---|
| `products_clean.csv` | Products with normalised `barcode_norm` column. |
| `expiration_normalized.csv` | Expiration rows with parsed ISO-8601 dates. |
| `products_with_expiration.csv` | Left-join: products repeated per expiration row. |
| `bad_expiration_rows.csv` | Rows whose dates could not be parsed or repaired. |
| `run_summary.json` | Counts of processed / bad / repaired rows and output paths. |

## Barcode Normalisation

Barcodes are reduced to digit-only strings. Excel scientific-notation values (e.g. `4.03e+12`) and float suffixes (`.0`) are handled automatically.

## Date Parsing

Dates are parsed primarily as `dd/mm/yyyy`. Common malformed strings are repaired:

- **Invalid day for month** (e.g. `30/02/2027`): day is clamped to the month maximum (`28` or `29` for February).
- **Fused separator** (e.g. `10/072025` → `10/07/2025`): missing slash between month and year is inserted.

If a date cannot be parsed or repaired it is recorded in `bad_expiration_rows.csv` with `expiration_date = NULL`.
