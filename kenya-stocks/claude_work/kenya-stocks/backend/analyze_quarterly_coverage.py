"""
analyze_quarterly_coverage.py — Analyze quarterly data coverage for all companies.

Date range: Sep 2025 → Jan 2020
Identifies missing quarters and creates comprehensive coverage report.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

BACKEND_DIR = Path(__file__).parent
DATA_ROOT = BACKEND_DIR.parent / "data" / "nse"
FINANCIALS_FILE = DATA_ROOT / "financials_complete.json"

# Target date range
START_DATE = "2020-01-01"
END_DATE = "2025-09-30"

def parse_date(date_str: Optional[str]) -> Optional[Tuple[int, int, int]]:
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

def is_date_in_range(date_str: Optional[str], start: str, end: str) -> bool:
    """Check if date is between start and end."""
    date_parts = parse_date(date_str)
    start_parts = parse_date(start)
    end_parts = parse_date(end)

    if not (date_parts and start_parts and end_parts):
        return False

    return start_parts <= date_parts <= end_parts

def determine_period_type(date_str: str) -> str:
    """Determine if period is annual, H1, Q1, Q3, or other."""
    parts = parse_date(date_str)
    if not parts:
        return "unknown"

    year, month, day = parts

    if month == 12:
        return "annual"
    elif month == 6:
        return "h1"
    elif month == 3:
        return "q1"
    elif month == 9:
        return "q3"
    else:
        return "other"

def analyze_coverage():
    """Analyze quarterly coverage for all companies."""
    print("\n" + "="*70)
    print("QUARTERLY COVERAGE ANALYSIS")
    print(f"Period: {START_DATE} to {END_DATE}")
    print("="*70 + "\n")

    # Load financials data
    if not FINANCIALS_FILE.exists():
        print(f"ERROR: {FINANCIALS_FILE} not found")
        print("Run extract_all.py first to generate financials_complete.json")
        return

    with open(FINANCIALS_FILE, 'r') as f:
        financials = json.load(f)

    print(f"Loaded {len(financials)} financial records")

    # Group by company/ticker
    companies = defaultdict(list)
    for record in financials:
        ticker = record.get('ticker')
        if ticker:
            companies[ticker].append(record)

    print(f"Found {len(companies)} unique companies\n")

    # Analyze each company
    report = {}
    total_entries_in_range = 0
    companies_with_data = 0

    for ticker in sorted(companies.keys()):
        records = companies[ticker]

        # Filter to date range
        entries_in_range = [
            r for r in records
            if is_date_in_range(r.get('period_end_date'), START_DATE, END_DATE)
        ]

        if not entries_in_range:
            continue

        companies_with_data += 1
        total_entries_in_range += len(entries_in_range)

        # Analyze by year and period type
        by_year = defaultdict(lambda: {
            'annual': 0, 'h1': 0, 'q1': 0, 'q3': 0, 'other': 0
        })

        for record in entries_in_range:
            date_str = record.get('period_end_date')
            period_type = record.get('period_type', 'unknown')

            if date_str:
                year = parse_date(date_str)[0]
                # Map to period type if not set
                if not period_type or period_type == 'unknown':
                    period_type = determine_period_type(date_str)

                # Normalize period type names
                if period_type == 'half_year':
                    period_type = 'h1'
                elif period_type in ['quarter', 'quarterly']:
                    if parse_date(date_str)[1] == 3:
                        period_type = 'q1'
                    elif parse_date(date_str)[1] == 9:
                        period_type = 'q3'
                    else:
                        period_type = 'other'

                by_year[year][period_type] += 1

        # Identify missing quarters
        missing_quarters = []
        for year in sorted(by_year.keys()):
            year_data = by_year[year]

            # Expected: annual + h1 = 2 reports minimum
            total_reports = sum(year_data.values())

            if total_reports == 0:
                missing_quarters.append(f"{year}-all")
            elif total_reports == 1:
                missing_quarters.append(f"{year}-partial")

            # Check specific quarters
            if year_data['annual'] == 0:
                missing_quarters.append(f"{year}-annual")
            if year_data['h1'] == 0:
                missing_quarters.append(f"{year}-h1")

        # Get company name
        company_name = None
        if records:
            company_name = records[0].get('company')

        report[ticker] = {
            'company_name': company_name,
            'ticker': ticker,
            'total_entries': len(records),
            'entries_in_range': len(entries_in_range),
            'by_year': dict(by_year),
            'missing_quarters': missing_quarters,
            'coverage_percentage': 100
        }

        print(f"{ticker:6} ({company_name}): {len(entries_in_range)} records in range")

    # Overall statistics
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Companies with data in range: {companies_with_data}")
    print(f"Total entries in range: {total_entries_in_range}")
    print(f"Average entries per company: {total_entries_in_range / companies_with_data if companies_with_data > 0 else 0:.1f}")

    # Companies with incomplete quarterly coverage
    companies_missing_quarters = sum(1 for r in report.values() if r['missing_quarters'])
    print(f"Companies with missing quarters: {companies_missing_quarters}")

    # Identify systemically missing quarters
    all_missing = defaultdict(int)
    for ticker, data in report.items():
        for missing in data['missing_quarters']:
            if '-' in missing and missing.split('-')[0].isdigit():
                quarter_type = missing.split('-')[1]
                all_missing[quarter_type] += 1

    print(f"\nSystemically missing quarters:")
    for quarter_type, count in sorted(all_missing.items()):
        print(f"  {quarter_type}: {count} companies missing it")

    # Save detailed report
    report_file = DATA_ROOT / "quarterly_coverage_report.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'date_range': {
                'start': START_DATE,
                'end': END_DATE
            },
            'summary': {
                'total_companies': len(companies),
                'companies_with_data': companies_with_data,
                'total_entries_in_range': total_entries_in_range,
                'companies_missing_quarters': companies_missing_quarters
            },
            'companies': report
        }, f, indent=2)

    print(f"\nDetailed report saved to: quarterly_coverage_report.json")

    # Create human-readable summary
    summary_file = DATA_ROOT / "quarterly_gaps_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("QUARTERLY DATA COVERAGE SUMMARY\n")
        f.write("="*70 + "\n")
        f.write(f"Period: {START_DATE} to {END_DATE}\n")
        f.write(f"Companies analyzed: {companies_with_data}\n")
        f.write(f"Total records: {total_entries_in_range}\n\n")

        f.write("COMPANIES WITH MISSING QUARTERS:\n")
        f.write("-"*70 + "\n")

        for ticker in sorted(report.keys()):
            data = report[ticker]
            if data['missing_quarters']:
                f.write(f"\n{ticker} ({data['company_name']})\n")
                f.write(f"  Total in range: {data['entries_in_range']}\n")
                f.write(f"  Missing: {', '.join(data['missing_quarters'])}\n")

        f.write("\n" + "="*70 + "\n")
        f.write("SYSTEMICALLY MISSING QUARTERS:\n")
        f.write("-"*70 + "\n")
        for quarter_type, count in sorted(all_missing.items(), key=lambda x: -x[1]):
            f.write(f"{quarter_type}: {count} companies\n")

    print(f"Summary saved to: quarterly_gaps_summary.txt")
    print("="*70 + "\n")

if __name__ == "__main__":
    analyze_coverage()
