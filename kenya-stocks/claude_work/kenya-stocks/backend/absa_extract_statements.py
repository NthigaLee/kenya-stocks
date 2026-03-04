"""ABSA-focused statement extractor (pilot).

Goal: For ABSA Bank Kenya PDFs, detect statement pages and extract raw
statement tables (Income, Balance Sheet, Cash Flow) so we can design a
clean mapping/template.

This is an exploration tool: it writes CSVs per statement and a small
JSON index for review, not final normalized data.

Usage (from backend dir, venv active):

    python absa_extract_statements.py

Outputs under:
    ../data/absa_review/
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pdfplumber

from fetch_nse_results_2023_2025 import DATA_ROOT, NSEDocument, load_index  # type: ignore

REVIEW_ROOT = DATA_ROOT.parent / "absa_review"


@dataclass
class StatementSlice:
    company: str
    year: int
    period: str
    statement_type: str  # income | balance_sheet | cash_flow | other
    pdf_path: str
    start_page: int
    end_page: int
    currency_hint: Optional[str]
    scale_hint: Optional[str]


INCOME_PATTERNS = [
    "statement of profit or loss",
    "statement of comprehensive income",
    "income statement",
]
BALANCE_PATTERNS = [
    "statement of financial position",
    "balance sheet",
]
CASHFLOW_PATTERNS = [
    "statement of cash flows",
    "cash flow statement",
]


def detect_statement_type(text: str) -> Optional[str]:
    t = text.lower()
    if any(p in t for p in INCOME_PATTERNS):
        return "income"
    if any(p in t for p in BALANCE_PATTERNS):
        return "balance_sheet"
    if any(p in t for p in CASHFLOW_PATTERNS):
        return "cash_flow"
    return None


def find_absa_docs() -> List[NSEDocument]:
    index = load_index()
    docs = [d for d in index.values() if d.local_path]
    absa_docs = [d for d in docs if d.company and "absa" in d.company.lower()]
    # Sort by year then title
    absa_docs.sort(key=lambda d: (d.year, d.title))
    return absa_docs


def extract_statements_from_pdf(doc: NSEDocument) -> List[StatementSlice]:
    path = Path(doc.local_path)
    slices: List[StatementSlice] = []

    if not path.exists():
        print(f"  PDF missing: {path}")
        return slices

    print(f"  Inspecting {path.name}")

    try:
        with pdfplumber.open(path) as pdf:
            num_pages = len(pdf.pages)
            current_type: Optional[str] = None
            current_start: Optional[int] = None

            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                text = page.extract_text() or ""
                low = text.lower()

                stmt_type = detect_statement_type(text)
                if stmt_type:
                    # If we were already in a statement, close the previous slice
                    if current_type and current_start is not None:
                        slices.append(
                            StatementSlice(
                                company=doc.company or "ABSA",
                                year=doc.year,
                                period=doc.period or "",
                                statement_type=current_type,
                                pdf_path=str(path),
                                start_page=current_start,
                                end_page=page_num - 1,
                                currency_hint=_detect_currency_hint(low),
                                scale_hint=_detect_scale_hint(low),
                            )
                        )
                    current_type = stmt_type
                    current_start = page_num

            # Close the last open slice if any
            if current_type and current_start is not None:
                slices.append(
                    StatementSlice(
                        company=doc.company or "ABSA",
                        year=doc.year,
                        period=doc.period or "",
                        statement_type=current_type,
                        pdf_path=str(path),
                        start_page=current_start,
                        end_page=num_pages,
                        currency_hint=None,
                        scale_hint=None,
                    )
                )
    except Exception as e:  # noqa: BLE001
        print(f"  Error reading {path}: {e}")

    return slices


def _detect_currency_hint(text_lower: str) -> Optional[str]:
    if "kes" in text_lower or "ksh" in text_lower or "shillings" in text_lower:
        return "KES"
    if "usd" in text_lower or "us$" in text_lower:
        return "USD"
    return None


def _detect_scale_hint(text_lower: str) -> Optional[str]:
    if "millions" in text_lower:
        return "millions"
    if "thousands" in text_lower:
        return "thousands"
    if "billions" in text_lower:
        return "billions"
    return None


def extract_tables_for_slice(stmt: StatementSlice) -> None:
    """Write raw tables for this slice to CSV under REVIEW_ROOT.

    One CSV per statement slice; if a statement spans multiple pages we
    append all tables from those pages into one file.
    """

    pdf_path = Path(stmt.pdf_path)
    rel_name = pdf_path.stem

    out_dir = REVIEW_ROOT / stmt.company.replace(" ", "_") / f"{stmt.year}_{stmt.period or 'unknown'}"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / f"{rel_name}_{stmt.statement_type}.csv"

    rows: List[List[str]] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(stmt.start_page, stmt.end_page + 1):
                if page_num - 1 >= len(pdf.pages):
                    continue
                page = pdf.pages[page_num - 1]
                tables = page.extract_tables() or []
                for tbl in tables:
                    for row in tbl:
                        # Normalize to strings and strip
                        rows.append([ (cell or "").strip() for cell in row ])
    except Exception as e:  # noqa: BLE001
        print(f"  Error extracting tables from {pdf_path}: {e}")
        return

    if not rows:
        print(f"  No tables found for {csv_path.name}")
        return

    # Simple CSV write (no external deps beyond stdlib)
    import csv

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)

    print(f"  Wrote tables to {csv_path}")


def main() -> None:
    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)

    absa_docs = find_absa_docs()
    if not absa_docs:
        print("No ABSA docs found in index; check that downloads and renaming ran.")
        return

    print(f"Found {len(absa_docs)} ABSA documents in index")

    all_slices: List[StatementSlice] = []

    for doc in absa_docs:
        print(f"\n=== {doc.year} :: {doc.title} ===")
        slices = extract_statements_from_pdf(doc)
        for s in slices:
            all_slices.append(s)
            extract_tables_for_slice(s)

    # Write a small JSON index of slices for reference
    index_path = REVIEW_ROOT / "absa_statement_slices.json"
    with index_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in all_slices], f, indent=2, ensure_ascii=False)

    print(f"\nWrote slice index to {index_path}")


if __name__ == "__main__":
    main()
