"""
NSE Live Prices — scrapes live.mystocks.co.ke mobile pages
Delayed end-of-day quotes, no API key required.
"""
from __future__ import annotations

import re
import time
from typing import Dict, Optional, List

import requests
from bs4 import BeautifulSoup

MYSTOCKS_BASE = "https://live.mystocks.co.ke/m/stock="

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
}

NSE_TICKERS = [
    "ABSA","BAMB","BAT","BKG","BOC","BRIT","CARB","CFC","CIC","COOP",
    "CPKL","CTM","DTK","EABL","EAPC","EQTY","FANB","FTGH","HAFR","HBZE",
    "HFCK","IMH","JUB","KAPA","KCB","KEGN","KPLC","NCBA","NMG","NSE",
    "SASN","SCAN","SCBK","SCOM","SGL","SLAM","TCL","TPSE","UMME","UNGA","WTK","XPRS",
]

# Internal alias map (our ticker → mystocks ticker)
TICKER_ALIAS = {
    "BATK": "BAT",
    "CTUM": "CTM",
}

# In-memory cache
_cache: Dict[str, tuple] = {}
CACHE_TTL = 300  # 5 minutes


def _parse_price_page(html: str, ticker: str) -> Optional[dict]:
    """Parse a mystocks mobile stock page and extract price data."""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    # Pattern: "KES 30.55   0.50 (1.61%)" or "KES 30.55   -0.50 (-1.61%)"
    price_match = re.search(r'KES\s+([\d,]+\.?\d*)\s+([-\d.]+)\s+\(([-\d.]+)%\)', text)
    if not price_match:
        # Try alternate: just price
        price_match2 = re.search(r'KES\s+([\d,]+\.?\d*)', text)
        if not price_match2:
            return None
        price = float(price_match2.group(1).replace(",", ""))
        return {"ticker": ticker, "price": price, "change": None, "change_pct": None, "currency": "KES", "cached_at": int(time.time())}

    price = float(price_match.group(1).replace(",", ""))
    change = float(price_match.group(2))
    change_pct = float(price_match.group(3))
    prev_close = round(price - change, 2)

    return {
        "ticker": ticker,
        "price": price,
        "prev_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "currency": "KES",
        "cached_at": int(time.time()),
    }


def get_price(ticker: str) -> Optional[dict]:
    """Fetch live price for a single NSE ticker."""
    ticker = ticker.upper()
    ms_ticker = TICKER_ALIAS.get(ticker, ticker)

    cached = _cache.get(ticker)
    if cached and (time.time() - cached[1]) < CACHE_TTL:
        return cached[0]

    try:
        resp = requests.get(f"{MYSTOCKS_BASE}{ms_ticker}", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        result = _parse_price_page(resp.text, ticker)
        if result:
            _cache[ticker] = (result, time.time())
        return result
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_all_prices(tickers: Optional[List[str]] = None) -> Dict[str, dict]:
    """Fetch prices for all (or subset of) NSE tickers."""
    if tickers is None:
        tickers = NSE_TICKERS

    now = time.time()
    results = {}

    for ticker in tickers:
        ticker = ticker.upper()
        cached = _cache.get(ticker)
        if cached and (now - cached[1]) < CACHE_TTL:
            results[ticker] = cached[0]
        else:
            data = get_price(ticker)
            if data and "error" not in data:
                results[ticker] = data
            time.sleep(0.1)  # polite delay

    return results
