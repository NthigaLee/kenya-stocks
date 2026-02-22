"""Download ABSA IR PDFs listed in absa_ir_index.json.

Usage (from backend dir, venv active):

    python absa_ir_scrape_index.py
    python absa_ir_download_pdfs.py

Downloads to data/absa_ir/<year>/... with a normalized filename.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List

import requests

from absa_ir_scrape_index import DATA_DIR, INDEX_PATH  # type: ignore

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}

SAFE_CHAR_RE = re.compile(r"[^A-Za-z0-9]+")


def safe_slug(s: str, max_len: int = 80) -> str:
    slug = SAFE_CHAR_RE.sub("_", s).strip("_")
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("_")
    return slug or "report"


def load_index() -> List[Dict[str, Any]]:
    if not INDEX_PATH.exists():
        raise SystemExit(f"Index not found at {INDEX_PATH}. Run absa_ir_scrape_index.py first.")
    import json

    with INDEX_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit("Index file does not contain a list.")
    return data


def main() -> None:
    index = load_index()

    session = requests.Session()

    for entry in index:
        url = entry.get("url")
        title = entry.get("title") or "absa_report"
        year = entry.get("year") or "unknown"
        year_str = str(year)

        out_dir = DATA_DIR / year_str
        out_dir.mkdir(parents=True, exist_ok=True)

        base_name = safe_slug(f"{title}_{year_str}") + ".pdf"
        out_path = out_dir / base_name

        if out_path.exists():
            print(f"Skipping already downloaded: {out_path}")
            continue

        print(f"Downloading {url} -> {out_path}")
        try:
            resp = session.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            print(f"  Error downloading {url}: {e}")
            continue

        content_type = resp.headers.get("Content-Type", "").lower()
        if "pdf" not in content_type:
            print(f"  Skipping (not a PDF) content-type={content_type}")
            continue

        out_path.write_bytes(resp.content)

    print("Done downloading ABSA IR PDFs.")


if __name__ == "__main__":
    main()
