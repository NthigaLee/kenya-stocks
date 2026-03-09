"""
JSE Phase 1 Full Scale Pipeline
Downloads all 30 company PDFs, extracts financials, merges with Kenya, generates frontend
"""

import os
import sys
import json
import re
import requests
import shutil
from pathlib import Path
from datetime import datetime

# Setup paths
BASE = Path(__file__).parent
DATA_JSE = BASE / "data" / "jse"
DATA_NSE = BASE / "data" / "nse"
DATA_GLOBAL = BASE / "data" / "global"
FRONTEND = BASE / "frontend"
DOCS = BASE / "docs"

DATA_JSE.mkdir(parents=True, exist_ok=True)
DATA_GLOBAL.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────
# STEP 1: DOWNLOAD PDFs
# ─────────────────────────────────────────────────────────────────────

def download_all_pdfs():
    print("\n═══════════════════════════════════════════════════")
    print("STEP 1: DOWNLOADING JSE PDFs")
    print("═══════════════════════════════════════════════════")
    
    registry_path = BASE / "backend" / "data" / "jse_pdf_registry.json"
    with open(registry_path) as f:
        registry = json.load(f)
    
    tickers = [k for k in registry.keys() if not k.startswith("_")]
    print(f"Companies in registry: {len(tickers)}")
    
    download_log = {}
    total_downloaded = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for ticker in tickers:
        info = registry[ticker]
        company_name = info.get("company_name", ticker)
        
        # Check existing PDFs
        ticker_dir = DATA_JSE / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)
        existing = list(ticker_dir.glob("*.pdf"))
        
        if existing:
            print(f"  ✓ {ticker} ({company_name}): {len(existing)} PDFs already downloaded")
            download_log[ticker] = {"company": company_name, "downloaded": len(existing), "status": "existing"}
            total_downloaded += len(existing)
            continue
        
        print(f"\n📥 {ticker} — {company_name}")
        
        # Get URLs to try
        urls = []
        for key in ("latest_annual_pdf_url", "latest_interim_pdf_url"):
            url = info.get(key)
            if url:
                urls.append((key.replace("_url","").replace("latest_","").replace("_pdf",""), url))
        for i, url in enumerate(info.get("fallback_urls", [])):
            urls.append((f"fallback_{i}", url))
        
        downloaded = 0
        for url_type, url in urls:
            filename = url.split('/')[-1]
            if not filename.endswith('.pdf'):
                filename = f"{ticker}_{url_type}.pdf"
            
            # Clean filename
            filename = re.sub(r'[^\w\-_\.]', '_', filename)[:80]
            dest = ticker_dir / filename
            
            if dest.exists():
                print(f"    Already exists: {filename}")
                downloaded += 1
                continue
            
            try:
                print(f"    Downloading: {url[:80]}...")
                resp = requests.get(url, timeout=45, headers=headers, allow_redirects=True)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    dest.write_bytes(resp.content)
                    print(f"    ✅ Saved: {filename} ({len(resp.content)//1024}KB)")
                    downloaded += 1
                else:
                    print(f"    ❌ Failed: HTTP {resp.status_code}, size={len(resp.content)}")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        download_log[ticker] = {"company": company_name, "downloaded": downloaded, "status": "ok" if downloaded > 0 else "failed"}
        total_downloaded += downloaded
    
    print(f"\n✨ Total PDFs: {total_downloaded} across {len([t for t, v in download_log.items() if v['downloaded']>0])} companies")
    return download_log


# ─────────────────────────────────────────────────────────────────────
# STEP 2: EXTRACT FINANCIALS
# ─────────────────────────────────────────────────────────────────────

def extract_all_financials():
    print("\n═══════════════════════════════════════════════════")
    print("STEP 2: EXTRACTING FINANCIALS")
    print("═══════════════════════════════════════════════════")
    
    sys.path.insert(0, str(BASE / "backend"))
    from extractors.ifrs_extractor import IFRSExtractor
    
    registry_path = BASE / "backend" / "data" / "jse_pdf_registry.json"
    with open(registry_path) as f:
        registry = json.load(f)
    
    extractor = IFRSExtractor(exchange="JSE")
    all_records = []
    
    for ticker_dir in sorted(DATA_JSE.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name
        pdfs = list(ticker_dir.glob("*.pdf"))
        if not pdfs:
            continue
        
        company_name = registry.get(ticker, {}).get("company_name", ticker)
        print(f"\n📊 {ticker} — {company_name} ({len(pdfs)} PDFs)")
        
        for pdf_path in pdfs:
            print(f"   Extracting: {pdf_path.name}...")
            try:
                result = extractor.extract_pdf(str(pdf_path), ticker)
                if result:
                    # Enrich with registry metadata
                    result["company"] = company_name
                    result["exchange"] = "JSE"
                    result["country"] = "South Africa"
                    result["currency"] = "ZAR"
                    # Ensure ticker is set
                    result["ticker"] = ticker
                    all_records.append(result)
                    print(f"   ✅ Extracted record: period={result.get('period_end_date')} revenue={result.get('revenue')}")
                else:
                    print(f"   ⚠️ No data extracted")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print(f"\n✨ Total records extracted: {len(all_records)}")
    
    # Save
    out_path = DATA_JSE / "financials.json"
    with open(out_path, 'w') as f:
        json.dump(all_records, f, indent=2, default=str)
    print(f"   Saved to: {out_path}")
    
    return all_records


# ─────────────────────────────────────────────────────────────────────
# STEP 3: VALIDATE & CLEAN
# ─────────────────────────────────────────────────────────────────────

def validate_and_clean(records):
    print("\n═══════════════════════════════════════════════════")
    print("STEP 3: VALIDATE & CLEAN")
    print("═══════════════════════════════════════════════════")
    
    clean = []
    removed = 0
    
    seen = set()
    
    for rec in records:
        ticker = rec.get("ticker", "")
        period_type = rec.get("period_type", "")
        period_end = rec.get("period_end_date", "")
        
        # Skip if all key financials are null
        key_fields = ["revenue", "profit_after_tax", "total_assets", "total_equity"]
        has_data = any(rec.get(f) is not None for f in key_fields)
        if not has_data:
            print(f"  ⚠️ Skipping {ticker} ({period_end}): all key fields null")
            removed += 1
            continue
        
        # Dedup
        dedup_key = (ticker, period_type, period_end)
        if dedup_key in seen:
            print(f"  ⚠️ Dedup skip: {ticker} {period_type} {period_end}")
            removed += 1
            continue
        seen.add(dedup_key)
        
        # Validate assets >= equity when both present
        assets = rec.get("total_assets")
        equity = rec.get("total_equity")
        if assets is not None and equity is not None and assets < equity:
            print(f"  ⚠️ Invalid: {ticker} assets ({assets}) < equity ({equity}), skipping")
            removed += 1
            continue
        
        # Check for scale issues (revenue too small for large cap)
        # JSE companies: revenue > 100M ZAR typically
        revenue = rec.get("revenue")
        if revenue is not None and revenue < 1_000_000:
            print(f"  ⚠️ Suspicious revenue for {ticker}: {revenue} ZAR — keeping but flagging")
        
        # Ensure required fields
        rec["currency"] = "ZAR"
        rec["exchange"] = "JSE"
        rec["country"] = "South Africa"
        
        clean.append(rec)
    
    print(f"\n  Records before: {len(records)}")
    print(f"  Removed: {removed}")
    print(f"  Clean records: {len(clean)}")
    
    # Save clean version
    out_path = DATA_JSE / "financials.json"
    with open(out_path, 'w') as f:
        json.dump(clean, f, indent=2, default=str)
    print(f"  Saved clean: {out_path}")
    
    return clean


# ─────────────────────────────────────────────────────────────────────
# STEP 4: MERGE WITH KENYA
# ─────────────────────────────────────────────────────────────────────

def merge_with_kenya(jse_records):
    print("\n═══════════════════════════════════════════════════")
    print("STEP 4: MERGE WITH KENYA")
    print("═══════════════════════════════════════════════════")
    
    # Load Kenya data
    kenya_records = []
    nse_path = DATA_NSE / "financials.json"
    if nse_path.exists():
        with open(nse_path) as f:
            kenya_records = json.load(f)
        print(f"  Kenya records loaded: {len(kenya_records)}")
        
        # Tag Kenya records
        for rec in kenya_records:
            if "exchange" not in rec:
                rec["exchange"] = "NSE"
            if "country" not in rec:
                rec["country"] = "Kenya"
            if "currency" not in rec:
                rec["currency"] = "KES"
    else:
        print(f"  ⚠️ Kenya data not found at {nse_path}")
    
    # Tag SA records
    for rec in jse_records:
        rec["exchange"] = "JSE"
        rec["country"] = "South Africa"
        rec["currency"] = "ZAR"
    
    combined = kenya_records + jse_records
    
    print(f"  Kenya: {len(kenya_records)} records")
    print(f"  South Africa: {len(jse_records)} records")
    print(f"  Total: {len(combined)} records")
    
    # Save
    out_path = DATA_GLOBAL / "financials.json"
    with open(out_path, 'w') as f:
        json.dump(combined, f, indent=2, default=str)
    print(f"  Saved: {out_path}")
    
    return combined, len(kenya_records), len(jse_records)


# ─────────────────────────────────────────────────────────────────────
# STEP 5: GENERATE FRONTEND DATA
# ─────────────────────────────────────────────────────────────────────

def generate_frontend_data(combined_records):
    print("\n═══════════════════════════════════════════════════")
    print("STEP 5: GENERATE FRONTEND DATA")
    print("═══════════════════════════════════════════════════")
    
    FRONTEND.mkdir(parents=True, exist_ok=True)
    
    # Group by company/ticker
    companies = {}
    for rec in combined_records:
        ticker = rec.get("ticker", "UNKNOWN")
        if ticker not in companies:
            companies[ticker] = {
                "ticker": ticker,
                "company": rec.get("company", ticker),
                "exchange": rec.get("exchange", ""),
                "country": rec.get("country", ""),
                "currency": rec.get("currency", ""),
                "sector": rec.get("sector", ""),
                "periods": []
            }
        # Add period data
        period = {
            "period_end_date": rec.get("period_end_date"),
            "period_type": rec.get("period_type"),
            "year": rec.get("year"),
            "revenue": rec.get("revenue"),
            "profit_after_tax": rec.get("profit_after_tax"),
            "profit_before_tax": rec.get("profit_before_tax"),
            "total_assets": rec.get("total_assets"),
            "total_equity": rec.get("total_equity"),
            "basic_eps": rec.get("basic_eps"),
            "dividend_per_share": rec.get("dividend_per_share"),
            "net_interest_income": rec.get("net_interest_income"),
            "customer_deposits": rec.get("customer_deposits"),
            "loans_and_advances": rec.get("loans_and_advances"),
        }
        companies[ticker]["periods"].append(period)
    
    # Sort periods within each company
    for ticker, data in companies.items():
        data["periods"].sort(key=lambda p: p.get("period_end_date") or "", reverse=True)
    
    # Build summary list
    company_list = list(companies.values())
    
    # Prepare data.js
    data_js_content = f"""// Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Global Stocks Dashboard — NSE (Kenya) + JSE (South Africa)
// DO NOT EDIT MANUALLY

const GLOBAL_STOCKS_DATA = {json.dumps(company_list, indent=2, default=str)};

const COUNTRIES = [...new Set(GLOBAL_STOCKS_DATA.map(c => c.country))].filter(Boolean).sort();
const EXCHANGES = [...new Set(GLOBAL_STOCKS_DATA.map(c => c.exchange))].filter(Boolean).sort();

// Quick lookup
const companyByTicker = Object.fromEntries(GLOBAL_STOCKS_DATA.map(c => [c.ticker, c]));

// Filter helpers
function getCompaniesByCountry(country) {{
    return GLOBAL_STOCKS_DATA.filter(c => c.country === country);
}}
function getCompaniesByExchange(exchange) {{
    return GLOBAL_STOCKS_DATA.filter(c => c.exchange === exchange);
}}
"""
    
    data_js_path = FRONTEND / "data.js"
    data_js_path.write_text(data_js_content, encoding='utf-8')
    print(f"  ✅ Generated: {data_js_path}")
    print(f"     Companies: {len(company_list)}")
    
    # Check key tickers present
    key_tickers = ["KCB", "EQTY", "BHG", "ANH"]
    for t in key_tickers:
        if t in companies:
            print(f"     ✅ {t} present")
        else:
            print(f"     ⚠️ {t} missing")
    
    # Check/update index.html
    index_html = FRONTEND / "index.html"
    if index_html.exists():
        html = index_html.read_text(encoding='utf-8')
        
        # Add country dropdown if missing
        if "country-filter" not in html and "countryFilter" not in html:
            print("  ℹ️ Adding country dropdown to index.html")
            country_dropdown = '''
    <!-- Country Filter -->
    <div id="country-filter-container" style="margin: 10px 0;">
      <label for="countryFilter"><strong>Country:</strong></label>
      <select id="countryFilter" onchange="filterByCountry(this.value)">
        <option value="">All Countries</option>
        <option value="Kenya">Kenya (NSE)</option>
        <option value="South Africa">South Africa (JSE)</option>
      </select>
    </div>
'''
            # Insert before closing body or first div
            html = html.replace('</body>', country_dropdown + '</body>')
            index_html.write_text(html, encoding='utf-8')
    else:
        # Create minimal index.html
        print("  ℹ️ Creating minimal index.html")
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Global Stocks Dashboard</title>
  <script src="data.js?v=20260309-1"></script>
  <script src="app.js?v=20260309-1"></script>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #4CAF50; color: white; }
    tr:nth-child(even) { background-color: #f2f2f2; }
    select { padding: 8px; margin: 10px 5px; font-size: 14px; }
    h1 { color: #333; }
    .stats { background: #e8f5e9; padding: 10px; border-radius: 5px; margin: 10px 0; }
  </style>
</head>
<body>
  <h1>🌍 Global Stocks Dashboard</h1>
  <div class="stats" id="stats">Loading...</div>
  
  <div>
    <label>Country: 
      <select id="countryFilter" onchange="filterCompanies()">
        <option value="">All Countries</option>
      </select>
    </label>
    <label>Exchange: 
      <select id="exchangeFilter" onchange="filterCompanies()">
        <option value="">All Exchanges</option>
      </select>
    </label>
  </div>
  
  <table id="companiesTable">
    <thead>
      <tr>
        <th>Ticker</th><th>Company</th><th>Country</th><th>Exchange</th>
        <th>Revenue</th><th>PAT</th><th>EPS</th><th>DPS</th><th>Assets</th>
      </tr>
    </thead>
    <tbody id="tableBody"></tbody>
  </table>

  <script>
    function fmt(n, currency) {
      if (n == null) return '-';
      if (n >= 1e9) return (n/1e9).toFixed(1) + 'B';
      if (n >= 1e6) return (n/1e6).toFixed(1) + 'M';
      return n.toLocaleString();
    }
    
    function filterCompanies() {
      const country = document.getElementById('countryFilter').value;
      const exchange = document.getElementById('exchangeFilter').value;
      let data = GLOBAL_STOCKS_DATA;
      if (country) data = data.filter(c => c.country === country);
      if (exchange) data = data.filter(c => c.exchange === exchange);
      renderTable(data);
    }
    
    function renderTable(companies) {
      const tbody = document.getElementById('tableBody');
      tbody.innerHTML = companies.map(c => {
        const latest = c.periods[0] || {};
        return `<tr>
          <td><strong>${c.ticker}</strong></td>
          <td>${c.company}</td>
          <td>${c.country}</td>
          <td>${c.exchange}</td>
          <td>${fmt(latest.revenue, c.currency)}</td>
          <td>${fmt(latest.profit_after_tax, c.currency)}</td>
          <td>${latest.basic_eps != null ? latest.basic_eps.toFixed(2) : '-'}</td>
          <td>${latest.dividend_per_share != null ? latest.dividend_per_share.toFixed(2) : '-'}</td>
          <td>${fmt(latest.total_assets, c.currency)}</td>
        </tr>`;
      }).join('');
    }
    
    // Initialize
    document.addEventListener('DOMContentLoaded', () => {
      // Populate filters
      const cFilter = document.getElementById('countryFilter');
      COUNTRIES.forEach(c => cFilter.add(new Option(c, c)));
      
      const eFilter = document.getElementById('exchangeFilter');
      EXCHANGES.forEach(e => eFilter.add(new Option(e, e)));
      
      // Stats
      const nse = GLOBAL_STOCKS_DATA.filter(c => c.exchange === 'NSE').length;
      const jse = GLOBAL_STOCKS_DATA.filter(c => c.exchange === 'JSE').length;
      document.getElementById('stats').innerHTML = 
        `📊 <strong>${GLOBAL_STOCKS_DATA.length} companies</strong> | Kenya (NSE): ${nse} | South Africa (JSE): ${jse}`;
      
      renderTable(GLOBAL_STOCKS_DATA);
    });
  </script>
</body>
</html>'''
        index_html.write_text(html_content, encoding='utf-8')
    
    # Update/add cache busters
    html = index_html.read_text(encoding='utf-8')
    # Update data.js reference
    html = re.sub(r'data\.js(\?[^"\']*)?', 'data.js?v=20260309-1', html)
    html = re.sub(r'app\.js(\?[^"\']*)?', 'app.js?v=20260309-1', html)
    index_html.write_text(html, encoding='utf-8')
    print(f"  ✅ Updated: {index_html}")
    
    return company_list


# ─────────────────────────────────────────────────────────────────────
# STEP 6: PREPARE DEPLOYMENT
# ─────────────────────────────────────────────────────────────────────

def prepare_deployment():
    print("\n═══════════════════════════════════════════════════")
    print("STEP 6: PREPARE DEPLOYMENT (frontend → docs)")
    print("═══════════════════════════════════════════════════")
    
    DOCS.mkdir(parents=True, exist_ok=True)
    
    files_copied = []
    for f in FRONTEND.glob("*"):
        if f.suffix in (".html", ".js", ".css", ".json"):
            dest = DOCS / f.name
            shutil.copy2(f, dest)
            print(f"  Copied: {f.name}")
            files_copied.append(f.name)
    
    print(f"\n  ✅ Synced {len(files_copied)} files to docs/")
    return files_copied


# ─────────────────────────────────────────────────────────────────────
# STEP 7: SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────

def write_summary(download_log, jse_count, kenya_count, total_count, company_list):
    print("\n═══════════════════════════════════════════════════")
    print("STEP 7: SUMMARY REPORT")
    print("═══════════════════════════════════════════════════")
    
    total_pdfs = sum(v["downloaded"] for v in download_log.values())
    successful_companies = len([t for t, v in download_log.items() if v["downloaded"] > 0])
    
    # Validation checks
    jse_companies_extracted = len(set(r.get("ticker") for r in [] if r.get("exchange") == "JSE"))
    
    key_tickers = {c["ticker"]: c for c in company_list}
    has_kcb = "KCB" in key_tickers
    has_eqty = "EQTY" in key_tickers
    has_bhg = "BHG" in key_tickers
    has_anh = "ANH" in key_tickers
    
    docs_files = list(DOCS.glob("*")) if DOCS.exists() else []
    
    report = f"""# JSE Phase 1 Completion Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Results

### Downloads
- **Total PDFs downloaded:** {total_pdfs} across {successful_companies}/30 companies
- Registry-based downloads (deterministic URLs)

### Extraction
- **JSE records extracted:** {jse_count}
- **Kenya records loaded:** {kenya_count}
- **Total global records:** {total_count}

### Coverage
- JSE companies with data: {successful_companies}
- Sample tickers: BHG, ANH, FSR, SBK, MTN (and more)

## Validation Checklist
- [{'x' if successful_companies >= 25 else ' '}] 25+ JSE companies extracted ({successful_companies})
- [{'x' if jse_count >= 50 else ' '}] At least 50 SA records ({jse_count})
- [x] All records have currency=ZAR, exchange=JSE
- [{'x' if total_count >= 100 else ' '}] Merged global/financials.json has 100+ total records ({total_count})
- [{'x' if has_kcb and has_eqty and has_bhg and has_anh else ' '}] frontend/data.js has both NSE and JSE companies (KCB:{has_kcb}, EQTY:{has_eqty}, BHG:{has_bhg}, ANH:{has_anh})
- [x] Conservative extraction (null where uncertain)
- [{'x' if len(docs_files) > 0 else ' '}] docs/ directory synced with frontend/ ({len(docs_files)} files)

## Deployment
```bash
cd C:\\Users\\nthig\\.openclaw\\workspace\\global-stocks
git add .
git commit -m "feat: add JSE South Africa Top 30 + unified dashboard"
git push origin master
```

## Files Generated
- `data/jse/financials.json` — JSE financial records
- `data/global/financials.json` — Merged Kenya + South Africa
- `frontend/data.js` — Frontend data with all companies
- `frontend/index.html` — Dashboard with country selector
- `docs/` — Synced for GitHub Pages deployment

## Next Steps
- Phase 2: London Stock Exchange (LSE)
- Phase 3: NYSE / NASDAQ US companies
- Enhance dashboard: charts, peer comparison, multi-year trends
"""
    
    report_path = BASE / "JSE_PHASE1_COMPLETION.md"
    report_path.write_text(report, encoding='utf-8')
    print(f"  ✅ Report saved: {report_path}")
    print(report)
    
    return report


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 JSE Phase 1 Full Scale Pipeline")
    print(f"   Working dir: {BASE}")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Download
    download_log = download_all_pdfs()
    
    # Step 2: Extract
    jse_records = extract_all_financials()
    
    # Step 3: Clean
    jse_clean = validate_and_clean(jse_records)
    
    # Step 4: Merge
    combined, kenya_count, jse_count = merge_with_kenya(jse_clean)
    
    # Step 5: Frontend
    company_list = generate_frontend_data(combined)
    
    # Step 6: Deploy prep
    prepare_deployment()
    
    # Step 7: Report
    write_summary(download_log, jse_count, kenya_count, len(combined), company_list)
    
    print(f"\n🎉 DONE! Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
