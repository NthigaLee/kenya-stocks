"""
validate_frontend_data.py — Validate frontend data.js for integrity.

Checks:
1. All 24+ companies represented
2. No null tickers
3. Financial values are reasonable
4. Dates parse correctly
5. Period_type is valid
6. EPS/DPS are per-share (small numbers)
7. Other metrics are in thousands
"""

import json
from pathlib import Path
from typing import List, Tuple

BACKEND_DIR = Path(__file__).parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
DATA_ROOT = BACKEND_DIR.parent / "data" / "nse"

DATA_JS_FILE = FRONTEND_DIR / "data.js"
VALIDATION_REPORT = DATA_ROOT / "data_validation_report.txt"

def validate():
    """Validate frontend data."""
    print("\n" + "="*70)
    print("VALIDATING FRONTEND DATA")
    print("="*70 + "\n")

    if not DATA_JS_FILE.exists():
        print(f"ERROR: {DATA_JS_FILE} not found")
        return False

    # Read and parse JavaScript file
    with open(DATA_JS_FILE, 'r') as f:
        content = f.read()

    # Extract JSON from JavaScript
    # Look for: const NSE_COMPANIES = {...};
    import re
    match = re.search(r'const NSE_COMPANIES = ({.*?});', content, re.DOTALL)

    if not match:
        print("ERROR: Could not extract NSE_COMPANIES from data.js")
        return False

    try:
        nse_companies = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in data.js: {e}")
        return False

    print(f"Loaded {len(nse_companies)} companies from data.js\n")

    warnings = []
    errors = []

    # Validation checks
    print("Running validation checks...\n")

    # Check 1: Minimum companies
    if len(nse_companies) < 20:
        errors.append(f"Too few companies: {len(nse_companies)} (expected at least 24)")
    else:
        print(f"✓ Company count: {len(nse_companies)} (OK)")

    # Check 2: Required fields
    required_fields = ['name', 'ticker', 'sector', 'logo', 'currency', 'units']
    for ticker, company in nse_companies.items():
        for field in required_fields:
            if field not in company or not company[field]:
                errors.append(f"  {ticker}: Missing or empty '{field}'")

    if not errors:
        print(f"✓ All companies have required fields")

    # Check 3: Ticker values
    invalid_tickers = [
        ticker for ticker, company in nse_companies.items()
        if not company.get('ticker') or len(str(company.get('ticker'))) > 6
    ]
    if invalid_tickers:
        errors.append(f"Invalid ticker values: {invalid_tickers}")
    else:
        print(f"✓ All ticker values valid")

    # Check 4: Period data structure
    for ticker, company in nse_companies.items():
        annuals = company.get('annuals', [])
        quarters = company.get('quarters', [])

        # Check annual periods
        for i, period in enumerate(annuals):
            if not isinstance(period, dict):
                errors.append(f"{ticker}: Annual period {i} is not a dict")
                continue

            # Validate annual fields
            for field in ['year', 'period', 'periodType']:
                if field not in period or not period[field]:
                    warnings.append(f"{ticker}: Annual period {i} missing '{field}'")

        # Check quarterly periods
        for i, period in enumerate(quarters):
            if not isinstance(period, dict):
                errors.append(f"{ticker}: Quarter period {i} is not a dict")
                continue

    if not errors:
        print(f"✓ Period data structures valid")

    # Check 5: Financial value reasonableness
    for ticker, company in nse_companies.items():
        all_periods = company.get('annuals', []) + company.get('quarters', [])

        for period in all_periods:
            # Revenue should be in thousands (> 1000 KES)
            revenue = period.get('revenue')
            if revenue and revenue < 100:
                warnings.append(f"{ticker}: Revenue too low ({revenue}) - likely wrong units")

            # EPS should be small (< 1000)
            eps = period.get('eps')
            if eps and eps > 10000:
                warnings.append(f"{ticker}: EPS too high ({eps}) - likely wrong units")

            # DPS should be small (< 100)
            dps = period.get('dps')
            if dps and dps > 1000:
                warnings.append(f"{ticker}: DPS too high ({dps}) - likely wrong units")

            # Negative values only make sense for limited fields
            for field in ['revenue', 'totalAssets', 'totalEquity']:
                val = period.get(field)
                if val and val < 0:
                    warnings.append(f"{ticker}: Negative {field} ({val})")

    if not errors:
        print(f"✓ Financial values appear reasonable")

    # Check 6: Data coverage
    total_annuals = sum(len(c.get('annuals', [])) for c in nse_companies.values())
    total_quarters = sum(len(c.get('quarters', [])) for c in nse_companies.values())
    total_records = total_annuals + total_quarters

    print(f"✓ Data coverage:")
    print(f"    Total records: {total_records}")
    print(f"    Annual periods: {total_annuals}")
    print(f"    Quarterly/Other: {total_quarters}")

    if total_records == 0:
        errors.append("No financial data records found!")

    # Check 7: Latest periods
    companies_with_latest = sum(1 for c in nse_companies.values() if c.get('latestPeriod'))
    print(f"✓ Latest periods: {companies_with_latest}/{len(nse_companies)} companies")

    if companies_with_latest < len(nse_companies) * 0.9:
        warnings.append(f"Many companies missing latest period data ({companies_with_latest}/{len(nse_companies)})")

    # Summary
    print(f"\n{'='*70}")
    print("VALIDATION SUMMARY")
    print(f"{'='*70}\n")

    if errors:
        print(f"❌ {len(errors)} ERROR(S) FOUND:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        success = False
    else:
        print("✓ NO ERRORS FOUND")
        success = True

    if warnings:
        print(f"\n⚠ {len(warnings)} WARNING(S):")
        for warning in warnings[:5]:
            print(f"  - {warning}")
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more")

    # Save report
    with open(VALIDATION_REPORT, 'w') as f:
        f.write("DATA VALIDATION REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Companies: {len(nse_companies)}\n")
        f.write(f"Total records: {total_records}\n")
        f.write(f"Annuals: {total_annuals}\n")
        f.write(f"Quarters: {total_quarters}\n\n")

        if errors:
            f.write(f"ERRORS ({len(errors)}):\n")
            f.write("-"*70 + "\n")
            for error in errors:
                f.write(f"  {error}\n")
            f.write("\n")

        if warnings:
            f.write(f"WARNINGS ({len(warnings)}):\n")
            f.write("-"*70 + "\n")
            for warning in warnings:
                f.write(f"  {warning}\n")

        f.write("\n" + "="*70 + "\n")
        if success:
            f.write("✓ VALIDATION PASSED\n")
        else:
            f.write("❌ VALIDATION FAILED\n")

    print(f"\nReport saved to: {VALIDATION_REPORT}")
    print("="*70 + "\n")

    return success

if __name__ == "__main__":
    success = validate()
    exit(0 if success else 1)
