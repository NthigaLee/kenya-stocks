"""
populate.py — Build frontend/data.js from data/nse/financials.json
All stored values in JSON are KES_thousands after unit normalisation.
Banks/others keep thousands; SCOM is divided by 1000 → millions for display.
"""

import json, re
from pathlib import Path
from datetime import datetime

JSON_FILE = Path(__file__).parent.parent / "data" / "nse" / "financials.json"
DATA_JS   = Path(__file__).parent.parent / "frontend" / "data.js"

# ── Company catalogue ──────────────────────────────────────────────────────────
# Keys MUST match the ticker values emitted by extract_all.py (internal tickers)
# NOTE: Some internal tickers differ from TradingView tickers:
#   DTB (internal) = DTK (TradingView)
#   BATK (internal) = BAT (TradingView)
#   CPKL (internal) = CRWN (TradingView)
#   EAPC (internal) = PORT (TradingView)
#   KAPA (internal) = KAPC (TradingView)
#   FMLY, HBZE, TCL — no TradingView ticker
COMPANY_META = {
    # ── Banking ──────────────────────────────────────────────────────────────
    "KCB":  {"name": "KCB Group PLC",                   "sector": "Banking",        "logo": "🏦", "price": 42.0,  "units": "thousands"},
    "EQTY": {"name": "Equity Group Holdings PLC",        "sector": "Banking",        "logo": "🏦", "price": 52.0,  "units": "thousands"},
    "COOP": {"name": "Co-operative Bank of Kenya",       "sector": "Banking",        "logo": "🏦", "price": 14.5,  "units": "thousands"},
    "NCBA": {"name": "NCBA Group PLC",                   "sector": "Banking",        "logo": "🏦", "price": 45.0,  "units": "thousands"},
    "ABSA": {"name": "ABSA Bank Kenya PLC",              "sector": "Banking",        "logo": "🏦", "price": 14.2,  "units": "thousands"},
    "SCBK": {"name": "Standard Chartered Bank Kenya",    "sector": "Banking",        "logo": "🏦", "price": 195.0, "units": "thousands"},
    "IMH":  {"name": "I&M Group PLC",                    "sector": "Banking",        "logo": "🏦", "price": 24.0,  "units": "thousands"},
    "DTB":  {"name": "Diamond Trust Bank Kenya",         "sector": "Banking",        "logo": "🏦", "price": 60.0,  "units": "thousands"},
    "FMLY": {"name": "Family Bank Ltd",                  "sector": "Banking",        "logo": "🏦", "price": 6.2,   "units": "thousands"},
    "HFCK": {"name": "HF Group PLC",                     "sector": "Banking",        "logo": "🏦", "price": 4.5,   "units": "thousands"},
    "SBIC": {"name": "Stanbic Holdings PLC",             "sector": "Banking",        "logo": "🏦", "price": 105.0, "units": "thousands"},
    "BKG":  {"name": "BK Group PLC",                     "sector": "Banking",        "logo": "🏦", "price": 50.0,  "units": "thousands"},
    # ── Telecoms ─────────────────────────────────────────────────────────────
    "SCOM": {"name": "Safaricom PLC",                    "sector": "Telecoms",       "logo": "📡", "price": 15.85, "units": "millions"},
    # ── Insurance ────────────────────────────────────────────────────────────
    "JUB":  {"name": "Jubilee Holdings Limited",         "sector": "Insurance",      "logo": "🏢", "price": 230.0, "units": "thousands"},
    "BRIT": {"name": "Britam Holdings PLC",              "sector": "Insurance",      "logo": "🏢", "price": 6.0,   "units": "thousands"},
    "SLAM": {"name": "Sanlam Allianz Kenya",             "sector": "Insurance",      "logo": "🏢", "price": 10.0,  "units": "thousands"},
    # ── FMCG ─────────────────────────────────────────────────────────────────
    "EABL": {"name": "East African Breweries Ltd",       "sector": "FMCG",           "logo": "🍺", "price": 155.0, "units": "thousands"},
    "BATK": {"name": "BAT Kenya PLC",                    "sector": "FMCG",           "logo": "🏭", "price": 465.0, "units": "thousands"},
    # ── Energy ───────────────────────────────────────────────────────────────
    "KEGN": {"name": "KenGen Co. PLC",                   "sector": "Energy",         "logo": "⚡", "price": 5.4,   "units": "thousands"},
    "KPLC": {"name": "Kenya Power and Lighting Co.",     "sector": "Energy",         "logo": "⚡", "price": 2.0,   "units": "thousands"},
    "UMME": {"name": "Umeme Limited",                    "sector": "Energy",         "logo": "⚡", "price": 5.0,   "units": "thousands"},
    # ── Media ────────────────────────────────────────────────────────────────
    "NMG":  {"name": "Nation Media Group",               "sector": "Media",          "logo": "📰", "price": 14.0,  "units": "thousands"},
    "SGL":  {"name": "Standard Group PLC",               "sector": "Media",          "logo": "📰", "price": 18.0,  "units": "thousands"},
    "SCAN": {"name": "WPP Scangroup PLC",                "sector": "Media",          "logo": "📢", "price": 4.0,   "units": "thousands"},
    "HBZE": {"name": "Homeboyz Entertainment PLC",       "sector": "Media",          "logo": "🎵", "price": 2.5,   "units": "thousands"},
    # ── Manufacturing / Industry ─────────────────────────────────────────────
    "CARB": {"name": "Carbacid Investments PLC",         "sector": "Manufacturing",  "logo": "🏭", "price": 12.0,  "units": "thousands"},
    "BOC":  {"name": "BOC Kenya PLC",                    "sector": "Manufacturing",  "logo": "🏭", "price": 95.0,  "units": "thousands"},
    "BAMB": {"name": "Bamburi Cement PLC",               "sector": "Manufacturing",  "logo": "🏭", "price": 65.0,  "units": "thousands"},
    "CPKL": {"name": "Crown Paints Kenya PLC",           "sector": "Manufacturing",  "logo": "🏭", "price": 40.0,  "units": "thousands"},
    "EAPC": {"name": "EA Portland Cement PLC",           "sector": "Manufacturing",  "logo": "🏭", "price": 8.0,   "units": "thousands"},
    "TCL":  {"name": "TransCentury PLC",                 "sector": "Manufacturing",  "logo": "🏭", "price": 1.5,   "units": "thousands"},
    "FTGH": {"name": "Flame Tree Group Holdings",        "sector": "Manufacturing",  "logo": "🏭", "price": 3.0,   "units": "thousands"},
    "XPRS": {"name": "Express Kenya Ltd",                "sector": "Logistics",      "logo": "🚚", "price": 5.0,   "units": "thousands"},
    # ── Agriculture ──────────────────────────────────────────────────────────
    "UNGA": {"name": "Unga Group Limited",               "sector": "Agriculture",    "logo": "🌾", "price": 26.0,  "units": "thousands"},
    "KAPA": {"name": "Kapchorua Tea Kenya PLC",          "sector": "Agriculture",    "logo": "🌱", "price": 130.0, "units": "thousands"},
    "SASN": {"name": "Sasini PLC",                       "sector": "Agriculture",    "logo": "🌱", "price": 20.0,  "units": "thousands"},
    "WTK":  {"name": "Williamson Tea Kenya PLC",         "sector": "Agriculture",    "logo": "🌱", "price": 330.0, "units": "thousands"},
    # ── Real Estate ──────────────────────────────────────────────────────────
    "HAFR": {"name": "Home Afrika Limited",              "sector": "Real Estate",    "logo": "🏘", "price": 0.5,   "units": "thousands"},
    # ── Other ────────────────────────────────────────────────────────────────
    "NSE":  {"name": "Nairobi Securities Exchange",      "sector": "Other",          "logo": "📈", "price": 7.0,   "units": "thousands"},
}

# ── Sanity limits (values stored in KES_thousands) ────────────────────────────
MAX_PAT     =  200_000_000   # 200B KES
MIN_PAT     =  -50_000_000   # -50B KES
MAX_REV     =  600_000_000   # 600B KES
MAX_NII     =  200_000_000   # 200B KES
MAX_ASSETS  = 5_000_000_000  # 5T KES
MAX_EPS     =  10_000        # KES per share — anything over 10k is clearly wrong
MIN_EPS     = -1_000
MAX_DPS     =  5_000

def clamp(v, lo, hi):
    if v is None: return None
    try:
        fv = float(v)
    except (ValueError, TypeError):
        return None
    return fv if lo <= fv <= hi else None

def parse_period_date(record):
    """Return a sortable date string from the record, e.g. '2023-12-31'."""
    d = record.get("period_end_date")
    if d:
        return d
    p = str(record.get("period", "") or "")
    # try various formats
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%d %B %Y", "%d %b %Y",
                "%Y-%m-%d", "%d-%b-%y"):
        try:
            return datetime.strptime(p.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return "0000-00-00"

def period_label(record):
    """Short display label like 'Dec2023', 'H1 2024', 'Q1 2025', 'Q3 2025'."""
    raw = str(record.get("period", "") or "").strip()
    d = record.get("period_end_date", "")
    if d:
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
            ptype = record.get("period_type", "")
            yr = dt.year
            mo = dt.month
            if ptype == "annual":
                return dt.strftime("%b%Y")
            if ptype in ("half_year", "quarter"):
                # Map month-end to quarter number (H1/Jun = Q2, Q3/Sep = Q3, etc.)
                q = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}.get(mo, f"Q{(mo-1)//3+1}")
                return f"{q} {yr}"
            return dt.strftime("%b%Y")
        except ValueError:
            pass
    return raw

def build_annual_row(r, display_units):
    """Build one annuals[] entry, applying sanity checks and unit conversion."""
    divisor = 1000 if display_units == "millions" else 1  # thousands → millions

    def v(field, lo, hi):
        raw = clamp(r.get(field), lo, hi)
        return round(raw / divisor, 2) if raw is not None else None

    pat = v("profit_after_tax",   MIN_PAT,    MAX_PAT)
    rev = v("revenue",            0,          MAX_REV)
    nii = v("net_interest_income",0,          MAX_NII)
    pbt = v("profit_before_tax",  MIN_PAT,    MAX_PAT)
    ta  = v("total_assets",       0,          MAX_ASSETS)
    te  = v("total_equity",       0,          MAX_ASSETS)
    dep = v("customer_deposits",  0,          MAX_ASSETS)
    lns = v("loans_and_advances", 0,          MAX_ASSETS)
    ebt = v("ebitda",             MIN_PAT,    MAX_PAT)
    mps = v("mpesa_revenue",      0,          MAX_PAT)
    eps = clamp(r.get("basic_eps"),  MIN_EPS, MAX_EPS)
    dps = clamp(r.get("dividend_per_share"), 0, MAX_DPS)

    # If PAT is null but EPS/DPS are present, they're likely wrong (scraped from wrong row)
    # Null them out to avoid misleading displays
    if pat is None:
        eps = None
        dps = None

    return {
        "year":        r.get("year"),
        "period":      period_label(r),
        "periodType":  r.get("period_type"),
        "dateKey":     parse_period_date(r),   # ISO date for reliable chronological sort
        "revenue":     rev,
        "pat":         pat,
        "pbt":         pbt,
        "nii":         nii,
        "eps":         round(eps, 4) if eps is not None else None,
        "dps":         round(dps, 4) if dps is not None else None,
        "totalAssets": ta,
        "totalEquity": te,
        "deposits":    dep,
        "loans":       lns,
        "ebitda":      ebt,
        "mpesa":       mps,
    }

def has_useful_data(row):
    """Return True if the row has at least one key financial metric."""
    return any(row[k] is not None for k in ("pat", "revenue", "nii", "eps"))

def scrub_pat(row):
    """
    If revenue/NII is very large but PAT is suspiciously tiny, null out PAT.
    This catches cases where the extractor grabbed a footnote ref instead of
    the actual profit figure (e.g. KCB Dec2020 PAT=19,604 vs revenue=75.8B).
    """
    pat = row.get("pat")
    rev = row.get("revenue")
    nii = row.get("net_interest_income") or row.get("nii")
    if pat is None:
        return row
    # If any large metric exists but PAT is < 0.1% of it, something is wrong
    for big in [rev, nii]:
        if big and big > 1_000_000 and abs(pat) < big * 0.001:
            row = dict(row)
            row["pat"] = None
            break
    return row

def parse_date_from_url(url):
    """Try to extract a date from a URL like '...Ended-31st-December-2023.pdf'."""
    import re
    if not url:
        return None
    MONTH_NAMES = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8,
        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    }
    # Pattern: "31st-December-2023" or "31-Mar-2024"
    m = re.search(r'(\d{1,2})(?:st|nd|rd|th)?[-\s]([A-Za-z]+)[-\s](\d{4})', url)
    if m:
        day, mon_str, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        month = MONTH_NAMES.get(mon_str)
        if month and 2018 <= year <= 2030:
            return f"{year}-{month:02d}-{day:02d}"
    # Pattern: "December-2023" without day
    m = re.search(r'([A-Za-z]+)-(\d{4})', url)
    if m:
        mon_str, year = m.group(1).lower(), int(m.group(2))
        month = MONTH_NAMES.get(mon_str)
        if month and 2018 <= year <= 2030:
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return f"{year}-{month:02d}-{last_day:02d}"
    return None


def infer_period_type(record, date_str):
    """Infer period_type from date and context if not set."""
    pt = record.get("period_type")
    if pt and pt not in (None, "unknown"):
        return pt
    source = (record.get("source_file") or "").lower()
    url = (record.get("url") or "").lower()
    # Use date month to distinguish annual from interim
    if date_str and date_str != "0000-00-00":
        try:
            month = int(date_str[5:7])
        except (ValueError, IndexError):
            month = None
        if month:
            # March/June/Sep year-end → quarterly or half_year
            if month in (3, 6, 9):
                # Unless the company clearly has a non-Dec fiscal year (tea companies use April)
                # and the source says "audited full year"
                if ("full-year" in url or "full_year" in url) and month in (3,):
                    return "annual"  # March year-end companies (Williamson, Kapchorua, NCBA)
                return "quarter" if month == 3 else "half_year"
            # December → annual if audited, else could be quarter (Q4 reporting)
            if month == 12:
                if "audited" in source or "audited" in url or "full-year" in url or "full_year" in url:
                    return "annual"
                # Unaudited December → likely annual or Q4; treat as annual
                return "annual"
            # April year-end (tea companies)
            if month == 4:
                if "audited" in source or "full-year" in url:
                    return "annual"
                return "quarter"
    # Fallback: trust audited marker
    if "audited" in source or "full-year" in url or "year-ended" in url or "full_year" in url:
        return "annual"
    return "unknown"


def main():
    with open(JSON_FILE, encoding="utf-8") as f:
        records = json.load(f)

    # Group records by ticker
    by_ticker: dict[str, list] = {}
    for r in records:
        t = r.get("ticker")
        if t in COMPANY_META:
            by_ticker.setdefault(t, []).append(r)

    js_companies = {}

    for ticker, recs in by_ticker.items():
        meta = COMPANY_META[ticker]
        units = meta["units"]

        # Enrich records: fill missing period_end_date from URL; infer period_type
        enriched = []
        for r in recs:
            r = dict(r)
            if not r.get("period_end_date"):
                d = parse_date_from_url(r.get("url"))
                if d:
                    r["period_end_date"] = d
                    if not r.get("year"):
                        r["year"] = int(d[:4])
            if not r.get("period_type") or r.get("period_type") == "unknown":
                r["period_type"] = infer_period_type(r, r.get("period_end_date"))
            enriched.append(r)
        recs = enriched

        # Separate annual vs interim records
        # Treat "unknown" as annual if infer_period_type couldn't determine otherwise
        annuals = [r for r in recs if r.get("period_type") in ("annual", "unknown")]
        interim = [r for r in recs if r.get("period_type") in ("half_year", "quarter")]

        # Deduplicate annuals by period_end_date (keep last if dupes)
        seen = {}
        for r in sorted(annuals, key=parse_period_date):
            key = r.get("period_end_date") or parse_period_date(r)
            seen[key] = r
        annuals = list(seen.values())

        # Filter to last 5 years (2020 onwards)
        annuals = [r for r in annuals if (r.get("year") or 0) >= 2020]

        # Remove records without a valid date
        annuals = [r for r in annuals if parse_period_date(r) != "0000-00-00"]

        # Sort by date
        annuals.sort(key=parse_period_date)

        # Build annual rows
        annual_rows = [scrub_pat(build_annual_row(r, units)) for r in annuals]
        annual_rows = [row for row in annual_rows if has_useful_data(row)]

        # Fallback: if no annual rows, use interim records as display data
        if not annual_rows and interim:
            interim_sorted = sorted(interim, key=parse_period_date)
            interim_sorted = [r for r in interim_sorted if parse_period_date(r) != "0000-00-00"
                              and (r.get("year") or 0) >= 2020]
            for r in interim_sorted:
                row = scrub_pat(build_annual_row(r, units))
                if has_useful_data(row):
                    annual_rows.append(row)

        if not annual_rows:
            continue

        # Latest interim period (most recent half_year or quarter)
        latest_period = None
        if interim:
            interim.sort(key=parse_period_date, reverse=True)
            # Filter to ones with useful data
            for r in interim:
                row = scrub_pat(build_annual_row(r, units))
                if has_useful_data(row):
                    latest_period = row
                    break

        # Build quarters[] — up to 6 most recent interim periods
        quarter_rows = []
        if interim:
            interim_sorted = sorted(interim, key=parse_period_date)
            for r in interim_sorted:
                row = scrub_pat(build_annual_row(r, units))
                if has_useful_data(row):
                    quarter_rows.append(row)
            # Keep only last 6
            quarter_rows = quarter_rows[-6:]

        co_obj = {
            "name":        meta["name"],
            "ticker":      ticker,
            "exchange":    "NSE",
            "sector":      meta["sector"],
            "logo":        meta["logo"],
            "currency":    "KES",
            "units":       units,
            "latestPrice": meta["price"],
            "annuals":     annual_rows,
            "quarters":    quarter_rows,
        }
        if latest_period:
            co_obj["latestPeriod"] = latest_period

        js_companies[ticker] = co_obj

    # Serialise
    indent = "  "
    lines = [
        "// Kenya NSE Companies — Embedded Financial Data",
        f"// Auto-generated by backend/populate.py",
        "// Values: KES thousands (banks) or KES millions (SCOM)",
        "// Source: NSE disclosure PDFs",
        "",
        "const NSE_COMPANIES = {",
    ]

    for i, (ticker, co) in enumerate(js_companies.items()):
        comma = "," if i < len(js_companies) - 1 else ""
        lines.append(f"")
        lines.append(f"  {ticker}: {{")
        lines.append(f'    name: {json.dumps(co["name"])},')
        lines.append(f'    ticker: {json.dumps(co["ticker"])},')
        lines.append(f'    exchange: "NSE",')
        lines.append(f'    sector: {json.dumps(co["sector"])},')
        lines.append(f'    logo: {json.dumps(co["logo"])},')
        lines.append(f'    currency: "KES",')
        lines.append(f'    units: {json.dumps(co["units"])},')
        lines.append(f'    latestPrice: {co["latestPrice"]},')

        if co.get("latestPeriod"):
            lp = co["latestPeriod"]
            lines.append(f'    latestPeriod: {json.dumps(lp)},')

        lines.append(f'    annuals: [')
        for j, row in enumerate(co["annuals"]):
            rc = "," if j < len(co["annuals"]) - 1 else ""
            lines.append(f'      {json.dumps(row)}{rc}')
        lines.append(f'    ],')

        qrows = co.get("quarters", [])
        lines.append(f'    quarters: [')
        for j, row in enumerate(qrows):
            rc = "," if j < len(qrows) - 1 else ""
            lines.append(f'      {json.dumps(row)}{rc}')
        lines.append(f'    ],')

        lines.append(f'  }}{comma}')

    lines.append("")
    lines.append("};")
    lines.append("")

    DATA_JS.write_text("\n".join(lines), encoding="utf-8")
    print(f"Done. Wrote {len(js_companies)} companies to {DATA_JS}")
    print(f"  Companies: {', '.join(js_companies.keys())}")
    for ticker, co in js_companies.items():
        n = len(co["annuals"])
        q = len(co.get("quarters", []))
        lp = " + latest interim" if co.get("latestPeriod") else ""
        print(f"  {ticker:6}: {n} annuals, {q} quarters{lp}")

if __name__ == "__main__":
    main()
