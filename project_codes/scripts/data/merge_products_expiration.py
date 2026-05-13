"""Merge products with expiration dates from CSV files."""
from __future__ import annotations

import csv
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Any


def normalize_barcode(barcode: str) -> str:
	"""Normalize barcode by removing leading zeros."""
	if not barcode or not isinstance(barcode, str):
		return ""
	barcode = str(barcode).strip()
	match = re.match(r'^0+(.+)$', barcode)
	if match:
		return match.group(1)
	return barcode


def parse_date(date_str: str) -> tuple[str, str]:
	"""Parse date in dd/mm/yyyy format. Returns (iso_date, original)."""
	if not date_str or not isinstance(date_str, str):
		return ("", "")
    
	date_str = str(date_str).strip()
	if not date_str:
		return ("", "")
    
	for fmt in ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%m/%d/%Y"]:
		try:
			dt = datetime.strptime(date_str, fmt)
			return (dt.strftime("%Y-%m-%d"), date_str)
		except ValueError:
			continue
    
	return ("", date_str)


def run_merge(products_xlsx: Path, expiration_csv: Path, out_dir: Path) -> dict[str, Any]:
	"""Merge products with expiration data."""
	import openpyxl
    
	wb = openpyxl.load_workbook(str(products_xlsx))
	ws = wb.active
    
	products = {}
	headers = []
	for i, row in enumerate(ws.iter_rows(values_only=True)):
		if i == 0:
			headers = [h or f"col_{j}" for j, h in enumerate(row)]
			barcode_idx = next((j for j, h in enumerate(headers) if "barcode" in str(h).lower()), 0)
			continue
		if not any(row):
			break
		barcode = str(row[barcode_idx] or "").strip()
		if barcode and barcode != "None":
			products[barcode] = row
    
	expirations = {}
	bad_rows = []
	with open(expiration_csv, encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			barcode_raw = str(row.get('barcode', '') or '').strip()
			if not barcode_raw:
				continue
            
			barcode_norm = normalize_barcode(barcode_raw)
			date_str = str(row.get('expiration_date', '') or '').strip()
			date_parsed, date_original = parse_date(date_str)
            
			if not date_parsed:
				bad_rows.append({'barcode': barcode_norm, 'barcode_raw': barcode_raw, 'original_value': date_original})
			else:
				expirations[barcode_norm] = {'barcode_raw': barcode_raw, 'expiration_date': date_parsed, 'raw_value': date_original}
    
	output_rows = []
	matched = 0
	for barcode_raw, product_row in products.items():
		barcode_norm = normalize_barcode(barcode_raw)
		output_row = list(product_row)
		if len(headers) <= len(output_row):
			output_row.append(barcode_norm)
		else:
			output_row.insert(-1, barcode_norm)
        
		if barcode_norm in expirations:
			exp_data = expirations[barcode_norm]
			output_row.append(exp_data['expiration_date'])
			output_row.append(exp_data.get('raw_value', ''))
			matched += 1
		else:
			output_row.append('')
			output_row.append('')
		output_rows.append(output_row)
    
	out_headers = list(headers) + ['barcode_norm', 'expiration_date', 'date_repaired']
	output_file = out_dir / "products_with_expiration.csv"
	with open(output_file, 'w', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerow(out_headers)
		for row in output_rows:
			writer.writerow(row)
    
	bad_file = out_dir / "bad_expiration_rows.csv"
	with open(bad_file, 'w', newline='', encoding='utf-8') as f:
		writer = csv.DictWriter(f, fieldnames=['barcode', 'barcode_raw', 'original_value'])
		writer.writeheader()
		writer.writerows(bad_rows)
    
	return {
		"products_total": len(products),
		"expiration_rows_clean": matched,
		"expiration_rows_bad": len(bad_rows),
		"expiration_dates_repaired": 0,
		"files": {
			"products_with_expiration": str(output_file),
			"bad_expiration_rows": str(bad_file),
		}
	}


def main() -> None:
	"""Entry point."""
	workspace_root = Path(__file__).resolve().parents[3]
	data_dir = workspace_root / "data"
	summary = run_merge(data_dir / "products.xlsx", data_dir / "expiration.csv", data_dir / "outputs")
	(data_dir / "outputs" / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
	print(f"Processed {summary['products_total']} products. Matched: {summary['expiration_rows_clean']}")


if __name__ == "__main__":
	main()
