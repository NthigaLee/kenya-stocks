
import json, sys, traceback
from pathlib import Path

# Add parent to path so we can import extract_all helpers
sys.path.insert(0, str(Path(__file__).parent))

import extract_all

pdf_path = Path(sys.argv[1])
result = extract_all.process_pdf(pdf_path, None)
if result:
    print(json.dumps(result))
