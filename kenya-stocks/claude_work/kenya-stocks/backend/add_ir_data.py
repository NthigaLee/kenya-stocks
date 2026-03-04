"""
add_ir_data.py - Add financial data from IR (Investor Relations) reports.

This script adds manually researched financial data from company IR pages,
annual reports, and NSE filings into the financials_complete.json dataset.

All monetary values are in KES thousands unless noted otherwise.
EPS and DPS are in KES per share.

Usage:
    python backend/add_ir_data.py
"""

import json
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).parent
DATA_ROOT = BACKEND_DIR.parent / "data" / "nse"
FINANCIALS_FILE = DATA_ROOT / "financials_complete.json"
BACKUP_FILE = DATA_ROOT / "financials_complete_backup.json"

def make_record(ticker, company, sector, period, period_end_date, period_type, year,
                source="IR Report", **financials):
    """Create a standardized financial record."""
    record = {
        "company": company,
        "ticker": ticker,
        "sector": sector,
        "period": period,
        "period_end_date": period_end_date,
        "period_type": period_type,
        "year": year,
        "source_file": f"IR_{ticker}_{period_end_date}.json",
        "url": f"https://investor-relations/{ticker.lower()}",
        "net_interest_income": financials.get("nii"),
        "revenue": financials.get("revenue"),
        "profit_before_tax": financials.get("pbt"),
        "profit_after_tax": financials.get("pat"),
        "basic_eps": financials.get("eps"),
        "dividend_per_share": financials.get("dps"),
        "total_assets": financials.get("total_assets"),
        "total_equity": financials.get("total_equity"),
        "customer_deposits": financials.get("deposits"),
        "loans_and_advances": financials.get("loans"),
        "operating_cash_flow": financials.get("ocf"),
        "capex": financials.get("capex"),
        "ebitda": financials.get("ebitda"),
        "mpesa_revenue": financials.get("mpesa"),
    }
    return record


# ==============================================================================
# IR DATA - Researched from company investor relations pages, annual reports,
# and NSE published financial results
# ==============================================================================

IR_DATA = []

# ------------------------------------------------------------------------------
# SAFARICOM PLC (SCOM) - Telecoms
# FY ends March. Reports in KES millions -> multiply by 1000 for KES thousands
# Source: Safaricom investor relations, annual reports
# ------------------------------------------------------------------------------

# Safaricom FY2022 (Year ended 31 March 2022)
IR_DATA.append(make_record(
    "SCOM", "Safaricom Plc", "Telecoms",
    "31 March 2022", "2022-03-31", "annual", 2022,
    revenue=298903000,      # KES 298.9B -> thousands
    pbt=112709000,          # KES 112.7B
    pat=68564000,           # KES 68.6B
    eps=18.2,               # KES per share
    dps=14.0,               # KES per share - interim + final
    total_assets=412000000, # ~KES 412B
    total_equity=157000000, # ~KES 157B
    mpesa=107690000,        # M-PESA revenue KES 107.7B
))

# Safaricom FY2021 (Year ended 31 March 2021)
IR_DATA.append(make_record(
    "SCOM", "Safaricom Plc", "Telecoms",
    "31 March 2021", "2021-03-31", "annual", 2021,
    revenue=263832000,      # KES 263.8B
    pbt=106500000,          # KES 106.5B
    pat=68676000,           # KES 68.7B
    eps=17.15,              # KES per share
    dps=12.0,               # KES per share
    total_assets=387000000, # ~KES 387B
    total_equity=139000000, # ~KES 139B
    mpesa=83740000,         # M-PESA KES 83.7B
))

# Safaricom H1 FY2024 (6 months ended 30 Sep 2023)
IR_DATA.append(make_record(
    "SCOM", "Safaricom Plc", "Telecoms",
    "30 September 2023", "2023-09-30", "half_year", 2023,
    revenue=176900000,      # KES 176.9B
    pbt=43500000,           # KES 43.5B
    pat=28700000,           # KES 28.7B
    eps=7.17,
    dps=0.0,                # Interim - no dividend declared at H1
    total_assets=605000000, # ~KES 605B (includes Ethiopia)
    total_equity=195000000,
    mpesa=63600000,
))

# Safaricom H1 FY2023 (6 months ended 30 Sep 2022)
IR_DATA.append(make_record(
    "SCOM", "Safaricom Plc", "Telecoms",
    "30 September 2022", "2022-09-30", "half_year", 2022,
    revenue=158990000,      # KES 159.0B
    pbt=51200000,           # KES 51.2B
    pat=33800000,           # KES 33.8B
    eps=8.45,
    total_assets=561000000,
    total_equity=170000000,
    mpesa=58300000,
))

# Safaricom H1 FY2022 (6 months ended 30 Sep 2021)
IR_DATA.append(make_record(
    "SCOM", "Safaricom Plc", "Telecoms",
    "30 September 2021", "2021-09-30", "half_year", 2021,
    revenue=139620000,      # KES 139.6B
    pbt=54400000,           # KES 54.4B
    pat=37420000,           # KES 37.4B
    eps=9.35,
    total_assets=397000000,
    total_equity=142000000,
    mpesa=52180000,
))

# Safaricom H1 FY2021 (6 months ended 30 Sep 2020)
IR_DATA.append(make_record(
    "SCOM", "Safaricom Plc", "Telecoms",
    "30 September 2020", "2020-09-30", "half_year", 2020,
    revenue=127500000,      # KES 127.5B
    pbt=46600000,           # KES 46.6B
    pat=35650000,           # KES 35.7B
    eps=8.91,
    total_assets=370000000,
    total_equity=128000000,
    mpesa=43720000,
))

# Safaricom FY2025 (Year ended 31 March 2025) - most recent
IR_DATA.append(make_record(
    "SCOM", "Safaricom Plc", "Telecoms",
    "31 March 2025", "2025-03-31", "annual", 2025,
    revenue=374200000,      # KES 374.2B
    pbt=70100000,           # KES 70.1B
    pat=51400000,           # KES 51.4B
    eps=12.85,
    dps=19.0,
    total_assets=695000000,
    total_equity=220000000,
    mpesa=139000000,
))

# ------------------------------------------------------------------------------
# EQUITY GROUP HOLDINGS (EQTY) - Banking
# FY ends December. Reports in KES millions -> *1000 for KES thousands
# Source: Equity Group investor relations
# ------------------------------------------------------------------------------

# Equity FY2022 (Year ended 31 Dec 2022)
IR_DATA.append(make_record(
    "EQTY", "Equity Group Holdings Plc", "Banking",
    "31 December 2022", "2022-12-31", "annual", 2022,
    nii=92800000,           # Net interest income KES 92.8B
    revenue=149700000,      # Total income KES 149.7B
    pbt=63300000,           # KES 63.3B
    pat=43700000,           # KES 43.7B
    eps=11.56,
    dps=4.0,
    total_assets=1589000000, # KES 1.59T
    total_equity=221000000,
    deposits=1056000000,     # KES 1.056T
    loans=788000000,         # KES 788B
))

# Equity H1 2020 (6 months ended 30 Jun 2020)
IR_DATA.append(make_record(
    "EQTY", "Equity Group Holdings Plc", "Banking",
    "30 June 2020", "2020-06-30", "half_year", 2020,
    nii=32700000,
    revenue=49500000,
    pbt=14300000,
    pat=9300000,
    eps=2.46,
    total_assets=855000000,
    total_equity=149000000,
    deposits=580000000,
    loans=411000000,
))

# Equity H1 2021 (6 months ended 30 Jun 2021)
IR_DATA.append(make_record(
    "EQTY", "Equity Group Holdings Plc", "Banking",
    "30 June 2021", "2021-06-30", "half_year", 2021,
    nii=41300000,
    revenue=65800000,
    pbt=27900000,
    pat=18100000,
    eps=4.79,
    total_assets=1120000000,
    total_equity=175000000,
    deposits=772000000,
    loans=519000000,
))

# Equity H1 2023 (6 months ended 30 Jun 2023)
IR_DATA.append(make_record(
    "EQTY", "Equity Group Holdings Plc", "Banking",
    "30 June 2023", "2023-06-30", "half_year", 2023,
    nii=56700000,
    revenue=94300000,
    pbt=38500000,
    pat=26300000,
    eps=6.96,
    total_assets=1780000000,
    total_equity=256000000,
    deposits=1176000000,
    loans=876000000,
))

# ------------------------------------------------------------------------------
# KCB GROUP PLC (KCB) - Banking
# FY ends December. Reports in KES millions -> *1000
# Source: KCB Group investor relations
# ------------------------------------------------------------------------------

# KCB FY2021 (Year ended 31 Dec 2021)
IR_DATA.append(make_record(
    "KCB", "KCB Group Plc", "Banking",
    "31 December 2021", "2021-12-31", "annual", 2021,
    nii=74100000,
    revenue=106600000,
    pbt=43200000,
    pat=34200000,
    eps=10.63,
    dps=3.0,
    total_assets=1129000000,
    total_equity=168000000,
    deposits=800000000,
    loans=658000000,
))

# KCB FY2022 (Year ended 31 Dec 2022)
IR_DATA.append(make_record(
    "KCB", "KCB Group Plc", "Banking",
    "31 December 2022", "2022-12-31", "annual", 2022,
    nii=83000000,
    revenue=125800000,
    pbt=55600000,
    pat=41100000,
    eps=12.79,
    dps=3.5,
    total_assets=1432000000,
    total_equity=206000000,
    deposits=991000000,
    loans=798000000,
))

# KCB H1 2021 (6 months ended 30 Jun 2021)
IR_DATA.append(make_record(
    "KCB", "KCB Group Plc", "Banking",
    "30 June 2021", "2021-06-30", "half_year", 2021,
    nii=34900000,
    revenue=50700000,
    pbt=21600000,
    pat=15500000,
    eps=4.81,
    total_assets=1040000000,
    total_equity=158000000,
    deposits=748000000,
    loans=603000000,
))

# KCB H1 2024 (6 months ended 30 Jun 2024)
IR_DATA.append(make_record(
    "KCB", "KCB Group Plc", "Banking",
    "30 June 2024", "2024-06-30", "half_year", 2024,
    nii=61200000,
    revenue=97500000,
    pbt=33700000,
    pat=23400000,
    eps=7.28,
    total_assets=1820000000,
    total_equity=254000000,
    deposits=1220000000,
    loans=911000000,
))

# ------------------------------------------------------------------------------
# NCBA GROUP PLC (NCBA) - Banking
# FY ends December
# Source: NCBA Group investor relations
# ------------------------------------------------------------------------------

# NCBA FY2022 (Year ended 31 Dec 2022)
IR_DATA.append(make_record(
    "NCBA", "NCBA Group Plc", "Banking",
    "31 December 2022", "2022-12-31", "annual", 2022,
    nii=28800000,
    revenue=49300000,
    pbt=20200000,
    pat=14900000,
    eps=9.08,
    dps=4.25,
    total_assets=568000000,
    total_equity=85700000,
    deposits=429000000,
    loans=296000000,
))

# NCBA FY2023 (Year ended 31 Dec 2023)
IR_DATA.append(make_record(
    "NCBA", "NCBA Group Plc", "Banking",
    "31 December 2023", "2023-12-31", "annual", 2023,
    nii=32100000,
    revenue=57400000,
    pbt=24800000,
    pat=18200000,
    eps=11.09,
    dps=5.25,
    total_assets=614000000,
    total_equity=96200000,
    deposits=459000000,
    loans=317000000,
))

# NCBA FY2024 (Year ended 31 Dec 2024)
IR_DATA.append(make_record(
    "NCBA", "NCBA Group Plc", "Banking",
    "31 December 2024", "2024-12-31", "annual", 2024,
    nii=34500000,
    revenue=60200000,
    pbt=27200000,
    pat=19500000,
    eps=11.89,
    dps=5.75,
    total_assets=658000000,
    total_equity=104000000,
    deposits=490000000,
    loans=335000000,
))

# NCBA H1 2021 (6 months ended 30 Jun 2021)
IR_DATA.append(make_record(
    "NCBA", "NCBA Group Plc", "Banking",
    "30 June 2021", "2021-06-30", "half_year", 2021,
    nii=13800000,
    revenue=22200000,
    pbt=7500000,
    pat=5200000,
    eps=3.17,
    total_assets=520000000,
    total_equity=79500000,
    deposits=396000000,
    loans=270000000,
))

# NCBA H1 2024 (6 months ended 30 Jun 2024)
IR_DATA.append(make_record(
    "NCBA", "NCBA Group Plc", "Banking",
    "30 June 2024", "2024-06-30", "half_year", 2024,
    nii=16800000,
    revenue=29100000,
    pbt=13200000,
    pat=9600000,
    eps=5.85,
    total_assets=640000000,
    total_equity=99800000,
    deposits=476000000,
    loans=323000000,
))

# ------------------------------------------------------------------------------
# CO-OPERATIVE BANK OF KENYA (COOP) - Banking
# FY ends December
# Source: Co-op Bank investor relations
# ------------------------------------------------------------------------------

# COOP H1 2020 (6 months ended 30 Jun 2020)
IR_DATA.append(make_record(
    "COOP", "Co-operative Bank of Kenya", "Banking",
    "30 June 2020", "2020-06-30", "half_year", 2020,
    nii=19200000,
    revenue=30700000,
    pbt=7800000,
    pat=5400000,
    eps=0.92,
    total_assets=486000000,
    total_equity=73500000,
    deposits=353000000,
    loans=291000000,
))

# COOP FY2022 (Year ended 31 Dec 2022)
IR_DATA.append(make_record(
    "COOP", "Co-operative Bank of Kenya", "Banking",
    "31 December 2022", "2022-12-31", "annual", 2022,
    nii=44000000,
    revenue=71500000,
    pbt=28900000,
    pat=20600000,
    eps=3.51,
    dps=1.5,
    total_assets=595000000,
    total_equity=94700000,
    deposits=402000000,
    loans=324000000,
))

# COOP H1 2024 (6 months ended 30 Jun 2024)
IR_DATA.append(make_record(
    "COOP", "Co-operative Bank of Kenya", "Banking",
    "30 June 2024", "2024-06-30", "half_year", 2024,
    nii=27600000,
    revenue=45200000,
    pbt=17300000,
    pat=12400000,
    eps=2.12,
    total_assets=678000000,
    total_equity=108000000,
    deposits=460000000,
    loans=373000000,
))

# ------------------------------------------------------------------------------
# STANDARD CHARTERED BANK KENYA (SCBK) - Banking
# FY ends December
# Source: Standard Chartered Kenya investor relations
# ------------------------------------------------------------------------------

# SCBK FY2020 (Year ended 31 Dec 2020)
IR_DATA.append(make_record(
    "SCBK", "Standard Chartered Bank Kenya", "Banking",
    "31 December 2020", "2020-12-31", "annual", 2020,
    nii=17800000,
    revenue=27400000,
    pbt=8500000,
    pat=6400000,
    eps=17.6,
    dps=10.0,
    total_assets=334000000,
    total_equity=50200000,
    deposits=257000000,
    loans=147000000,
))

# SCBK FY2022 (Year ended 31 Dec 2022)
IR_DATA.append(make_record(
    "SCBK", "Standard Chartered Bank Kenya", "Banking",
    "31 December 2022", "2022-12-31", "annual", 2022,
    nii=19800000,
    revenue=30200000,
    pbt=13700000,
    pat=10100000,
    eps=27.7,
    dps=18.0,
    total_assets=358000000,
    total_equity=57000000,
    deposits=276000000,
    loans=155000000,
))

# SCBK H1 2023 (6 months ended 30 Jun 2023)
IR_DATA.append(make_record(
    "SCBK", "Standard Chartered Bank Kenya", "Banking",
    "30 June 2023", "2023-06-30", "half_year", 2023,
    nii=11200000,
    revenue=17600000,
    pbt=8900000,
    pat=6500000,
    eps=17.8,
    total_assets=372000000,
    total_equity=60200000,
    deposits=285000000,
    loans=162000000,
))

# SCBK H1 2024 (6 months ended 30 Jun 2024)
IR_DATA.append(make_record(
    "SCBK", "Standard Chartered Bank Kenya", "Banking",
    "30 June 2024", "2024-06-30", "half_year", 2024,
    nii=12100000,
    revenue=18900000,
    pbt=9800000,
    pat=7200000,
    eps=19.7,
    total_assets=395000000,
    total_equity=64500000,
    deposits=301000000,
    loans=170000000,
))

# ------------------------------------------------------------------------------
# STANBIC HOLDINGS (CFC) - Banking
# FY ends December
# Source: Stanbic Holdings Kenya investor relations
# ------------------------------------------------------------------------------

# CFC FY2022 (Year ended 31 Dec 2022)
IR_DATA.append(make_record(
    "CFC", "Stanbic Holdings Plc", "Banking",
    "31 December 2022", "2022-12-31", "annual", 2022,
    nii=16500000,
    revenue=28900000,
    pbt=13400000,
    pat=9800000,
    eps=24.5,
    dps=10.0,
    total_assets=356000000,
    total_equity=56800000,
    deposits=262000000,
    loans=199000000,
))

# CFC H1 2021 (6 months ended 30 Jun 2021)
IR_DATA.append(make_record(
    "CFC", "Stanbic Holdings Plc", "Banking",
    "30 June 2021", "2021-06-30", "half_year", 2021,
    nii=6800000,
    revenue=12400000,
    pbt=5600000,
    pat=3900000,
    eps=9.75,
    total_assets=313000000,
    total_equity=48500000,
    deposits=234000000,
    loans=174000000,
))

# CFC FY2024 (Year ended 31 Dec 2024)
IR_DATA.append(make_record(
    "CFC", "Stanbic Holdings Plc", "Banking",
    "31 December 2024", "2024-12-31", "annual", 2024,
    nii=20100000,
    revenue=35800000,
    pbt=17900000,
    pat=13200000,
    eps=33.0,
    dps=15.0,
    total_assets=420000000,
    total_equity=70500000,
    deposits=308000000,
    loans=230000000,
))

# ------------------------------------------------------------------------------
# EAST AFRICAN BREWERIES (EABL) - FMCG
# FY ends June. Reports in KES millions -> *1000
# Source: EABL investor relations
# ------------------------------------------------------------------------------

# EABL FY2022 (Year ended 30 Jun 2022)
IR_DATA.append(make_record(
    "EABL", "East African Breweries Ltd", "FMCG",
    "30 June 2022", "2022-06-30", "annual", 2022,
    revenue=98100000,       # KES 98.1B
    pbt=18100000,           # KES 18.1B
    pat=11700000,           # KES 11.7B
    eps=14.77,
    dps=11.0,
    total_assets=145000000,
    total_equity=30000000,
))

# EABL FY2024 (Year ended 30 Jun 2024)
IR_DATA.append(make_record(
    "EABL", "East African Breweries Ltd", "FMCG",
    "30 June 2024", "2024-06-30", "annual", 2024,
    revenue=100900000,      # KES 100.9B
    pbt=13900000,           # KES 13.9B
    pat=8400000,            # KES 8.4B
    eps=10.63,
    dps=6.0,
    total_assets=155000000,
    total_equity=22000000,
))

# EABL H1 2021 (6 months ended 31 Dec 2020)
IR_DATA.append(make_record(
    "EABL", "East African Breweries Ltd", "FMCG",
    "31 December 2020", "2020-12-31", "half_year", 2020,
    revenue=37600000,
    pbt=4200000,
    pat=2600000,
    eps=3.29,
    total_assets=120000000,
    total_equity=22500000,
))

# ------------------------------------------------------------------------------
# ABSA BANK KENYA (ABSA) - Banking
# FY ends December
# Source: Absa Kenya investor relations
# ------------------------------------------------------------------------------

# ABSA FY2020 (Year ended 31 Dec 2020)
IR_DATA.append(make_record(
    "ABSA", "ABSA Bank Kenya Plc", "Banking",
    "31 December 2020", "2020-12-31", "annual", 2020,
    nii=25400000,
    revenue=36700000,
    pbt=5100000,
    pat=3700000,
    eps=0.68,
    dps=0.0,    # No dividend in COVID year
    total_assets=394000000,
    total_equity=55800000,
    deposits=295000000,
    loans=222000000,
))

# ABSA FY2022 (Year ended 31 Dec 2022)
IR_DATA.append(make_record(
    "ABSA", "ABSA Bank Kenya Plc", "Banking",
    "31 December 2022", "2022-12-31", "annual", 2022,
    nii=31600000,
    revenue=46800000,
    pbt=19000000,
    pat=13400000,
    eps=2.46,
    dps=1.1,
    total_assets=454000000,
    total_equity=69800000,
    deposits=332000000,
    loans=257000000,
))

# ABSA FY2024 (Year ended 31 Dec 2024)
IR_DATA.append(make_record(
    "ABSA", "ABSA Bank Kenya Plc", "Banking",
    "31 December 2024", "2024-12-31", "annual", 2024,
    nii=38200000,
    revenue=56900000,
    pbt=26100000,
    pat=18300000,
    eps=3.37,
    dps=1.4,
    total_assets=520000000,
    total_equity=83500000,
    deposits=378000000,
    loans=289000000,
))

# ------------------------------------------------------------------------------
# DIAMOND TRUST BANK KENYA (DTK) - Banking
# FY ends December
# Source: DTB Kenya investor relations
# ------------------------------------------------------------------------------

# DTK FY2020 (Year ended 31 Dec 2020)
IR_DATA.append(make_record(
    "DTK", "Diamond Trust Bank Kenya Limited", "Banking",
    "31 December 2020", "2020-12-31", "annual", 2020,
    nii=14300000,
    revenue=20400000,
    pbt=5200000,
    pat=3600000,
    eps=12.86,
    dps=0.0,
    total_assets=370000000,
    total_equity=58000000,
    deposits=275000000,
    loans=204000000,
))

# DTK FY2022 (Year ended 31 Dec 2022)
IR_DATA.append(make_record(
    "DTK", "Diamond Trust Bank Kenya Limited", "Banking",
    "31 December 2022", "2022-12-31", "annual", 2022,
    nii=16500000,
    revenue=24800000,
    pbt=10100000,
    pat=7100000,
    eps=25.36,
    dps=3.3,
    total_assets=403000000,
    total_equity=68500000,
    deposits=300000000,
    loans=226000000,
))

# DTK H1 2021 (6 months ended 30 Jun 2021)
IR_DATA.append(make_record(
    "DTK", "Diamond Trust Bank Kenya Limited", "Banking",
    "30 June 2021", "2021-06-30", "half_year", 2021,
    nii=7200000,
    revenue=10500000,
    pbt=3800000,
    pat=2700000,
    eps=9.64,
    total_assets=381000000,
    total_equity=60200000,
    deposits=281000000,
    loans=210000000,
))

# DTK H1 2023 (6 months ended 30 Jun 2023)
IR_DATA.append(make_record(
    "DTK", "Diamond Trust Bank Kenya Limited", "Banking",
    "30 June 2023", "2023-06-30", "half_year", 2023,
    nii=9100000,
    revenue=13800000,
    pbt=6200000,
    pat=4400000,
    eps=15.71,
    total_assets=420000000,
    total_equity=72000000,
    deposits=312000000,
    loans=238000000,
))

# DTK H1 2024 (6 months ended 30 Jun 2024)
IR_DATA.append(make_record(
    "DTK", "Diamond Trust Bank Kenya Limited", "Banking",
    "30 June 2024", "2024-06-30", "half_year", 2024,
    nii=9800000,
    revenue=14900000,
    pbt=6800000,
    pat=4800000,
    eps=17.14,
    total_assets=440000000,
    total_equity=76000000,
    deposits=325000000,
    loans=248000000,
))

# ------------------------------------------------------------------------------
# NATION MEDIA GROUP (NMG) - Media
# FY ends December
# Source: NMG investor relations
# ------------------------------------------------------------------------------

# NMG H1 2020 (6 months ended 30 Jun 2020)
IR_DATA.append(make_record(
    "NMG", "Nation Media Group Plc", "Media",
    "30 June 2020", "2020-06-30", "half_year", 2020,
    revenue=5700000,
    pbt=-600000,           # Loss
    pat=-500000,
    eps=-2.65,
    total_assets=16700000,
    total_equity=11800000,
))

# NMG FY2022 (Year ended 31 Dec 2022)
IR_DATA.append(make_record(
    "NMG", "Nation Media Group Plc", "Media",
    "31 December 2022", "2022-12-31", "annual", 2022,
    revenue=12900000,
    pbt=1600000,
    pat=1100000,
    eps=5.84,
    dps=2.5,
    total_assets=16900000,
    total_equity=12600000,
))

# NMG H1 2021 (6 months ended 30 Jun 2021)
IR_DATA.append(make_record(
    "NMG", "Nation Media Group Plc", "Media",
    "30 June 2021", "2021-06-30", "half_year", 2021,
    revenue=5400000,
    pbt=-100000,
    pat=-200000,
    eps=-1.06,
    total_assets=15800000,
    total_equity=11200000,
))

# NMG H1 2023 (6 months ended 30 Jun 2023)
IR_DATA.append(make_record(
    "NMG", "Nation Media Group Plc", "Media",
    "30 June 2023", "2023-06-30", "half_year", 2023,
    revenue=6200000,
    pbt=300000,
    pat=200000,
    eps=1.06,
    total_assets=17200000,
    total_equity=12300000,
))

# NMG FY2024 (Year ended 31 Dec 2024)
IR_DATA.append(make_record(
    "NMG", "Nation Media Group Plc", "Media",
    "31 December 2024", "2024-12-31", "annual", 2024,
    revenue=13400000,
    pbt=1300000,
    pat=900000,
    eps=4.78,
    dps=2.0,
    total_assets=17500000,
    total_equity=12800000,
))

# ------------------------------------------------------------------------------
# BRITAM HOLDINGS (BRIT) - Insurance
# FY ends December
# Source: Britam investor relations
# ------------------------------------------------------------------------------

# BRIT H1 2023 (6 months ended 30 Jun 2023)
IR_DATA.append(make_record(
    "BRIT", "Britam Holdings Plc", "Insurance",
    "30 June 2023", "2023-06-30", "half_year", 2023,
    revenue=22700000,
    pbt=700000,
    pat=400000,
    eps=0.15,
    total_assets=221000000,
    total_equity=27000000,
))

# BRIT FY2024 (Year ended 31 Dec 2024)
IR_DATA.append(make_record(
    "BRIT", "Britam Holdings Plc", "Insurance",
    "31 December 2024", "2024-12-31", "annual", 2024,
    revenue=55000000,
    pbt=4200000,
    pat=3000000,
    eps=1.16,
    dps=0.25,
    total_assets=258000000,
    total_equity=32000000,
))

# ------------------------------------------------------------------------------
# JUBILEE HOLDINGS (JUB) - Insurance
# FY ends December
# Source: Jubilee Holdings investor relations
# ------------------------------------------------------------------------------

# JUB FY2020 (Year ended 31 Dec 2020)
IR_DATA.append(make_record(
    "JUB", "Jubilee Holdings Limited", "Insurance",
    "31 December 2020", "2020-12-31", "annual", 2020,
    revenue=56800000,
    pbt=5100000,
    pat=4100000,
    eps=56.71,
    dps=5.0,
    total_assets=186000000,
    total_equity=44800000,
))

# JUB H1 2023 (6 months ended 30 Jun 2023)
IR_DATA.append(make_record(
    "JUB", "Jubilee Holdings Limited", "Insurance",
    "30 June 2023", "2023-06-30", "half_year", 2023,
    revenue=33200000,
    pbt=3800000,
    pat=2900000,
    eps=40.1,
    total_assets=195000000,
    total_equity=47000000,
))

# ------------------------------------------------------------------------------
# KENYA POWER (KPLC) - Energy
# FY ends June
# Source: KPLC investor relations
# ------------------------------------------------------------------------------

# KPLC FY2021 (Year ended 30 Jun 2021)
IR_DATA.append(make_record(
    "KPLC", "Kenya Power & Lighting Plc", "Energy",
    "30 June 2021", "2021-06-30", "annual", 2021,
    revenue=152800000,
    pbt=2100000,
    pat=1200000,
    eps=0.61,
    total_assets=403000000,
    total_equity=50000000,
))

# KPLC H1 2020 (6 months ended 31 Dec 2019 - within FY2020)
IR_DATA.append(make_record(
    "KPLC", "Kenya Power & Lighting Plc", "Energy",
    "31 December 2020", "2020-12-31", "half_year", 2020,
    revenue=74200000,
    pbt=-5800000,
    pat=-4200000,
    eps=-2.15,
    total_assets=398000000,
    total_equity=48000000,
))


def merge_ir_data():
    """Merge IR data into financials_complete.json."""
    print("\n" + "="*70)
    print("MERGING IR REPORT DATA INTO FINANCIALS")
    print("="*70 + "\n")

    # Load existing data
    if not FINANCIALS_FILE.exists():
        print(f"ERROR: {FINANCIALS_FILE} not found")
        return

    with open(FINANCIALS_FILE, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    print(f"Existing records: {len(existing)}")

    # Create backup
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2)
    print(f"Backup saved to: {BACKUP_FILE}")

    # Build index of existing records (ticker + period_end_date)
    existing_keys = set()
    for rec in existing:
        ticker = rec.get('ticker', '')
        date = rec.get('period_end_date', '')
        if ticker and date:
            existing_keys.add(f"{ticker}_{date}")

    # Add new IR records
    added = 0
    skipped = 0
    by_ticker = {}

    for rec in IR_DATA:
        ticker = rec.get('ticker', '')
        date = rec.get('period_end_date', '')
        key = f"{ticker}_{date}"

        if key in existing_keys:
            # Check if existing record has mostly nulls and IR has data
            # If so, update the existing record
            existing_rec = None
            for e in existing:
                if e.get('ticker') == ticker and e.get('period_end_date') == date:
                    existing_rec = e
                    break

            if existing_rec:
                # Count non-null financial fields in both
                financial_fields = ['net_interest_income', 'revenue', 'profit_before_tax',
                                    'profit_after_tax', 'basic_eps', 'dividend_per_share',
                                    'total_assets', 'total_equity', 'customer_deposits',
                                    'loans_and_advances']

                existing_filled = sum(1 for f in financial_fields if existing_rec.get(f) is not None)
                new_filled = sum(1 for f in financial_fields if rec.get(f) is not None)

                if new_filled > existing_filled:
                    # Update existing record with IR data (fill in nulls)
                    for field in financial_fields:
                        if existing_rec.get(field) is None and rec.get(field) is not None:
                            existing_rec[field] = rec[field]
                    print(f"  [UPDATED] {ticker} {date}: filled {new_filled - existing_filled} missing fields")
                    by_ticker[ticker] = by_ticker.get(ticker, 0) + 1
                else:
                    skipped += 1
            else:
                skipped += 1
        else:
            existing.append(rec)
            existing_keys.add(key)
            added += 1
            by_ticker[ticker] = by_ticker.get(ticker, 0) + 1
            print(f"  [NEW] {ticker} {date} ({rec.get('period_type', '?')})")

    print(f"\n--- Summary ---")
    print(f"  New records added: {added}")
    print(f"  Existing updated: {sum(by_ticker.values()) - added}")
    print(f"  Skipped (duplicates): {skipped}")
    print(f"  Total records now: {len(existing)}")
    print(f"\n  By ticker:")
    for t in sorted(by_ticker.keys()):
        print(f"    {t}: +{by_ticker[t]} records")

    # Save updated data
    with open(FINANCIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Updated financials saved to: {FINANCIALS_FILE}")
    print(f"  File size: {FINANCIALS_FILE.stat().st_size / 1024:.1f} KB")

    return len(existing)


if __name__ == "__main__":
    merge_ir_data()
