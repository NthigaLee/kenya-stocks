"""
update_verified_2024.py - BATCH 2: Verified 2024 IR Data

Covers period_end_dates in 2024:
- SCOM FY2024 (Mar 2024), EABL FY2024 (Jun 2024)
- FY2023 annual results for Dec year-end companies (ABSA, EQTY, KCB, NCBA, COOP, SCBK, DTK, CFC)

Sources: NSE filings, African Financials, Cytonn, Kingdom Securities, company press releases
"""

import json
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
DATA_ROOT = BACKEND_DIR.parent / "data" / "nse"
FINANCIALS_FILE = DATA_ROOT / "financials_complete.json"


def update_or_add(data, ticker, period_end_date, updates):
    for rec in data:
        if rec.get('ticker') == ticker and rec.get('period_end_date') == period_end_date:
            for k, v in updates.items():
                if v is not None or k not in rec or rec[k] is None:
                    rec[k] = v
            rec['source_file'] = f"VERIFIED_IR_{ticker}_{period_end_date}.json"
            return "UPDATED"
    data.append(updates)
    return "ADDED"


def run():
    print("\n" + "="*70)
    print("BATCH 2: VERIFIED 2024 IR DATA UPDATE")
    print("="*70 + "\n")

    with open(FINANCIALS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Starting records: {len(data)}")
    changes = []

    # ==================================================================
    # SAFARICOM FY2024 (Year ended 31 March 2024)
    # Source: Safaricom FY24 Press Release (May 9, 2024)
    # https://www.safaricom.co.ke/images/Downloads/FY24-Press-Release-9-May-2024.pdf
    # Revenue: KES 349.45B, Group PBT: KES 84.69B, EPS: KES 1.57
    # M-PESA: KES 140.01B, Shareholders' equity: KES 335.75B
    # ==================================================================
    r = update_or_add(data, "SCOM", "2024-03-31", {
        "company": "Safaricom Plc",
        "ticker": "SCOM",
        "sector": "Telecoms",
        "period": "31 March 2024",
        "period_end_date": "2024-03-31",
        "period_type": "annual",
        "year": 2024,
        "source_file": "VERIFIED_IR_SCOM_2024-03-31.json",
        "url": "https://www.safaricom.co.ke/investor-relations-landing/reports/financial-report/financial-results",
        "net_interest_income": None,
        "revenue": 349450000,        # KES 349.45B
        "profit_before_tax": 84690000,  # KES 84.69B Group PBT
        "profit_after_tax": 62900000,   # ~KES 62.9B (EPS 1.57 * 40.065B shares)
        "basic_eps": 1.57,
        "dividend_per_share": 1.20,
        "total_assets": None,
        "total_equity": 335750000,    # KES 335.75B
        "customer_deposits": None,
        "loans_and_advances": None,
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": 140010000,  # KES 140.01B
    })
    changes.append(f"  [{r}] SCOM FY2024 - Revenue 349.5B, PBT 84.7B, PAT 62.9B, EPS 1.57")

    # ==================================================================
    # EABL FY2024 (Year ended 30 June 2024)
    # Source: EABL FY2024 Financial Results, NCBA Investment Bank
    # Revenue: KES 124.1B, PBT: KES 16.77B, PAT: KES 10.9B
    # EPS: KES 10.30, DPS: KES 7.00
    # ==================================================================
    r = update_or_add(data, "EABL", "2024-06-30", {
        "company": "East African Breweries Ltd",
        "ticker": "EABL",
        "sector": "FMCG",
        "period": "30 June 2024",
        "period_end_date": "2024-06-30",
        "period_type": "annual",
        "year": 2024,
        "source_file": "VERIFIED_IR_EABL_2024-06-30.json",
        "url": "https://www.eabl.com/investors/financial-results",
        "net_interest_income": None,
        "revenue": 124130000,       # KES 124.13B
        "profit_before_tax": 16770000,  # KES 16.77B
        "profit_after_tax": 10900000,   # KES 10.9B
        "basic_eps": 10.30,
        "dividend_per_share": 7.0,
        "total_assets": None,
        "total_equity": None,
        "customer_deposits": None,
        "loans_and_advances": None,
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": None,
    })
    changes.append(f"  [{r}] EABL FY2024 - Revenue 124.1B, PBT 16.8B, PAT 10.9B, EPS 10.30")

    # ==================================================================
    # EQUITY GROUP FY2023 (Year ended 31 December 2023)
    # Source: Kingdom Securities, Cytonn, equitygroupholdings.com
    # PBT: KES 51.88B, PAT: KES 43.74B, EPS: KES 11.12
    # ==================================================================
    r = update_or_add(data, "EQTY", "2023-12-31", {
        "company": "Equity Group Holdings Plc",
        "ticker": "EQTY",
        "sector": "Banking",
        "period": "31 December 2023",
        "period_end_date": "2023-12-31",
        "period_type": "annual",
        "year": 2023,
        "source_file": "VERIFIED_IR_EQTY_2023-12-31.json",
        "url": "https://equitygroupholdings.com/investor-relations/",
        "net_interest_income": None,
        "revenue": None,
        "profit_before_tax": 51880000,  # KES 51.88B
        "profit_after_tax": 43740000,   # KES 43.74B
        "basic_eps": 11.12,
        "dividend_per_share": None,
        "total_assets": None,
        "total_equity": None,
        "customer_deposits": None,
        "loans_and_advances": None,
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": None,
    })
    changes.append(f"  [{r}] EQTY FY2023 - PBT 51.9B, PAT 43.7B, EPS 11.12")

    # ==================================================================
    # KCB GROUP FY2023 (Year ended 31 December 2023)
    # Source: KCB Group press release, Kenyan Wallstreet, Cytonn
    # Revenue: KES 165.2B, NII: KES 107.33B, PAT: KES 37.46B
    # DPS: KES 0 (no dividend), Total assets: KES 2.17T
    # Equity: KES 236.4B, EPS: ~KES 11.7
    # ==================================================================
    r = update_or_add(data, "KCB", "2023-12-31", {
        "company": "KCB Group Plc",
        "ticker": "KCB",
        "sector": "Banking",
        "period": "31 December 2023",
        "period_end_date": "2023-12-31",
        "period_type": "annual",
        "year": 2023,
        "source_file": "VERIFIED_IR_KCB_2023-12-31.json",
        "url": "https://kcbgroup.com/download-report?document=kcb-group-plc-fy-2023-financial-results-press-release.pdf",
        "net_interest_income": 107334000,  # KES 107.33B
        "revenue": 165200000,        # KES 165.2B
        "profit_before_tax": None,
        "profit_after_tax": 37460000,   # KES 37.46B
        "basic_eps": 11.7,
        "dividend_per_share": 0,     # No dividend in 2023
        "total_assets": 2170000000,  # KES 2.17T
        "total_equity": 236400000,   # KES 236.4B
        "customer_deposits": None,
        "loans_and_advances": None,
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": None,
    })
    changes.append(f"  [{r}] KCB FY2023 - Revenue 165.2B, NII 107.3B, PAT 37.5B, Assets 2.17T")

    # ==================================================================
    # ABSA BANK KENYA FY2023 (Year ended 31 December 2023)
    # Source: Cytonn, FIB, NSE filing
    # Revenue: KES 54.6B, PAT: KES 16.37B, EPS: KES 3.0
    # DPS: KES 1.55, Loans: KES 336B
    # ==================================================================
    r = update_or_add(data, "ABSA", "2023-12-31", {
        "company": "ABSA Bank Kenya Plc",
        "ticker": "ABSA",
        "sector": "Banking",
        "period": "31 December 2023",
        "period_end_date": "2023-12-31",
        "period_type": "annual",
        "year": 2023,
        "source_file": "VERIFIED_IR_ABSA_2023-12-31.json",
        "url": "https://www.nse.co.ke/wp-content/uploads/ABSA-Bank-Kenya-Plc-Audited-Group-Results-for-the-Year-Ended-31-Dec-2023.pdf",
        "net_interest_income": None,
        "revenue": 54600000,         # KES 54.6B total operating income
        "profit_before_tax": None,
        "profit_after_tax": 16370000,   # KES 16.37B
        "basic_eps": 3.0,
        "dividend_per_share": 1.55,
        "total_assets": None,
        "total_equity": None,
        "customer_deposits": None,
        "loans_and_advances": 336000000,  # KES 336B
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": None,
    })
    changes.append(f"  [{r}] ABSA FY2023 - Revenue 54.6B, PAT 16.4B, EPS 3.0, DPS 1.55")

    # ==================================================================
    # NCBA GROUP FY2023 (Year ended 31 December 2023)
    # Source: NCBA press release, Cytonn, African Financials
    # Revenue: KES 63.7B, PAT: KES 21.5B, EPS: KES 13.0
    # DPS: KES 4.75, Deposits: KES 579.4B
    # ==================================================================
    r = update_or_add(data, "NCBA", "2023-12-31", {
        "company": "NCBA Group Plc",
        "ticker": "NCBA",
        "sector": "Banking",
        "period": "31 December 2023",
        "period_end_date": "2023-12-31",
        "period_type": "annual",
        "year": 2023,
        "source_file": "VERIFIED_IR_NCBA_2023-12-31.json",
        "url": "https://ncbagroup.com/wp-content/uploads/2024/04/Press-Release-NCBA-Full-Year-2023-Financial-Results-Final.pdf",
        "net_interest_income": None,
        "revenue": 63700000,         # KES 63.7B
        "profit_before_tax": None,
        "profit_after_tax": 21500000,   # KES 21.5B
        "basic_eps": 13.0,
        "dividend_per_share": 4.75,
        "total_assets": None,
        "total_equity": None,
        "customer_deposits": 579400000,  # KES 579.4B
        "loans_and_advances": None,
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": None,
    })
    changes.append(f"  [{r}] NCBA FY2023 - Revenue 63.7B, PAT 21.5B, EPS 13.0, DPS 4.75")

    # ==================================================================
    # CO-OPERATIVE BANK FY2023 (Year ended 31 December 2023)
    # Source: Cytonn, Business Daily, Co-op Bank IR
    # PBT: KES 32.4B, PAT: KES 23.2B, EPS: ~KES 3.95
    # DPS: KES 1.50, Total assets: KES 671.1B
    # ==================================================================
    r = update_or_add(data, "COOP", "2023-12-31", {
        "company": "Co-operative Bank of Kenya",
        "ticker": "COOP",
        "sector": "Banking",
        "period": "31 December 2023",
        "period_end_date": "2023-12-31",
        "period_type": "annual",
        "year": 2023,
        "source_file": "VERIFIED_IR_COOP_2023-12-31.json",
        "url": "https://www.co-opbank.co.ke/investor-relations/financial-statements/",
        "net_interest_income": 45200000,  # KES 45.2B
        "revenue": 71700000,         # KES 71.7B total operating income
        "profit_before_tax": 32400000,  # KES 32.4B
        "profit_after_tax": 23200000,   # KES 23.2B
        "basic_eps": 3.95,
        "dividend_per_share": 1.50,
        "total_assets": 671100000,   # KES 671.1B
        "total_equity": None,
        "customer_deposits": None,
        "loans_and_advances": 374200000,  # KES 374.2B
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": None,
    })
    changes.append(f"  [{r}] COOP FY2023 - Revenue 71.7B, PBT 32.4B, PAT 23.2B, Assets 671.1B")

    # ==================================================================
    # STANDARD CHARTERED KENYA FY2023 (Year ended 31 December 2023)
    # Source: NSE filing, HapaKenya, African Financials
    # PBT: KES 19.7B, PAT: KES 13.8B, EPS: KES 36.17
    # DPS: KES 29.00, NII grew 32%
    # ==================================================================
    r = update_or_add(data, "SCBK", "2023-12-31", {
        "company": "Standard Chartered Bank Kenya",
        "ticker": "SCBK",
        "sector": "Banking",
        "period": "31 December 2023",
        "period_end_date": "2023-12-31",
        "period_type": "annual",
        "year": 2023,
        "source_file": "VERIFIED_IR_SCBK_2023-12-31.json",
        "url": "https://www.nse.co.ke/wp-content/uploads/Standard-Chartered-Bank-Kenya-Ltd-Financial-Results-for-the-Year-Ended-31-Dec-2023.pdf",
        "net_interest_income": None,
        "revenue": None,             # Revenue grew 23.5% but exact not confirmed
        "profit_before_tax": 19700000,  # KES 19.7B
        "profit_after_tax": 13800000,   # KES 13.8B
        "basic_eps": 36.17,
        "dividend_per_share": 29.0,
        "total_assets": None,
        "total_equity": None,
        "customer_deposits": None,
        "loans_and_advances": None,
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": None,
    })
    changes.append(f"  [{r}] SCBK FY2023 - PBT 19.7B, PAT 13.8B, EPS 36.17, DPS 29.00")

    # ==================================================================
    # DIAMOND TRUST BANK FY2023 (Year ended 31 December 2023)
    # Source: NSE filing, African Financials
    # NII: KES 27.6B, PAT: KES 7.8B, EPS: KES 24.60
    # DPS: KES 6.00, Total assets: KES 635B
    # ==================================================================
    r = update_or_add(data, "DTK", "2023-12-31", {
        "company": "Diamond Trust Bank Kenya Limited",
        "ticker": "DTK",
        "sector": "Banking",
        "period": "31 December 2023",
        "period_end_date": "2023-12-31",
        "period_type": "annual",
        "year": 2023,
        "source_file": "VERIFIED_IR_DTK_2023-12-31.json",
        "url": "https://www.nse.co.ke/wp-content/uploads/Diamond-Trust-Bank-Kenya-Limited-Audited-Group-Bank-Results-for-the-Year-Ended-31-Dec-2023.pdf",
        "net_interest_income": 27575000,  # KES 27.6B
        "revenue": None,             # NII 27.6B + NFI 11.4B = 39B
        "profit_before_tax": None,
        "profit_after_tax": 7800000,    # KES 7.8B
        "basic_eps": 24.60,
        "dividend_per_share": 6.0,
        "total_assets": 635000000,   # KES 635B
        "total_equity": None,
        "customer_deposits": None,
        "loans_and_advances": None,
        "operating_cash_flow": None,
        "capex": None,
        "ebitda": None,
        "mpesa_revenue": None,
    })
    changes.append(f"  [{r}] DTK FY2023 - NII 27.6B, PAT 7.8B, EPS 24.60, DPS 6.00, Assets 635B")

    # Save
    with open(FINANCIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Final records: {len(data)}")
    print(f"\nChanges ({len(changes)}):")
    for c in changes:
        print(c)
    print(f"\n[OK] Verified 2024 batch saved to: {FINANCIALS_FILE}")
    print(f"  File size: {FINANCIALS_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    run()
