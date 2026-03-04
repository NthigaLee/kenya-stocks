import json
from pathlib import Path

import pandas as pd

from fetch_nse_results_2023_2025 import DATA_ROOT  # type: ignore


json_path = DATA_ROOT / "financials.json"
xlsx_path = DATA_ROOT / "financials.xlsx"

if not json_path.exists():
    raise SystemExit(f"financials.json not found at {json_path}. Run extract_financials_from_pdfs.py first.")

with json_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list):
    raise SystemExit("financials.json does not contain a list of records.")

df = pd.DataFrame(data)
xlsx_path.parent.mkdir(parents=True, exist_ok=True)
df.to_excel(xlsx_path, index=False)

print(f"Wrote {len(df)} rows to {xlsx_path}")
