"""
generate_frontend_data.py — Generate frontend/data.js from extracted financials.

Transforms financials_complete.json into NSE_COMPANIES JavaScript object.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

BACKEND_DIR = Path(__file__).parent
DATA_ROOT = BACKEND_DIR.parent / "data" / "nse"
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

FINANCIALS_FILE = DATA_ROOT / "financials_complete.json"
OUTPUT_FILE = FRONTEND_DIR / "data.js"

# Company info and sectors
COMPANY_INFO = {
    "ABSA": {"name": "ABSA Bank Kenya", "logo": "🏦", "sector": "Banking"},
    "SCBK": {"name": "Standard Chartered Bank Kenya", "logo": "🏦", "sector": "Banking"},
    "SCOM": {"name": "Safaricom PLC", "logo": "📱", "sector": "Telecoms"},
    "EQTY": {"name": "Equity Group Holdings", "logo": "🏦", "sector": "Banking"},
    "KCB": {"name": "KCB Group", "logo": "🏦", "sector": "Banking"},
    "NCBA": {"name": "NCBA Group", "logo": "🏦", "sector": "Banking"},
    "COOP": {"name": "Co-operative Bank of Kenya", "logo": "🏦", "sector": "Banking"},
    "DTK": {"name": "Diamond Trust Bank", "logo": "🏦", "sector": "Banking"},
    "CFC": {"name": "Stanbic Holdings", "logo": "🏦", "sector": "Banking"},
    "IMH": {"name": "I&M Holdings", "logo": "🏦", "sector": "Banking"},
    "FANB": {"name": "Family Bank", "logo": "🏦", "sector": "Banking"},
    "HFCK": {"name": "Housing Finance", "logo": "🏦", "sector": "Banking"},
    "BKG": {"name": "BK Group", "logo": "🏦", "sector": "Banking"},
    "EABL": {"name": "East African Breweries", "logo": "🍺", "sector": "FMCG"},
    "BAMB": {"name": "Bamburi Cement", "logo": "🏗️", "sector": "Construction"},
    "BATK": {"name": "BAT Kenya", "logo": "🚬", "sector": "FMCG"},
    "BRIT": {"name": "Britam Holdings", "logo": "🛡️", "sector": "Insurance"},
    "JUB": {"name": "Jubilee Holdings", "logo": "🛡️", "sector": "Insurance"},
    "SLAM": {"name": "Sanlam Kenya", "logo": "🛡️", "sector": "Insurance"},
    "NMG": {"name": "Nation Media Group", "logo": "📰", "sector": "Media"},
    "SCAN": {"name": "WPP Scangroup", "logo": "📺", "sector": "Media"},
    "KPLC": {"name": "Kenya Power", "logo": "⚡", "sector": "Energy"},
    "KEGN": {"name": "KenGen", "logo": "⚡", "sector": "Energy"},
    "SASN": {"name": "Sasini", "logo": "🌾", "sector": "Agriculture"},
    "WTK": {"name": "Williamson Tea", "logo": "🌾", "sector": "Agriculture"},
    "CARB": {"name": "Carbacid", "logo": "🏭", "sector": "Manufacturing"},
    "BOC": {"name": "BOC Kenya", "logo": "🏭", "sector": "Manufacturing"},
    "CPKL": {"name": "Crown Paints", "logo": "🎨", "sector": "Manufacturing"},
    "XPRS": {"name": "Express Kenya", "logo": "🚚", "sector": "Logistics"},
    "FTGH": {"name": "Flame Tree", "logo": "🌳", "sector": "Diversified"},
    "HAFR": {"name": "Home Afrika", "logo": "🏠", "sector": "Real Estate"},
    "HBZE": {"name": "Homeboyz", "logo": "🎬", "sector": "Entertainment"},
    "TCL": {"name": "TransCentury", "logo": "🏗️", "sector": "Infrastructure"},
    "TPSE": {"name": "TPS Eastern Africa", "logo": "🏨", "sector": "Hospitality"},
    "UMME": {"name": "Umeme", "logo": "⚡", "sector": "Energy"},
    "NSE": {"name": "Nairobi Securities Exchange", "logo": "📊", "sector": "Financial Services"},
}

def parse_date(date_str: Optional[str]) -> Optional[tuple]:
    """Parse ISO date string to (year, month, day)."""
    if not date_str:
        return None
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
    except:
        pass
    return None

def period_label(date_str: str, period_type: Optional[str]) -> str:
    """Generate human-readable period label."""
    parts = parse_date(date_str)
    if not parts:
        return "Unknown"

    year, month, day = parts
    months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_name = months[month]

    if period_type == 'annual':
        return f"FY{year}"
    elif period_type == 'half_year':
        return f"H1 {month_name}{year}"
    elif period_type == 'quarter':
        if month == 3:
            return f"Q1 {year}"
        elif month == 6:
            return f"H1 {year}"
        elif month == 9:
            return f"Q3 {year}"
        else:
            return f"{month_name}{year}"
    else:
        return f"{month_name}{year}"

def normalize_value(value: Any) -> Optional[float]:
    """Normalize value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except:
        return None

def generate_frontend_data():
    """Generate frontend data.js from financials."""
    print("\n" + "="*70)
    print("GENERATING FRONTEND DATA")
    print("="*70 + "\n")

    # Load financials
    if not FINANCIALS_FILE.exists():
        print(f"ERROR: {FINANCIALS_FILE} not found")
        print("Run extract_all.py first to generate financials_complete.json")
        return

    with open(FINANCIALS_FILE, 'r') as f:
        financials = json.load(f)

    print(f"Loaded {len(financials)} financial records")

    # Group by ticker
    by_ticker = defaultdict(list)
    for record in financials:
        ticker = record.get('ticker')
        if ticker:
            by_ticker[ticker].append(record)

    print(f"Found {len(by_ticker)} unique tickers\n")

    # Build NSE_COMPANIES object
    nse_companies = {}

    for ticker in sorted(by_ticker.keys()):
        # Filter out records with no date and sort by date
        records = [r for r in by_ticker[ticker] if r.get('period_end_date')]
        records = sorted(records, key=lambda r: r.get('period_end_date', ''), reverse=True)

        if not records:
            continue

        # Get company info
        company_info = COMPANY_INFO.get(ticker, {
            "name": records[0].get('company', ticker),
            "logo": "📊",
            "sector": records[0].get('sector', 'Other')
        })

        # Separate annuals and quarters
        annuals = []
        quarters = []

        for record in records:
            period_type = record.get('period_type', '').lower()
            date_str = record.get('period_end_date')

            if not date_str:
                continue

            # Build period object
            period_obj = {
                'year': parse_date(date_str)[0] if parse_date(date_str) else None,
                'period': period_label(date_str, period_type),
                'periodType': period_type,
                'revenue': normalize_value(record.get('revenue')),
                'pat': normalize_value(record.get('profit_after_tax')),
                'pbt': normalize_value(record.get('profit_before_tax')),
                'nii': normalize_value(record.get('net_interest_income')),
                'eps': normalize_value(record.get('basic_eps')),
                'dps': normalize_value(record.get('dividend_per_share')),
                'totalAssets': normalize_value(record.get('total_assets')),
                'totalEquity': normalize_value(record.get('total_equity')),
                'deposits': normalize_value(record.get('customer_deposits')),
                'loans': normalize_value(record.get('loans_and_advances')),
                'ebitda': normalize_value(record.get('ebitda')),
                'mpesa': normalize_value(record.get('mpesa_revenue')),
            }

            # Remove None values to keep JSON clean
            period_obj = {k: v for k, v in period_obj.items() if v is not None}

            if period_type == 'annual':
                annuals.append(period_obj)
            else:
                quarters.append(period_obj)

        # Limit to most recent 20 entries to keep JS file manageable
        annuals = annuals[:10]
        quarters = quarters[:20]

        # Get latest period
        latest_period = None
        if annuals:
            latest_period = annuals[0]
        elif quarters:
            latest_period = quarters[0]

        # Build company entry
        nse_companies[ticker] = {
            'name': company_info['name'],
            'ticker': ticker,
            'exchange': 'NSE',
            'sector': company_info['sector'],
            'logo': company_info['logo'],
            'currency': 'KES',
            'units': 'thousands',
            'latestPrice': None,  # Will be populated by fetch_prices.py
            'latestPeriod': latest_period,
            'annuals': annuals,
            'quarters': quarters
        }

        print(f"  {ticker}: {len(annuals)} annual + {len(quarters)} quarterly records")

    print(f"\nTotal companies for frontend: {len(nse_companies)}\n")

    # Generate JavaScript file
    js_content = "// Auto-generated on {}\n".format(__import__('datetime').datetime.now().isoformat())
    js_content += "// Do not edit manually - regenerate with generate_frontend_data.py\n\n"

    js_content += "const NSE_COMPANIES = " + json.dumps(nse_companies, indent=2) + ";\n\n"

    # Add index of tickers
    ticker_list = sorted(nse_companies.keys())
    js_content += "const NSE_INDEX = " + json.dumps(ticker_list) + ";\n\n"

    # Add company count
    js_content += f"const NSE_COMPANY_COUNT = {len(nse_companies)};\n"

    # Write to file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(js_content)

    print(f"[OK] Frontend data generated: {OUTPUT_FILE}")
    print(f"  File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    print(f"  Companies: {len(nse_companies)}")
    print(f"  Total records: {sum(len(c['annuals']) + len(c['quarters']) for c in nse_companies.values())}")

    # Validation report
    validation = {
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'total_companies': len(nse_companies),
        'companies': list(nse_companies.keys()),
        'total_annuals': sum(len(c['annuals']) for c in nse_companies.values()),
        'total_quarters': sum(len(c['quarters']) for c in nse_companies.values()),
    }

    with open(DATA_ROOT / "frontend_data_validation.json", 'w') as f:
        json.dump(validation, f, indent=2)

    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    generate_frontend_data()
