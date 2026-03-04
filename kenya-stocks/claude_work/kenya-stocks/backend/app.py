from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from scrapers import fetch_africanfinancials_sample, fetch_nse_announcements_sample
from prices import get_price, get_all_prices, NSE_TICKER_MAP

app = FastAPI(title="Kenya Stocks API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


# ── Prices ──────────────────────────────────────────────────────────────────

@app.get("/prices")
async def all_prices(tickers: Optional[str] = Query(None, description="Comma-separated tickers, e.g. SCOM,KCB,EQTY")):
    """
    Fetch live/delayed prices for NSE stocks.
    - No params → all supported tickers
    - ?tickers=SCOM,KCB → specific tickers only
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",")] if tickers else None
    prices = get_all_prices(ticker_list)
    return {
        "count": len(prices),
        "tickers": prices,
        "note": "Prices delayed ~15 min via Yahoo Finance. Cache TTL: 5 min."
    }


@app.get("/prices/{ticker}")
async def single_price(ticker: str):
    """Fetch live/delayed price for a single NSE ticker (e.g. SCOM, KCB, EQTY)."""
    ticker = ticker.upper()
    if ticker not in NSE_TICKER_MAP:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not supported. GET /tickers for full list.")
    result = get_price(ticker)
    if not result:
        raise HTTPException(status_code=503, detail=f"Could not fetch price for {ticker}.")
    return result


@app.get("/tickers")
async def list_tickers():
    """List all supported NSE tickers and their Yahoo Finance equivalents."""
    return {
        "count": len(NSE_TICKER_MAP),
        "tickers": NSE_TICKER_MAP,
    }


# ── Announcements ────────────────────────────────────────────────────────────

@app.get("/announcements/africanfinancials")
async def announcements_af(limit: int = 15):
    anns = fetch_africanfinancials_sample(limit=limit)
    return {"source": "africanfinancials", "count": len(anns), "announcements": [
        {"company": a.company, "title": a.title, "date": a.date, "url": a.url} for a in anns
    ]}


@app.get("/announcements/nse")
async def announcements_nse(limit: int = 20):
    anns = fetch_nse_announcements_sample(limit=limit)
    return {"source": "nse", "count": len(anns), "announcements": [
        {"company": a.company, "title": a.title, "date": a.date, "url": a.url} for a in anns
    ]}
