"""
extract_financials_v2.py — Rewritten PDF extractor for NSE financial results.

Key fixes over v1:
  1. Skip leading row-reference numbers (e.g. "21 Total assets…" → don't return 21)
  2. Standalone dashes are zero placeholders, not negative signs
     (e.g. "Profit for year  - - - 9,043,839" → +9,043,839, not -9,043,839)
  3. Comma-thousands matching (only real financial values, not single digits)
  4. Parenthesised negatives: (4,551) → -4551
  5. Company-specific extraction (banks vs telco)
  6. Unit/consolidation detection

Usage (from backend/ with venv active):
    python extract_financials_v2.py

Outputs: data/nse/financials.json  (same schema as v1, with extra fields)
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber

# ── paths ──────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent
DATA_ROOT   = BACKEND_DIR.parent / "data" / "nse"
INDEX_FILE  = DATA_ROOT / "index_2023_2025.json"
OUTPUT_FILE = DATA_ROOT / "financials.json"


# ── data model ─────────────────────────────────────────────────────────────────
@dataclass
class FinancialSnapshot:
    # identity
    url:           str
    year:          int
    title:         str
    company:       Optional[str]
    period:        Optional[str]
    currency:      Optional[str]
    units:         Optional[str]        # "KES_thousands" | "KES_millions" | "KES_billions"
    consolidation: Optional[str]       # "group" | "company" | "unknown"

    # P&L
    revenue:             Optional[float]   # total_income (banks) / service_revenue (telco)
    net_interest_income: Optional[float]   # banks
    operating_expenses:  Optional[float]
    profit_before_tax:   Optional[float]
    profit_after_tax:    Optional[float]

    # per-share
    basic_eps:         Optional[float]
    dividend_per_share: Optional[float]

    # balance sheet
    total_assets:       Optional[float]
    total_equity:       Optional[float]
    customer_deposits:  Optional[float]    # banks
    loans_and_advances: Optional[float]    # banks

    # cash flow
    operating_cash_flow: Optional[float]
    capex:               Optional[float]

    # telco-specific
    ebitda:       Optional[float]
    mpesa_revenue: Optional[float]


# ── text extraction ────────────────────────────────────────────────────────────
def extract_text(path: Path) -> str:
    chunks: List[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t:
                chunks.append(t)
    return "\n".join(chunks)


def _fix_doubled_token(token: str) -> str:
    """Fix PDF doubled-character artifact seen in some Safaricom PDFs.

    e.g. '114433..0088' → '143.08', '((00..22%%))' → '(0.2%)'
    Rule: if every character in the token is repeated in adjacent pairs, halve it.
    Only applied to tokens that contain at least one digit.
    """
    if not any(c.isdigit() for c in token):
        return token
    if len(token) < 4 or len(token) % 2 != 0:
        return token
    if all(token[i] == token[i + 1] for i in range(0, len(token), 2)):
        return token[::2]
    return token


def normalise_line(line: str) -> str:
    """Clean a raw PDF text line for parsing."""
    line = line.replace("\u00a0", " ")               # non-breaking space
    line = line.replace("\u2019", "'")               # curly right-quote → straight
    line = line.replace("\u2018", "'")               # curly left-quote → straight
    line = re.sub(r"(\d)\s+,(\d)", r"\1,\2", line)  # "6 ,920,271" → "6,920,271"
    # StanChart spaced-digit: "1 3,835,467" → "13,835,467", "2 95,955,246" → "295,955,246"
    line = re.sub(r"(?<!\d)(\d)\s+(\d{1,2},\d{3})", r"\1\2", line)
    # StanChart spaced-decimal: "3 1.47" → "31.47", "3 6.17" → "36.17"
    line = re.sub(r"(?<!\d)(\d)\s+(\d{1,2}\.\d+)", r"\1\2", line)
    # Spaced dot-decimal: "8 .00" → "8.00", "4 5.00" already handled above
    line = re.sub(r"(?<!\d)(\d)\s+\.(\d+)", r"\1.\2", line)
    # Fix doubled-character PDF artifact: "114433..0088" → "143.08" (Safaricom 2020)
    tokens = line.split()
    tokens = [_fix_doubled_token(t) for t in tokens]
    line = " ".join(tokens)
    line = " ".join(line.split())                    # collapse whitespace
    return line


def get_lines(text: str) -> List[str]:
    return [normalise_line(l) for l in text.splitlines() if l.strip()]


# ── number parsing ─────────────────────────────────────────────────────────────
# Matches comma-thousands formatted numbers: 9,043,839 or 9,043,839.50
_COMMA_NUM = re.compile(r"\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?)\b")
# Matches parenthesised negatives: (4,551) or (4551)
_PAREN_NUM = re.compile(r"\((\d[\d,]*(?:\.\d+)?)\)")
# Matches plain decimals: 0.98, 12.76, 251.22
_DECIMAL   = re.compile(r"\b(\d+\.\d+)\b")
# Leading row-reference: "21 ", "9. ", "5.0 ", "3.1 "
_ROW_REF   = re.compile(r"^\s*\d{1,2}(?:\.\d{1,2})?\s*\.?\s+")


def _candidates(line: str) -> List[Tuple[float, int]]:
    """
    Return (value, char_position) pairs for all financial numbers in line,
    sorted by position ascending (leftmost = current-period column).

    Deliberately ignores standalone dashes (zero placeholders in tables).
    """
    results: List[Tuple[float, int]] = []

    # parenthesised negatives first
    for m in _PAREN_NUM.finditer(line):
        try:
            results.append((-float(m.group(1).replace(",", "")), m.start()))
        except ValueError:
            pass

    # comma-thousands positives
    for m in _COMMA_NUM.finditer(line):
        try:
            results.append((float(m.group(1).replace(",", "")), m.start()))
        except ValueError:
            pass

    # plain decimals (for EPS / ratios — only added if no comma-thousands found yet
    # so we don't double-count "9,043.50" as both comma and decimal)
    decimal_hits = {m.start() for _, pos in results for m in []}  # empty placeholder
    for m in _DECIMAL.finditer(line):
        # don't double-count positions already covered by comma-num
        if not any(abs(pos - m.start()) < 5 for _, pos in results):
            try:
                results.append((float(m.group(1)), m.start()))
            except ValueError:
                pass

    results.sort(key=lambda x: x[1])
    return results


def parse_value(line: str, want_ratio: bool = False) -> Optional[float]:
    """
    Extract first financial value from a line, skipping leading row-reference.

    Args:
        line:        The normalised text line.
        want_ratio:  If True, also accept small decimals (EPS, DPS).
    """
    if not line:
        return None

    # strip leading row-reference number
    stripped = _ROW_REF.sub("", line)

    hits = _candidates(stripped)
    if not hits:
        return None

    # for financial values (want_ratio=False), prefer comma-formatted large numbers
    # (ignore single-digit or small floats that might be section numbers)
    if not want_ratio:
        large = [(v, p) for v, p in hits if abs(v) >= 1000 or v != int(v)]
        if large:
            return large[0][0]
        # no large number found — fall back to first candidate
        return hits[0][0]
    else:
        return hits[0][0]


# ── line finder ────────────────────────────────────────────────────────────────
def find_line(lines: List[str], *patterns: str) -> Optional[str]:
    """Return first line containing any of the given patterns (case-insensitive)."""
    pats = [p.lower() for p in patterns]
    for line in lines:
        low = line.lower()
        if any(p in low for p in pats):
            return line
    return None


def find_line_excluding(lines: List[str], pattern: str, *excludes: str) -> Optional[str]:
    """Like find_line but skip lines that contain any exclude string."""
    excl = [e.lower() for e in excludes]
    for line in lines:
        low = line.lower()
        if pattern.lower() in low and not any(e in low for e in excl):
            return line
    return None


# ── consolidation & unit detection ────────────────────────────────────────────
def detect_consolidation(text: str) -> str:
    t = text.lower()
    if "group" in t and "company" in t:
        return "group_and_company"
    if "consolidated" in t or "group" in t:
        return "group"
    if "company" in t:
        return "company"
    return "unknown"


def detect_units(text: str) -> str:
    t = text.lower()
    # Check millions FIRST — table headers like "Group (KShs Mn)" are stronger indicators
    # than in-narrative mentions like "(KShs Bn)" which refer to total amounts, not table units.
    if ("kes millions" in t or "ksh millions" in t or "in millions" in t
            or "ksh mn" in t or "kshs mn" in t or "ksh. mn" in t or "kshs. mn" in t):
        return "KES_millions"
    if ("kes billions" in t or "ksh billions" in t or "in billions" in t
            or "kshs bn" in t or "ksh bn" in t or "kes bn" in t
            or "kshs. bn" in t or "ksh. bn" in t):
        return "KES_billions"
    # Most NSE bank results are in KES thousands (stated as "KES thousands" or just implied)
    if "thousands" in t:
        return "KES_thousands"
    # Safaricom 2024+ uses millions; Safaricom 2020 uses billions
    # Banks use thousands by default
    return "KES_thousands"


def detect_currency(text: str) -> str:
    t = text.lower()
    if "kes" in t or "ksh" in t or "kshs" in t or "shillings" in t:
        return "KES"
    if "usd" in t or "us$" in t:
        return "USD"
    return "KES"


# ── bank extractor (ABSA / StanChart format) ───────────────────────────────────
def extract_bank_metrics(lines: List[str]) -> Dict[str, Optional[float]]:
    """
    Extract metrics from NSE standardised bank results table.

    These PDFs use numbered rows:
      3 / 3.0  NET INTEREST INCOME          [val]  [val] ...
      5 / 5.0  TOTAL OPERATING INCOME       [val]  [val] ...
      6        OTHER OPERATING EXPENSES     ...
      7 / 7.0  PROFIT BEFORE TAX            [val]  [val] ...
      9        LOANS AND ADVANCES           [val]  [val] ...
     21        TOTAL ASSETS                 [val]  [val] ...
     23        CUSTOMER DEPOSITS            [val]  [val] ...
     35        PAID UP / ASSIGNED CAPITAL   [val]  [val] ...

    For "profit after tax / profit for the year" we look for the P&L line,
    not the equity movement line (which has the same words but different context).
    """

    def val(line: Optional[str], ratio: bool = False) -> Optional[float]:
        return parse_value(line, want_ratio=ratio) if line else None

    # Net interest income
    nii_line = find_line(lines, "net interest income")
    nii = val(nii_line)

    # Total operating income / total income
    inc_line = find_line(lines, "total operating income", "total income")
    income = val(inc_line)

    # Operating expenses
    opex_line = find_line(lines, "other operating expenses", "operating expenses")
    opex = val(opex_line)

    # Profit before tax — avoid "deferred tax" lines
    pbt_line = find_line_excluding(lines, "profit before tax", "deferred", "income tax expense")
    if pbt_line is None:
        pbt_line = find_line_excluding(lines, "profit before taxation", "deferred")
    pbt = val(pbt_line)

    # Profit after tax / profit for the period — look for the P&L summary line.
    # Note: ABSA uses "profit after tax and exceptional items" — do NOT exclude "exceptional".
    # Avoid equity-movement lines ("retained earnings", "balance at end").
    # Also avoid merged two-column lines where "loans and advances" table row has "profit after
    # tax" narrative text appended to it (ABSA two-column layout PDF artifact).
    pat_line = find_line_excluding(
        lines,
        "profit after tax",
        "retained", "balance at", "total equity",
        "loans and advances", "advances to customers",
    )
    if pat_line is None:
        pat_line = find_line_excluding(
            lines,
            "profit for the year",
            "retained", "balance", "total equity"
        )
    if pat_line is None:
        pat_line = find_line_excluding(
            lines,
            "profit for the period",
            "retained", "balance", "total equity"
        )
    # StanChart format: "net profit for the period"
    if pat_line is None:
        pat_line = find_line_excluding(lines, "net profit for the period", "retained")
    pat = val(pat_line)

    # EPS
    eps_line = find_line(lines, "earnings per share", "basic eps")
    eps = val(eps_line, ratio=True)

    # DPS — use ratio mode; standalone dashes give no match → returns first actual number
    dps_line = find_line(lines, "dividend per share", "dividends per share")
    dps = val(dps_line, ratio=True)

    # Total assets — some ABSA PDFs use "Total asset" (no trailing 's')
    assets_line = find_line(lines, "total assets", "total asset")
    assets = val(assets_line)

    # Total equity / shareholders' funds
    # Try several phrasings; the apostrophe varies between PDFs (straight vs curly, already
    # normalised in normalise_line, but search must be flexible).
    equity_line = find_line_excluding(
        lines,
        "total shareholders' funds",
        "minimum", "excess", "deficiency"
    )
    if equity_line is None:
        equity_line = find_line_excluding(lines, "total shareholders funds", "minimum")
    if equity_line is None:
        equity_line = find_line_excluding(lines, "total equity", "minimum")
    # ABSA uses "C Shareholders' Funds" — section header, actual total is "Total equity" or
    # listed as a line item. If still None, accept any "shareholders" line with a large value.
    if equity_line is None:
        for candidate in lines:
            if "shareholder" in candidate.lower():
                v = parse_value(candidate)
                if v is not None and abs(v) >= 1000:
                    equity_line = candidate
                    break
    equity = val(equity_line)

    # Customer deposits
    deposits_line = find_line(lines, "customer deposits")
    deposits = val(deposits_line)

    # Loans and advances — exclude "non-performing" / "insider" / fee / provision lines
    # that appear earlier in ABSA's CBK regulatory table and would be matched first.
    loans_line = find_line_excluding(
        lines,
        "loans and advances to customers",
        "non-performing", "non performing", "insider", "fees", "provision",
    )
    if loans_line is None:
        loans_line = find_line_excluding(
            lines,
            "loans and advances",
            "non-performing", "non performing", "insider", "fees", "provision",
            "contingent",
        )
    if loans_line is None:
        loans_line = find_line(lines, "net loans", "advances to customers")
    loans = val(loans_line)

    return {
        "net_interest_income": nii,
        "revenue":             income,
        "operating_expenses":  opex,
        "profit_before_tax":   pbt,
        "profit_after_tax":    pat,
        "basic_eps":           eps,
        "dividend_per_share":  dps,
        "total_assets":        assets,
        "total_equity":        equity,
        "customer_deposits":   deposits,
        "loans_and_advances":  loans,
        "operating_cash_flow": None,
        "capex":               None,
        "ebitda":              None,
        "mpesa_revenue":       None,
    }


# ── telco extractor (Safaricom format) ────────────────────────────────────────
def extract_telco_metrics(lines: List[str]) -> Dict[str, Optional[float]]:
    """
    Extract metrics from Safaricom results.

    Safaricom uses a narrative + table format, NOT the numbered-row bank format.
    Year-end: 31 March.
    Units: KES billions (up to ~2022), KES millions (2023+).
    """

    def val(line: Optional[str], ratio: bool = False) -> Optional[float]:
        return parse_value(line, want_ratio=ratio) if line else None

    # Revenue — "service revenue" is the primary top line
    rev_line = find_line(lines, "service revenue", "total revenue", "revenue")
    revenue = val(rev_line)

    # EBITDA
    ebitda_line = find_line(lines, "ebitda")
    ebitda = val(ebitda_line)

    # Operating profit
    opex_line = find_line(lines, "operating profit", "profit from operations", "ebit")
    opex = val(opex_line)

    # PBT
    pbt_line = find_line(lines, "profit before tax", "profit before income tax")
    pbt = val(pbt_line)

    # PAT
    pat_line = find_line_excluding(lines, "profit after tax", "retained")
    pat = val(pat_line)

    # EPS
    eps_line = find_line(lines, "basic", "earnings per share", "eps")
    eps = val(eps_line, ratio=True)

    # DPS — must contain "per share" to avoid total-dividend cash-flow lines
    dps_line = find_line(lines, "dividend per share", "dividends per share")
    if dps_line is None:
        dps_line = find_line(lines, "proposed dividend per share")
    # Sanity: DPS should be a small number (< 100). If the extracted value is huge
    # (i.e. we accidentally grabbed the total dividend payment), treat as None.
    dps_raw = val(dps_line, ratio=True)
    dps = dps_raw if (dps_raw is None or abs(dps_raw) < 100) else None

    # Total assets
    assets_line = find_line(lines, "total assets")
    assets = val(assets_line)

    # Total equity
    equity_line = find_line(lines, "total equity", "shareholders' equity", "shareholders equity")
    equity = val(equity_line)

    # M-PESA revenue
    mpesa_line = find_line(lines, "m-pesa revenue", "mpesa revenue", "mobile money revenue")
    mpesa = val(mpesa_line)

    # Operating cash flow
    ocf_line = find_line(lines, "net cash from operating", "net cash generated from operating", "cash generated from operations")
    ocf = val(ocf_line)

    # Capex
    capex_line = find_line(lines, "capital expenditure", "capex", "purchase of property", "purchase of plant")
    capex = val(capex_line)

    return {
        "net_interest_income": None,
        "revenue":             revenue,
        "operating_expenses":  opex,
        "profit_before_tax":   pbt,
        "profit_after_tax":    pat,
        "basic_eps":           eps,
        "dividend_per_share":  dps,
        "total_assets":        assets,
        "total_equity":        equity,
        "customer_deposits":   None,
        "loans_and_advances":  None,
        "operating_cash_flow": ocf,
        "capex":               capex,
        "ebitda":              ebitda,
        "mpesa_revenue":       mpesa,
    }


# ── generic extractor (fallback for unknown companies) ────────────────────────
def extract_generic_metrics(lines: List[str]) -> Dict[str, Optional[float]]:
    def val(line: Optional[str], ratio: bool = False) -> Optional[float]:
        return parse_value(line, want_ratio=ratio) if line else None

    return {
        "net_interest_income": None,
        "revenue":             val(find_line(lines, "revenue", "turnover", "total income", "total operating income")),
        "operating_expenses":  val(find_line(lines, "operating expenses")),
        "profit_before_tax":   val(find_line_excluding(lines, "profit before tax", "deferred")),
        "profit_after_tax":    val(find_line_excluding(lines, "profit after tax", "retained")),
        "basic_eps":           val(find_line(lines, "earnings per share"), ratio=True),
        "dividend_per_share":  val(find_line(lines, "dividend per share"), ratio=True),
        "total_assets":        val(find_line(lines, "total assets")),
        "total_equity":        val(find_line(lines, "total equity", "shareholders")),
        "customer_deposits":   None,
        "loans_and_advances":  None,
        "operating_cash_flow": val(find_line(lines, "net cash from operating")),
        "capex":               val(find_line(lines, "capital expenditure", "purchase of property")),
        "ebitda":              val(find_line(lines, "ebitda")),
        "mpesa_revenue":       None,
    }


# ── company classifier ────────────────────────────────────────────────────────
BANK_KEYWORDS = [
    "absa", "standard chartered", "stanchart", "equity bank", "equity group",
    "kcb", "cooperative bank", "co-op bank", "diamond trust", "dtb",
    "ncba", "stanbic", "family bank", "im bank", "i&m", "hf group",
    "national bank", "sbk", "bank"
]
TELCO_KEYWORDS = ["safaricom", "telkom", "airtel"]


def classify_company(company: Optional[str], title: str, text_snippet: str) -> str:
    """Return 'bank', 'telco', or 'generic'."""
    probe = " ".join(filter(None, [company, title, text_snippet[:500]])).lower()
    if any(k in probe for k in TELCO_KEYWORDS):
        return "telco"
    if any(k in probe for k in BANK_KEYWORDS):
        return "bank"
    return "generic"


# ── index loading (compatible with existing fetch script) ────────────────────
@dataclass
class NSEDoc:
    url: str
    year: int
    title: str
    company: Optional[str]
    period: Optional[str]
    local_path: Optional[str]


def load_index() -> List[NSEDoc]:
    if not INDEX_FILE.exists():
        print(f"Index file not found: {INDEX_FILE}", file=sys.stderr)
        return []
    with INDEX_FILE.open(encoding="utf-8") as f:
        raw = json.load(f)

    docs: List[NSEDoc] = []
    for item in raw.values() if isinstance(raw, dict) else raw:
        if isinstance(item, dict):
            docs.append(NSEDoc(
                url=item.get("url", ""),
                year=item.get("year", 0),
                title=item.get("title", ""),
                company=item.get("company"),
                period=item.get("period"),
                local_path=item.get("local_path"),
            ))
    return docs


# ── main ──────────────────────────────────────────────────────────────────────
def process_pdf(doc: NSEDoc) -> Optional[FinancialSnapshot]:
    pdf_path = Path(doc.local_path)
    if not pdf_path.exists():
        return None

    try:
        text = extract_text(pdf_path)
    except Exception as e:
        print(f"  ✗ Error reading PDF: {e}", file=sys.stderr)
        return None

    lines = get_lines(text)
    snippet = text[:1000]

    company_type = classify_company(doc.company, doc.title, snippet)
    currency     = detect_currency(text)
    units        = detect_units(text)
    consolidation = detect_consolidation(text)

    if company_type == "bank":
        metrics = extract_bank_metrics(lines)
    elif company_type == "telco":
        metrics = extract_telco_metrics(lines)
    else:
        metrics = extract_generic_metrics(lines)

    return FinancialSnapshot(
        url=doc.url,
        year=doc.year,
        title=doc.title,
        company=doc.company,
        period=doc.period,
        currency=currency,
        units=units,
        consolidation=consolidation,
        **metrics,
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    docs = [d for d in load_index() if d.local_path]
    docs.sort(key=lambda d: (d.year, d.company or "", d.title))

    print(f"Found {len(docs)} documents with local PDFs.")

    snapshots: List[FinancialSnapshot] = []
    errors = 0

    for i, doc in enumerate(docs, 1):
        label = f"{doc.company or '?'} | {doc.period or '?'}"
        print(f"[{i}/{len(docs)}] {label}")
        snap = process_pdf(doc)
        if snap:
            snapshots.append(snap)
        else:
            errors += 1

    print(f"\nDone. {len(snapshots)} extracted, {errors} errors.")
    print(f"Writing to {OUTPUT_FILE}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in snapshots], f, indent=2, ensure_ascii=False)

    print("✓ Done")


if __name__ == "__main__":
    main()
