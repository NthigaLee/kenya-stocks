"""
fetch_prices.py — Fetch latest NSE stock prices.

Sources (in order of preference):
  1. yfinance (NSE tickers use .NR suffix)
  2. mystocks.co.ke scrape (fallback)

Outputs: data/nse/prices.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
DATA_ROOT   = BACKEND_DIR.parent / "data" / "nse"
OUTPUT_FILE = DATA_ROOT / "prices.json"

# NSE ticker → yfinance symbol
TICKERS: dict[str, str] = {
    "SCOM":  "SCOM.NR",
    "EQTY":  "EQTY.NR",
    "KCB":   "KCB.NR",
    "ABSA":  "ABSA.NR",
    "SCBK":  "SCBK.NR",
    "COOP":  "COOP.NR",
    "NCBA":  "NCBA.NR",
    "DTK":   "DTK.NR",
    "CFC":   "CFC.NR",
    "IMH":   "IMH.NR",
    "FANB":  "FANB.NR",
    "HFCK":  "HFCK.NR",
    "EABL":  "EABL.NR",
    "BATK":  "BATK.NR",
    "NMG":   "NMG.NR",
    "BRIT":  "BRIT.NR",
    "JUB":   "JUB.NR",
    "KPLC":  "KPLC.NR",
    "KEGN":  "KEGN.NR",
    "BAMB":  "BAMB.NR",
    "SASN":  "SASN.NR",
    "WTK":   "WTK.NR",
    "KAPA":  "KAPA.NR",
    "CARB":  "CARB.NR",
    "BOC":   "BOC.NR",
    "UNGA":  "UNGA.NR",
    "SCAN":  "SCAN.NR",
    "SGL":   "SGL.NR",
    "NSE":   "NSE.NR",
    "TCL":   "TCL.NR",
    "BKG":   "BKG.NR",
    "CPKL":  "CPKL.NR",
    "SLAM":  "SLAM.NR",
}


def fetch_yfinance() -> dict:
    """Fetch prices via yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        print("yfinance not installed, skipping.", file=sys.stderr)
        return {}

    results = {}
    symbols = list(TICKERS.values())
    print(f"Fetching {len(symbols)} tickers from yfinance...")

    # Batch download for efficiency
    try:
        data = yf.download(symbols, period="5d", progress=False, auto_adjust=True)
        close = data.get("Close") if hasattr(data, "get") else data["Close"]

        for ticker, symbol in TICKERS.items():
            try:
                series = close[symbol].dropna()
                if len(series) == 0:
                    continue
                last_price = float(series.iloc[-1])
                prev_price = float(series.iloc[-2]) if len(series) >= 2 else last_price
                change = last_price - prev_price
                change_pct = (change / prev_price * 100) if prev_price else 0
                last_date = str(series.index[-1].date())
                results[ticker] = {
                    "price":      round(last_price, 2),
                    "change":     round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "date":       last_date,
                    "source":     "yfinance",
                }
                print(f"  ✓ {ticker}: {last_price:.2f} ({change:+.2f})")
            except Exception as e:
                print(f"  ✗ {ticker}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Batch download failed ({e}), trying individual...", file=sys.stderr)
        for ticker, symbol in TICKERS.items():
            try:
                t = yf.Ticker(symbol)
                hist = t.history(period="5d")
                if hist.empty:
                    continue
                last_price = float(hist["Close"].iloc[-1])
                prev_price = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else last_price
                change = last_price - prev_price
                change_pct = (change / prev_price * 100) if prev_price else 0
                last_date = str(hist.index[-1].date())
                results[ticker] = {
                    "price":      round(last_price, 2),
                    "change":     round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "date":       last_date,
                    "source":     "yfinance",
                }
                print(f"  ✓ {ticker}: {last_price:.2f}")
            except Exception as e:
                print(f"  ✗ {ticker}: {e}", file=sys.stderr)

    return results


def fetch_mystocks(missing_tickers: list[str]) -> dict:
    """Fallback: scrape mystocks.co.ke for missing tickers."""
    if not missing_tickers:
        return {}

    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("requests/beautifulsoup4 not installed, skipping mystocks.", file=sys.stderr)
        return {}

    results = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for ticker in missing_tickers:
        try:
            url = f"https://mystocks.co.ke/stock/{ticker}"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try to find price in the page
            price_el = (soup.find(class_="stock-price") or
                        soup.find(class_="current-price") or
                        soup.find("span", {"class": re.compile(r"price", re.I)}))
            if not price_el:
                continue

            price_text = re.sub(r"[^\d.]", "", price_el.get_text())
            if not price_text:
                continue

            price = float(price_text)
            results[ticker] = {
                "price":      price,
                "change":     None,
                "change_pct": None,
                "date":       str(date.today()),
                "source":     "mystocks",
            }
            print(f"  ✓ {ticker} (mystocks): {price:.2f}")
        except Exception as e:
            print(f"  ✗ {ticker} mystocks: {e}", file=sys.stderr)

    return results


def fetch_nse_web(missing_tickers: list[str]) -> dict:
    """Second fallback: try web search for NSE prices."""
    if not missing_tickers:
        return {}

    results = {}
    try:
        import requests
        headers = {"User-Agent": "Mozilla/5.0"}

        for ticker in missing_tickers[:10]:  # limit requests
            try:
                # NSE website equity page
                url = f"https://www.nse.co.ke/quotes/{ticker.lower()}/"
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    continue

                # Try to extract price from page
                price_match = re.search(r'"lastPrice"\s*:\s*"?(\d+\.?\d*)"?', resp.text)
                if not price_match:
                    price_match = re.search(r'class="[^"]*last[^"]*"[^>]*>[\s]*([\d,.]+)', resp.text)
                if price_match:
                    price = float(price_match.group(1).replace(",", ""))
                    results[ticker] = {
                        "price":      price,
                        "change":     None,
                        "change_pct": None,
                        "date":       str(date.today()),
                        "source":     "nse_web",
                    }
                    print(f"  ✓ {ticker} (nse_web): {price:.2f}")
            except Exception as e:
                print(f"  ✗ {ticker} nse_web: {e}", file=sys.stderr)
    except ImportError:
        pass

    return results


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("=== Fetching NSE Stock Prices ===")

    prices = fetch_yfinance()

    # Find missing tickers
    missing = [t for t in TICKERS.keys() if t not in prices]
    if missing:
        print(f"\n{len(missing)} tickers not found in yfinance, trying mystocks...")
        mystocks_prices = fetch_mystocks(missing)
        prices.update(mystocks_prices)

        still_missing = [t for t in missing if t not in prices]
        if still_missing:
            print(f"\n{len(still_missing)} still missing, trying NSE web...")
            nse_prices = fetch_nse_web(still_missing)
            prices.update(nse_prices)

    print(f"\n✓ Got prices for {len(prices)}/{len(TICKERS)} tickers")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "prices":     prices,
        }, f, indent=2, ensure_ascii=False)

    print(f"✓ Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
