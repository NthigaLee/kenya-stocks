"""
NSE Live Prices module
Fetches real-time/delayed prices for Nairobi Securities Exchange stocks
using yfinance (NSE tickers use .NR suffix on Yahoo Finance).
"""
from __future__ import annotations

import time
from typing import Dict, Optional
import yfinance as yf

# Mapping: our internal ticker -> Yahoo Finance ticker
# NSE stocks trade on Yahoo Finance with .NR suffix
NSE_TICKER_MAP = {
    "ABSA":  "ABSA.NR",
    "BAMB":  "BAMB.NR",
    "BATK":  "BAT.NR",
    "BKG":   "BKG.NR",
    "BOC":   "BOC.NR",
    "BRIT":  "BRIT.NR",
    "CARB":  "CARB.NR",
    "CFC":   "CFC.NR",
    "CIC":   "CIC.NR",
    "COOP":  "COOP.NR",
    "CPKL":  "CPIN.NR",
    "DTK":   "DTK.NR",
    "EABL":  "EABL.NR",
    "EAPC":  "EAPC.NR",
    "EQTY":  "EQTY.NR",
    "FANB":  "FANB.NR",
    "FTGH":  "FTGH.NR",
    "HAFR":  "HAFR.NR",
    "HBZE":  "HBZE.NR",
    "HFCK":  "HFCK.NR",
    "IMH":   "IMH.NR",
    "JUB":   "JUB.NR",
    "KAKZ":  "KAKZ.NR",
    "KAPA":  "KAPA.NR",
    "KCB":   "KCB.NR",
    "KEGN":  "KEGN.NR",
    "KPLC":  "KPLC.NR",
    "LKH":   "LKH.NR",
    "LMRU":  "LMRU.NR",
    "LONG":  "LONG.NR",
    "NCBA":  "NCBA.NR",
    "NMG":   "NMG.NR",
    "NSE":   "NSE.NR",
    "SASN":  "SASN.NR",
    "SCAN":  "SCAN.NR",
    "SCBK":  "SCBK.NR",
    "SCOM":  "SCOM.NR",
    "SGL":   "SGL.NR",
    "SLAM":  "SLAM.NR",
    "TCL":   "TCL.NR",
    "TOTL":  "TOTL.NR",
    "TPSE":  "TPSE.NR",
    "UMME":  "UMME.NR",
    "UNGA":  "UNGA.NR",
    "WTK":   "WTK.NR",
    "XPRS":  "XPRS.NR",
}

# Simple in-memory cache (price, timestamp)
_cache: Dict[str, tuple] = {}
CACHE_TTL_SECONDS = 300  # 5-minute cache


def get_price(ticker: str) -> Optional[dict]:
    """
    Fetch live/delayed price for a single NSE ticker.
    Returns dict with price, change, change_pct, volume, currency.
    """
    yf_ticker = NSE_TICKER_MAP.get(ticker.upper())
    if not yf_ticker:
        return None

    # Check cache
    cached = _cache.get(ticker)
    if cached and (time.time() - cached[1]) < CACHE_TTL_SECONDS:
        return cached[0]

    try:
        t = yf.Ticker(yf_ticker)
        info = t.fast_info

        price = getattr(info, "last_price", None)
        prev_close = getattr(info, "previous_close", None)
        volume = getattr(info, "last_volume", None)

        if not price:
            # Fallback: try history
            hist = t.history(period="2d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else None

        if not price:
            return None

        change = round(price - prev_close, 2) if prev_close else None
        change_pct = round((change / prev_close) * 100, 2) if change and prev_close else None

        result = {
            "ticker": ticker,
            "yf_ticker": yf_ticker,
            "price": round(price, 2),
            "prev_close": round(prev_close, 2) if prev_close else None,
            "change": change,
            "change_pct": change_pct,
            "volume": volume,
            "currency": "KES",
            "cached_at": int(time.time()),
        }

        _cache[ticker] = (result, time.time())
        return result

    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_all_prices(tickers: Optional[list] = None) -> Dict[str, dict]:
    """
    Fetch prices for all (or a subset of) NSE tickers in bulk.
    Uses yfinance download for efficiency.
    """
    if tickers is None:
        tickers = list(NSE_TICKER_MAP.keys())

    # Check which need fresh fetch
    now = time.time()
    stale = [t for t in tickers if t not in _cache or (now - _cache[t][1]) >= CACHE_TTL_SECONDS]
    fresh = {t: _cache[t][0] for t in tickers if t not in stale}

    if stale:
        yf_tickers = [NSE_TICKER_MAP[t] for t in stale if t in NSE_TICKER_MAP]
        try:
            data = yf.download(
                tickers=" ".join(yf_tickers),
                period="2d",
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )

            for ticker in stale:
                yf_t = NSE_TICKER_MAP.get(ticker)
                if not yf_t:
                    continue
                try:
                    if len(yf_tickers) == 1:
                        closes = data["Close"]
                    else:
                        closes = data[yf_t]["Close"]

                    closes = closes.dropna()
                    if closes.empty:
                        continue

                    price = float(closes.iloc[-1])
                    prev_close = float(closes.iloc[-2]) if len(closes) > 1 else None
                    change = round(price - prev_close, 2) if prev_close else None
                    change_pct = round((change / prev_close) * 100, 2) if change and prev_close else None

                    result = {
                        "ticker": ticker,
                        "price": round(price, 2),
                        "prev_close": round(prev_close, 2) if prev_close else None,
                        "change": change,
                        "change_pct": change_pct,
                        "currency": "KES",
                        "cached_at": int(now),
                    }
                    _cache[ticker] = (result, now)
                    fresh[ticker] = result

                except Exception:
                    continue

        except Exception as e:
            # Bulk fetch failed — return whatever we have cached
            pass

    return fresh
