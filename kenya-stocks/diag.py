"""Diagnose financials.json - show per-company coverage."""
import json
from pathlib import Path
from collections import defaultdict

DATA = Path("data/nse/financials.json")
records = json.loads(DATA.read_text(encoding="utf-8"))

by_ticker = defaultdict(list)
for r in records:
    t = r.get("ticker")
    if t:
        by_ticker[t].append(r)

print(f"Total records: {len(records)}")
print(f"Companies: {sorted(by_ticker.keys())}\n")

for ticker in sorted(by_ticker.keys()):
    recs = by_ticker[ticker]
    annuals = [(r.get("year"), r.get("period_end_date"), r.get("period_type"), r.get("group_or_company","?")) for r in recs if r.get("period_type") == "annual"]
    interim = [(r.get("year"), r.get("period_end_date"), r.get("period_type"), r.get("group_or_company","?")) for r in recs if r.get("period_type") in ("half_year","quarter")]
    print(f"{ticker} ({len(recs)} records):")
    print(f"  Annuals: {sorted(annuals, key=lambda x: x[1] or '')}")
    if interim:
        print(f"  Interim: {sorted(interim, key=lambda x: x[1] or '')}")
