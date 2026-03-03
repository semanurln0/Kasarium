"""Input validation for the Phase 1 data pipeline."""
from __future__ import annotations

from pathlib import Path

REQUIRED_PRODUCT_COLUMNS = [
    "Barcode",
    "Name",
    "Sales Price",
    "Sales Description",
    "Description for the website",
    "Origin",
    "Website Product Category",
]


def validate_inputs(products_xlsx: Path, expiration_csv: Path) -> None:
    """Validate that the required input files exist and have expected structure.

    Raises:
        FileNotFoundError: If a required input file is missing.
        ValueError: If a file has an unexpected structure.
    """
    if not products_xlsx.exists():
        raise FileNotFoundError(f"Products file not found: {products_xlsx}")
    if not expiration_csv.exists():
        raise FileNotFoundError(f"Expiration file not found: {expiration_csv}")

    import pandas as pd  # noqa: PLC0415 — local import to keep top-level light

    try:
        df = pd.read_excel(products_xlsx, nrows=0)
    except Exception as exc:
        raise ValueError(f"Cannot read products file '{products_xlsx}': {exc}") from exc

    missing = [c for c in REQUIRED_PRODUCT_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"products.xlsx is missing required columns: {missing}\n"
            f"Found columns: {df.columns.tolist()}"
        )

    try:
        with expiration_csv.open(encoding="utf-8", errors="replace") as fh:
            lines = [fh.readline() for _ in range(3)]
    except Exception as exc:
        raise ValueError(f"Cannot read expiration file '{expiration_csv}': {exc}") from exc

    if len(lines) < 2:
        raise ValueError(
            f"expiration.csv has too few lines (expected 1 description row, "
            f"1 header row, and at least 1 data row)."
        )
