"""Extract key financial metrics from NSE PDF results — v2 rewrite.

Key improvements over v1:
- Skips leading row-reference numbers (e.g. "21 Total assets ...") that
  caused the old extractor to store row numbers instead of values.
- Treats standalone dashes as zero/null (not negative signs).
- Handles parenthesised negatives correctly: (4,551) → -4551.
- Company-specific extraction for ABSA, StanChart (bank format) and
  Safaricom (telco format).
- Detects Group vs Company consolidation.
- Records the currency unit (KES thousands / millions / billions).

Usage (from backend directory, with venv active):

    python extract_financials_from_pdfs.py

Writes results to ../data/nse/financials.json.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber

# ── paths ──────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent
DATA_DIR    = BACKEND_DIR.parent / "data" / "nse"
OUTPUT_FILE = DATA_DIR / "financials.json"

# We still read the same index that the old scraper produced.
sys.path.insert(0, str(BACKEND_DIR))
from fetch_nse_results_2023_2025 import load_index  # type: ignore


# ── data model ─────────────────────────────────────────────────────────────

@dataclass
class FinancialSnapshot:
    # identity
    url:         str
    year:        int
    title:       str
    company:     Optional[str]
    period:      Optional[str]
    currency:    Optional[str]
    units:       Optional[str]          # "KES_thousands" | "KES_millions" | "KES_billions"
    consolidation: Optional[str]        # "group" | "company" | "unknown"

    # income statement (all in the unit above)
    net_interest_income:   Optional[float]  # banks
    revenue:               Optional[float]  # total_income (banks) / service_revenue (telco)
    operating_expenses:    Optional[float]
    impairment_charges:    Optional[float]  # banks: loan-loss / credit-impairment
    profit_before_tax:     Optional[float]
    profit_after_tax:      Optional[float]
    ebitda:                Optional[float]  # telco

    # per-share
    basic_eps:             Optional[float]
    dividend_per_share:    Optional[float]

    # balance sheet
    total_assets:          Optional[float]
    total_equity:          Optional[float]
    customer_deposits:     Optional[float]  # banks
    loans_and_advances:    Optional[float]  # banks

    # cash flow
    operating_cash_flow:   Optional[float]
    capex:                 Optional[float]

    # telco extras
    mpesa_revenue:         Optional[float]
    subscribers:           Optional[float]


# ── number parsing ──────────────────────────────────────────────────────────

# Matches a leading row-reference that NSE bank tables use, e.g.:
#   "21 Total assets 377,935,772 ..."  →  strip "21 "
#   "5.0 Total operating income ..."   →  strip "5.0 "
#   "9. Loans and advances ..."        →  strip "9. "
_ROW_REF_RE = re.compile(r'^\s*\d{1,2}(?:\.\d)?\s*\.?\s+')

# Comma-thousands number  (e.g.  9,043,839  or  9,043,839.50)
_COMMA_NUM_RE = re.compile(r'\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?)\b')
# Parenthesised negative  (e.g.  (4,551)  or  (4,551.2) )
_PAREN_NUM_RE = re.compile(r'\((\d[\d,.]*)\)')
# Plain decimal / ratio   (e.g.  0.98  or  12.76)
_DECIMAL_RE   = re.compile(r'\b(\d+\.\d+)\b')
# Plain integer without comma (only used as last resort)
_INT_RE       = re.compile(r'\b(\d{4,})\b')   # 4+ digit plain integer


def _candidates(line: str) -> List[Tuple[float, int]]:
    """Return (value, position) tuples for every recognisable number in *line*.

    Standalone dashes (" - ") are intentionally ignored — they are zero
    placeholders in NSE bank tables, not negative signs.

    Also handles digit-space-number patterns from spaced-font PDFs, e.g.:
      "2 95,955,246"  → 295955246   (StanChart 2019-2020 total assets)
      "1 3,835,467"   → 13835467    (StanChart 2024 PAT)
      "1 2.76"        → 12.76       (StanChart 2019 EPS)
    """
    found: List[Tuple[float, int]] = []

    # Parenthesised negatives (highest priority if present)
    for m in _PAREN_NUM_RE.finditer(line):
        try:
            found.append((-float(m.group(1).replace(',', '')), m.start()))
        except ValueError:
            pass

    # Digit-space-comma-thousands  (spaced-font fix)
    # e.g. "2 95,955,246"  or  "1 3,835,467"  or  "3 77,283,638"
    for m in re.finditer(r'(?<!\d)(\d)\s+(\d{1,3}(?:,\d{3})+(?:\.\d+)?)\b', line):
        try:
            combined = m.group(1) + m.group(2).replace(',', '')
            found.append((float(combined), m.start()))
        except ValueError:
            pass

    # Digit-space-digit.decimal  (e.g. "1 2.76" → 12.76, "2 2.00" → 22.00)
    for m in re.finditer(r'(?<!\d)(\d)\s+(\d+\.\d+)\b', line):
        try:
            found.append((float(m.group(1) + m.group(2)), m.start()))
        except ValueError:
            pass

    # Digit-space-dot-decimal  (e.g. "5 .00" → 5.00, "6 .89" → 6.89)
    for m in re.finditer(r'(?<!\d)(\d)\s+\.(\d+)\b', line):
        try:
            found.append((float(m.group(1) + '.' + m.group(2)), m.start()))
        except ValueError:
            pass

    # Comma-thousands positives (standard format)
    for m in _COMMA_NUM_RE.finditer(line):
        try:
            found.append((float(m.group(1).replace(',', '')), m.start()))
        except ValueError:
            pass

    # Decimal ratios (EPS, DPS, %)
    for m in _DECIMAL_RE.finditer(line):
        try:
            found.append((float(m.group(1)), m.start()))
        except ValueError:
            pass

    return found


def parse_value(line: str, want_ratio: bool = False) -> Optional[float]:
    """Extract the first meaningful financial value from *line*.

    Steps:
      1. Strip a leading row-reference number (e.g. "21 Total assets…").
      2. Collect all candidate numbers (comma-thousands, parens, decimals).
      3. Return the leftmost candidate.

    If *want_ratio* is True, plain decimals like 0.98 are also candidates
    even when no comma-thousands number is found (used for EPS / DPS).
    """
    if not line:
        return None

    # Normalise whitespace
    line = line.replace('\u00a0', ' ')
    # Fix "digit space comma digit" from spaced-font PDFs ("6 ,920,271" → "6,920,271")
    line = re.sub(r'(\d)\s+,(\d)', r'\1,\2', line)

    # Strip leading row reference
    line = _ROW_REF_RE.sub('', line, count=1)

    cands = _candidates(line)
    if not cands:
        return None

    # If only decimals remain and we don't want a ratio, discard
    large = [(v, p) for v, p in cands if abs(v) >= 1 or want_ratio]
    if not large:
        return None

    # Sort by position and return first (= current-period / Group column)
    large.sort(key=lambda x: x[1])
    return large[0][0]


# ── text utilities ──────────────────────────────────────────────────────────

_MAX_LINE = 600   # characters — long lines cause slow regex; truncate safely


def pdf_lines(path: Path) -> List[str]:
    """Extract text from every page and return cleaned, non-empty lines.

    Lines longer than _MAX_LINE chars are truncated — they typically arise
    from PDF corruption or multi-column bleed-through, and the financial
    figure we want is in the first part of the line anyway.
    """
    chunks: List[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t:
                chunks.append(t)
    raw = "\n".join(chunks)
    return [
        " ".join(ln.split())[:_MAX_LINE]
        for ln in raw.splitlines()
        if ln.strip()
    ]


def find_line(lines: List[str], *patterns: str) -> Optional[str]:
    """Return the first line that contains any of *patterns* (case-insensitive)."""
    pats = [p.lower() for p in patterns]
    for ln in lines:
        low = ln.lower()
        if any(p in low for p in pats):
            return ln
    return None


def find_table_line(lines: List[str], *patterns: str) -> Optional[str]:
    """Like find_line, but prefers lines that start with an NSE row-reference
    number (e.g. "12 Profit after tax…").  Falls back to first any-match.

    This avoids picking up narrative text that re-uses the same keywords
    but carries a different number (e.g. equity-movement "Profit for the
    period" rows which contain retained-earnings balances, not P&L profit).
    """
    pats = [p.lower() for p in patterns]
    table_hit: Optional[str] = None
    any_hit:   Optional[str] = None

    for ln in lines:
        low = ln.lower()
        if any(p in low for p in pats):
            if any_hit is None:
                any_hit = ln
            if table_hit is None and _ROW_REF_RE.match(ln):
                table_hit = ln
                break          # table row wins immediately

    return table_hit or any_hit


def first_value(lines: List[str], *patterns: str,
                want_ratio: bool = False,
                prefer_table: bool = False) -> Optional[float]:
    """Find the first matching line, then parse its first financial value."""
    if prefer_table:
        ln = find_table_line(lines, *patterns)
    else:
        ln = find_line(lines, *patterns)
    return parse_value(ln, want_ratio=want_ratio) if ln else None


# ── consolidation / unit detection ─────────────────────────────────────────

def detect_consolidation(lines: List[str]) -> str:
    """Return "group", "company", or "unknown"."""
    text_sample = " ".join(lines[:40]).lower()
    if "consolidated" in text_sample or "group" in text_sample:
        return "group"
    if "standalone" in text_sample or "company only" in text_sample:
        return "company"
    return "unknown"


def detect_units(lines: List[str]) -> str:
    """Return "KES_thousands", "KES_millions", or "KES_billions"."""
    text_sample = " ".join(lines[:60]).lower()
    if "kes millions" in text_sample or "ksh millions" in text_sample \
            or "in millions" in text_sample or "kshs millions" in text_sample \
            or "(millions)" in text_sample:
        return "KES_millions"
    if "kes billions" in text_sample or "ksh billions" in text_sample \
            or "in billions" in text_sample or "(kes bn)" in text_sample \
            or "kes bn" in text_sample:
        return "KES_billions"
    # NSE bank results default to KES thousands
    return "KES_thousands"


def detect_currency(lines: List[str]) -> str:
    text = " ".join(lines[:40]).lower()
    if "kes" in text or "ksh" in text or "kshs" in text or "kenya shilling" in text:
        return "KES"
    if "usd" in text or "us$" in text:
        return "USD"
    return "KES"


# ── company-type detection ──────────────────────────────────────────────────

def company_type(company: Optional[str]) -> str:
    """Return "bank", "telco", or "generic"."""
    if not company:
        return "generic"
    c = company.lower()
    if "safaricom" in c:
        return "telco"
    if any(x in c for x in ("bank", "absa", "equity", "kcb", "stanchart",
                              "standard chartered", "co-operative", "ncba",
                              "diamond trust", "family bank", "stanbic", "im group",
                              "hf group", "credit bank", "national bank")):
        return "bank"
    return "generic"


# ── bank extractor ──────────────────────────────────────────────────────────

def extract_bank_metrics(lines: List[str]) -> Dict[str, Optional[float]]:
    """
    Extract key metrics from NSE-formatted bank results.

    NSE bank PDFs use a numbered-row table:
        "3  Net interest income        16,801,899  23,126,804  ..."
        "5  Total operating income     24,321,027  33,144,829  ..."
        "9  Loans and advances         194,193,949 194,894,941 ..."
        "21 Total assets               377,935,772 428,746,218 ..."
        "35 Paid up/Assigned capital   2,715,768   2,715,768   ..."

    The first value after the description is the current-period Group figure.
    """

    def v(*pats: str, ratio: bool = False, table: bool = False) -> Optional[float]:
        return first_value(lines, *pats, want_ratio=ratio, prefer_table=table)

    return {
        "net_interest_income": v("net interest income"),
        "revenue":             v("total operating income", "total income",
                                  "total revenue", "operating income"),
        "operating_expenses":  v("operating expenses", "other operating expenses"),
        "impairment_charges":  v("impairment loss", "credit impairment",
                                  "loan loss provision", "impairment charges",
                                  "impairment on financial"),
        # prefer_table avoids matching equity-movement "Profit for the period"
        "profit_before_tax":   v("profit before tax", "profit before income tax",
                                  "profit before taxation", table=True),
        "profit_after_tax":    v("profit after tax and exceptional",
                                  "profit after tax",
                                  "profit for the year", "profit for the period",
                                  "net profit for the period", table=True),
        "ebitda":              None,
        "basic_eps":           v("earnings per share", ratio=True),
        "dividend_per_share":  v("dividend per share", "dividends per share",
                                  ratio=True),
        "total_assets":        v("total assets"),
        # total equity: try explicit labels first, then fallback to section lines
        "total_equity":        v("total equity", "total shareholders equity",
                                  "total capital and reserves",
                                  "shareholders' funds", "shareholders funds",
                                  "total stockholders"),
        "customer_deposits":   v("customer deposits"),
        "loans_and_advances":  v("loans and advances to customers",
                                  "loans and advances"),
        "operating_cash_flow": v("net cash from operating",
                                  "net cash generated from operating"),
        "capex":               v("purchase of property", "purchase of plant",
                                  "capital expenditure"),
        "mpesa_revenue":       None,
        "subscribers":         None,
    }


# ── telco extractor ─────────────────────────────────────────────────────────

def extract_telco_metrics(lines: List[str]) -> Dict[str, Optional[float]]:
    """
    Extract key metrics from Safaricom-style telco results.

    Safaricom PDFs are more narrative — no numbered rows — but the
    key line labels are consistent across years.
    """

    def v(*pats: str, ratio: bool = False) -> Optional[float]:
        return first_value(lines, *pats, want_ratio=ratio)

    return {
        "net_interest_income": None,
        "revenue":             v("service revenue", "total revenue", "revenue"),
        "operating_expenses":  v("operating expenses", "direct costs"),
        "impairment_charges":  None,
        "profit_before_tax":   v("profit before tax", "profit before income tax"),
        "profit_after_tax":    v("profit after tax"),
        "ebitda":              v("ebitda", "earnings before interest, tax"),
        "basic_eps":           v("earnings per share", "basic", ratio=True),
        # "proposed dividend per share" is specific enough; avoid "dividends paid"
        # which carries a total-dividend lump sum, not per-share
        "dividend_per_share":  v("proposed dividend per share",
                                  "final dividend per share",
                                  "dividend per share (dps)",
                                  "recommended dividend per share",
                                  ratio=True),
        "total_assets":        v("total assets"),
        "total_equity":        v("total equity", "shareholders' funds",
                                  "shareholders funds"),
        "customer_deposits":   None,
        "loans_and_advances":  None,
        "operating_cash_flow": v("net cash from operating", "cash generated from operations"),
        "capex":               v("capital expenditure", "purchase of property",
                                  "additions to"),
        "mpesa_revenue":       v("m-pesa", "mpesa revenue"),
        "subscribers":         None,
    }


# ── generic extractor ───────────────────────────────────────────────────────

def extract_generic_metrics(lines: List[str]) -> Dict[str, Optional[float]]:
    """Fallback for non-bank, non-telco companies."""

    def v(*pats: str, ratio: bool = False) -> Optional[float]:
        return first_value(lines, *pats, want_ratio=ratio)

    return {
        "net_interest_income": None,
        "revenue":             v("revenue", "turnover", "total income",
                                  "total revenue"),
        "operating_expenses":  v("operating expenses"),
        "impairment_charges":  None,
        "profit_before_tax":   v("profit before tax", "profit before income tax"),
        "profit_after_tax":    v("profit after tax", "profit for the year",
                                  "profit for the period"),
        "ebitda":              v("ebitda"),
        "basic_eps":           v("earnings per share", ratio=True),
        "dividend_per_share":  v("dividend per share", "dividends per share",
                                  ratio=True),
        "total_assets":        v("total assets"),
        "total_equity":        v("total equity", "shareholders' funds",
                                  "shareholders funds"),
        "customer_deposits":   None,
        "loans_and_advances":  None,
        "operating_cash_flow": v("net cash from operating",
                                  "net cash generated from operating"),
        "capex":               v("purchase of property", "capital expenditure"),
        "mpesa_revenue":       None,
        "subscribers":         None,
    }


# ── main driver ─────────────────────────────────────────────────────────────

_NULL_METRICS: Dict[str, None] = {k: None for k in [
    "net_interest_income", "revenue", "operating_expenses",
    "impairment_charges", "profit_before_tax", "profit_after_tax",
    "ebitda", "basic_eps", "dividend_per_share", "total_assets",
    "total_equity", "customer_deposits", "loans_and_advances",
    "operating_cash_flow", "capex", "mpesa_revenue", "subscribers",
]}


def main() -> None:
    index = load_index()
    docs = [d for d in index.values() if d.local_path]
    docs.sort(key=lambda d: (d.year, d.company or "", d.title))

    print(f"Processing {len(docs)} PDFs …", flush=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    # Write JSON incrementally to avoid accumulating all snapshots in RAM.
    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        out.write("[\n")
        first = True

        for i, doc in enumerate(docs, start=1):
            pdf_path = Path(doc.local_path)
            if not pdf_path.exists():
                continue

            print(f"  [{i}/{len(docs)}] {pdf_path.name}", flush=True)

            try:
                lines = pdf_lines(pdf_path)
            except Exception as exc:
                print(f"    !! PDF read error: {exc}", flush=True)
                continue

            try:
                ctype = company_type(doc.company)
                if ctype == "bank":
                    metrics = extract_bank_metrics(lines)
                elif ctype == "telco":
                    metrics = extract_telco_metrics(lines)
                else:
                    metrics = extract_generic_metrics(lines)
            except Exception as exc:
                print(f"    !! Metric extraction error: {exc}", flush=True)
                metrics = dict(_NULL_METRICS)

            snap = FinancialSnapshot(
                url=doc.url,
                year=doc.year,
                title=doc.title,
                company=doc.company,
                period=doc.period,
                currency=detect_currency(lines),
                units=detect_units(lines),
                consolidation=detect_consolidation(lines),
                **metrics,
            )

            if not first:
                out.write(",\n")
            json.dump(asdict(snap), out, indent=2, ensure_ascii=False)
            first = False
            count += 1
            # Release lines from memory immediately
            del lines

        out.write("\n]\n")

    print(f"\nWrote {count} snapshots → {OUTPUT_FILE}", flush=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
