"""Extract key financial metrics from NSE PDF results.

Usage (from backend directory, with venv active):

    pip install -r requirements.txt  # once, to get pdfplumber
    python extract_financials_from_pdfs.py

This will:
- Read data/nse/index_2023_2025.json (also used by 2015_2022 script)
- For each document with a local_path
- Extract text using pdfplumber
- Try to parse core metrics via simple regex heuristics
- Write results to data/nse/financials.json (append/overwrite)

This is a first-pass extractor; we'll refine company-by-company.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pdfplumber

from fetch_nse_results_2023_2025 import DATA_ROOT, INDEX_FILE, NSEDocument, load_index  # type: ignore

OUTPUT_FILE = DATA_ROOT / "financials.json"


@dataclass
class FinancialSnapshot:
    url: str
    year: int
    title: str
    company: Optional[str]
    period: Optional[str]
    currency: Optional[str]

    revenue: Optional[float]
    gross_profit: Optional[float]
    operating_profit: Optional[float]
    profit_before_tax: Optional[float]
    profit_after_tax: Optional[float]

    basic_eps: Optional[float]
    dividend_per_share: Optional[float]

    total_assets: Optional[float]
    total_equity: Optional[float]
    interest_bearing_debt: Optional[float]
    cash_and_equivalents: Optional[float]

    operating_cash_flow: Optional[float]
    capex: Optional[float]


NUMBER_RE = re.compile(r"([-+]?[0-9][0-9,]*\.?[0-9]*)")


def _parse_number(text: str) -> Optional[float]:
    m = NUMBER_RE.search(text.replace("\u00a0", " "))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def extract_text_from_pdf(path: Path) -> str:
    chunks: List[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t:
                chunks.append(t)
    return "\n".join(chunks)


def find_line(lines: List[str], *patterns: str) -> Optional[str]:
    patterns_l = [p.lower() for p in patterns]
    for line in lines:
        low = line.lower()
        if any(p in low for p in patterns_l):
            return line
    return None


def extract_metrics_from_text(text: str) -> Dict[str, Optional[float]]:
    lines = [" ".join(l.split()) for l in text.splitlines() if l.strip()]

    def num_for(*patterns: str) -> Optional[float]:
        line = find_line(lines, *patterns)
        return _parse_number(line) if line else None

    metrics: Dict[str, Optional[float]] = {
        "revenue": num_for("revenue", "turnover", "total income"),
        "gross_profit": num_for("gross profit"),
        "operating_profit": num_for("operating profit", "profit from operations"),
        "profit_before_tax": num_for("profit before tax", "profit before income tax"),
        "profit_after_tax": num_for("profit after tax", "profit for the year", "profit for the period"),
        "basic_eps": num_for("basic earnings per share", "basic eps"),
        "dividend_per_share": num_for("dividend per share", "dps"),
        "total_assets": num_for("total assets"),
        "total_equity": num_for("total equity", "shareholders' funds", "shareholders funds"),
        "interest_bearing_debt": num_for("borrowings", "interest bearing"),
        "cash_and_equivalents": num_for("cash and cash equivalents"),
        "operating_cash_flow": num_for("net cash from operating activities", "net cash generated from operating activities"),
        "capex": num_for("purchase of property", "purchase of plant", "capital expenditure"),
    }

    return metrics


def detect_currency(text: str) -> Optional[str]:
    t = text.lower()
    if "kes" in t:
        return "KES"
    if "ksh" in t or "kshs" in t or "shillings" in t:
        return "KES"
    if "usd" in t or "us$" in t:
        return "USD"
    return None


def main() -> None:
    index = load_index()
    docs: List[NSEDocument] = list(index.values())

    # Only process docs that have a local_path
    docs = [d for d in docs if d.local_path]

    print(f"Found {len(docs)} documents with local PDFs.")

    snapshots: List[FinancialSnapshot] = []

    for i, doc in enumerate(sorted(docs, key=lambda d: (d.year, d.company or "", d.title))):
        pdf_path = Path(doc.local_path)
        if not pdf_path.exists():
            continue

        print(f"[{i+1}/{len(docs)}] Extracting from {pdf_path} ({doc.title})")
        try:
            text = extract_text_from_pdf(pdf_path)
        except Exception as e:  # noqa: BLE001
            print(f"  Error reading PDF: {e}")
            continue

        currency = detect_currency(text)
        metrics = extract_metrics_from_text(text)

        snapshots.append(
            FinancialSnapshot(
                url=doc.url,
                year=doc.year,
                title=doc.title,
                company=doc.company,
                period=doc.period,
                currency=currency,
                revenue=metrics["revenue"],
                gross_profit=metrics["gross_profit"],
                operating_profit=metrics["operating_profit"],
                profit_before_tax=metrics["profit_before_tax"],
                profit_after_tax=metrics["profit_after_tax"],
                basic_eps=metrics["basic_eps"],
                dividend_per_share=metrics["dividend_per_share"],
                total_assets=metrics["total_assets"],
                total_equity=metrics["total_equity"],
                interest_bearing_debt=metrics["interest_bearing_debt"],
                cash_and_equivalents=metrics["cash_and_equivalents"],
                operating_cash_flow=metrics["operating_cash_flow"],
                capex=metrics["capex"],
            )
        )

    print(f"Writing {len(snapshots)} snapshots to {OUTPUT_FILE}")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in snapshots], f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
