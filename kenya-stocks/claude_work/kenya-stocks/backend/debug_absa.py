from extract_all import extract_text, get_lines, extract_bank_metrics
from pathlib import Path
import json

pdf = Path(r'C:\Users\nthig\.openclaw\workspace\kenya-stocks\data\nse\2022\ABSA_Bank_Kenya_Plc_31_Dec_2021_audited.pdf')
text = extract_text(pdf)
lines = get_lines(text)

print("=== PAT-related lines ===")
for l in lines:
    if any(k in l.lower() for k in ['profit after', 'profit for', 'net profit']):
        print('  ', l[:120])

print("\n=== Metrics ===")
metrics = extract_bank_metrics(lines)
print(json.dumps(metrics, indent=2))
