"""
extract_with_timeout.py — Runs extract_all.py per-PDF with subprocess timeouts.
Processes PDFs one by one, kills any that take > 90 seconds.
"""
from __future__ import annotations
import json, sys, subprocess, os
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
DATA_ROOT   = BACKEND_DIR.parent / "data" / "nse"
OUTPUT_FILE = DATA_ROOT / "financials.json"
TIMEOUT_SEC = 90

SINGLE_PDF_SCRIPT = BACKEND_DIR / "_extract_one_pdf.py"

# Write the single-PDF extraction script
SINGLE_PDF_SCRIPT.write_text('''
import json, sys, traceback
from pathlib import Path

# Add parent to path so we can import extract_all helpers
sys.path.insert(0, str(Path(__file__).parent))

import extract_all

pdf_path = Path(sys.argv[1])
result = extract_all.process_pdf(pdf_path, None)
if result:
    print(json.dumps(result))
''', encoding='utf-8')

def load_existing():
    if OUTPUT_FILE.exists():
        with OUTPUT_FILE.open(encoding='utf-8') as f:
            return json.load(f)
    return []

def save(records):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def main():
    raw_args = sys.argv[1:]
    company_filters = [a.lower() for a in raw_args if not a.startswith('--')]
    
    # Find PDFs
    ticker_name_map = {
        'eqty': 'EQTY', 'equity': 'EQTY',
        'coop': 'COOP', 'co_operative': 'COOP', 'cooperative': 'COOP',
        'absa': 'ABSA',
        'scbk': 'SCBK', 'standard_chartered': 'SCBK',
        'ncba': 'NCBA',
        'dtb': 'DTK', 'diamond_trust': 'DTK',
    }
    
    pdfs = []
    for year_dir in sorted(DATA_ROOT.iterdir()):
        if year_dir.is_dir() and year_dir.name.isdigit() and int(year_dir.name) >= 2020:
            for f in sorted(year_dir.glob('*.pdf')):
                fname = f.name.lower()
                if company_filters:
                    if any(cf in fname for cf in company_filters):
                        pdfs.append(f)
                else:
                    pdfs.append(f)
    
    print(f"Found {len(pdfs)} PDFs to process")
    
    # Load existing, determine which tickers we're replacing
    existing = load_existing()
    target_tickers = set()
    for cf in company_filters:
        for key, ticker in ticker_name_map.items():
            if cf in key or key in cf:
                target_tickers.add(ticker)
    # Also remove by filename match
    existing_filtered = [r for r in existing if r.get('ticker') not in target_tickers]
    print(f"Keeping {len(existing_filtered)} existing records, replacing tickers: {target_tickers}")
    
    new_results = []
    skipped = []
    errors = []
    
    for i, pdf_path in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] {pdf_path.name[:70]}", end=' ', flush=True)
        try:
            proc = subprocess.run(
                [sys.executable, str(SINGLE_PDF_SCRIPT), str(pdf_path)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SEC,
                cwd=str(BACKEND_DIR)
            )
            if proc.returncode == 0 and proc.stdout.strip():
                try:
                    record = json.loads(proc.stdout.strip())
                    new_results.append(record)
                    print(f"OK {record.get('ticker','?')} {record.get('period','')}")
                except json.JSONDecodeError:
                    print(f"FAIL JSON parse error")
                    errors.append(pdf_path.name)
            else:
                stderr = proc.stderr.strip()[:100] if proc.stderr else ''
                print(f"FAIL no result {stderr}")
                errors.append(pdf_path.name)
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT - skipped")
            skipped.append(pdf_path.name)
        except Exception as e:
            print(f"ERR Error: {e}")
            errors.append(pdf_path.name)
    
    # Merge and save
    combined = existing_filtered + new_results
    save(combined)
    
    print(f"\n✓ Extracted: {len(new_results)}")
    print(f"⏱ Timed out: {len(skipped)}")
    print(f"✗ Errors: {len(errors)}")
    print(f"Total records: {len(combined)}")
    
    if skipped:
        print("\nTimed-out PDFs:")
        for s in skipped:
            print(f"  {s}")
    
    # Summary by ticker
    from collections import Counter
    tickers = Counter(r.get('ticker') or '?' for r in combined)
    print("\nBy ticker:")
    for t, c in sorted(tickers.items()):
        print(f"  {t}: {c}")

if __name__ == '__main__':
    main()
