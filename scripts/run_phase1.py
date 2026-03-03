from __future__ import annotations

import json
from pathlib import Path

from .validate_inputs import validate_inputs
from .merge_products_expiration import run_merge

def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    products_xlsx = data_dir / "products.xlsx"
    expiration_csv = data_dir / "expiration.csv"
    outputs_dir = data_dir / "outputs"

    # Remove the outputs folder and all its contents if it exists
    import shutil
    if outputs_dir.exists():
        shutil.rmtree(outputs_dir)
    outputs_dir.mkdir(exist_ok=True)

    validate_inputs(products_xlsx, expiration_csv)

    summary = run_merge(
        products_xlsx=products_xlsx,
        expiration_csv=expiration_csv,
        out_dir=outputs_dir,
    )

    (outputs_dir / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()