"""
JSE-specific financial extractor that handles:
- Space-separated thousands (e.g., 25 202 = 25,202)
- South African/European number formats
- Table-based layouts in PDFs
- Narrative text with numbers (US$5.5bn)
"""
import json
import re
import pypdf
from pathlib import Path

OUTPUT_BASE = Path("data/jse")

KEYWORDS_REVENUE = [
    r'revenue',
    r'total revenue',
    r'operating revenue',
    r'turnover',
]

KEYWORDS_PAT = [
    r'profit (?:after (?:taxation|tax)|for the (?:year|period))',
    r'net profit',
    r'net income',
    r'profit after tax',
]

KEYWORDS_PBT = [
    r'(?:normalised\s+)?profit before (?:taxation|tax)',
    r'income before tax',
]

KEYWORDS_EPS = [
    r'(?:basic|adjusted|diluted|headline)?\s*(?:earnings|heps|eps) per (?:ordinary )?share',
    r'eps',
]

KEYWORDS_DPS = [
    r'dividend(?:s)? per (?:ordinary )?share',
    r'total dividend',
]

KEYWORDS_ASSETS = [
    r'total assets',
]

KEYWORDS_EQUITY = [
    r'total equity',
    r"(?:shareholders'?|equity holders'?) equity",
    r'equity attributable',
]

KEYWORDS_EBITDA = [
    r'(?:normalised\s+)?ebitda',
]


def extract_number_from_text(text: str, keywords: list) -> float | None:
    """
    Try multiple strategies to extract a number following a keyword.
    Handles:
    - Standard: "Revenue: 25,202" 
    - Space-sep: "Revenue 25 202"
    - Narrative: "revenue grew to R25.2bn"
    - Table row: "Revenue  25 202  23 699  6.3"
    """
    
    # Strategy 1: keyword followed by space-separated number (SA table format)
    # e.g., "Revenue 25 202 23 699"
    for kw in keywords:
        pattern = rf'(?i){kw}\s+(-?\d{{1,3}}(?:\s\d{{3}})+)'
        m = re.search(pattern, text)
        if m:
            val = float(m.group(1).replace(' ', ''))
            if abs(val) > 100:
                return val
    
    # Strategy 2: keyword then colon/whitespace then comma-separated number
    for kw in keywords:
        pattern = rf'(?i){kw}[:\s]+(-?\d{{1,3}}(?:,\d{{3}})+(?:\.\d+)?)'
        m = re.search(pattern, text)
        if m:
            val = float(m.group(1).replace(',', ''))
            if abs(val) > 100:
                return val
    
    # Strategy 3: keyword then a plain number (possibly decimal)
    for kw in keywords:
        pattern = rf'(?i){kw}[:\s]+(-?\d+(?:\.\d+)?)'
        m = re.search(pattern, text)
        if m:
            val = float(m.group(1))
            if abs(val) > 1000:
                return val
    
    # Strategy 4: billions notation "R25.2bn" / "US$5.5bn"
    for kw in keywords:
        pattern = rf'(?i){kw}[^\n]{{0,60}}(?:R|ZAR|US\$|USD)\s*(\d+(?:\.\d+)?)\s*(?:bn|billion)'
        m = re.search(pattern, text)
        if m:
            return float(m.group(1)) * 1_000_000_000
    
    # Strategy 5: millions notation "R25 202m" / "R25 202 million"
    for kw in keywords:
        pattern = rf'(?i){kw}[^\n]{{0,60}}(?:R|ZAR|US\$)?\s*(\d+(?:\s\d{{3}})*)\s*(?:m|million)'
        m = re.search(pattern, text)
        if m:
            val = float(m.group(1).replace(' ', ''))
            if val > 0:
                return val * 1_000_000
    
    return None


def extract_per_share(text: str, keywords: list) -> float | None:
    """Extract per-share metrics which tend to be small decimal numbers."""
    for kw in keywords:
        # Pattern: keyword followed by a number like "113.7" or "1 134.5"
        pattern = rf'(?i){kw}[:\s\(]+(-?\d+(?:\.\d+)?)\s*(?:cents?|c\b)'
        m = re.search(pattern, text)
        if m:
            val = float(m.group(1))
            if 0 < val < 100000:
                return val / 100  # convert cents to ZAR
    
    # Without cents indicator
    for kw in keywords:
        pattern = rf'(?i){kw}[:\s\(]+(-?\d+(?:\.\d+)?)'
        m = re.search(pattern, text)
        if m:
            val = float(m.group(1))
            if 0 < abs(val) < 100000:
                return val
    
    return None


def detect_year(text: str, filename: str) -> int | None:
    m = re.search(r'\b(20\d{2})\b', filename)
    if m:
        return int(m.group(1))
    m = re.search(r'year ended[^\n]{0,60}(20\d{2})', text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Extract all years mentioned, take most common
    years = re.findall(r'\b(20\d{2})\b', text)
    if years:
        from collections import Counter
        return int(Counter(years).most_common(1)[0][0])
    return None


def detect_scale(text: str) -> float:
    """Detect if numbers in tables are in millions/thousands."""
    # Look for scale indicators
    if re.search(r'\bR\s*million\b|\bRm\b|\bin millions\b|expressed in millions', text, re.IGNORECASE):
        return 1_000_000
    if re.search(r'\bin thousands\b|R\s*thousand|expressed in thousands', text, re.IGNORECASE):
        return 1_000
    if re.search(r'\bR\s*billion\b|\bin billions\b', text, re.IGNORECASE):
        return 1_000_000_000
    return 1_000_000  # Default: assume millions for JSE


def extract_from_pdf(pdf_path: str, ticker: str) -> dict:
    with open(pdf_path, 'rb') as f:
        pdf = pypdf.PdfReader(f)
        text = ""
        for page in pdf.pages[:25]:
            t = page.extract_text()
            if t:
                # Normalize non-breaking spaces and thin spaces to regular spaces
                t = t.replace('\xa0', ' ').replace('\u2009', ' ').replace('\u202f', ' ')
                text += t + "\n"
    
    filename = Path(pdf_path).stem
    scale = detect_scale(text)
    year = detect_year(text, filename)
    
    # Detect period type
    period_type = "annual"
    if re.search(r'\b(h1|half.?year|six.?months|interim)\b', text + filename, re.IGNORECASE):
        period_type = "half_year"
    
    # Extract metrics
    revenue = extract_number_from_text(text, KEYWORDS_REVENUE)
    pat = extract_number_from_text(text, KEYWORDS_PAT)
    pbt = extract_number_from_text(text, KEYWORDS_PBT)
    assets = extract_number_from_text(text, KEYWORDS_ASSETS)
    equity = extract_number_from_text(text, KEYWORDS_EQUITY)
    ebitda = extract_number_from_text(text, KEYWORDS_EBITDA)
    eps = extract_per_share(text, KEYWORDS_EPS)
    dps = extract_per_share(text, KEYWORDS_DPS)
    
    # Scale up if values seem to be in millions
    def scale_val(v):
        if v is None:
            return None
        # If v looks like it's already in millions range and scale suggests millions
        # e.g., revenue=25202 with scale=1M means 25202 * 1M = 25.2B ZAR
        # But we need to be careful: if v=25202 and scale=1M, that's 25.2 trillion which is wrong
        # NTC revenue is 25,202 million ZAR = 25.2B ZAR
        # So table value 25202 * 1M would give 25.2T (wrong)
        # Actually 25202 IS in millions per the "Rm" indicator, so final = 25202 * 1M
        # Let's just store as-is (in millions) and note the unit
        return v  # Keep raw table value; caller knows scale
    
    return {
        "ticker": ticker,
        "source_file": Path(pdf_path).name,
        "year": year,
        "period_type": period_type,
        "currency": "ZAR",
        "scale_unit": "millions" if scale == 1_000_000 else ("thousands" if scale == 1_000 else "billions"),
        "revenue": revenue,
        "profit_before_tax": pbt,
        "profit_after_tax": pat,
        "total_assets": assets,
        "total_equity": equity,
        "ebitda": ebitda,
        "basic_eps": eps,
        "dividend_per_share": dps,
    }


# Process all PDFs
results = []
failures = []
tickers = ["BHG", "ANH", "BTI", "NTC", "PRX"]

for ticker in tickers:
    ticker_dir = OUTPUT_BASE / ticker
    if not ticker_dir.exists():
        continue
    for pdf in sorted(ticker_dir.glob("*.pdf")):
        print(f"Extracting {ticker}/{pdf.name}...")
        try:
            record = extract_from_pdf(str(pdf), ticker)
            results.append(record)
            print(f"  revenue={record['revenue']}, PAT={record['profit_after_tax']}, assets={record['total_assets']}, EPS={record['basic_eps']}, DPS={record['dividend_per_share']}")
        except Exception as e:
            print(f"  ERROR: {e}")
            failures.append({"ticker": ticker, "file": pdf.name, "reason": str(e)})

# Save
out_data = {"records": results, "failures": failures}
out_path = OUTPUT_BASE / "financials_test.json"
with open(out_path, "w") as f:
    json.dump(out_data, f, indent=2, default=str)

print(f"\nTotal records: {len(results)}, failures: {len(failures)}")
print(f"Saved to: {out_path}")
