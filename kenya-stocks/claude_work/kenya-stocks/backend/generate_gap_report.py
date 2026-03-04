"""
generate_gap_report.py — Generate comprehensive missing data summary.

Analyzes gaps in financial data for all companies from Sep 2025 to Jan 2020.
Identifies which fields are missing and which time periods lack data.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

BACKEND_DIR = Path(__file__).parent
DATA_ROOT = BACKEND_DIR.parent / "data" / "nse"

FINANCIALS_FILE = DATA_ROOT / "financials_complete.json"
COVERAGE_REPORT_FILE = DATA_ROOT / "quarterly_coverage_report.json"
OUTPUT_JSON = DATA_ROOT / "missing_data_summary.json"
OUTPUT_TXT = DATA_ROOT / "missing_data_summary.txt"

# Target date range
START_DATE = "2020-01-01"
END_DATE = "2025-09-30"

# All financial fields
FINANCIAL_FIELDS = [
    'revenue', 'profit_before_tax', 'profit_after_tax', 'net_interest_income',
    'basic_eps', 'dividend_per_share', 'total_assets', 'total_equity',
    'customer_deposits', 'loans_and_advances', 'operating_cash_flow',
    'capex', 'ebitda', 'mpesa_revenue'
]

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

def is_in_range(date_str: str, start: str, end: str) -> bool:
    """Check if date is in range."""
    d = parse_date(date_str)
    s = parse_date(start)
    e = parse_date(end)
    return d and s and e and s <= d <= e

def generate_gap_report():
    """Generate missing data summary."""
    print("\n" + "="*70)
    print("GENERATING MISSING DATA SUMMARY")
    print("="*70 + "\n")

    # Load financials
    if not FINANCIALS_FILE.exists():
        print(f"ERROR: {FINANCIALS_FILE} not found")
        return

    with open(FINANCIALS_FILE, 'r') as f:
        financials = json.load(f)

    print(f"Loaded {len(financials)} financial records\n")

    # Group by ticker
    by_ticker = defaultdict(list)
    for record in financials:
        ticker = record.get('ticker')
        if ticker:
            by_ticker[ticker].append(record)

    # Load coverage report if available
    coverage_data = {}
    if COVERAGE_REPORT_FILE.exists():
        try:
            with open(COVERAGE_REPORT_FILE, 'r') as f:
                coverage_data = json.load(f).get('companies', {})
        except:
            pass

    # Analyze gaps
    company_gaps = {}
    total_entries_in_range = 0
    field_coverage = defaultdict(lambda: {'total': 0, 'filled': 0, 'companies_with': set(), 'companies_missing': set()})

    for ticker in sorted(by_ticker.keys()):
        records = by_ticker[ticker]

        # Filter to range
        entries_in_range = [r for r in records if is_in_range(r.get('period_end_date', ''), START_DATE, END_DATE)]

        if not entries_in_range:
            continue

        total_entries_in_range += len(entries_in_range)

        # Analyze field coverage for this company
        field_stats = {}
        for field in FINANCIAL_FIELDS:
            filled = sum(1 for r in entries_in_range if r.get(field))
            missing = len(entries_in_range) - filled

            field_stats[field] = {
                'filled': filled,
                'missing': missing,
                'coverage': (filled / len(entries_in_range) * 100) if entries_in_range else 0
            }

            # Track overall coverage
            field_coverage[field]['total'] += len(entries_in_range)
            field_coverage[field]['filled'] += filled
            if filled > 0:
                field_coverage[field]['companies_with'].add(ticker)
            else:
                field_coverage[field]['companies_missing'].add(ticker)

        # Get company name
        company_name = records[0].get('company', ticker) if records else ticker

        # Quarterly completeness
        quarterly_stats = {}
        if ticker in coverage_data:
            quarterly_data = coverage_data[ticker].get('by_year', {})
            for year, period_counts in quarterly_data.items():
                total_periods = sum(period_counts.values())
                quarterly_stats[year] = total_periods

        # Identify priority gaps
        priority_gaps = []
        for field, stats in field_stats.items():
            if stats['coverage'] < 50:
                priority_gaps.append(f"{field} (only {stats['coverage']:.0f}% filled)")

        company_gaps[ticker] = {
            'company_name': company_name,
            'ticker': ticker,
            'total_periods_in_range': len(entries_in_range),
            'total_periods_overall': len(records),
            'field_coverage': field_stats,
            'quarterly_completeness': quarterly_stats,
            'priority_gaps': priority_gaps[:3],  # Top 3 gaps
        }

        print(f"{ticker:6}: {len(entries_in_range)} periods, {len(priority_gaps)} priority gaps")

    print(f"\nTotal entries in range: {total_entries_in_range}")
    print(f"Companies with data: {len(company_gaps)}\n")

    # Field summary
    print("Field Coverage Summary:")
    print("-"*70)
    for field in FINANCIAL_FIELDS:
        coverage = field_coverage[field]
        if coverage['total'] > 0:
            pct = coverage['filled'] / coverage['total'] * 100
            companies = len(coverage['companies_with'])
            missing_companies = len(coverage['companies_missing'])
            print(f"  {field:25} {pct:5.1f}% ({coverage['filled']:4}/{coverage['total']:4}) | {companies:2} companies")

    # Build output
    output = {
        'report_date': datetime.now().isoformat(),
        'date_range': {
            'start': START_DATE,
            'end': END_DATE
        },
        'summary': {
            'total_companies': len(by_ticker),
            'companies_with_data_in_range': len(company_gaps),
            'total_periods_in_range': total_entries_in_range,
            'avg_periods_per_company': total_entries_in_range / len(company_gaps) if company_gaps else 0
        },
        'companies': company_gaps,
        'field_summary': {
            field: {
                'overall_coverage_pct': coverage['filled'] / coverage['total'] * 100 if coverage['total'] > 0 else 0,
                'companies_with_data': len(coverage['companies_with']),
                'companies_missing_data': len(coverage['companies_missing']),
            }
            for field, coverage in field_coverage.items()
        }
    }

    # Save JSON report
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nDetailed JSON report: {OUTPUT_JSON}")

    # Create human-readable text report
    with open(OUTPUT_TXT, 'w') as f:
        f.write("MISSING FINANCIAL DATA SUMMARY\n")
        f.write("="*70 + "\n")
        f.write(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Period Analyzed: {START_DATE} to {END_DATE}\n")
        f.write(f"Total Companies: {len(by_ticker)}\n")
        f.write(f"Companies with data in period: {len(company_gaps)}\n")
        f.write(f"Total financial records in period: {total_entries_in_range}\n\n")

        f.write("PRIORITY GAPS BY COMPANY\n")
        f.write("-"*70 + "\n\n")

        for ticker in sorted(company_gaps.keys()):
            company = company_gaps[ticker]
            if company['priority_gaps']:
                f.write(f"{ticker} ({company['company_name']})\n")
                f.write(f"  Records in range: {company['total_periods_in_range']}\n")
                f.write(f"  Priority gaps:\n")
                for gap in company['priority_gaps']:
                    f.write(f"    - {gap}\n")
                f.write("\n")

        f.write("\n" + "="*70 + "\n")
        f.write("FIELD COVERAGE SUMMARY\n")
        f.write("-"*70 + "\n\n")

        for field in FINANCIAL_FIELDS:
            coverage = output['field_summary'][field]
            pct = coverage['overall_coverage_pct']
            f.write(f"{field}:\n")
            f.write(f"  Coverage: {pct:.1f}%\n")
            f.write(f"  Companies with data: {coverage['companies_with_data']}\n")
            f.write(f"  Companies missing data: {coverage['companies_missing_data']}\n\n")

        f.write("="*70 + "\n")
        f.write("HIGH-PRIORITY TARGETS FOR SUPPLEMENTAL DATA\n")
        f.write("-"*70 + "\n\n")
        f.write("Focus on these companies first for data gap filling:\n")

        # Find top companies with most gaps
        top_gaps = sorted(
            company_gaps.items(),
            key=lambda x: len(x[1]['priority_gaps']),
            reverse=True
        )[:10]

        for ticker, company in top_gaps:
            f.write(f"  {ticker}: {len(company['priority_gaps'])} major gaps\n")

    print(f"Human-readable report: {OUTPUT_TXT}")
    print("="*70 + "\n")

if __name__ == "__main__":
    generate_gap_report()
