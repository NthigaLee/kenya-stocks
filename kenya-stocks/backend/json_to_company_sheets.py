"""Create an Excel workbook with one sheet per company.

Each sheet summarizes the extracted financial metrics per period and
includes a link to the local PDF so you can open the original file
from Excel.

Usage (from backend directory, venv active):

    python json_to_company_sheets.py

Requires:
    - data/nse/financials.json (from extract_financials_from_pdfs.py)
    - data/nse/index_2023_2025.json (for PDF paths)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from fetch_nse_results_2023_2025 import DATA_ROOT, INDEX_FILE, NSEDocument, load_index  # type: ignore

FINANCIALS_JSON = DATA_ROOT / "financials.json"
OUTPUT_XLSX = DATA_ROOT / "financials_by_company.xlsx"


def load_financials() -> pd.DataFrame:
    if not FINANCIALS_JSON.exists():
        raise SystemExit(f"financials.json not found at {FINANCIALS_JSON}. Run extract_financials_from_pdfs.py first.")
    with FINANCIALS_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit("financials.json does not contain a list of records.")
    return pd.DataFrame(data)


def load_index_map() -> Dict[str, NSEDocument]:
    index = load_index()
    return index


def main() -> None:
    df = load_financials()
    index_map = load_index_map()

    # Add a PDF path column by looking up URL in the index
    def pdf_path_for(url: str) -> str | None:
        doc = index_map.get(url)
        if doc and doc.local_path:
            return str(Path(doc.local_path).resolve())
        return None

    df["pdf_path"] = df["url"].apply(pdf_path_for)

    # Group by company (use 'Unknown' for missing)
    df["company_safe"] = df["company"].fillna("Unknown")

    OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        for company, group in df.sort_values(["company_safe", "year", "period"]).groupby("company_safe"):
            sheet_name = company[:31] if company else "Unknown"
            # Reorder columns for readability
            cols_order: List[str] = [
                "year",
                "period",
                "title",
                "currency",
                "revenue",
                "gross_profit",
                "operating_profit",
                "profit_before_tax",
                "profit_after_tax",
                "basic_eps",
                "dividend_per_share",
                "total_assets",
                "total_equity",
                "interest_bearing_debt",
                "cash_and_equivalents",
                "operating_cash_flow",
                "capex",
                "pdf_path",
                "url",
            ]
            available_cols = [c for c in cols_order if c in group.columns]
            group[available_cols].to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Wrote per-company workbook to {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
