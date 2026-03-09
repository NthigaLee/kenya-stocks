"""
Direct download script for JSE Phase 1 Test (5 companies).
Uses manually found PDF URLs since IR page scraping is unreliable.
"""
import os
import sys
import requests
from pathlib import Path

PDFS = {
    "BHG": [
        ("https://bidvest.com/pdf/results/annual-results/2024/bidvest-company-2024-afs.pdf", "BHG_AFS_2024.pdf"),
        ("https://bidvest.co.za/pdf/results/annual-results/2024/fy2024-booklet.pdf", "BHG_Annual_Results_2024.pdf"),
        ("https://bidvest.co.za/pdf/results/interim-results/2025/1hfy2025.pdf", "BHG_Interim_H1_FY2025.pdf"),
    ],
    "ANH": [
        ("https://www.aspenpharma.com/wp-content/uploads/2024/09/FY-2024-Annual-Results-Presentation.pdf", "ANH_Annual_Results_2024.pdf"),
    ],
    "BTI": [
        ("https://www.bat.com/content/dam/batcom/global/main-nav/investors-and-reporting/results-centre/pdf/FY_2024_Announcement.pdf", "BTI_FY2024_Results.pdf"),
    ],
    "NTC": [
        ("https://www.netcare.co.za/portals/0/Annual%20Reports/pdf/Netcare-AFS-2024.pdf", "NTC_AFS_2024.pdf"),
        ("https://www.netcare.co.za/portals/0/Annual%20Reports/pdf/Netcare-Shareholder-Report-2024.pdf", "NTC_Shareholder_Report_2024.pdf"),
        ("https://www.netcare.co.za/Portals/0/Investor%20Relations/Financial%20Results/2024%20-%20Annual%20Results/Netcare%20results%20booklet.pdf", "NTC_Results_Booklet_2024.pdf"),
    ],
    "PRX": [
        ("https://www.prosus.com/~/media/Files/P/Prosus-CORP/AR2024/1latestfinancialresults/05summaryfinancialstatements/fy2024summaryconsolidatedfinancialstatements.pdf", "PRX_Summary_FS_FY2024.pdf"),
        ("https://www.prosusreport2024.com/pdf/finacial-statements.pdf", "PRX_Financial_Statements_2024.pdf"),
    ],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

OUTPUT_BASE = Path("data/jse")
results = {}

for ticker, files in PDFS.items():
    ticker_dir = OUTPUT_BASE / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)
    results[ticker] = []

    for url, filename in files:
        out_path = ticker_dir / filename
        print(f"Downloading {ticker}/{filename}...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
            if r.status_code == 200:
                content_type = r.headers.get("content-type", "")
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                size_kb = out_path.stat().st_size // 1024
                print(f"  OK ({size_kb} KB) - {content_type[:40]}")
                results[ticker].append(str(out_path))
            else:
                print(f"  FAILED: HTTP {r.status_code}")
        except Exception as e:
            print(f"  ERROR: {e}")

print("\n=== DOWNLOAD SUMMARY ===")
total = 0
for ticker, files in results.items():
    print(f"  {ticker}: {len(files)} files")
    total += len(files)
print(f"  TOTAL: {total} PDFs")
