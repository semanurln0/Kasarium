"""Merge products and expiration data for Phase 1 pipeline."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from dateutil.parser import ParserError
from dateutil.parser import parse as dateutil_parse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRODUCT_COLUMNS = [
    "Barcode",
    "Name",
    "Sales Price",
    "Sales Description",
    "Description for the website",
    "Origin",
    "Website Product Category",
]

# Months that cannot have more than N days (used for date repair).
_MONTH_MAX_DAYS = {
    1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
}

# ---------------------------------------------------------------------------
# Barcode normalisation
# ---------------------------------------------------------------------------

_SCIENTIFIC_RE = re.compile(r"^([0-9]+\.?[0-9]*)([eE][+]?([0-9]+))$")


def _normalize_barcode(raw: Any) -> str:
    """Return a digits-only barcode string.

    Handles:
    - Plain integer / float stored by Excel  (e.g. 4032489019859 -> "4032489019859")
    - Scientific notation strings  (e.g. "4.03e+12" -> integer via float conversion)
    - Strings with non-digit characters stripped
    - NaN / None -> empty string ""
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return ""
    s = str(raw).strip()
    # Excel sometimes stores large barcodes as floats, e.g. 4032489019859.0
    m = _SCIENTIFIC_RE.match(s)
    if m:
        try:
            s = str(int(float(s)))
        except (ValueError, OverflowError):
            pass
    elif s.endswith(".0"):
        s = s[:-2]
    # Strip any remaining non-digit characters
    digits = re.sub(r"\D", "", s)
    return digits


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

def _repair_date(day: int, month: int, year: int) -> date | None:
    """Attempt to repair a dd/mm/yyyy triple that contains an invalid day.

    Strategy: clamp day to the maximum for that month/year.
    Returns None if the triple is fundamentally invalid.
    """
    if not (1 <= month <= 12):
        return None
    if year < 1900 or year > 2100:
        return None
    # Determine true max day (handle leap year for February)
    if month == 2:
        import calendar  # noqa: PLC0415
        max_day = 29 if calendar.isleap(year) else 28
    else:
        max_day = _MONTH_MAX_DAYS[month]
    clamped_day = min(day, max_day)
    try:
        return date(year, month, clamped_day)
    except ValueError:
        return None


def _parse_date(raw: Any) -> tuple[date | None, bool]:
    """Parse a date value from the expiration CSV.

    Returns:
        (parsed_date_or_None, was_repaired)
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None, False

    if isinstance(raw, (date,)):
        return raw, False

    # pandas Timestamp
    if hasattr(raw, "date"):
        try:
            return raw.date(), False
        except Exception:
            pass

    s = str(raw).strip()
    if not s:
        return None, False

    # Attempt to repair missing separator: dd/mmyyyy pattern
    # e.g. "10/072025" -> "10/07/2025"
    fused_re = re.match(r"^(\d{1,2})/(\d{2})(\d{4})$", s)
    if fused_re:
        s = f"{fused_re.group(1)}/{fused_re.group(2)}/{fused_re.group(3)}"

    # Primary format: dd/mm/yyyy  (also handles d/m/yyyy)
    parts = re.split(r"[/\-\.]", s)
    if len(parts) == 3:
        try:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            dt = date(y, m, d)  # may raise ValueError for invalid dates
            return dt, False
        except ValueError:
            # Try to repair (e.g. day 30 in February)
            try:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                repaired = _repair_date(d, m, y)
                if repaired is not None:
                    return repaired, True
            except (ValueError, TypeError):
                pass

    # Fallback: dateutil with dayfirst=True
    try:
        dt = dateutil_parse(s, dayfirst=True).date()
        return dt, False
    except (ParserError, OverflowError, ValueError):
        pass

    return None, False


# ---------------------------------------------------------------------------
# Reading input files
# ---------------------------------------------------------------------------

def _read_products(products_xlsx: Path) -> pd.DataFrame:
    """Read and clean the products spreadsheet."""
    df = pd.read_excel(products_xlsx, dtype=str)
    df = df[PRODUCT_COLUMNS].copy()
    df["barcode_norm"] = df["Barcode"].apply(_normalize_barcode)
    df = df.sort_values("barcode_norm", kind="stable").reset_index(drop=True)
    return df


def _read_expiration(expiration_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read expiration CSV and return (clean_df, bad_rows_df).

    The CSV has:
    - Row 0: free-text description (skip)
    - Row 1: column headers  (Brūkšninis kodas, Galiojimo Pabaigos Data)
    - Row 2+: data

    Handles leading commas (extra empty columns) and messy header rows.
    """
    # Read with skiprows=1 so the second line becomes the header.
    # Use dtype=str to avoid pandas auto-converting barcodes to floats.
    raw = pd.read_csv(
        expiration_csv,
        skiprows=1,
        header=0,
        dtype=str,
        encoding="utf-8",
        on_bad_lines="skip",
    )

    # Drop columns that are entirely empty (artefact of leading commas)
    raw = raw.dropna(axis=1, how="all")
    raw.columns = [c.strip() for c in raw.columns]

    # The first non-empty column is barcode; second is expiration date.
    # Rename to canonical names regardless of Lithuanian header text.
    cols = raw.columns.tolist()
    if len(cols) < 2:
        raise ValueError(
            "expiration.csv: expected at least 2 data columns after header, "
            f"found: {cols}"
        )
    raw = raw.rename(columns={cols[0]: "barcode_raw", cols[1]: "expiration_raw"})
    # Keep only the two relevant columns
    raw = raw[["barcode_raw", "expiration_raw"]].copy()
    # Drop rows where both barcode and date are empty
    raw = raw.dropna(subset=["barcode_raw"]).reset_index(drop=True)
    raw["barcode_raw"] = raw["barcode_raw"].str.strip()
    raw["expiration_raw"] = raw["expiration_raw"].fillna("").str.strip()
    # Remove any row that looks like a header repeat
    raw = raw[~raw["barcode_raw"].str.lower().str.contains("barcode|brūkšninis|kodas", na=False)]
    raw = raw.reset_index(drop=True)

    # Normalise barcodes
    raw["barcode_norm"] = raw["barcode_raw"].apply(_normalize_barcode)

    # Parse dates
    parsed_dates: list[date | None] = []
    repaired_flags: list[bool] = []
    for val in raw["expiration_raw"]:
        dt, repaired = _parse_date(val)
        parsed_dates.append(dt)
        repaired_flags.append(repaired)

    raw["expiration_date"] = [d.isoformat() if d else None for d in parsed_dates]
    raw["date_repaired"] = repaired_flags

    # Split into good and bad
    bad_mask = raw["expiration_date"].isna()
    bad_rows = raw[bad_mask][["barcode_norm", "barcode_raw", "expiration_raw"]].copy()
    bad_rows = bad_rows.rename(
        columns={"barcode_norm": "barcode", "expiration_raw": "original_value"}
    )

    clean = raw[~bad_mask][["barcode_norm", "expiration_date", "date_repaired"]].copy()
    clean = clean.rename(columns={"barcode_norm": "barcode"})
    clean = clean.sort_values(["barcode", "expiration_date"], kind="stable").reset_index(drop=True)

    return clean, bad_rows


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_merge(
    products_xlsx: Path,
    expiration_csv: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Run the full merge pipeline and write output files.

    Returns a summary dict written to run_summary.json.
    """
    products = _read_products(products_xlsx)
    expiration, bad_rows = _read_expiration(expiration_csv)

    # ---- Write clean input snapshots ----------------------------------------
    products_clean_path = out_dir / "products_clean.csv"
    products.to_csv(products_clean_path, index=False, encoding="utf-8")

    expiration_norm_path = out_dir / "expiration_normalized.csv"
    expiration.to_csv(expiration_norm_path, index=False, encoding="utf-8")

    # ---- Merge: left join products -> expiration (repeat per expiration row) --
    merged = products.merge(
        expiration,
        left_on="barcode_norm",
        right_on="barcode",
        how="left",
    )
    # Drop the duplicate barcode column from the right side
    if "barcode" in merged.columns and "barcode_norm" in merged.columns:
        merged = merged.drop(columns=["barcode"])

    merged = merged.sort_values(
        ["barcode_norm", "expiration_date"], kind="stable"
    ).reset_index(drop=True)

    merged_path = out_dir / "products_with_expiration.csv"
    merged.to_csv(merged_path, index=False, encoding="utf-8")

    # ---- Bad rows report -----------------------------------------------------
    bad_path = out_dir / "bad_expiration_rows.csv"
    bad_rows.to_csv(bad_path, index=False, encoding="utf-8")

    # ---- Summary -------------------------------------------------------------
    repaired_count = int(expiration["date_repaired"].sum())
    summary: dict[str, Any] = {
        "products_total": len(products),
        "expiration_rows_clean": len(expiration),
        "expiration_rows_bad": len(bad_rows),
        "expiration_dates_repaired": repaired_count,
        "merged_rows": len(merged),
        "outputs": {
            "products_clean": str(products_clean_path),
            "expiration_normalized": str(expiration_norm_path),
            "products_with_expiration": str(merged_path),
            "bad_expiration_rows": str(bad_path),
        },
    }
    return summary
