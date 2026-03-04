from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from scrapers import fetch_africanfinancials_sample, fetch_nse_announcements_sample
from prices import get_price, get_all_prices, NSE_TICKERS
from history import get_price_history

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
    result = get_price(ticker.upper())
    if not result:
        raise HTTPException(status_code=503, detail=f"Could not fetch price for {ticker}.")
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


@app.get("/tickers")
async def list_tickers():
    """List all supported NSE tickers."""
    return {"count": len(NSE_TICKERS), "tickers": NSE_TICKERS}


@app.get("/history/{ticker}")
async def price_history(ticker: str, range: str = "1y"):
    """
    Fetch historical price data for a NSE ticker.
    range: 1d | 5d | 1mo | 6mo | 1y | 5y
    Returns: { ticker, range, points: [{t: ms, v: price}] }
    """
    points = await get_price_history(ticker.upper(), range)
    return {"ticker": ticker.upper(), "range": range, "points": points or []}


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
