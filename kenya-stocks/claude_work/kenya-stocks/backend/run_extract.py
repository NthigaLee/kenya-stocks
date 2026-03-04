"""Run full extraction with error capture — writes log directly to file."""
import sys
import traceback
import io
from pathlib import Path

log_path = Path(__file__).parent.parent / "extract_log.txt"

with open(log_path, "w", encoding="utf-8") as log_file:
    sys.stdout = log_file
    sys.stderr = log_file
    try:
        import extract_financials_from_pdfs as e
        e.main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
