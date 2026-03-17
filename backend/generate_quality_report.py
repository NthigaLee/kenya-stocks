#!/usr/bin/env python3
"""
Generate a static data quality report for GitHub Pages.

Reads financials_complete.json + review_state.json, runs auto-detection,
and outputs frontend/data_quality.json for the read-only admin panel.

Usage: python generate_quality_report.py
"""

import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FINANCIALS_PATH = os.path.join(REPO_ROOT, 'data', 'nse', 'financials_complete.json')
REVIEW_STATE_PATH = os.path.join(REPO_ROOT, 'data', 'nse', 'review_state.json')
OUTPUT_PATH = os.path.join(REPO_ROOT, 'frontend', 'data_quality.json')


def load_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return [] if path == FINANCIALS_PATH else {}


def make_record_key(record):
    ticker = record.get('ticker', 'UNK')
    year = record.get('year') or 'none'
    period_type = record.get('period_type') or 'unknown'
    period_end = record.get('period_end_date') or ''
    return f"{ticker}|{year}|{period_type}|{period_end}"


def detect_issues(record):
    issues = []

    critical = ['ticker', 'year', 'period_end_date', 'period_type']
    for field in critical:
        if not record.get(field):
            issues.append(f"Missing {field}")

    company = record.get('company', '')
    if company == company.upper() and len(company) > 30:
        issues.append("Company name may be a parsing artifact")
    if 'GROUP COMPANY GROUP COMPANY' in company:
        issues.append("Duplicate company name pattern")

    numeric_fields = [
        'revenue', 'profit_after_tax', 'total_assets', 'total_equity',
        'net_interest_income', 'customer_deposits', 'loans_and_advances'
    ]
    for field in numeric_fields:
        val = record.get(field)
        if val is not None:
            if val < 0 and field not in ('profit_after_tax', 'operating_cash_flow'):
                issues.append(f"Negative {field}: {val}")

    eps = record.get('basic_eps')
    if eps is not None and abs(eps) > 500:
        issues.append(f"Unusually high EPS: {eps}")

    financial_fields = ['revenue', 'profit_after_tax', 'basic_eps', 'total_assets',
                        'net_interest_income', 'customer_deposits']
    all_null = all(record.get(f) is None for f in financial_fields)
    if all_null:
        issues.append("All key financial fields are null")

    return issues


def main():
    financials = load_json(FINANCIALS_PATH)
    review_state = load_json(REVIEW_STATE_PATH)

    records = []
    for rec in financials:
        key = make_record_key(rec)
        review = review_state.get(key, {})
        issues = detect_issues(rec)

        records.append({
            'key': key,
            'ticker': rec.get('ticker', ''),
            'company': rec.get('company', ''),
            'sector': rec.get('sector', ''),
            'year': rec.get('year'),
            'period': rec.get('period', ''),
            'period_type': rec.get('period_type', ''),
            'period_end_date': rec.get('period_end_date', ''),
            'source_file': rec.get('source_file', ''),
            'url': rec.get('url', ''),
            'data': {
                'revenue': rec.get('revenue'),
                'profit_before_tax': rec.get('profit_before_tax'),
                'profit_after_tax': rec.get('profit_after_tax'),
                'basic_eps': rec.get('basic_eps'),
                'dividend_per_share': rec.get('dividend_per_share'),
                'net_interest_income': rec.get('net_interest_income'),
                'total_assets': rec.get('total_assets'),
                'total_equity': rec.get('total_equity'),
                'customer_deposits': rec.get('customer_deposits'),
                'loans_and_advances': rec.get('loans_and_advances'),
                'operating_cash_flow': rec.get('operating_cash_flow'),
                'capex': rec.get('capex'),
                'ebitda': rec.get('ebitda'),
                'mpesa_revenue': rec.get('mpesa_revenue'),
            },
            'issues': issues,
            'review_status': review.get('status', 'unreviewed'),
            'review_comment': review.get('comment', ''),
            'reviewed_by': review.get('reviewed_by', ''),
            'reviewed_at': review.get('reviewed_at', ''),
        })

    # Summary stats
    total = len(records)
    with_issues = sum(1 for r in records if r['issues'])
    by_status = {}
    for r in records:
        s = r['review_status']
        by_status[s] = by_status.get(s, 0) + 1

    tickers = sorted(set(r['ticker'] for r in records))

    output = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total': total,
        'with_issues': with_issues,
        'by_status': by_status,
        'tickers': tickers,
        'records': records,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Generated data quality report: {OUTPUT_PATH}")
    print(f"  Total records: {total}")
    print(f"  With issues: {with_issues}")
    print(f"  By status: {by_status}")


if __name__ == '__main__':
    main()
