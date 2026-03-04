"""Quick test of extract_financials_v2 on ABSA, StanChart, Safaricom PDFs only."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
from extract_financials_v2 import (
    extract_text, get_lines,
    extract_bank_metrics, extract_telco_metrics,
    detect_units, detect_consolidation,
)

DATA = Path(__file__).parent.parent / "data" / "nse"

TEST_PDFS = {
    "ABSA_Sep2020":   DATA / "2020/ABSA_Bank_Kenya_Plc_30_Sep_2020_financials.pdf",
    "ABSA_Dec2023":   DATA / "2024/ABSA_Bank_Kenya_Plc_31_Dec_2023_audited.pdf",
    "ABSA_Jun2024":   DATA / "2024/ABSA_Bank_Kenya_Plc_30_Jun_2024_financials.pdf",
    "SCBK_Jun2019":   DATA / "2019/Standard_Chartered_Bank_Kenya_Ltd_30_Jun_2019_financials.pdf",
    "SCBK_Jun2022":   DATA / "2022/Standard_Chartered_Bank_Kenya_Ltd_30_Jun_2022_financials.pdf",
    "SCBK_Dec2023":   DATA / "2024/Standard_Chartered_Bank_Kenya_Ltd_31_Dec_2023_financials.pdf",
    "SCBK_Dec2024":   DATA / "2025/Standard_Chartered_Bank_Ltd_31_Dec_2024_financials.pdf",
    "SCBK_H1_2025":   DATA / "2025/Standard_Chartered_Bank_Kenya_Ltd_00_1_51_financials.pdf",
    "SCOM_Mar2020":   DATA / "2020/Safaricom_Plc_31_Mar_2020_audited.pdf",
    "SCOM_Mar2024":   DATA / "2024/extracts_from_the_financial_books_of_Safaricom_PLC_31_Mar_2024_audited.pdf",
}

FIELDS = [
    "net_interest_income", "revenue", "profit_before_tax", "profit_after_tax",
    "basic_eps", "dividend_per_share", "total_assets", "total_equity",
    "customer_deposits", "loans_and_advances",
]

SEP = "-" * 72

for label, pdf_path in TEST_PDFS.items():
    print(f"\n{SEP}")
    print(f"  {label}  —  {pdf_path.name}")
    print(SEP)

    if not pdf_path.exists():
        print("  FILE NOT FOUND")
        continue

    try:
        text  = extract_text(pdf_path)
        lines = get_lines(text)
    except Exception as e:
        print(f"  ERROR reading PDF: {e}")
        continue

    is_telco = "SCOM" in label
    metrics  = extract_telco_metrics(lines) if is_telco else extract_bank_metrics(lines)
    units    = detect_units(text)
    consol   = detect_consolidation(text)

    print(f"  Units: {units}  |  Consolidation: {consol}")
    print()

    RATIO_FIELDS = {"basic_eps", "dividend_per_share"}
    for field in FIELDS:
        v = metrics.get(field)
        flag = "✓" if v is not None else "✗"
        if isinstance(v, float):
            if field in RATIO_FIELDS or abs(v) < 1000:
                val_str = f"{v:,.4f}".rstrip("0").rstrip(".")
            else:
                val_str = f"{v:,.0f}"
        else:
            val_str = str(v)
        print(f"  {flag}  {field:<25}  {val_str}")

print(f"\n{SEP}\nDone.\n")
