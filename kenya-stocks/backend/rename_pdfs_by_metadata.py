"""Rename NSE PDF files to clean, meaningful names based on metadata.

Target pattern (best-effort):

    <Company>_<PeriodEndDate>_<audited|unaudited|financials>.pdf

Examples:
    ABSA_Bank_Kenya_Plc_2023-12-31_audited.pdf
    Safaricom_PLC_2024-09-30_unaudited.pdf

We start from the index (data/nse/index_2023_2025.json), using:
- doc.title
- doc.company
- doc.period (if present)
- audited_flag classified from the title

If company/period are missing in the index, we keep the existing filename
for now (to avoid aggressive renames). We can improve this later by
parsing the first page of the PDF.

Usage (from backend directory, venv active):

    python rename_pdfs_by_metadata.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import pdfplumber

from fetch_nse_results_2023_2025 import (  # type: ignore
    DATA_ROOT,
    INDEX_FILE,
    NSEDocument,
    classify_audited_flag,
    extract_company_and_period,
    load_index,
    save_index,
)

SAFE_CHAR_RE = re.compile(r"[^A-Za-z0-9]+")


def safe_slug(s: str, max_len: int = 60) -> str:
    slug = SAFE_CHAR_RE.sub("_", s).strip("_")
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("_")
    return slug or "Unknown"


def guess_company_from_pdf(path: Path) -> Optional[str]:
    """Best-effort guess of company name from first page of the PDF.

    We look at the first few non-empty lines and return the one that
    looks most like a company name (contains Plc, Limited, Bank, etc.).
    """

    try:
        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                return None
            text = pdf.pages[0].extract_text() or ""
    except Exception:  # noqa: BLE001
        return None

    lines = [" ".join(l.split()) for l in text.splitlines() if l.strip()]
    if not lines:
        return None

    # Simple heuristics: prefer lines with these keywords
    preferred_keywords = ["plc", "limited", "ltd", "bank", "group"]

    def score(line: str) -> int:
        low = line.lower()
        return sum(1 for kw in preferred_keywords if kw in low)

    best_line = max(lines, key=score)
    if score(best_line) == 0:
        # Fallback: just use the first line if nothing matches
        best_line = lines[0]

    return best_line.strip() or None


def guess_period_from_pdf(path: Path) -> Optional[str]:
    """Best-effort guess of period/quarter from PDF text.

    We scan the first couple of pages for phrases like
    "for the year ended 31-Dec-2023" or "for the period ended 30-Sep-2025".
    """

    try:
        with pdfplumber.open(path) as pdf:
            pages = pdf.pages[:2]
            text = "\n".join((p.extract_text() or "") for p in pages)
    except Exception:  # noqa: BLE001
        return None

    if not text:
        return None

    # Simple regex for dates like 31-Dec-2023 / 31 Dec 2023 / 31/12/2023
    date_patterns = [
        r"\d{1,2}[-/ ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/ ]\d{2,4}",
        r"\d{1,2}[-/ ]\d{1,2}[-/ ]\d{2,4}",
    ]

    for pat in date_patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(0)

    return None


def derive_metadata(doc: NSEDocument, pdf_path: Path) -> tuple[str | None, str | None, str]:
    """Return (company, period, flag) from index + title + PDF content.

    period is a free-form string (e.g., "31-Dec-2023" or "2023-12-31").
    """

    company = doc.company
    period = doc.period

    # If company/period are missing in the index, try to infer from title
    if not (company and period):
        c2, p2 = extract_company_and_period(doc.title)
        company = company or c2
        period = period or p2

    # Second pass: if company is still missing, try to guess from PDF
    if not company:
        company = guess_company_from_pdf(pdf_path)

    # Second pass for period/quarter: if still missing, try PDF
    if not period:
        period = guess_period_from_pdf(pdf_path)

    flag = classify_audited_flag(doc.title)
    if flag == "unknown":
        # Fallback label when we don't see audited/unaudited clearly
        flag = "financials"

    return company, period, flag


def main() -> None:
    index = load_index()
    changed = 0

    print(f"Loaded index with {len(index)} entries from {INDEX_FILE}")

    for url, doc in list(index.items()):
        if not doc.local_path:
            continue

        old_path = Path(doc.local_path)
        if not old_path.exists():
            print(f"Skipping missing file: {old_path}")
            continue

        company, period, flag = derive_metadata(doc, old_path)

        # Only rename when we at least know the company; otherwise skip
        if not company:
            continue

        company_slug = safe_slug(company, max_len=50)
        period_slug = safe_slug(period, max_len=20) if period else "unknown_period"
        flag_slug = safe_slug(flag, max_len=20)

        new_name = f"{company_slug}_{period_slug}_{flag_slug}.pdf"
        new_path = old_path.with_name(new_name)

        # Avoid renaming if name is already in the desired form
        if old_path.name == new_name:
            continue

        # Avoid clobbering existing files; add suffix if needed
        counter = 1
        candidate = new_path
        while candidate.exists() and candidate != old_path:
            candidate = old_path.with_name(f"{company_slug}_{period_slug}_{flag_slug}_{counter}.pdf")
            counter += 1

        print(f"Renaming:\n  {old_path.name}\n  -> {candidate.name}")
        os.rename(old_path, candidate)

        # Update index entry
        doc.local_path = str(candidate)
        index[url] = doc
        changed += 1

    if changed:
        save_index(index)
        print(f"Updated index and renamed {changed} files.")
    else:
        print("No files renamed (either already clean or missing metadata).")


if __name__ == "__main__":
    main()
