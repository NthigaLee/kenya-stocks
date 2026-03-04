"""Quick smoke-test for the rewritten extractor.

Runs only on ABSA, StanChart, and Safaricom PDFs.
Prints results so you can eyeball them before doing the full run.
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))

from extract_financials_from_pdfs import (
    company_type,
    detect_consolidation,
    detect_units,
    extract_bank_metrics,
    extract_telco_metrics,
    pdf_lines,
)

DATA_DIR = Path(__file__).parent.parent / "data" / "nse"

TARGETS = {
    "ABSA":      ["ABSA"],
    "StanChart": ["Standard_Chartered"],
    "Safaricom": ["Safaricom"],
}

def fmt(v):
    if v is None:
        return "[null]"
    if isinstance(v, float) and v == int(v):
        return f"{int(v):,}"
    return f"{v:,.3f}" if abs(v) < 100 else f"{v:,.0f}"

def test_company(label: str, keywords: list[str]) -> None:
    print(f"\n{'='*72}")
    print(f"  {label}")
    print(f"{'='*72}")

    pdfs = sorted(p for p in DATA_DIR.rglob("*.pdf")
                  if any(k in p.name for k in keywords))

    for pdf in pdfs:
        print(f"\n  PDF: {pdf.parent.name}/{pdf.name}")
        try:
            lines = pdf_lines(pdf)
        except Exception as e:
            print(f"    ERROR: {e}")
            continue

        ctype = company_type(label)
        consolidation = detect_consolidation(lines)
        units = detect_units(lines)
        metrics = extract_bank_metrics(lines) if ctype == "bank" else extract_telco_metrics(lines)

        print(f"  Consolidation: {consolidation} | Units: {units}")
        key_fields = [
            "revenue", "net_interest_income", "profit_before_tax",
            "profit_after_tax", "basic_eps", "dividend_per_share",
            "total_assets", "total_equity", "customer_deposits",
            "loans_and_advances",
        ]
        for k in key_fields:
            v = metrics.get(k)
            print(f"    {k:<30} {fmt(v)}")

for label, kws in TARGETS.items():
    test_company(label, kws)

print("\n\nDone.")
