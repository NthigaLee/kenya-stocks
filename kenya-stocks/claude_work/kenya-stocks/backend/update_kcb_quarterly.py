"""
KCB Group — Fill quarterly gaps with verified IR data.
Sources: KCB press releases, Cytonn earnings notes, The Star
All monetary values in KES thousands.
"""
import json

DB = "data/nse/financials_complete.json"

with open(DB) as f:
    data = json.load(f)

def update_or_add(data, ticker, period_end_date, period_type, updates):
    """Update existing record or add new one."""
    for rec in data:
        if rec.get('ticker') == ticker and rec.get('period_end_date') == period_end_date:
            for k, v in updates.items():
                if v is not None:
                    rec[k] = v
            rec['source_file'] = f"VERIFIED_IR_{ticker}_{period_end_date}.json"
            return "UPDATED"
    # Add new record
    year = int(period_end_date[:4])
    month = period_end_date[5:7]
    if period_type == 'annual':
        period_label = f"FY{year}"
    elif period_type == 'half_year':
        period_label = f"H1 {year}"
    elif month == '03':
        period_label = f"Q1 {year}"
    elif month == '09':
        period_label = f"Q3 {year}"
    else:
        period_label = f"{period_end_date}"

    new_rec = {
        'company': 'KCB Group Plc',
        'ticker': ticker,
        'sector': 'Banking',
        'period': period_label,
        'period_end_date': period_end_date,
        'period_type': period_type,
        'year': year,
        'source_file': f"VERIFIED_IR_{ticker}_{period_end_date}.json",
    }
    new_rec.update({k: v for k, v in updates.items() if v is not None})
    data.append(new_rec)
    return "ADDED"


records_to_process = [
    # ── KCB Q1 2022 — update equity (rest already fixed) ──
    # Source: ke.kcbgroup.com press release
    ("KCB", "2022-03-31", "quarter", {
        "total_equity": 181_800_000,  # 181.8B
    }),

    # ── KCB H1 2021 — update with Cytonn verified data ──
    # Source: cytonn.com/topicals/kcb-group-plc-h12021-earnings-note
    ("KCB", "2021-06-30", "half_year", {
        "profit_after_tax": 15_300_000,   # 15.3B
        "revenue": 51_200_000,            # 51.2B (total operating income)
        "net_interest_income": 36_400_000, # 36.4B
        "profit_before_tax": 21_900_000,  # 21.9B
        "total_assets": 1_022_200_000,    # 1.022T
        "customer_deposits": 786_000_000, # 786B
        "loans_and_advances": 607_000_000,# 607B
        "total_equity": 152_900_000,      # 152.9B
        "basic_eps": 4.76,
    }),

    # ── KCB Q3 2021 (NEW — 9 months to Sep 2021) ──
    # Source: kenyanwallstreet.com "KCB Q3 2021 Net Earnings Rise 131%"
    ("KCB", "2021-09-30", "quarter", {
        "profit_after_tax": 25_200_000,    # 25.2B
        "total_assets": 1_122_000_000,     # 1.122T
        "loans_and_advances": 718_000_000, # 718B
        "total_equity": 163_000_000,       # 163B
        "dividend_per_share": 1.00,        # Interim DPS
        "basic_eps": 7.85,                 # 25.2B / 3.21B shares
    }),

    # ── KCB Q1 2023 (NEW — 3 months to Mar 2023) ──
    # Source: ke.kcbgroup.com "KCB Group Records KShs. 9.75 Billion Q1 Net Profit"
    ("KCB", "2023-03-31", "quarter", {
        "profit_after_tax": 9_750_000,     # 9.75B
        "revenue": 36_900_000,             # 36.9B
        "total_assets": 1_630_000_000,     # 1.63T
        "customer_deposits": 1_200_000_000,# 1.20T
        "loans_and_advances": 928_800_000, # 928.8B
        "total_equity": 214_800_000,       # 214.8B
        "basic_eps": 3.04,                 # 9.75B / 3.21B shares
    }),

    # ── KCB H1 2023 — update with press release data ──
    # Source: ke.kcbgroup.com "KCB Group Total Assets Rise by 54% to KShs. 1.86 Trillion"
    # Existing PDF data had PAT 13.9B (wrong) — should be 16.1B
    ("KCB", "2023-06-30", "half_year", {
        "profit_after_tax": 16_100_000,    # 16.1B
        "revenue": 73_100_000,             # 73.1B
        "total_assets": 1_860_000_000,     # 1.86T
        "customer_deposits": 1_470_000_000,# 1.47T
        "loans_and_advances": 964_800_000, # 964.8B
        "total_equity": 218_000_000,       # 218B
    }),

    # ── KCB Q1 2024 — update with press release data ──
    # Source: the-star.co.ke "KCB regains top bank badge with 69% net profit jump"
    # Existing PDF data had PAT 11.17B (wrong) — should be 16.5B
    ("KCB", "2024-03-31", "quarter", {
        "profit_after_tax": 16_500_000,    # 16.5B
        "revenue": 48_500_000,             # 48.5B
        "total_assets": 2_000_000_000,     # 2.0T
        "customer_deposits": 1_500_000_000,# 1.5T
        "loans_and_advances": 1_130_000_000,# 1.13T
        "total_equity": 238_600_000,       # 238.6B
        "basic_eps": 5.14,                 # 16.5B / 3.21B shares
    }),

    # ── KCB Q3 2024 — update existing empty/wrong record ──
    # Source: ke.kcbgroup.com "KCB Group Plc Posts 49% Rise in Profit After Tax"
    ("KCB", "2024-09-30", "quarter", {
        "profit_after_tax": 45_800_000,    # 45.8B
        "revenue": 142_900_000,            # 142.9B
        "total_assets": 2_000_000_000,     # 2.0T
        "customer_deposits": 1_500_000_000,# 1.5T
        "loans_and_advances": 1_100_000_000,# 1.1T
        "total_equity": 249_000_000,       # 249B
        "basic_eps": 14.27,                # 45.8B / 3.21B shares
    }),

    # ── KCB Q1 2025 — update with press release data ──
    # Source: standardmedia.co.ke "Kenya's top lender KCB posts Q1 profit of Sh16.53b"
    ("KCB", "2025-03-31", "quarter", {
        "profit_after_tax": 16_530_000,    # 16.53B
        "revenue": 49_400_000,             # 49.4B
        "total_assets": 2_030_000_000,     # 2.03T
        "basic_eps": 5.15,                 # 16.53B / 3.21B shares
    }),
]

print("=" * 60)
print("UPDATING KCB QUARTERLY DATA")
print("=" * 60)

added = 0
updated = 0

for ticker, date, ptype, updates in records_to_process:
    result = update_or_add(data, ticker, date, ptype, updates)
    print(f"  {ticker} {date}: {result}")
    if result == "ADDED":
        added += 1
    else:
        updated += 1

with open(DB, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\nDone: {updated} updated, {added} added")
total = len(data)
print(f"Total records: {total}")
