from __future__ import annotations

from dataclasses import dataclass
from typing import List

import requests
from bs4 import BeautifulSoup


AFRICAN_FINANCIALS_KENYA_URL = "https://africanfinancials.com/kenya-listed-company-documents/"
NSE_ANNOUNCEMENTS_URL = "https://www.nse.co.ke/listed-company-announcements/"


@dataclass
class Announcement:
    company: str
    title: str
    date: str | None
    url: str


def fetch_africanfinancials_sample(limit: int = 20) -> List[Announcement]:
    """Fetch a sample of announcements from AfricanFinancials (Kenya).

    This is intentionally conservative: one page, small limit, no heavy crawling.
    """

    # Some sites block default Python user agents; send a more browser-like UA.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(AFRICAN_FINANCIALS_KENYA_URL, headers=headers, timeout=20)
        resp.raise_for_status()
    except requests.HTTPError:
        # Site is blocking us (e.g. 403) or some other HTTP issue.
        # For now, fail gracefully and let the caller handle empty results.
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    # The exact HTML structure may evolve; this is a best-effort first pass.
    # We look for article/list entries with links to documents.
    announcements: List[Announcement] = []

    # Try common patterns: articles with class, list items, etc.
    for link in soup.select("a[href]"):
        href = link.get("href", "").strip()
        text = " ".join(link.get_text(strip=True).split())
        if not href or not text:
            continue

        # Heuristic: document links often contain '/company/' or '/document/'
        if "kenya" not in href.lower() and "document" not in href.lower():
            continue

        # Very rough split: "Company – Title" or "Company: Title"
        company = ""
        title = text
        for sep in [" – ", " - ", " | ", ": "]:
            if sep in text:
                parts = text.split(sep, 1)
                company, title = parts[0].strip(), parts[1].strip()
                break

        # Placeholder date for now (we can improve when we reverse-engineer the DOM)
        date = None

        announcements.append(
            Announcement(
                company=company or "Unknown",
                title=title,
                date=date,
                url=href,
            )
        )

        if len(announcements) >= limit:
            break

    return announcements


def fetch_nse_announcements_sample(limit: int = 20) -> List[Announcement]:
    """Fetch a sample of announcements from the NSE website.

    This is a light-touch, first-pass scraper for the main announcements page.
    It may need adjustment as we learn the actual DOM structure.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(NSE_ANNOUNCEMENTS_URL, headers=headers, timeout=20)
        resp.raise_for_status()
    except requests.HTTPError:
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    announcements: List[Announcement] = []

    # Heuristic: look for rows or cards that represent announcements.
    # We start with links inside table rows.
    for row in soup.select("table tr"):
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        # Try to infer date/company/title from columns.
        text_cols = [" ".join(c.get_text(strip=True).split()) for c in cols]
        date = text_cols[0] or None
        title = text_cols[1] if len(text_cols) > 1 else ""

        link = cols[1].find("a") if len(cols) > 1 else None
        href = link.get("href", "").strip() if link and link.has_attr("href") else ""

        if not title and not href:
            continue

        # Company often appears in another column or within the title; we keep it simple for now.
        company = text_cols[2] if len(text_cols) > 2 else "Unknown"

        announcements.append(
            Announcement(
                company=company or "Unknown",
                title=title or (link.get_text(strip=True) if link else "Announcement"),
                date=date,
                url=href or NSE_ANNOUNCEMENTS_URL,
            )
        )

        if len(announcements) >= limit:
            break

    # If table pattern fails, fall back to any announcement-like links.
    if not announcements:
        for link in soup.select("a[href]"):
            href = link.get("href", "").strip()
            text = " ".join(link.get_text(strip=True).split())
            if not href or not text:
                continue

            if "announcement" not in text.lower() and "results" not in text.lower():
                continue

            announcements.append(
                Announcement(
                    company="Unknown",
                    title=text,
                    date=None,
                    url=href,
                )
            )

            if len(announcements) >= limit:
                break

    return announcements
