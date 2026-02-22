"""
Audit PDFs for ABSA, Standard Chartered, and Safaricom.

For each PDF:
- Extract text
- Detect if it's Group or Company (unconsolidated)
- Extract key financial metrics
- Compare to what's in financials.json
- Print a detailed comparison report

Usage (from backend/ with venv active):
    python audit_company_pdfs.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import pdfplumber

# Force UTF-8 output on Windows (avoids cp1252 encoding errors with Unicode chars)
sys.stdout.reconfigure(encoding="utf-8")

DATA_ROOT = Path(__file__).parent.parent / "data" / "nse"
FINANCIALS_JSON = DATA_ROOT / "financials.json"

# Target companies and the keywords to find them in filenames
TARGETS = {
    "ABSA": ["ABSA_Bank_Kenya", "Absa_Bank_Kenya"],
    "StanChart": ["Standard_Chartered_Bank_Kenya", "Standard_Chartered_Bank_Ltd"],
    "Safaricom": ["Safaricom"],
}

# ── Text extraction ────────────────────────────────────────────────────────────

def extract_text(pdf_path: Path, max_pages: int = 20) -> str:
    """Extract text from first N pages of a PDF."""
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:max_pages]:
            t = page.extract_text() or ""
            if t:
                chunks.append(t)
    return "\n".join(chunks)

def extract_all_text(pdf_path: Path) -> str:
    """Extract text from all pages."""
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t:
                chunks.append(t)
    return "\n".join(chunks)

# ── Group vs Company detection ─────────────────────────────────────────────────

def detect_consolidation(text: str) -> str:
    """Detect if financial statements are Group or Company level."""
    text_lower = text.lower()
    first_2000 = text_lower[:2000]
    
    has_group = any(p in first_2000 for p in [
        "consolidated", "group financial", "group results",
        "group statement", "group and company"
    ])
    has_company = any(p in first_2000 for p in [
        "company financial", "company statement", "company only",
        "bank only", "unconsolidated"
    ])
    
    if has_group and has_company:
        return "Group + Company"
    elif has_group:
        return "Group (Consolidated)"
    elif has_company:
        return "Company (Unconsolidated)"
    else:
        # Check body of document for clues
        if "consolidated" in text_lower[:5000]:
            return "Group (Consolidated)"
        return "Unknown"

# ── Financial metric extraction ────────────────────────────────────────────────

NUMBER_RE = re.compile(r"([-]?[0-9][0-9,\s]*\.?[0-9]*)")

def _parse_num(text: str) -> Optional[float]:
    """Parse the first number from a string (in thousands by default)."""
    cleaned = text.replace("\u00a0", " ").replace(" ", "")
    m = NUMBER_RE.search(cleaned)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "").replace(" ", ""))
    except ValueError:
        return None

def find_value_near(lines: List[str], *patterns: str, context_lines: int = 3) -> Tuple[Optional[float], Optional[str]]:
    """Find a numeric value near a pattern match. Returns (value, matched_line)."""
    pats_lower = [p.lower() for p in patterns]
    for i, line in enumerate(lines):
        low = line.lower()
        if any(p in low for p in pats_lower):
            # Try to get number from same line first
            val = _parse_num(line)
            if val is not None and val != 0:
                return val, line
            # Try next few lines
            for j in range(1, context_lines + 1):
                if i + j < len(lines):
                    val = _parse_num(lines[i + j])
                    if val is not None:
                        return val, lines[i + j]
    return None, None

def extract_bank_metrics(text: str) -> Dict[str, Any]:
    """Extract metrics specific to banking companies (ABSA, StanChart)."""
    lines = [" ".join(l.split()) for l in text.splitlines() if l.strip()]
    
    metrics = {}
    
    # Net Interest Income — primary revenue line for banks
    val, src = find_value_near(lines, "net interest income")
    metrics["net_interest_income"] = {"value": val, "source_line": src}
    
    # Total income / operating income
    val, src = find_value_near(lines, "total operating income", "total income", "net operating income")
    metrics["total_income"] = {"value": val, "source_line": src}
    
    # Operating expenses
    val, src = find_value_near(lines, "total operating expenses", "operating expenses")
    metrics["operating_expenses"] = {"value": val, "source_line": src}
    
    # Profit before tax
    val, src = find_value_near(lines, "profit before tax", "profit before income tax")
    metrics["profit_before_tax"] = {"value": val, "source_line": src}
    
    # Profit after tax
    val, src = find_value_near(lines, "profit after tax", "profit for the year", "profit for the period")
    metrics["profit_after_tax"] = {"value": val, "source_line": src}
    
    # Basic EPS
    val, src = find_value_near(lines, "basic earnings per share", "earnings per share")
    metrics["basic_eps"] = {"value": val, "source_line": src}
    
    # Dividend per share
    val, src = find_value_near(lines, "dividend per share", "dividends per share")
    metrics["dividend_per_share"] = {"value": val, "source_line": src}
    
    # Total assets
    val, src = find_value_near(lines, "total assets")
    metrics["total_assets"] = {"value": val, "source_line": src}
    
    # Total equity
    val, src = find_value_near(lines, "total equity", "shareholders' equity", "shareholders equity", "shareholders' funds")
    metrics["total_equity"] = {"value": val, "source_line": src}
    
    # Customer deposits
    val, src = find_value_near(lines, "customer deposits", "deposits from customers")
    metrics["customer_deposits"] = {"value": val, "source_line": src}
    
    # Loans and advances
    val, src = find_value_near(lines, "loans and advances to customers", "net loans and advances")
    metrics["loans_and_advances"] = {"value": val, "source_line": src}
    
    # NPL / impairment
    val, src = find_value_near(lines, "loan loss", "impairment losses", "credit impairment")
    metrics["impairment_charges"] = {"value": val, "source_line": src}
    
    # Capital adequacy
    val, src = find_value_near(lines, "core capital ratio", "total capital ratio", "capital adequacy")
    metrics["capital_ratio"] = {"value": val, "source_line": src}

    return metrics

def extract_telco_metrics(text: str) -> Dict[str, Any]:
    """Extract metrics for Safaricom (telco)."""
    lines = [" ".join(l.split()) for l in text.splitlines() if l.strip()]
    
    metrics = {}
    
    # Revenue
    val, src = find_value_near(lines, "total revenue", "revenue")
    metrics["revenue"] = {"value": val, "source_line": src}
    
    # EBITDA
    val, src = find_value_near(lines, "ebitda", "earnings before interest")
    metrics["ebitda"] = {"value": val, "source_line": src}
    
    # Operating profit
    val, src = find_value_near(lines, "operating profit", "profit from operations")
    metrics["operating_profit"] = {"value": val, "source_line": src}
    
    # Profit before tax
    val, src = find_value_near(lines, "profit before tax")
    metrics["profit_before_tax"] = {"value": val, "source_line": src}
    
    # Profit after tax
    val, src = find_value_near(lines, "profit after tax", "profit for the year", "profit for the period")
    metrics["profit_after_tax"] = {"value": val, "source_line": src}
    
    # EPS
    val, src = find_value_near(lines, "basic earnings per share", "earnings per share")
    metrics["basic_eps"] = {"value": val, "source_line": src}
    
    # DPS
    val, src = find_value_near(lines, "dividend per share")
    metrics["dividend_per_share"] = {"value": val, "source_line": src}
    
    # Total assets
    val, src = find_value_near(lines, "total assets")
    metrics["total_assets"] = {"value": val, "source_line": src}
    
    # M-Pesa revenue
    val, src = find_value_near(lines, "m-pesa", "mpesa")
    metrics["mpesa_revenue"] = {"value": val, "source_line": src}
    
    # Subscribers
    val, src = find_value_near(lines, "total subscribers", "active customers", "subscribers")
    metrics["subscribers"] = {"value": val, "source_line": src}
    
    # Free Cash Flow
    val, src = find_value_near(lines, "free cash flow", "net cash from operating")
    metrics["operating_cash_flow"] = {"value": val, "source_line": src}
    
    # Capex
    val, src = find_value_near(lines, "capital expenditure", "capex", "purchase of property")
    metrics["capex"] = {"value": val, "source_line": src}

    return metrics

# ── Report printing ────────────────────────────────────────────────────────────

def print_divider(char="-", width=80):
    print(char * width)

def print_metrics(metrics: Dict[str, Any]):
    for key, data in metrics.items():
        val = data.get("value")
        src = data.get("source_line", "")
        if val is not None:
            # Truncate source line
            src_short = (src[:70] + "…") if src and len(src) > 70 else src or ""
            print(f"  {key:<30} {val:>15,.0f}    ← {src_short}")
        else:
            print(f"  {key:<30} {'[not found]':>15}")

# ── Main audit ─────────────────────────────────────────────────────────────────

def find_pdfs_for_company(company_key: str) -> List[Path]:
    """Find all PDFs for a given company across all year directories."""
    keywords = TARGETS[company_key]
    pdfs = []
    for year_dir in sorted(DATA_ROOT.iterdir()):
        if not year_dir.is_dir():
            continue
        for pdf in sorted(year_dir.glob("*.pdf")):
            if any(kw in pdf.name for kw in keywords):
                pdfs.append(pdf)
    return pdfs

def load_json_data_for_company(company_key: str) -> List[Dict]:
    """Load existing financials.json entries for a company."""
    keywords = {
        "ABSA": ["ABSA", "Absa"],
        "StanChart": ["Standard Chartered"],
        "Safaricom": ["Safaricom"],
    }
    
    if not FINANCIALS_JSON.exists():
        return []
    
    with FINANCIALS_JSON.open() as f:
        all_data = json.load(f)
    
    kws = keywords[company_key]
    return [d for d in all_data if any(kw in (d.get("company") or "") for kw in kws)]

def audit_company(company_key: str, extractor_fn):
    print_divider("=")
    print(f"  AUDIT: {company_key}")
    print_divider("=")
    
    pdfs = find_pdfs_for_company(company_key)
    json_entries = load_json_data_for_company(company_key)
    
    print(f"\n  PDFs found: {len(pdfs)}")
    print(f"  JSON entries: {len(json_entries)}\n")
    
    # Map JSON entries by period for quick lookup
    json_by_period = {e.get("period", ""): e for e in json_entries}
    
    for pdf_path in pdfs:
        print_divider()
        print(f"  FILE: {pdf_path.parent.name}/{pdf_path.name}")
        
        try:
            text = extract_text(pdf_path, max_pages=15)
        except Exception as e:
            print(f"  WARNING: ERROR reading PDF: {e}")
            continue
        
        consolidation = detect_consolidation(text)
        print(f"  CONSOLIDATION: {consolidation}")
        
        metrics = extractor_fn(text)
        print(f"\n  EXTRACTED METRICS:")
        print_metrics(metrics)
        
        # Cross-check with JSON
        # Try to find matching JSON entry
        matching_json = None
        for period, entry in json_by_period.items():
            # Match by filename containing period indicators
            pdf_name_lower = pdf_path.name.lower()
            if period and any(p in pdf_name_lower for p in [
                period.lower().replace("-", "_"),
                period.lower().replace("-", " "),
            ]):
                matching_json = entry
                break
        
        if matching_json:
            print(f"\n  JSON MATCH FOUND (period: {matching_json.get('period', '?')}):")
            # Compare key fields
            comparisons = [
                ("revenue/total_income", matching_json.get("revenue")),
                ("total_assets", matching_json.get("total_assets")),
                ("total_equity", matching_json.get("total_equity")),
                ("profit_after_tax", matching_json.get("profit_after_tax")),
                ("basic_eps", matching_json.get("basic_eps")),
            ]
            for field_name, json_val in comparisons:
                pdf_val = None
                # Try to get corresponding metric from extracted
                for mkey in [field_name, "total_income", "profit_after_tax", "basic_eps", "total_assets", "total_equity"]:
                    if mkey in metrics and metrics[mkey]["value"] is not None:
                        pdf_val = metrics[mkey]["value"]
                        break
                
                if json_val is not None:
                    diff_str = ""
                    if pdf_val is not None:
                        diff = abs(pdf_val - json_val) / max(abs(json_val), 1) * 100
                        diff_str = f"  (diff: {diff:.1f}%)"
                    print(f"  {field_name:<30} JSON={json_val:>15,.0f}  PDF≈{pdf_val!s:>15}{diff_str}")
                else:
                    print(f"  {field_name:<30} JSON=[null]  PDF≈{pdf_val!s:>15}")
        else:
            print(f"\n  WARNING: No matching JSON entry found for this PDF")
        
        print()
    
    print(f"\n  COVERAGE SUMMARY for {company_key}:")
    print(f"  PDFs available: {[str(p.parent.name) + '/' + p.name for p in pdfs]}")
    missing_pdfs = []
    for entry in json_entries:
        period = str(entry.get("period") or "")
        pdf_names = [str(p.name) for p in pdfs]
        # Check if any PDF might correspond to this period
        if period:
            found = any(period.replace("-", "_") in n or period.replace("-","").replace(" ","") in n.replace("_","").replace("-","") for n in pdf_names)
        else:
            found = False
        if not found:
            missing_pdfs.append(f"JSON entry period={period!r} has no obvious matching PDF")
    if missing_pdfs:
        for m in missing_pdfs:
            print(f"  WARNING: {m}")
    print()


def main():
    print("\nKENYA STOCKS — PDF AUDIT REPORT")
    print(f"Generated: 2026-02-22\n")
    
    audit_company("ABSA", extract_bank_metrics)
    audit_company("StanChart", extract_bank_metrics)
    audit_company("Safaricom", extract_telco_metrics)
    
    print_divider("=")
    print("AUDIT COMPLETE")
    print_divider("=")


if __name__ == "__main__":
    main()

