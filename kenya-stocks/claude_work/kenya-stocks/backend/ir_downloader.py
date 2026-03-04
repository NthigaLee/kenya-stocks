#!/usr/bin/env python3
"""
ir_downloader.py — Download financial results PDFs from NSE top-5 IR sites.

Strategy:
  1. Try scraping IR page HTML for PDF links (works on non-JS-rendered pages)
  2. Fall back to KNOWN_PDFS hardcoded list for JS-heavy sites

Usage:
  python ir_downloader.py                  # download all new PDFs
  python ir_downloader.py --dry-run        # preview without downloading
  python ir_downloader.py --company equity # single company
  python ir_downloader.py --company kcb --dry-run

Output: data/nse/{YEAR}/{filename}.pdf
"""

from __future__ import annotations
import argparse
import re
import sys
import urllib.parse
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BACKEND_DIR = Path(__file__).parent
DATA_ROOT   = BACKEND_DIR.parent / "data" / "nse"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}
TIMEOUT = 15
MIN_YEAR = 2020

# ── Known direct PDF URLs (hardcoded, confirmed real) ────────────────────────
# Add new URLs here as they become known. Format: (ticker, url)
KNOWN_PDFS: list[tuple[str, str]] = [
    # Equity Group
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2025/10/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-September-2025.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2025/08/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-and-other-Disclosures-for-the-Period-Ended-30th-June-2025.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2025/08/Equity-Group-Holdings-PLC-HY-2025-Investor-Booklet.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2025/05/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-31st-March-2025.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2025/03/Equity-Group-Holdings-PLC-Audited-Financial-Statements-for-the-Year-Ended-31st-December-2024.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2025/03/Equity-Group-Holdings-PLC-FY-2024-Investor-Booklet.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2024/11/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-September-2024.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2024/08/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-June-2024.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2024/05/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-31st-March-2024.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2024/03/Equity-Group-Holdings-PLC-Audited-Financial-Statements-for-the-Year-Ended-31st-December-2023.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2023/11/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-September-2023.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2023/08/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-June-2023.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2023/05/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-31st-March-2023.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2023/03/Equity-Group-Holdings-PLC-Audited-Financial-Statements-for-the-Year-Ended-31st-December-2022.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2022/11/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-September-2022.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2022/08/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-June-2022.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2022/05/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-31st-March-2022.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2022/03/Equity-Group-Holdings-PLC-Audited-Financial-Statements-for-the-Year-Ended-31st-December-2021.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2021/11/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-September-2021.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2021/08/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-June-2021.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2021/05/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-31st-March-2021.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2021/03/Equity-Group-Holdings-PLC-Audited-Financial-Statements-for-the-Year-Ended-31st-December-2020.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2020/11/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-September-2020.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2020/08/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-30th-June-2020.pdf"),
    ("EQTY", "https://equitygroupholdings.com/wp-content/uploads/2020/05/Equity-Group-Holdings-PLC-Unaudited-Financial-Statements-for-the-Period-Ended-31st-March-2020.pdf"),
    # KCB Group
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q3-2025-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-hy-2025-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q1-2025-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-fy-2024-financial-results-press-release.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q3-2024-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-hy-2024-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q1-2024-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-fy-2023-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q3-2023-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-hy-2023-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q1-2023-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-fy-2022-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q3-2022-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-hy-2022-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q1-2022-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-fy-2021-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q3-2021-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-hy-2021-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q1-2021-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-fy-2020-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q3-2020-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-hy-2020-financial-results.pdf"),
    ("KCB", "https://kcbgroup.com/download-report?document=kcb-group-plc-q1-2020-financial-results.pdf"),
]

# ── IR pages to scrape for PDF links ────────────────────────────────────────
IR_PAGES: list[tuple[str, str]] = [
    ("SCOM", "https://www.safaricom.co.ke/investor-relations-landing/reports/financial-report/financial-results"),
    ("KCB",  "https://kcbgroup.com/financial-statements"),
    ("EQTY", "https://equitygroupholdings.com/investor-relations/"),
    ("COOP", "https://www.co-opbank.co.ke/investor-relations/financial-statements/"),
    ("ABSA", "https://www.absabank.co.ke/investor-relations/"),
]

PDF_KEYWORDS = re.compile(
    r"(result|financial|interim|annual|quarter|Q[1-4]|half.year|HY|FY|report|statement)",
    re.IGNORECASE
)

YEAR_RE = re.compile(r"(202[0-9]|201[0-9])")


def get_existing_files() -> set[str]:
    """Return set of all existing PDF filenames across all year folders."""
    existing = set()
    for year_dir in DATA_ROOT.iterdir():
        if year_dir.is_dir() and year_dir.name.isdigit():
            for f in year_dir.glob("*.pdf"):
                existing.add(f.name.lower())
    return existing


def guess_year_from_url(url: str) -> int:
    """Extract year from URL or default to current year."""
    m = YEAR_RE.search(url)
    if m:
        return int(m.group(1))
    return datetime.now().year


def filename_from_url(ticker: str, url: str) -> str:
    """Generate a clean filename from a URL."""
    parsed = urllib.parse.urlparse(url)
    # Use query param 'document' if present (KCB pattern)
    qs = urllib.parse.parse_qs(parsed.query)
    if "document" in qs:
        base = qs["document"][0]
    else:
        base = Path(parsed.path).name
    # Ensure ticker prefix
    base = base.replace("%20", "_").replace(" ", "_")
    if not base.lower().startswith(ticker.lower()):
        base = f"{ticker}_{base}"
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    return base


def dest_path(ticker: str, url: str) -> Path:
    year = guess_year_from_url(url)
    if year < MIN_YEAR:
        return None
    folder = DATA_ROOT / str(year)
    folder.mkdir(parents=True, exist_ok=True)
    return folder / filename_from_url(ticker, url)


def download_pdf(url: str, path: Path, dry_run: bool) -> bool:
    if dry_run:
        print(f"  [DRY RUN] Would download → {path.relative_to(DATA_ROOT)}")
        return True
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if r.status_code != 200:
            print(f"  FAIL HTTP {r.status_code}: {url}")
            return False
        ct = r.headers.get("content-type", "")
        if "pdf" not in ct and "octet" not in ct and "download" not in ct:
            # Check first bytes
            chunk = next(r.iter_content(512), b"")
            if not chunk.startswith(b"%PDF"):
                print(f"  FAIL Not a PDF ({ct}): {url}")
                return False
            path.write_bytes(chunk + b"".join(r.iter_content(8192)))
        else:
            path.write_bytes(r.content)
        print(f"  OK → {path.relative_to(DATA_ROOT)} ({path.stat().st_size // 1024}KB)")
        return True
    except Exception as e:
        print(f"  FAIL Error: {e} — {url}")
        return False


def scrape_ir_page(ticker: str, url: str) -> list[str]:
    """Scrape IR page for PDF links."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        found = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.lower().endswith(".pdf"):
                continue
            if not PDF_KEYWORDS.search(href + " " + (a.get_text() or "")):
                continue
            # Make absolute
            full = urllib.parse.urljoin(url, href)
            # Year filter
            y = guess_year_from_url(full)
            if y < MIN_YEAR:
                continue
            found.append(full)
        return found
    except Exception as e:
        print(f"  SCRAPE ERROR ({ticker}): {e}")
        return []


def process_company(ticker: str, urls: list[str], existing: set[str], dry_run: bool) -> dict:
    stats = {"downloaded": 0, "skipped": 0, "failed": 0}
    for url in urls:
        path = dest_path(ticker, url)
        if path is None:
            continue
        if path.name.lower() in existing:
            stats["skipped"] += 1
            continue
        ok = download_pdf(url, path, dry_run)
        if ok:
            stats["downloaded"] += 1
            existing.add(path.name.lower())
        else:
            stats["failed"] += 1
    return stats


def main():
    parser = argparse.ArgumentParser(description="NSE IR PDF Downloader")
    parser.add_argument("--dry-run", action="store_true", help="Preview without downloading")
    parser.add_argument("--company", help="Filter to one company ticker (e.g. equity, kcb)")
    args = parser.parse_args()

    company_filter = args.company.upper() if args.company else None

    print(f"{'[DRY RUN] ' if args.dry_run else ''}NSE IR Downloader — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Data root: {DATA_ROOT}\n")

    existing = get_existing_files()
    print(f"Existing PDFs: {len(existing)} files\n")

    # Build per-ticker URL lists
    ticker_urls: dict[str, list[str]] = {}

    # 1. Known PDFs
    for ticker, url in KNOWN_PDFS:
        if company_filter and ticker != company_filter:
            continue
        ticker_urls.setdefault(ticker, []).append(url)

    # 2. Scraped IR pages
    for ticker, ir_url in IR_PAGES:
        if company_filter and ticker != company_filter:
            continue
        print(f"Scraping {ticker} IR page...")
        scraped = scrape_ir_page(ticker, ir_url)
        print(f"  Found {len(scraped)} PDF link(s) on page")
        ticker_urls.setdefault(ticker, []).extend(scraped)

    # Deduplicate
    for ticker in ticker_urls:
        ticker_urls[ticker] = list(dict.fromkeys(ticker_urls[ticker]))

    # Process each company
    totals = {"downloaded": 0, "skipped": 0, "failed": 0}
    for ticker, urls in sorted(ticker_urls.items()):
        print(f"\n{'='*50}")
        print(f"  {ticker} — {len(urls)} URL(s) to check")
        print(f"{'='*50}")
        stats = process_company(ticker, urls, existing, args.dry_run)
        print(f"  → Downloaded: {stats['downloaded']} | Skipped: {stats['skipped']} | Failed: {stats['failed']}")
        for k in totals:
            totals[k] += stats[k]

    print(f"\n{'='*50}")
    print(f"TOTAL — Downloaded: {totals['downloaded']} | Skipped: {totals['skipped']} | Failed: {totals['failed']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
