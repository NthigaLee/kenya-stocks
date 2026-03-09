"""
Extract financials from all downloaded JSE test PDFs.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from backend.extractors.ifrs_extractor import IFRSExtractor

extractor = IFRSExtractor(exchange="JSE")
OUTPUT_BASE = Path("data/jse")
results = []
failures = []

tickers = ["BHG", "ANH", "BTI", "NTC", "PRX"]

for ticker in tickers:
    ticker_dir = OUTPUT_BASE / ticker
    if not ticker_dir.exists():
        print(f"No dir for {ticker}")
        continue
    pdfs = list(ticker_dir.glob("*.pdf"))
    print(f"\n{ticker}: {len(pdfs)} PDFs")
    for pdf in pdfs:
        print(f"  Extracting {pdf.name}...")
        try:
            record = extractor.extract_pdf(str(pdf), ticker)
            if record:
                record["source_file"] = pdf.name
                results.append(record)
                # Show key metrics
                rev = record.get("revenue")
                pat = record.get("profit_after_tax")
                assets = record.get("total_assets")
                print(f"    revenue={rev}, PAT={pat}, assets={assets}")
            else:
                failures.append({"ticker": ticker, "file": pdf.name, "reason": "extract returned None"})
        except Exception as e:
            print(f"    ERROR: {e}")
            failures.append({"ticker": ticker, "file": pdf.name, "reason": str(e)})

# Save
out_path = OUTPUT_BASE / "financials_test.json"
output = {"records": results, "failures": failures}
with open(out_path, "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"\n=== EXTRACTION SUMMARY ===")
print(f"  Total records: {len(results)}")
print(f"  Failures: {len(failures)}")
print(f"  Saved to: {out_path}")
