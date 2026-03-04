"""
Diagnostic script — print relevant lines from problematic PDFs.
"""
import sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
import pdfplumber

DATA_ROOT = Path(__file__).parent.parent / "data" / "nse"

TARGETS = {
    "ABSA_Sep2020": DATA_ROOT / "2020/ABSA_Bank_Kenya_Plc_30_Sep_2020_financials.pdf",
    "ABSA_Jun2024": DATA_ROOT / "2024/ABSA_Bank_Kenya_Plc_30_Jun_2024_financials.pdf",
    "ABSA_Dec2023": DATA_ROOT / "2024/ABSA_Bank_Kenya_Plc_31_Dec_2023_audited.pdf",
    "SCOM_Mar2020": DATA_ROOT / "2020/Safaricom_Plc_31_Mar_2020_audited.pdf",
    "SCBK_H1_2025": DATA_ROOT / "2025/Standard_Chartered_Bank_Kenya_Ltd_00_1_51_financials.pdf",
}

KEYWORDS = {
    "ABSA_Sep2020": ["total assets", "assets", "21"],
    "ABSA_Jun2024": ["total assets", "assets", "21"],
    "ABSA_Dec2023": ["profit after tax", "profit for", "deferred tax", "tax"],
    "SCOM_Mar2020": ["billion", "million", "thousand", "unit", "kes", "ksh",
                     "total assets", "equity", "shareholders"],
    "SCBK_H1_2025": ["net interest income", "total operating", "profit", "total assets",
                     "earnings per share", "dividend"],
}

def extract_text(path):
    chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:10]:
            t = page.extract_text() or ""
            if t:
                chunks.append(t)
    return "\n".join(chunks)

def normalise(line):
    line = line.replace("\u00a0", " ")
    line = " ".join(line.split())
    return line

for label, path in TARGETS.items():
    if not path.exists():
        print(f"\n{'='*60}")
        print(f"  {label}: FILE NOT FOUND — {path}")
        continue

    print(f"\n{'='*60}")
    print(f"  {label}: {path.name}")
    print(f"{'='*60}")

    text = extract_text(path)
    lines = [normalise(l) for l in text.splitlines() if l.strip()]
    kws = [k.lower() for k in KEYWORDS.get(label, [])]

    for line in lines:
        low = line.lower()
        if any(kw in low for kw in kws):
            print(f"  >>> {line}")
