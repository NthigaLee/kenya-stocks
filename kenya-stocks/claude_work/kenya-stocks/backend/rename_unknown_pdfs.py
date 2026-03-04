"""
rename_unknown_pdfs.py — Identify and rename PDFs with "unknown" in filename.

Strategy:
1. Find all files with "unknown" in name across data/nse/[year]/ folders
2. Extract PDF metadata (title, subject, creator)
3. Extract first page text to find company name and period
4. Parse company name and date using TICKER_MAP and date patterns
5. Rename file to: CompanyName_DD_MonthAbr_YYYY_[audited|financials].pdf
6. Create audit log of results

Usage: python rename_unknown_pdfs.py --dry-run (preview changes)
       python rename_unknown_pdfs.py --apply (rename files)
"""

from __future__ import annotations
import json, re, sys, os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple
import pdfplumber

BACKEND_DIR = Path(__file__).parent
DATA_ROOT = BACKEND_DIR.parent / "data" / "nse"
AUDIT_FILE = DATA_ROOT / "unknown_files_audit.json"

# Ticker mappings to identify companies
TICKER_MAP = {
    "absa": "ABSA", "standard chartered": "SCBK", "safaricom": "SCOM",
    "equity group": "EQTY", "equity bank": "EQTY", "kcb": "KCB",
    "ncba": "NCBA", "co-operative bank": "COOP", "co_operative": "COOP",
    "diamond trust": "DTK", "dtb": "DTK", "stanbic": "CFC",
    "i&m": "IMH", "i and m": "IMH", "family bank": "FANB",
    "hf group": "HFCK", "housing finance": "HFCK",
    "east african breweries": "EABL", "eabl": "EABL",
    "bamburi": "BAMB", "bat kenya": "BATK", "britam": "BRIT",
    "jubilee": "JUB", "sanlam": "SLAM", "kenya power": "KPLC",
    "kengen": "KEGN", "nation media": "NMG", "nse": "NSE",
    "standard group": "SGL", "wpp scangroup": "SCAN", "bk group": "BKG",
    "unga group": "UNGA", "sasini": "SASN", "williamson tea": "WTK",
    "kapchorua tea": "KAPA", "carbacid": "CARB", "boc kenya": "BOC",
    "home afrika": "HAFR", "homeboyz": "HBZE", "transcentury": "TCL",
    "tps eastern africa": "TPSE", "express kenya": "XPRS", "flame tree": "FTGH",
    "crown paints": "CPKL", "east african portland": "EAPC", "umeme": "UMME",
    "i_m_group": "IMH", "i_m_holdings": "IMH", "i_m bank": "IMH",
}

# Reverse map for known company names to tickers
COMPANY_NAME_MAP = {
    "absa bank kenya": "ABSA", "absa bank kenya plc": "ABSA",
    "standard chartered bank": "SCBK", "standard chartered bank kenya": "SCBK",
    "safaricom": "SCOM", "safaricom plc": "SCOM",
    "equity group holdings": "EQTY", "equity bank": "EQTY",
    "kcb group": "KCB", "kcb bank": "KCB",
    "ncba group": "NCBA", "ncba bank": "NCBA",
    "co-operative bank of kenya": "COOP", "cooperative bank": "COOP",
    "diamond trust bank": "DTK", "diamond trust": "DTK",
    "stanbic holdings": "CFC", "stanbic": "CFC",
    "i&m holdings": "IMH", "i and m holdings": "IMH",
    "family bank": "FANB", "family bank ltd": "FANB",
    "housing finance": "HFCK", "hf group": "HFCK",
    "east african breweries": "EABL",
    "bamburi cement": "BAMB", "bamburi": "BAMB",
    "bat kenya": "BATK", "british american tobacco": "BATK",
    "britam holdings": "BRIT", "britam": "BRIT",
    "jubilee holdings": "JUB", "jubilee": "JUB",
    "sanlam kenya": "SLAM", "sanlam": "SLAM",
    "kenya power and lighting": "KPLC", "kenya power": "KPLC",
    "kengen": "KEGN", "kenyatta energy": "KEGN",
    "nation media group": "NMG", "nation media": "NMG",
    "kenya power & lighting": "KPLC",
    "wpp scangroup": "SCAN", "scangroup": "SCAN",
    "bk group": "BKG", "bk group plc": "BKG",
    "unga group": "UNGA", "unga": "UNGA",
    "sasini": "SASN", "sasini plc": "SASN",
    "williamson tea": "WTK", "williamson tea kenya": "WTK",
    "kapchorua tea": "KAPA", "kapchorua": "KAPA",
    "carbacid": "CARB", "carbacid products": "CARB",
    "boc kenya": "BOC", "boc": "BOC",
    "home afrika": "HAFR", "home africa": "HAFR",
    "homeboyz": "HBZE", "homeboyz entertainment": "HBZE",
    "transcentury": "TCL", "transcentury limited": "TCL",
    "tps eastern africa": "TPSE", "tps": "TPSE",
    "express kenya": "XPRS", "express": "XPRS",
    "flame tree": "FTGH", "flame tree group": "FTGH",
    "crown paints": "CPKL", "crown paints kenya": "CPKL",
    "east african portland": "EAPC", "eapc": "EAPC",
    "umeme": "UMME",
    "nairobi business ventures": "NBV", "nairobi business ventures plc": "NBV",
    "olympia capital holdings": "OCH", "olympia capital": "OCH",
}

def extract_text_from_pdf(pdf_path: Path) -> Optional[str]:
    """Extract first page text from PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                return pdf.pages[0].extract_text() or ""
    except Exception as e:
        pass
    return None

def extract_metadata_from_pdf(pdf_path: Path) -> Dict[str, Optional[str]]:
    """Extract metadata from PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            metadata = pdf.metadata
            return {
                "title": metadata.get("Title") if metadata else None,
                "subject": metadata.get("Subject") if metadata else None,
                "creator": metadata.get("Creator") if metadata else None,
            }
    except:
        pass
    return {"title": None, "subject": None, "creator": None}

def parse_company_from_text(text: str) -> Optional[str]:
    """Extract company name from PDF text."""
    if not text:
        return None

    # Look for common patterns
    lines = text.split('\n')[:20]  # First 20 lines
    text_lower = text.lower()[:1000]  # First 1000 chars

    # Check against known company names
    for company_name, ticker in COMPANY_NAME_MAP.items():
        if company_name in text_lower:
            return company_name

    # Check for ticker keywords
    for keyword, ticker in TICKER_MAP.items():
        if keyword in text_lower:
            return keyword

    return None

def parse_date_from_text(text: str, filename_hint: str = "") -> Optional[Tuple[str, str]]:
    """
    Extract date from PDF text.
    Returns: (day_month_year_str, period_type)
    Example: ("30_Jun_2023", "annual")
    """
    if not text:
        return None

    # Normalize month names
    month_map = {
        'jan': 'Jan', 'january': 'Jan',
        'feb': 'Feb', 'february': 'Feb',
        'mar': 'Mar', 'march': 'Mar',
        'apr': 'Apr', 'april': 'Apr',
        'may': 'May',
        'jun': 'Jun', 'june': 'Jun',
        'jul': 'Jul', 'july': 'Jul',
        'aug': 'Aug', 'august': 'Aug',
        'sep': 'Sep', 'september': 'Sep',
        'oct': 'Oct', 'october': 'Oct',
        'nov': 'Nov', 'november': 'Nov',
        'dec': 'Dec', 'december': 'Dec',
    }

    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Pattern 1: "for the period ended XX Month YYYY" or "for the year ended"
    pattern1 = r'for\s+the\s+(?:period|year)\s+ended\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)[,\s]+(\d{4})'
    match = re.search(pattern1, text, re.IGNORECASE)

    if match:
        day, month_str, year = match.groups()
        day = day.zfill(2)
        month = month_map.get(month_str.lower(), month_str[:3].capitalize())

        if month in month_list:
            month_num = month_list.index(month) + 1
            period_type = "audited" if month_num in [12, 6] else "financials"
            return (f"{day}_{month}_{year}", period_type)

    # Pattern 2: "ended XX Month YYYY" (more flexible)
    pattern2 = r'ended\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)[,\s]+(\d{4})'
    match = re.search(pattern2, text, re.IGNORECASE)

    if match:
        day, month_str, year = match.groups()
        day = day.zfill(2)
        month = month_map.get(month_str.lower(), month_str[:3].capitalize())

        if month in month_list:
            month_num = month_list.index(month) + 1
            period_type = "audited" if month_num in [12, 6] else "financials"
            return (f"{day}_{month}_{year}", period_type)

    # Pattern 3: "31ST DECEMBER 2019" format
    pattern3 = r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})'
    matches = re.finditer(pattern3, text, re.IGNORECASE)

    for match in matches:
        day, month_str, year = match.groups()
        month = month_map.get(month_str.lower(), month_str[:3].capitalize())

        if month in month_list:
            day = day.zfill(2)
            month_num = month_list.index(month) + 1
            period_type = "audited" if month_num in [12, 6] else "financials"
            return (f"{day}_{month}_{year}", period_type)

    return None

def guess_from_filename(filename: str) -> Optional[Tuple[str, str, str]]:
    """
    Try to extract company name and date from filename itself.
    Returns: (company_name, day_month_year, period_type) or None
    """
    name = filename.replace('.pdf', '')

    # Pattern 1: CompanyName_DD_Month_YYYY
    pattern = r'([A-Za-z_]+)_(\d{1,2})_([A-Za-z]+)_(\d{4})'
    match = re.search(pattern, name)
    if match:
        company_part, day, month_str, year = match.groups()
        day = day.zfill(2)
        month_map = {
            'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr',
            'May': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Aug',
            'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dec': 'Dec',
        }
        month = month_map.get(month_str, month_str)
        date_str = f"{day}_{month}_{year}"
        period_type = "audited" if month in ['Jun', 'Dec'] else "financials"

        # Normalize company name
        company_clean = company_part.replace('_', ' ')
        company_key = company_clean.lower()
        ticker = COMPANY_NAME_MAP.get(company_key)

        if ticker:
            return (company_clean, date_str, period_type)

    # Pattern 2: DD_Month_YYYY (no company name)
    pattern = r'(\d{1,2})_([A-Za-z]+)_(\d{4})'
    match = re.search(pattern, name)
    if match:
        day, month_str, year = match.groups()
        day = day.zfill(2)
        return (None, f"{day}_{month_str}_{year}", "audited")

    return None

def rename_file(pdf_path: Path, dry_run: bool = True) -> Dict:
    """
    Analyze PDF file and determine new name.
    Returns: {"status": "success|failed", "original": "", "new_name": "", "reason": ""}
    """
    filename = pdf_path.name

    result = {
        "file": filename,
        "status": "unknown",
        "new_name": None,
        "reason": "",
        "company": None,
        "date": None,
    }

    # Try filename parsing first
    filename_parse = guess_from_filename(filename)
    if filename_parse and filename_parse[0]:
        company, date_str, period_type = filename_parse
        new_name = f"{company}_{date_str}_{period_type}.pdf"
        result["status"] = "success"
        result["new_name"] = new_name
        result["company"] = company
        result["date"] = date_str
        result["reason"] = "Parsed from filename"
    else:
        # Try PDF content
        text = extract_text_from_pdf(pdf_path)
        company = parse_company_from_text(text or "")
        date_info = parse_date_from_text(text or "", filename)

        if company and date_info:
            date_str, period_type = date_info
            company_clean = company.replace('_', ' ')
            new_name = f"{company_clean}_{date_str}_{period_type}.pdf"
            result["status"] = "success"
            result["new_name"] = new_name
            result["company"] = company_clean
            result["date"] = date_str
            result["reason"] = "Extracted from PDF content"
        elif company and not date_info:
            result["status"] = "partial"
            result["company"] = company
            result["reason"] = "Found company but no date in PDF"
        elif not company and filename_parse:
            # Has date but no company name
            _, date_str, period_type = filename_parse
            new_name = f"Unknown_{date_str}_{period_type}.pdf"
            result["status"] = "partial"
            result["new_name"] = new_name
            result["date"] = date_str
            result["reason"] = "Found date but no company name"
        else:
            result["status"] = "failed"
            result["reason"] = "Could not determine company or date"

    # Perform rename if requested
    if result["status"] == "success" and result["new_name"] and not dry_run:
        try:
            new_path = pdf_path.parent / result["new_name"]
            pdf_path.rename(new_path)
            result["reason"] += " [RENAMED]"
        except Exception as e:
            result["status"] = "failed"
            result["reason"] = f"Rename failed: {str(e)}"

    return result

def main():
    """Find and rename all unknown PDF files."""
    import argparse
    parser = argparse.ArgumentParser(description="Rename unknown PDF files")
    parser.add_argument("--apply", action="store_true", help="Actually rename files (default: dry-run)")
    args = parser.parse_args()

    dry_run = not args.apply
    mode = "DRY-RUN" if dry_run else "APPLY"

    print(f"\n{'='*70}")
    print(f"RENAME UNKNOWN PDFs [{mode}]")
    print(f"{'='*70}\n")

    # Find all unknown files
    unknown_files = []
    for year_dir in DATA_ROOT.glob("*/"):
        if year_dir.is_dir() and year_dir.name not in ['absa_ir', 'absa_review']:
            for pdf_file in year_dir.glob("*.pdf"):
                if "unknown" in pdf_file.name.lower():
                    unknown_files.append(pdf_file)

    print(f"Found {len(unknown_files)} unknown files\n")

    audit_results = []
    success_count = 0
    partial_count = 0
    failed_count = 0

    for i, pdf_path in enumerate(sorted(unknown_files), 1):
        print(f"[{i}/{len(unknown_files)}] {pdf_path.relative_to(DATA_ROOT)}...", end=" ", flush=True)

        result = rename_file(pdf_path, dry_run=dry_run)
        audit_results.append(result)

        if result["status"] == "success":
            print(f"[OK] {result['new_name']}")
            success_count += 1
        elif result["status"] == "partial":
            print(f"[PARTIAL] {result['reason']}")
            partial_count += 1
        else:
            print(f"[FAIL] {result['reason']}")
            failed_count += 1

    # Write audit report
    if not dry_run:
        audit_file_path = DATA_ROOT / "unknown_files_audit.json"
    else:
        audit_file_path = DATA_ROOT / "unknown_files_audit_dryrun.json"

    with open(audit_file_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "total_files": len(unknown_files),
            "success": success_count,
            "partial": partial_count,
            "failed": failed_count,
            "results": audit_results
        }, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Results: {success_count} success, {partial_count} partial, {failed_count} failed")
    print(f"Audit report: {audit_file_path}")
    print(f"{'='*70}\n")

    if dry_run:
        print("DRY-RUN MODE: No files were actually renamed.")
        print("Run with --apply flag to rename files.")
    else:
        print("Files have been renamed!")

if __name__ == "__main__":
    main()
