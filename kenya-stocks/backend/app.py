from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from scrapers import fetch_africanfinancials_sample, fetch_nse_announcements_sample

app = FastAPI(title="Kenya Stocks API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/stocks/sample")
async def sample_stocks():
    """Temporary sample data until we wire real NSE data."""
    return {
        "stocks": [
            {"symbol": "EQTY", "name": "Equity Group Holdings", "price": 40.25, "change": 0.35},
            {"symbol": "SCOM", "name": "Safaricom PLC", "price": 18.10, "change": -0.10},
            {"symbol": "KCB", "name": "KCB Group PLC", "price": 22.50, "change": 0.05},
        ]
    }


@app.get("/announcements/sample")
async def announcements_sample():
    """Sample of announcements from AfricanFinancials (Kenya).

    This is a first pass, limited to a handful of entries.
    """

    anns = fetch_africanfinancials_sample(limit=15)
    return {
        "source": "africanfinancials",
        "count": len(anns),
        "announcements": [
            {
                "company": a.company,
                "title": a.title,
                "date": a.date,
                "url": a.url,
            }
            for a in anns
        ],
    }


@app.get("/announcements/nse")
async def announcements_nse_sample():
    """Sample of announcements from the NSE website.

    Light-touch scraper for experimentation; structure may change.
    """

    anns = fetch_nse_announcements_sample(limit=20)
    return {
        "source": "nse",
        "count": len(anns),
        "announcements": [
            {
                "company": a.company,
                "title": a.title,
                "date": a.date,
                "url": a.url,
            }
            for a in anns
        ],
    }
