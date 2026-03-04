"""One-off script to fetch NSE financial results PDFs for 2025-2023.

Usage (from backend directory, with venv active):

    python fetch_nse_results_2023_2025.py

This will:
- Walk NSE result pages for years 2025, 2024, 2023
- For each card, filter titles containing "audited" or "unaudited" (case-insensitive)
- Download PDFs into ../data/nse/<year>/
- Maintain an index JSON file so we don't re-download the same URLs

This is intentionally conservative with rate limits.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.nse.co.ke"
ANNOUNCEMENTS_URL = f"{BASE_URL}/listed-company-announcements/"

DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "nse"
INDEX_FILE = DATA_ROOT / "index_2023_2025.json"

# Polite scraping settings
REQUEST_DELAY_SECONDS = 2.0  # delay between page/PDF requests
TIMEOUT_SECONDS = 30
MAX_PAGES_PER_YEAR = 20  # safety cap in case pagination is odd


@dataclass
class NSEDocument:
    year: int
    title: str
    url: str
    company: str | None
    period: str | None
    audited_flag: str  # "audited" | "unaudited" | "unknown"
    local_path: str | None


session = requests.Session()
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}


def load_index() -> Dict[str, NSEDocument]:
    if not INDEX_FILE.exists():
        return {}
    with INDEX_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    index: Dict[str, NSEDocument] = {}
    for url, doc in raw.items():
        index[url] = NSEDocument(**doc)
    return index


def save_index(index: Dict[str, NSEDocument]) -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    serializable = {url: asdict(doc) for url, doc in index.items()}
    with INDEX_FILE.open("w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)


def is_financial_results_title(title: str) -> bool:
    t = title.lower()
    # Include audited/unaudited financial results/statements
    return (
        "audited" in t
        or "unaudited" in t
        or "financial results" in t
        or "financial statements" in t
    )


def classify_audited_flag(title: str) -> str:
    t = title.lower()
    if "audited" in t and "unaudited" in t:
        return "unknown"
    if "audited" in t:
        return "audited"
    if "unaudited" in t:
        return "unaudited"
    return "unknown"


def extract_company_and_period(title: str) -> tuple[str | None, str | None]:
    # Heuristic: "<Company> - <rest> <date>" style titles
    company = None
    period = None

    # Split on common separators
    for sep in [" - ", " – ", "  ", " : "]:
        if sep in title:
            parts = title.split(sep, 1)
            company = parts[0].strip() or None
            break

    # Rough period parsing: look for date-like patterns
    m = re.search(r"(\d{1,2}[-/ ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/ ]\d{2,4})",
                  title, flags=re.IGNORECASE)
    if m:
        period = m.group(1)

    return company, period


def fetch_year_page(year: int, page: int) -> str | None:
    """Fetch one announcements page via the NSE WordPress AJAX endpoint.

    Based on browser Network capture, the site posts to /wp-admin/admin-ajax.php with
    form fields including page, action=list_dwnlds, security=<nonce>, nse_id=15, tags=<year>.

    Note: the `security` token is hard-coded from the capture and may expire when NSE
    rotates nonces. If that happens, this script will start returning empty HTML or
    errors and we will need to refresh the token.
    """

    form = {
        "page": str(page),
        "action": "list_dwnlds",
        "security": "3d0be6550a",  # captured from Network panel; may need refresh
        "nse_id": "15",
        "limit": "",
        "tags": str(year),
        "expiry": "",
    }

    try:
        resp = session.post(
            f"{BASE_URL}/wp-admin/admin-ajax.php",
            headers={**HEADERS, "Referer": ANNOUNCEMENTS_URL},
            data=form,
            timeout=TIMEOUT_SECONDS,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        # The response is an HTML fragment containing the cards.
        # If the fragment is essentially empty, treat it as end-of-pages.
        text = resp.text.strip()
        if not text:
            return None
        return text
    except requests.RequestException:
        return None


def parse_cards_from_html(html: str, year: int) -> List[NSEDocument]:
    soup = BeautifulSoup(html, "lxml")
    docs: List[NSEDocument] = []

    # Cards live inside <div class="nse_col_3"> with a nested
    # <div class="nectar-fancy-box ...">, and the title is in <h3>.
    for card in soup.select("div.nse_col_3 div.nectar-fancy-box"):
        title_el = card.find("h3") or card.find("a") or card.find("h4")
        if not title_el:
            continue
        title = " ".join(title_el.get_text(strip=True).split())
        if not title or not is_financial_results_title(title):
            continue

        # Link is in the overlay anchor with class "box-link"
        link_el = card.find("a", class_="box-link") or title_el
        href = (link_el.get("href") or "").strip()
        if not href:
            continue
        if href.startswith("/"):
            url = BASE_URL + href
        elif href.startswith("http"):
            url = href
        else:
            url = f"{BASE_URL}/{href.lstrip('./')}"

        audited_flag = classify_audited_flag(title)
        company, period = extract_company_and_period(title)

        docs.append(
            NSEDocument(
                year=year,
                title=title,
                url=url,
                company=company,
                period=period,
                audited_flag=audited_flag,
                local_path=None,
            )
        )

    return docs


def download_pdf(doc: NSEDocument) -> str | None:
    year_dir = DATA_ROOT / str(doc.year)
    year_dir.mkdir(parents=True, exist_ok=True)

    # Build a simple filename from company + period + audited flag
    base_name_parts = []
    if doc.company:
        base_name_parts.append(re.sub(r"[^A-Za-z0-9]+", "_", doc.company)[:40])
    if doc.period:
        base_name_parts.append(re.sub(r"[^A-Za-z0-9]+", "_", doc.period)[:30])
    base_name_parts.append(doc.audited_flag)
    base_name = "_".join(p for p in base_name_parts if p) or "result"

    file_path = year_dir / f"{base_name}.pdf"

    if file_path.exists():
        return str(file_path)

    try:
        print(f"Downloading PDF: {doc.url}")
        resp = session.get(doc.url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        # Simple content-type check
        if "pdf" not in resp.headers.get("Content-Type", "").lower():
            print(f"  Skipping (not a PDF) content-type={resp.headers.get('Content-Type')}")
            return None
        file_path.write_bytes(resp.content)
        time.sleep(REQUEST_DELAY_SECONDS)
        return str(file_path)
    except requests.RequestException as e:
        print(f"  Error downloading {doc.url}: {e}")
        return None


def main() -> None:
    index = load_index()
    print(f"Loaded index with {len(index)} existing entries")

    for year in [2025, 2024, 2023]:
        print(f"\n=== Year {year} ===")
        for page in range(1, MAX_PAGES_PER_YEAR + 1):
            print(f"Fetching year={year} page={page}...")
            html = fetch_year_page(year, page)
            if not html:
                print("  No HTML (404 or error). Stopping pagination for this year.")
                break

            docs = parse_cards_from_html(html, year=year)
            if not docs:
                print("  No matching cards on this page.")
            else:
                print(f"  Found {len(docs)} candidate financial results docs.")

            # Merge into index and download
            for doc in docs:
                if doc.url in index and index[doc.url].local_path:
                    # Already downloaded
                    continue

                local_path = download_pdf(doc)
                if local_path:
                    doc.local_path = local_path
                    index[doc.url] = doc
                    save_index(index)

            time.sleep(REQUEST_DELAY_SECONDS)

    print("\nDone. Final index size:", len(index))


if __name__ == "__main__":
    os.makedirs(DATA_ROOT, exist_ok=True)
    main()
