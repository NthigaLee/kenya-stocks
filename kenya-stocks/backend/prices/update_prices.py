#!/usr/bin/env python3
"""update_prices.py

One‑shot helper for NSE Insights price history.

Goal: keep the workflow consistent with your other projects → **one command** to
refresh local price JSONs used by the Chart.js charts.

What this script does today:
  1. Checks that the expected Wanjawa Mendeley CSVs exist under
     `data/prices/raw/`.
  2. If any are missing, it prints the dataset URLs + expected filenames and
     exits with a non‑zero status (so CI / cron can fail loud).
  3. If all are present, it runs `build_price_history.py` to regenerate
     `data/prices/{TICKER}.json`.

Important limitation (Mendeley):
  The Mendeley Data UI serves downloads via dynamic, time‑limited links behind
  a web frontend ("Download All" buttons and per‑file links). There is no
  stable, documented unauthenticated CSV download endpoint we can safely bake
  into a long‑lived CLI script here without scraping their UI / cookies.

  Because of that, this script does **not** attempt to log in or click the
  "Download" buttons for you. Instead, it gives you a consistent single entry
  point for "update local data" while still expecting the initial CSV exports
  to be downloaded once and dropped into `data/prices/raw/`.

Usage (from repo root):

  python backend/prices/update_prices.py

If you want to restrict to a subset of tickers, you can pass them through to
`build_price_history.py` using `--` to terminate this script's args, e.g.:

  python backend/prices/update_prices.py -- --ticker KCB EQTY SCBK

If, in the future, we discover stable, public CSV download URLs (or add a small
authenticated helper), we can extend this script with a real `--download`
implementation without changing the top‑level workflow.
"""

import os
import sys
import subprocess
from typing import List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RAW_DIR = os.path.join(REPO_ROOT, "data", "prices", "raw")

# These filenames match the expectations in build_price_history.py
EXPECTED_PRICE_FILES: List[str] = [
    "NSE_data_all_stocks_2013_2020.csv",   # optional combined file
    "NSE_data_all_stocks_2021.csv",
    "NSE_data_all_stocks_2022.csv",
    "NSE_data_all_stocks_2023_2024.csv",  # optional combined file
    "NSE_data_all_stocks_2025.csv",
]

EXPECTED_SECTOR_FILES: List[str] = [
    "NSE_data_stock_market_sectors_2013_2020.csv",  # optional
    "NSE_data_stock_market_sectors_2021.csv",
    "NSE_data_stock_market_sectors_2022.csv",
    "NSE_data_stock_market_sectors_2023.csv",
    "NSE_data_stock_market_sectors_2024.csv",
    "NSE_data_stock_market_sectors_2025.csv",
]

DATASET_URLS = {
    "2013-2020": "https://data.mendeley.com/datasets/73rb78pmzw/2",
    "2021":      "https://data.mendeley.com/datasets/97hkwn5y3x/3",
    "2022":      "https://data.mendeley.com/datasets/jmcdmnyh2s/2",
    "2023-2024": "https://data.mendeley.com/datasets/ss5pfw8xnk/3",
    "2025":      "https://data.mendeley.com/datasets/2b63rx67xt/1",
}


def _file_exists(name: str) -> bool:
    return os.path.exists(os.path.join(RAW_DIR, name))


def _print_header(title: str) -> None:
    print("\n" + title)
    print("=" * len(title))


def main(argv: List[str]) -> int:
    """Entry point.

    All args after a literal `--` are passed through to build_price_history.py.
    """
    # Split our args vs downstream args
    if "--" in argv:
        sep_index = argv.index("--")
        our_args = argv[:sep_index]
        downstream_args = argv[sep_index + 1 :]
    else:
        our_args = argv
        downstream_args = []

    _print_header("NSE Insights price update")
    print(f"Repo root: {REPO_ROOT}")
    print(f"Raw CSV dir: {RAW_DIR}")

    os.makedirs(RAW_DIR, exist_ok=True)

    # Check for expected price CSVs
    print("\nChecking for expected Mendeley CSVs...")
    missing_price = [fn for fn in EXPECTED_PRICE_FILES if not _file_exists(fn)]

    if missing_price:
        print("\nSome expected price CSVs are missing from data/prices/raw/:")
        for fn in missing_price:
            print(f"  - {fn}")

        print("\nPlease download the Wanjawa Mendeley datasets and export the CSVs:")
        for label, url in DATASET_URLS.items():
            print(f"  {label:9} → {url}")
        print("\nThen place the downloaded CSV files into:")
        print(f"  {RAW_DIR}")
        print("\nOnce the files are in place, rerun:")
        print("  python backend/prices/update_prices.py")
        return 1

    print("All expected price CSVs found. (Per‑year extras are also supported.)")

    # Sector files are optional; just report if present/missing
    print("\nSector CSVs (optional):")
    for fn in EXPECTED_SECTOR_FILES:
        status = "OK" if _file_exists(fn) else "missing"
        print(f"  {fn:40} [{status}]")

    # Run build_price_history.py with any pass‑through args
    _print_header("Building per‑ticker JSON price history")
    cmd = [
        sys.executable,
        os.path.join(SCRIPT_DIR, "build_price_history.py"),
    ] + downstream_args

    print("Running:")
    print("  " + " ".join(cmd))

    try:
        subprocess.check_call(cmd, cwd=REPO_ROOT)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: build_price_history.py failed with exit code {e.returncode}")
        return e.returncode or 1

    print("\nDone. Local price JSONs in data/prices/{TICKER}.json are up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
