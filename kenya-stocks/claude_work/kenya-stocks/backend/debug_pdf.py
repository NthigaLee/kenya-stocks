"""
debug_pdf.py — Show raw extracted lines from a PDF around key financial terms.
Usage: python debug_pdf.py <path_to_pdf>
"""
import sys
from pathlib import Path

import pdfplumber

TARGET_KEYWORDS = [
    "revenue", "net interest income", "profit", "earnings per share",
    "dividend", "total assets", "total equity", "ebitda", "million", "thousand", "unit"
]

def extract_lines(path):
    chunks = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages[:5]):  # first 5 pages
            t = page.extract_text() or ""
            if t:
                chunks.append(f"\n=== PAGE {i+1} ===\n" + t)
    return "\n".join(chunks)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_pdf.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    print(f"Debugging: {pdf_path.name}\n")
    
    text = extract_lines(pdf_path)
    lines = text.splitlines()
    
    # Show unit/header lines
    print("=== UNIT / HEADER DETECTION ===")
    for line in lines:
        ll = line.lower()
        if any(u in ll for u in ["million", "thousand", "billion", "unit", "kes", "ksh", "in thousands", "in millions"]):
            print(f"  [{lines.index(line):3d}] {line.strip()}")
    
    print("\n=== KEY FINANCIAL LINES ===")
    for i, line in enumerate(lines):
        ll = line.lower()
        if any(k in ll for k in TARGET_KEYWORDS):
            print(f"  [{i:3d}] {line.strip()}")
