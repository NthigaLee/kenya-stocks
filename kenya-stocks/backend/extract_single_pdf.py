#!/usr/bin/env python3
"""Extract financial data from a single PDF file."""

import sys
from pathlib import Path
from typing import List, Optional

# Add backend directory to path to import modules
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))

from extract_financials_from_pdfs import (
    pdf_lines, 
    company_type,
    extract_bank_metrics,
    extract_telco_metrics,
    extract_generic_metrics,
    detect_currency,
    detect_units,
    detect_consolidation,
    FinancialSnapshot,
    asdict
)


def process_single_pdf(pdf_path: str, company_name: str = "KCB"):
    """Process a single PDF file and extract financial data."""
    
    # Convert to Path object
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} does not exist")
        return
    
    print(f"Processing {pdf_path.name}")
    
    try:
        # Extract text from PDF
        lines = pdf_lines(pdf_path)
        print(f"Extracted {len(lines)} lines from PDF")
    except Exception as exc:
        print(f"Error reading PDF: {exc}")
        return
    
    try:
        # Determine company type
        ctype = company_type(company_name)
        print(f"Company type: {ctype}")
        
        # Extract metrics based on company type
        if ctype == "bank":
            metrics = extract_bank_metrics(lines)
        elif ctype == "telco":
            metrics = extract_telco_metrics(lines)
        else:
            metrics = extract_generic_metrics(lines)
            
        print("Extracted metrics:")
        for key, value in metrics.items():
            if value is not None:
                print(f"  {key}: {value}")
                
        # Detect currency and units
        currency = detect_currency(lines)
        units = detect_units(lines)
        consolidation = detect_consolidation(lines)
        
        print(f"Currency: {currency}")
        print(f"Units: {units}")
        print(f"Consolidation: {consolidation}")
        
        # Create a minimal snapshot (we don't have all the metadata)
        snapshot = FinancialSnapshot(
            url=f"file://{pdf_path.absolute()}",
            year=2025,  # Default year
            title=pdf_path.stem,
            company=company_name,
            period="Q3",  # Default period
            currency=currency,
            units=units,
            consolidation=consolidation,
            **metrics,
        )
        
        # Print the snapshot as JSON
        import json
        print("\nFinancial Snapshot:")
        print(json.dumps(asdict(snapshot), indent=2, ensure_ascii=False))
        
    except Exception as exc:
        print(f"Error extracting metrics: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_single_pdf.py <pdf_file_path> [company_name]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    company_name = sys.argv[2] if len(sys.argv) > 2 else "KCB"
    
    process_single_pdf(pdf_path, company_name)