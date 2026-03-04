"""
extract_all.py — NSE PDF extractor (rewritten for reliable CBK bank format parsing).

Strategy:
  - CBK bank disclosures: positional column extraction based on header date order
  - Safaricom: keyword + positional extraction, units in millions
  - Other companies: keyword-based extraction

Usage: python extract_all.py [--since YEAR] [company_filter ...]
Output: data/nse/financials.json
"""

from __future__ import annotations
import json, re, sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pdfplumber

BACKEND_DIR = Path(__file__).parent
DATA_ROOT   = BACKEND_DIR.parent / "data" / "nse"
OUTPUT_FILE = DATA_ROOT / "financials.json"

# ── Ticker / Sector mapping ───────────────────────────────────────────────────

TICKER_MAP: Dict[str, str] = {
    "absa":                   "ABSA",
    "standard chartered":     "SCBK",
    "stanchart":              "SCBK",
    "safaricom":              "SCOM",
    "equity group":           "EQTY",
    "equity bank":            "EQTY",
    "kcb":                    "KCB",
    "national bank":          "NBK",
    "ncba":                   "NCBA",
    "co-operative bank":      "COOP",
    "cooperative bank":       "COOP",
    "co operative bank":      "COOP",
    "co_operative":           "COOP",
    "diamond trust":          "DTK",
    "dtb":                    "DTK",
    "stanbic":                "CFC",
    "i&m":                    "IMH",
    "i and m":                "IMH",
    "im bank":                "IMH",
    "i_m_group":              "IMH",
    "i_m_holdings":           "IMH",
    "family bank":            "FANB",
    "hf group":               "HFCK",
    "housing finance":        "HFCK",
    "east african breweries": "EABL",
    "eabl":                   "EABL",
    "bamburi":                "BAMB",
    "bat kenya":              "BATK",
    "britam":                 "BRIT",
    "jubilee":                "JUB",
    "sanlam kenya":           "SLAM",
    "kenya power":            "KPLC",
    "kengen":                 "KEGN",
    "nation media":           "NMG",
    "standard group":         "SGL",
    "wpp scangroup":          "SCAN",
    "bk group":               "BKG",
    "crown paints":           "CPKL",
    "unga group":             "UNGA",
    "sasini":                 "SASN",
    "williamson tea":         "WTK",
    "kapchorua tea":          "KAPA",
    "carbacid":               "CARB",
    "boc kenya":              "BOC",
    "east african portland":  "EAPC",
    "umeme":                  "UMME",
    "express kenya":          "XPRS",
    "flame tree":             "FTGH",
    "home afrika":            "HAFR",
    "homeboyz":               "HBZE",
    "transcentury":           "TCL",
    "tps eastern africa":     "TPSE",
    "nse":                    "NSE",
}

SECTOR_MAP: Dict[str, str] = {
    "ABSA": "Banking", "SCBK": "Banking", "EQTY": "Banking", "KCB": "Banking",
    "NBK": "Banking", "NCBA": "Banking", "COOP": "Banking", "DTK": "Banking",
    "CFC": "Banking", "IMH": "Banking", "FANB": "Banking", "HFCK": "Banking",
    "BKG": "Banking",
    "SCOM": "Telecoms",
    "EABL": "FMCG", "BATK": "FMCG", "UNGA": "FMCG",
    "BAMB": "Construction", "EAPC": "Construction",
    "BRIT": "Insurance", "JUB": "Insurance", "SLAM": "Insurance",
    "NMG": "Media", "SGL": "Media", "SCAN": "Media",
    "KPLC": "Energy", "KEGN": "Energy", "UMME": "Energy",
    "SASN": "Agriculture", "WTK": "Agriculture", "KAPA": "Agriculture",
    "CARB": "Manufacturing", "BOC": "Manufacturing", "CPKL": "Manufacturing",
    "XPRS": "Logistics", "FTGH": "Diversified", "HAFR": "Real Estate",
    "HBZE": "Entertainment", "TCL": "Infrastructure", "TPSE": "Hospitality",
    "NSE": "Financial Services",
}

BANK_TICKERS = {"ABSA","SCBK","EQTY","KCB","NBK","NCBA","COOP","DTK","CFC","IMH","FANB","HFCK","BKG"}

MONTH_MAP = {
    "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
    "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12,
    "january":1,"february":2,"march":3,"april":4,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_ticker(name: str) -> Optional[str]:
    if not name: return None
    low = name.lower()
    for key, ticker in TICKER_MAP.items():
        if key in low:
            return ticker
    return None

def get_ticker_from_filename(filename: str) -> Optional[str]:
    fn = filename.lower()
    for key, ticker in TICKER_MAP.items():
        if key.replace(" ", "_") in fn or key.replace(" ", "") in fn:
            return ticker
        if key.split()[0] in fn:
            return ticker
    return None

def parse_period_from_filename(filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    m = re.search(r'_(\d{1,2})_([A-Za-z]+)_(\d{4})', filename, re.I)
    if not m:
        return None, None, None
    day, month_str, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    month = MONTH_MAP.get(month_str)
    if not month:
        return None, None, None
    try:
        d = date(year, month, day)
    except ValueError:
        return None, None, None
    date_str = d.isoformat()
    fn_lower = filename.lower()
    is_scom = "safaricom" in fn_lower or "scom" in fn_lower
    if month == 12 and day >= 30:
        return f"FY{year}", date_str, "annual"
    elif month == 3 and day >= 30:
        if is_scom:
            return f"FY{year}", date_str, "annual"
        return f"Q1 FY{year}", date_str, "quarter"
    elif month == 6 and day >= 29:
        return f"H1 FY{year}", date_str, "half_year"
    elif month == 9 and day >= 29:
        return f"Q3 FY{year}", date_str, "quarter"
    elif month == 7 and day >= 31:
        return f"FY{year}", date_str, "annual"
    else:
        return date_str, date_str, "unknown"

def extract_text(path: Path) -> str:
    chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                chunks.append(t)
    return "\n".join(chunks)

# ── Number parsing utilities ──────────────────────────────────────────────────

_NUM_PAT = re.compile(r"""
    \([\d,]+(?:\.\d+)?\)    |   # parenthesised negative like (1,234)
    -?[\d,]+\.\d+           |   # decimal number like 1,234.56 or -1.23
    \d{1,3}(?:,\d{3})+      |   # comma-separated integer like 1,234,567
    (?<![.\d])\d+(?![,.\d])      # plain integer (not part of decimal/comma num)
""", re.VERBOSE)

_DASH_TOKEN = re.compile(r'(?<!\w)-(?!\w)')  # standalone dash (not hyphenated word)

def parse_number(token: str) -> Optional[float]:
    """Parse a single number token."""
    token = token.strip()
    if not token or token == '-':
        return None
    neg = False
    if token.startswith('(') and token.endswith(')'):
        neg = True
        token = token[1:-1]
    token = token.replace(',', '')
    try:
        v = float(token)
        return -v if neg else v
    except ValueError:
        return None

def extract_all_numbers(line: str) -> List[Optional[float]]:
    """Extract all data column values from a line, preserving position.
    Returns numbers and None for dashes."""
    results = []
    # We need to parse in order: find numbers and standalone dashes
    # First, strip the row label (everything before the first number or dash)
    # Find the position of the first number-like token
    first_num = _NUM_PAT.search(line)
    if not first_num:
        return results
    
    data_part = line[first_num.start():]
    
    # Tokenize: split by whitespace, classify each token
    tokens = data_part.split()
    for t in tokens:
        if t == '-':
            results.append(None)
        else:
            v = parse_number(t)
            if v is not None:
                results.append(v)
            # else: skip non-numeric tokens (like "Kshs", labels mixed in)
    return results

def extract_numbers_only(line: str) -> List[float]:
    """Extract only actual numbers (skip dashes/None)."""
    return [v for v in extract_all_numbers(line) if v is not None]

# ── CBK Bank Format Parser ────────────────────────────────────────────────────

def detect_cbk_format(text: str) -> bool:
    """Detect if text is in CBK banking disclosure format."""
    low = text[:2000].lower()
    return ("statement of financial position" in low and 
            ("kshs 000" in low or "shs '000" in low or "shs 000" in low or "kes 000" in low))

def detect_header_date_order(text: str) -> Tuple[int, int]:
    """Detect the date ordering in header.
    Returns (curr_idx, num_cols_per_entity).
    curr_idx: 0 if descending (newer first), 1 if ascending (older first).
    """
    # Look at first ~15 lines for date patterns
    lines = text.split('\n')[:15]
    for line in lines:
        # Find all 4-digit years in the line
        years = re.findall(r'20[12]\d', line)
        if len(years) >= 2:
            y1, y2 = int(years[0]), int(years[1])
            if y1 > y2:
                return 0, len(years)  # descending: current year first
            elif y1 < y2:
                return 1, len(years)  # ascending: current year second
            else:
                # Same year — look at months
                # e.g. "31-Mar-24 31-Dec-23" within same year
                continue
    
    # Fallback: check for specific date patterns
    for line in lines:
        dates = re.findall(r'(\d{1,2})-([A-Za-z]+)-(\d{2,4})', line)
        if len(dates) >= 2:
            y1 = int(dates[0][2])
            y2 = int(dates[1][2])
            if y1 < 100: y1 += 2000
            if y2 < 100: y2 += 2000
            if y1 > y2:
                return 0, len(dates)
            elif y1 < y2:
                return 1, len(dates)
    
    return 0, 4  # default: descending, 4 columns

def find_cbk_section(lines: List[str], section_marker: str) -> int:
    """Find the line index where a section starts."""
    marker_low = section_marker.lower()
    for i, line in enumerate(lines):
        if marker_low in line.lower():
            return i
    return -1

def cbk_find_row(lines: List[str], start: int, end: int, 
                  keywords: List[str], exclude: List[str] = None) -> Optional[str]:
    """Find a row by keywords within a line range."""
    exclude = [e.lower() for e in (exclude or [])]
    for i in range(max(0, start), min(end, len(lines))):
        low = lines[i].lower()
        if any(k.lower() in low for k in keywords):
            if not any(e in low for e in exclude):
                return lines[i]
    return None

def cbk_find_numbered_row(lines: List[str], start: int, end: int, row_num: int) -> Optional[str]:
    """Find a row by its CBK row number (e.g., row 12 = PAT)."""
    patterns = [f"{row_num}.", f"{row_num} "]
    for i in range(max(0, start), min(end, len(lines))):
        stripped = lines[i].strip()
        for p in patterns:
            if stripped.startswith(p):
                # Verify it has numbers
                nums = extract_numbers_only(lines[i])
                if nums:
                    return lines[i]
    return None

def cbk_get_value(line: Optional[str], curr_idx: int, is_ratio: bool = False) -> Optional[float]:
    """Extract the current-year value from a CBK row at the correct column position."""
    if not line:
        return None
    
    all_vals = extract_all_numbers(line)
    if not all_vals:
        return None
    
    # For rows with dashes, all_vals includes None entries
    if curr_idx < len(all_vals):
        val = all_vals[curr_idx]
        if val is not None:
            return val
    
    # Fallback: just get the first non-None value
    for v in all_vals:
        if v is not None:
            return v
    return None

def cbk_get_value_safe(line: Optional[str], curr_idx: int, 
                        is_ratio: bool = False, min_threshold: float = 500) -> Optional[float]:
    """Get value with footnote reference filtering."""
    val = cbk_get_value(line, curr_idx, is_ratio)
    if val is None:
        return None
    if not is_ratio and abs(val) < min_threshold:
        return None  # likely a footnote reference
    return val

def extract_cbk_bank(text: str, filename: str) -> Dict[str, Any]:
    """Extract financials from CBK banking disclosure format."""
    curr_idx, total_cols = detect_header_date_order(text)
    lines = text.split('\n')
    
    # Find key sections
    bs_start = find_cbk_section(lines, "STATEMENT OF FINANCIAL POSITION")
    if bs_start < 0:
        bs_start = find_cbk_section(lines, "statement of financial position")
    
    is_start = find_cbk_section(lines, "STATEMENT OF COMPREHENSIVE INCOME")
    if is_start < 0:
        is_start = find_cbk_section(lines, "statement of comprehensive income")
    
    disc_start = find_cbk_section(lines, "OTHER DISCLOSURES")
    if disc_start < 0:
        disc_start = find_cbk_section(lines, "other disclosures")
    if disc_start < 0:
        disc_start = len(lines)
    
    bs_end = is_start if is_start > 0 else disc_start
    is_end = disc_start if disc_start > is_start else len(lines)
    
    # Balance sheet items
    assets_line = cbk_find_row(lines, bs_start, bs_end, ["TOTAL ASSETS", "Total assets"])
    deposits_line = cbk_find_row(lines, bs_start, bs_end, 
                                  ["Customer deposits", "Customers' deposits", "Customer Deposits"])
    loans_line = cbk_find_row(lines, bs_start, bs_end, 
                               ["Loans and advances to customers", "loans and advances to customers"],
                               exclude=["Non-performing", "Insider", "provision"])
    equity_line = cbk_find_row(lines, bs_start, bs_end, 
                                ["TOTAL SHAREHOLDERS", "Total shareholders", "total shareholders"])
    
    # Income statement items  
    nii_line = cbk_find_row(lines, is_start, is_end, 
                             ["NET INTEREST INCOME", "Net interest income"])
    revenue_line = cbk_find_row(lines, is_start, is_end, 
                                 ["TOTAL OPERATING INCOME", "Total operating income"])
    
    # PBT: try row 7 by keyword first, then by number
    pbt_line = cbk_find_row(lines, is_start, is_end, 
                             ["Profit before tax", "PROFIT BEFORE TAX"],
                             exclude=["deferred"])
    if not pbt_line:
        pbt_line = cbk_find_numbered_row(lines, is_start, is_end, 7)
    
    # PAT: try keyword first
    pat_line = cbk_find_row(lines, is_start, is_end, 
                             ["Profit after tax", "PROFIT AFTER TAX"],
                             exclude=["retained", "balance", "total equity", "minority"])
    if not pat_line:
        # Row 12 in CBK format = PAT (often unlabelled)
        pat_line = cbk_find_numbered_row(lines, is_start, is_end, 12)
    
    # EPS and DPS
    eps_line = cbk_find_row(lines, is_start, is_end + 20, 
                             ["EARNINGS PER SHARE", "Earnings per share", "Basic earnings per share"])
    dps_line = cbk_find_row(lines, is_start, is_end + 20, 
                             ["DIVIDEND PER SHARE", "Dividends per share", "Dividend per share"])
    
    # Extract values
    total_assets = cbk_get_value_safe(assets_line, curr_idx)
    deposits = cbk_get_value_safe(deposits_line, curr_idx)
    loans = cbk_get_value_safe(loans_line, curr_idx)
    equity = cbk_get_value_safe(equity_line, curr_idx)
    nii = cbk_get_value_safe(nii_line, curr_idx)
    revenue = cbk_get_value_safe(revenue_line, curr_idx)
    pbt = cbk_get_value_safe(pbt_line, curr_idx)
    pat = cbk_get_value_safe(pat_line, curr_idx)
    eps = cbk_get_value(eps_line, curr_idx, is_ratio=True)
    dps = cbk_get_value(dps_line, curr_idx, is_ratio=True)
    
    # Validate EPS/DPS are reasonable (< 100)
    if eps is not None and abs(eps) > 500:
        eps = None
    if dps is not None and abs(dps) > 500:
        dps = None
    
    return {
        "net_interest_income": nii,
        "revenue": revenue,
        "profit_before_tax": pbt,
        "profit_after_tax": pat,
        "basic_eps": eps,
        "dividend_per_share": dps,
        "total_assets": total_assets,
        "total_equity": equity,
        "customer_deposits": deposits,
        "loans_and_advances": loans,
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": None,
    }

# ── Safaricom Parser ──────────────────────────────────────────────────────────

def extract_safaricom(text: str, filename: str) -> Dict[str, Any]:
    """Extract Safaricom financials. Units in KShs Mn → multiply by 1000."""
    curr_idx, _ = detect_header_date_order(text)
    lines = text.split('\n')
    
    def find_and_get(keywords, exclude=None, is_ratio=False):
        exclude = [e.lower() for e in (exclude or [])]
        for line in lines:
            low = line.lower()
            if any(k.lower() in low for k in keywords):
                if any(e in low for e in exclude):
                    continue
                nums = extract_numbers_only(line)
                if nums and curr_idx < len(nums):
                    return nums[curr_idx]
                elif nums:
                    return nums[0]
        return None
    
    mult = 1000.0  # millions → thousands
    
    total_rev = find_and_get(["Total revenue"])
    service_rev = find_and_get(["Service revenue"])
    revenue = total_rev or service_rev
    
    ebitda = find_and_get(["EBITDA"])
    # EBITDA line might be split: "Amortisation (EBITDA)" or "163,292.6 139,862.4"
    # Look for the line after "Earnings Before Interest"
    if ebitda is None:
        for i, line in enumerate(lines):
            if "earnings before interest" in line.lower():
                # EBITDA value might be on next line
                if i + 1 < len(lines):
                    nums = extract_numbers_only(lines[i + 1])
                    if nums and curr_idx < len(nums):
                        ebitda = nums[curr_idx]
                    elif nums:
                        ebitda = nums[0]
                # Or on the same line
                if ebitda is None:
                    nums = extract_numbers_only(line)
                    if nums and curr_idx < len(nums):
                        ebitda = nums[curr_idx]
                break
    
    pbt = find_and_get(["Profit before income tax", "Profit before tax"])
    
    # PAT: "Profit after tax" (group level, before split to equity holders)
    pat = find_and_get(["Profit after tax"], exclude=["attributable", "retained"])
    # Or use "Attributable to Equity holders of the parent"
    pat_equity = find_and_get(["Equity holders of the parent", "equity holders of the parent"])
    
    eps_val = find_and_get(["Basic earnings per share", "Earnings per share"], is_ratio=True)
    dps_val = find_and_get(["Dividend per share", "Dividends per share"], is_ratio=True)
    assets = find_and_get(["Total assets"])
    equity = find_and_get(["Total equity", "Total shareholders"])
    mpesa = find_and_get(["M-PESA revenue", "M-Pesa revenue", "MPESA revenue"])
    ocf = find_and_get(["Net cash generated from operating", "Net cash from operating"])
    
    def scale(v):
        return round(v * mult) if v is not None else None
    
    # For EPS/DPS don't scale - they're per share
    return {
        "net_interest_income": None,
        "revenue": scale(revenue),
        "profit_before_tax": scale(pbt),
        "profit_after_tax": scale(pat or pat_equity),
        "basic_eps": eps_val,
        "dividend_per_share": dps_val,
        "total_assets": scale(assets),
        "total_equity": scale(equity),
        "customer_deposits": None,
        "loans_and_advances": None,
        "operating_cash_flow": scale(ocf),
        "capex": None,
        "ebitda": scale(ebitda),
        "mpesa_revenue": scale(mpesa),
    }

# ── Generic (non-bank, non-telco) Parser ──────────────────────────────────────

def detect_units(text: str) -> Tuple[str, float]:
    """Detect units and return (unit_label, multiplier_to_thousands)."""
    t = text[:3000].lower()
    if re.search(r"\bkes\s+000\b", t) or re.search(r"\bksh\s+000\b", t) or "shs '000" in t or "shs 000" in t:
        return "KES_thousands", 1.0
    if any(x in t for x in ["kes millions", "ksh millions", "kshs millions", "in millions",
                              "ksh mn", "kshs mn", "kshs. mn", "kshs mn"]):
        return "KES_millions", 1000.0
    if any(x in t for x in ["kes billions", "ksh billions", "in billions",
                              "kshs bn", "ksh bn"]):
        return "KES_billions", 1_000_000.0
    if "thousands" in t:
        return "KES_thousands", 1.0
    return "KES_thousands", 1.0

def extract_generic(text: str, filename: str) -> Dict[str, Any]:
    """Extract financials from generic income statement format."""
    lines = text.split('\n')
    _, mult = detect_units(text)
    
    # Detect date order
    curr_idx = 0
    for line in lines[:20]:
        years = re.findall(r'20[12]\d', line)
        if len(years) >= 2:
            if int(years[0]) < int(years[1]):
                curr_idx = 1
            break
    
    def find_val(keywords, exclude=None, is_ratio=False):
        exclude = [e.lower() for e in (exclude or [])]
        for line in lines:
            low = line.lower()
            if any(k.lower() in low for k in keywords):
                if any(e in low for e in exclude):
                    continue
                nums = extract_numbers_only(line)
                if not nums:
                    continue
                idx = min(curr_idx, len(nums) - 1)
                val = nums[idx]
                if not is_ratio and abs(val) < 500 and mult == 1.0:
                    continue  # skip footnote ref
                return val
        return None
    
    def scale(v):
        return round(v * mult) if v is not None else None
    
    revenue = find_val(["Total revenue", "Revenue", "Turnover", "Total income", 
                         "Total operating income", "Service revenue"])
    pat = find_val(["Profit after tax", "Profit for the year", "Profit for the period",
                     "Net profit"], 
                    exclude=["retained", "balance", "total equity"])
    pbt = find_val(["Profit before tax", "Profit before income tax"],
                    exclude=["deferred"])
    eps = find_val(["Earnings per share", "Basic earnings per share", "Basic eps"], is_ratio=True)
    dps = find_val(["Dividend per share", "Dividends per share"], is_ratio=True)
    assets = find_val(["Total assets"])
    equity = find_val(["Total equity", "Total shareholders", "Shareholders' equity"])
    ebitda = find_val(["EBITDA"])
    
    return {
        "net_interest_income": None,
        "revenue": scale(revenue),
        "profit_before_tax": scale(pbt),
        "profit_after_tax": scale(pat),
        "basic_eps": eps,
        "dividend_per_share": dps,
        "total_assets": scale(assets),
        "total_equity": scale(equity),
        "customer_deposits": None,
        "loans_and_advances": None,
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": scale(ebitda),
        "mpesa_revenue": None,
    }

# ── Main processing ───────────────────────────────────────────────────────────

def classify_company(ticker: Optional[str], filename: str, text: str) -> str:
    if ticker in BANK_TICKERS:
        return "bank"
    probe = (filename + " " + text[:500]).lower()
    if "safaricom" in probe:
        return "telco"
    if any(k in probe for k in ["bank", "stanchart", "stanbic"]):
        return "bank"
    return "generic"

def extract_company_name(filename: str, index_company: Optional[str]) -> str:
    if index_company:
        return index_company
    name = Path(filename).stem
    name = re.sub(r'_\d{1,2}_[A-Za-z]+_\d{4}.*', '', name)
    return name.replace('_', ' ').strip()

def scan_all_pdfs(min_year: int = 0) -> List[Path]:
    pdfs = []
    for year_dir in sorted(DATA_ROOT.iterdir()):
        if year_dir.is_dir() and year_dir.name.isdigit():
            if min_year and int(year_dir.name) < min_year:
                continue
            pdfs.extend(sorted(year_dir.glob("*.pdf")))
    return pdfs

def load_index_company_map() -> Dict[str, Dict]:
    index_file = DATA_ROOT / "index_2023_2025.json"
    if not index_file.exists():
        return {}
    with index_file.open(encoding="utf-8") as f:
        raw = json.load(f)
    items = list(raw.values()) if isinstance(raw, dict) else raw
    result = {}
    for item in items:
        if isinstance(item, dict) and item.get("local_path"):
            result[Path(item["local_path"]).name] = item
    return result

def process_pdf(pdf_path: Path, index_entry: Optional[Dict]) -> Optional[Dict]:
    filename = pdf_path.name
    company_name = extract_company_name(filename, index_entry.get("company") if index_entry else None)
    ticker = get_ticker(company_name) or get_ticker_from_filename(filename)
    
    period_label, period_end_date, period_type = parse_period_from_filename(filename)
    if index_entry and index_entry.get("period"):
        period_label = index_entry["period"]
    
    try:
        text = extract_text(pdf_path)
    except Exception as e:
        print(f"  ✗ {filename}: {e}", file=sys.stderr)
        return None
    
    if not text or len(text.strip()) < 100:
        print(f"  ⚠ {filename}: empty/scanned PDF, skipping")
        return None
    
    company_type = classify_company(ticker, filename, text)
    
    # Extract based on company type
    if company_type == "bank" and detect_cbk_format(text):
        metrics = extract_cbk_bank(text, filename)
    elif company_type == "telco":
        metrics = extract_safaricom(text, filename)
    else:
        metrics = extract_generic(text, filename)
    
    year = int(period_end_date[:4]) if period_end_date else None
    
    return {
        "company": company_name,
        "ticker": ticker,
        "sector": SECTOR_MAP.get(ticker, "Other") if ticker else "Other",
        "period": period_label,
        "period_end_date": period_end_date,
        "period_type": period_type,
        "year": year,
        "source_file": filename,
        "url": index_entry.get("url", "") if index_entry else "",
        **metrics,
    }

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    
    raw_args = sys.argv[1:]
    min_year = 0
    company_filters = []
    i = 0
    while i < len(raw_args):
        if raw_args[i] == "--since" and i + 1 < len(raw_args):
            min_year = int(raw_args[i + 1])
            i += 2
        else:
            company_filters.append(raw_args[i].lower())
            i += 1
    
    if min_year:
        print(f"Filtering to years >= {min_year}")
    if company_filters:
        print(f"Filtering to companies: {company_filters}")
    
    pdfs = scan_all_pdfs(min_year=min_year)
    if company_filters:
        pdfs = [p for p in pdfs if any(f in p.name.lower() for f in company_filters)]
    print(f"Processing {len(pdfs)} PDF files.")
    
    index_map = load_index_company_map()
    print(f"Index has {len(index_map)} entries for cross-referencing.")
    
    results = []
    errors = 0
    
    for i, pdf_path in enumerate(pdfs, 1):
        filename = pdf_path.name
        index_entry = index_map.get(filename)
        print(f"[{i}/{len(pdfs)}] {filename[:70]}")
        
        entry = process_pdf(pdf_path, index_entry)
        if entry:
            results.append(entry)
        else:
            errors += 1
    
    # Merge if filtered
    if company_filters and OUTPUT_FILE.exists():
        with OUTPUT_FILE.open(encoding="utf-8") as f:
            existing = json.load(f)
        new_tickers = {r.get("ticker") for r in results}
        kept = [r for r in existing if r.get("ticker") not in new_tickers]
        results = kept + results
        print(f"Merged: kept {len(kept)} existing + {len(results) - len(kept)} new")
    
    print(f"\n✓ Extracted: {len(results)}  Errors: {errors}")
    print(f"Writing to {OUTPUT_FILE}")
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Summary
    companies: Dict[str, int] = {}
    for r in results:
        c = r.get("ticker") or r.get("company", "?")
        companies[c] = companies.get(c, 0) + 1
    print("\nCompany summary:")
    for c, count in sorted(companies.items()):
        print(f"  {c}: {count} periods")
    print("\n✓ Done")

if __name__ == "__main__":
    main()
