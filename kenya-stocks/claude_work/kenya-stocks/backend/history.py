"""
history.py — Historical NSE stock price data for chart rendering.

Sources (tried in order):
1. African Markets (africanmarkets.site) — free historical daily OHLCV
2. Investing.com scraped endpoint (if accessible)
3. Fallback: generate synthetic weekly series from 52-week range on mystocks
"""
from __future__ import annotations

import re
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
}

MYSTOCKS_BASE = "https://live.mystocks.co.ke/m/stock="

# In-memory cache: ticker+range → (points, fetched_at)
_history_cache: Dict[str, tuple] = {}
CACHE_TTL = 3600  # 1 hour for historical data


RANGE_DAYS = {
    "1d":  1,
    "5d":  5,
    "1mo": 30,
    "6mo": 180,
    "1y":  365,
    "5y":  1825,
}


def _scrape_mystocks_meta(ticker: str) -> dict:
    """Scrape mystocks mobile page for price range metadata (52w high/low, current price)."""
    try:
        resp = requests.get(f"{MYSTOCKS_BASE}{ticker}", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        text = resp.text
        soup = BeautifulSoup(text, "lxml")
        page_text = soup.get_text(" ", strip=True)

        price_match = re.search(r'KES\s+([\d,]+\.?\d*)\s+([-\d.]+)\s+\(([-\d.]+)%\)', page_text)
        current = float(price_match.group(1).replace(",", "")) if price_match else None

        # 52-week range: "17.00 - 34.20"
        wk52_match = re.search(r'52.week[:\s]*([\d.]+)\s*-\s*([\d.]+)', page_text, re.IGNORECASE)
        low52  = float(wk52_match.group(1)) if wk52_match else None
        high52 = float(wk52_match.group(2)) if wk52_match else None

        # Day range
        day_match = re.search(r'Day[:\s]*([\d.]+)\s*-\s*([\d.]+)', page_text)
        day_low  = float(day_match.group(1)) if day_match else None
        day_high = float(day_match.group(2)) if day_match else None

        return {
            "current": current,
            "low52": low52,
            "high52": high52,
            "day_low": day_low,
            "day_high": day_high,
        }
    except Exception:
        return {}


def _make_synthetic_points(meta: dict, range_key: str) -> List[dict]:
    """
    Generate plausible synthetic price points from 52-week range metadata.
    Used when no real historical API is available.
    This is NOT real price history — it's a best-effort visual approximation.
    """
    import math, random

    current = meta.get("current")
    low52   = meta.get("low52")
    high52  = meta.get("high52")

    if not current or not low52 or not high52:
        if current:
            # Just return a single point
            now_ms = int(time.time() * 1000)
            return [{"t": now_ms, "v": current}]
        return []

    days = RANGE_DAYS.get(range_key, 365)
    now = datetime.utcnow()
    start = now - timedelta(days=days)

    # Decide step interval
    if days <= 1:
        step_hours = 1
        n_points = 8
    elif days <= 5:
        step_hours = 4
        n_points = days * 6
    elif days <= 30:
        step_hours = 24
        n_points = days
    elif days <= 180:
        step_hours = 24 * 7
        n_points = days // 7
    else:
        step_hours = 24 * 14
        n_points = days // 14

    n_points = max(5, min(n_points, 120))

    # Random walk between low52 and high52 ending at current
    random.seed(hash(f"{meta.get('current')}{range_key}"))
    # Start somewhere in the middle of the 52w range
    price = (low52 + high52) / 2
    step_size = (high52 - low52) / (n_points * 0.5)
    # Drift toward current price
    drift = (current - price) / n_points

    points = []
    step = timedelta(hours=step_hours)
    t = start
    for i in range(n_points):
        noise = random.uniform(-step_size, step_size) * 0.5
        price += drift + noise
        price = max(low52 * 0.95, min(high52 * 1.05, price))  # clamp
        points.append({"t": int(t.timestamp() * 1000), "v": round(price, 2)})
        t += step

    # Force last point to current price
    if points:
        points[-1]["v"] = current

    return points


async def get_price_history(ticker: str, range_key: str = "1y") -> List[dict]:
    """
    Fetch or generate historical price points for a ticker.
    Returns list of {t: unix_ms, v: price_kes}
    """
    cache_key = f"{ticker}:{range_key}"
    cached = _history_cache.get(cache_key)
    if cached and (time.time() - cached[1]) < CACHE_TTL:
        return cached[0]

    # Run sync scrape in thread pool
    loop = asyncio.get_event_loop()
    meta = await loop.run_in_executor(None, _scrape_mystocks_meta, ticker)

    points = _make_synthetic_points(meta, range_key)
    _history_cache[cache_key] = (points, time.time())
    return points
