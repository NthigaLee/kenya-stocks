"""One-off script to fetch NSE financial results PDFs for 2022-2015.

Usage (from backend directory, with venv active):

    python fetch_nse_results_2015_2022.py

This script reuses the same logic as fetch_nse_results_2023_2025.py but
walks years 2022 down to 2015. It shares the same data root and index
file so downloads are deduplicated across runs.
"""

from __future__ import annotations

from fetch_nse_results_2023_2025 import (  # type: ignore
    DATA_ROOT,
    INDEX_FILE,
    MAX_PAGES_PER_YEAR,
    NSEDocument,
    download_pdf,
    fetch_year_page,
    load_index,
    parse_cards_from_html,
    save_index,
    REQUEST_DELAY_SECONDS,
)


def main() -> None:
    index = load_index()
    print(f"Loaded index with {len(index)} existing entries")

    for year in range(2022, 2014, -1):  # 2022 down to 2015
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

            for doc in docs:
                if doc.url in index and index[doc.url].local_path:
                    continue

                local_path = download_pdf(doc)
                if local_path:
                    doc.local_path = local_path
                    index[doc.url] = doc
                    save_index(index)

            # Slightly higher delay when running in parallel with the other script
            from time import sleep

            sleep(max(REQUEST_DELAY_SECONDS, 3.0))

    print("\nDone. Final index size:", len(index))


if __name__ == "__main__":
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    main()
