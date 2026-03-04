"""Scrape ABSA Kenya investor-relations page for report links.

This is a first-pass indexer. It looks for PDF links on the main
investor-relations page and tries to infer:
- year
- category
- title

Results are written to data/absa_ir/absa_ir_index.json.

Selectors/heuristics may need adjustment once we see more of the
HTML structure over time.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

ABSA_IR_URL = "https://www.absabank.co.ke/investor-relations/"

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "absa_ir"
INDEX_PATH = DATA_DIR / "absa_ir_index.json"


@dataclass
class AbsaReport:
    company: str
    title: str
    url: str
    year: Optional[int]
    category: Optional[str]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}


def guess_year(text: str) -> Optional[int]:
    """Best-effort year extraction from title or href."""

    m = re.search(r"(20[0-9]{2})", text)
    if not m:
        return None
    try:
        yr = int(m.group(1))
        if 2000 <= yr <= 2100:
            return yr
    except ValueError:
        return None
    return None


def guess_category(text: str) -> Optional[str]:
    t = text.lower()
    if "integrated" in t:
        return "integrated_report"
    if "financial" in t or "results" in t:
        return "financial_results"
    if "annual" in t:
        return "annual_report"
    return None


def scrape_index() -> List[AbsaReport]:
    resp = requests.get(ABSA_IR_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    reports: List[AbsaReport] = []

    # Heuristic: any <a> with href ending in .pdf and text mentioning
    # "financial", "results", "report", etc.
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href.lower().endswith(".pdf"):
            continue

        text = " ".join(a.get_text(strip=True).split())
        t_low = text.lower()
        if not any(w in t_low for w in ["financial", "results", "report", "statements"]):
            continue

        if href.startswith("/"):
            url = "https://www.absabank.co.ke" + href
        elif href.startswith("http"):
            url = href
        else:
            url = "https://www.absabank.co.ke/" + href.lstrip("./")

        year = guess_year(text) or guess_year(href)
        category = guess_category(text)

        reports.append(
            AbsaReport(
                company="ABSA Bank Kenya Plc",
                title=text or href,
                url=url,
                year=year,
                category=category,
            )
        )

    # Deduplicate by URL
    seen = set()
    unique: List[AbsaReport] = []
    for r in reports:
        if r.url in seen:
            continue
        seen.add(r.url)
        unique.append(r)

    return unique


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    reports = scrape_index()

    print(f"Found {len(reports)} PDF report links on ABSA IR page")

    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in reports], f, indent=2, ensure_ascii=False)

    print(f"Wrote index to {INDEX_PATH}")


if __name__ == "__main__":
    main()
