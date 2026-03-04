"""
test_extraction.py — Test extraction script on sample PDFs and validate output.

Validates against known targets from agent_task.md.
"""

from pathlib import Path
import json
import subprocess
from extract_all import extract_from_pdf, BACKEND_DIR, DATA_ROOT

DATA_ROOT = BACKEND_DIR.parent / "data" / "nse"

# Known validation targets (from agent_task.md)
VALIDATION_TARGETS = {
    "KCB Dec2024": {
        "file": "2024/KCB_Group_Plc_31_Dec_2024_audited.pdf",
        "ticker": "KCB",
        "date": "2024-12-31",
        "targets": {
            "revenue": 126653268,
            "pat": 45029313,
            "eps": 0.83,
            "dps": 0.24,
            "total_assets": 1277766539,
        }
    }
}

def test_extraction():
    """Test extraction on sample files."""
    print("\n" + "="*70)
    print("TESTING PDF EXTRACTION")
    print("="*70 + "\n")

    # Test sample files
    test_files = [
        DATA_ROOT / "2024" / "KCB_Group_Plc_31_Dec_2024_audited.pdf",
        DATA_ROOT / "2024" / "SAFARICOM_PLC_31_Dec_2024_financials.pdf",
        DATA_ROOT / "2023" / "ABSA_Bank_Kenya_Plc_30_Jun_2023_audited.pdf",
    ]

    results = []

    for pdf_path in test_files:
        if not pdf_path.exists():
            print(f"[SKIP] {pdf_path.name} - file not found")
            continue

        print(f"Testing: {pdf_path.name}...", end=" ", flush=True)

        try:
            # Try to extract from this PDF
            data = extract_from_pdf(str(pdf_path))

            if data:
                print(f"[OK] Extracted {len(data) if isinstance(data, list) else 1} record(s)")
                results.append({
                    "file": pdf_path.name,
                    "status": "success",
                    "records": len(data) if isinstance(data, list) else 1,
                    "sample": data[0] if isinstance(data, list) else data
                })
            else:
                print(f"[EMPTY] No data extracted")
                results.append({
                    "file": pdf_path.name,
                    "status": "empty",
                    "records": 0
                })

        except Exception as e:
            print(f"[ERROR] {str(e)[:50]}")
            results.append({
                "file": pdf_path.name,
                "status": "error",
                "error": str(e)[:100]
            })

    # Validate against targets
    print(f"\n{'='*70}")
    print("VALIDATION AGAINST TARGETS")
    print(f"{'='*70}\n")

    for test_name, target_info in VALIDATION_TARGETS.items():
        file_path = DATA_ROOT / target_info["file"]
        if not file_path.exists():
            print(f"[SKIP] {test_name} - file not found")
            continue

        print(f"\nValidating {test_name}...")

        try:
            data_list = extract_from_pdf(str(file_path))

            if data_list and len(data_list) > 0:
                data = data_list[0] if isinstance(data_list, list) else data_list

                print(f"  Ticker: {data.get('ticker')} (expect {target_info['ticker']})")

                all_pass = True
                for field, expected_value in target_info["targets"].items():
                    actual_value = data.get(field)

                    if actual_value is None:
                        print(f"  [{field}] MISSING (expected {expected_value})")
                        all_pass = False
                    else:
                        # Allow 5% tolerance for floating point
                        tolerance = expected_value * 0.05 if isinstance(expected_value, (int, float)) else 0
                        if abs(actual_value - expected_value) <= tolerance:
                            print(f"  [{field}] OK ({actual_value})")
                        else:
                            print(f"  [{field}] MISMATCH (actual {actual_value}, expected {expected_value})")
                            all_pass = False

                if all_pass:
                    print(f"✓ {test_name} PASSED")
                else:
                    print(f"✗ {test_name} has issues")

            else:
                print(f"✗ {test_name} - No data extracted")

        except Exception as e:
            print(f"✗ {test_name} - Error: {str(e)}")

    # Save results
    with open(DATA_ROOT / "extraction_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Results saved to: extraction_test_results.json")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    test_extraction()
