"""Management command to import Phase 1 CSV output into the database."""
from __future__ import annotations

import csv
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

_SCIENTIFIC_RE = re.compile(r"^[0-9]+\.?[0-9]*[eE][+]?[0-9]+$")

from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import Product, ProductCategory
from apps.inventory.models import ExpirationEntry

_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y"]


def _parse_date(value: str):
    """Try known date formats; return a date object or None."""
    v = value.strip()
    if not v:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_barcode(value: str) -> str:
    """Keep digits only, preserving leading zeros.

    Also handles Excel artefacts written by pandas dtype=str:
    - Float suffix  e.g. "4032489019859.0"  → "4032489019859"
    - Scientific notation e.g. "4.032489019859e+12" → "4032489019859"
      (uses Decimal to avoid float precision loss on 13+ digit barcodes)
    """
    s = value.strip()
    if not s:
        return ""
    if _SCIENTIFIC_RE.match(s):
        try:
            s = str(int(Decimal(s)))
        except (ValueError, OverflowError, InvalidOperation):
            pass
    elif s.endswith(".0"):
        s = s[:-2]
    return re.sub(r"\D", "", s)


class Command(BaseCommand):
    help = "Import data/outputs/products_with_expiration.csv into the database (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            default=None,
            help="Path to products_with_expiration.csv (default: data/outputs/products_with_expiration.csv)",
        )

    def handle(self, *args, **options):
        # Walk upward from this file to find manage.py (marks Django directory)
        _here = Path(__file__).resolve()
        manage_py_dir = _here
        for parent in _here.parents:
            if (parent / "manage.py").exists():
                manage_py_dir = parent
                break
        
        # Go up from django/ to workspace root
        workspace_root = manage_py_dir.parent.parent
        csv_path = Path(options["csv"]) if options["csv"] else workspace_root / "data" / "outputs" / "products_with_expiration.csv"

        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        products_created = 0
        products_updated = 0
        expiry_created = 0

        # utf-8-sig handles both plain UTF-8 and UTF-8-with-BOM files (e.g.
        # exported from Excel), preventing the BOM from being prepended to the
        # first column name and causing every row to be silently skipped.
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Barcode: use ONLY the Barcode column (ignore barcode_norm)
                barcode = _normalize_barcode(row.get("Barcode", ""))
                if not barcode:
                    continue  # Skip discount / header rows with no barcode

                name = row.get("Name", "").strip()
                if not name:
                    continue  # Skip rows with no product name

                # Category
                category_name = row.get("Website Product Category", "").strip()
                category = None
                if category_name:
                    category, _ = ProductCategory.objects.get_or_create(name=category_name)

                # Price
                raw_price = row.get("Sales Price", "0").strip()
                try:
                    price = Decimal(raw_price)
                except (InvalidOperation, ValueError):
                    price = Decimal("0.00")

                defaults = {
                    "name": name,
                    "sales_price": price,
                    "sales_description": row.get("Sales Description", "").strip(),
                    "website_description": row.get("Description for the website", "").strip(),
                    "origin": row.get("Origin", "").strip(),
                    "category": category,
                }

                product, created = Product.objects.update_or_create(
                    barcode=barcode,
                    defaults=defaults,
                )
                if created:
                    products_created += 1
                else:
                    products_updated += 1

                # Expiration date — must be a date object (or None), never a string
                exp_date_raw = row.get("expiration_date", "").strip()
                exp_date: date | None = _parse_date(exp_date_raw)

                # raw_value must never be NULL; derive from available columns or use ""
                raw_value = (
                    row.get("expiration_date", "")
                    or row.get("date_repaired", "")
                    or ""
                ).strip()

                # Idempotent: skip if (product, expiration_date, raw_value, source) already exists
                if not ExpirationEntry.objects.filter(
                    product=product,
                    expiration_date=exp_date,
                    raw_value=raw_value,
                    source="phase1_import",
                ).exists():
                    ExpirationEntry.objects.create(
                        product=product,
                        expiration_date=exp_date,
                        raw_value=raw_value,
                        source="phase1_import",
                    )
                    expiry_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {products_created} products created, "
                f"{products_updated} updated, {expiry_created} expiry entries created."
            )
        )
