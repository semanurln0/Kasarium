"""Validate input files for Phase 1 data pipeline."""
from __future__ import annotations

from pathlib import Path


def validate_inputs(products_xlsx: Path, expiration_csv: Path) -> None:
    """Validate that required input files exist.
    
    Args:
        products_xlsx: Path to products.xlsx file
        expiration_csv: Path to expiration.csv file
        
    Raises:
        FileNotFoundError: If any required file doesn't exist
    """
    errors = []
    
    if not Path(products_xlsx).exists():
        errors.append(f"Products file not found: {products_xlsx}")
    
    if not Path(expiration_csv).exists():
        errors.append(f"Expiration file not found: {expiration_csv}")
    
    if errors:
        raise FileNotFoundError("\n".join(errors))
