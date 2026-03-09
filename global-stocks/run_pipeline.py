"""
Run the full pipeline: merge -> frontend -> docs
"""
import json, shutil, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
DATA_NSE = BASE / 'data' / 'nse'
DATA_JSE = BASE / 'data' / 'jse'
DATA_GLOBAL = BASE / 'data' / 'global'
FRONTEND = BASE / 'frontend'
DOCS = BASE / 'docs'

for d in [DATA_GLOBAL, FRONTEND, DOCS]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────
# MERGE
# ─────────────────────────────────────────────────────────────────────
nse = json.loads((DATA_NSE / 'financials.json').read_text(encoding='utf-8'))
jse = json.loads((DATA_JSE / 'financials.json').read_text(encoding='utf-8'))

for r in nse:
    r['exchange'] = 'NSE'
    r['country'] = 'Kenya'
    r['currency'] = 'KES'
for r in jse:
    r['exchange'] = 'JSE'
    r['country'] = 'South Africa'
    r['currency'] = 'ZAR'

combined = nse + jse
print(f'Kenya: {len(nse)}, SA: {len(jse)}, Total: {len(combined)}')

(DATA_GLOBAL / 'financials.json').write_text(
    json.dumps(combined, indent=2, default=str), encoding='utf-8'
)
print(f'Saved: {DATA_GLOBAL}/financials.json')

# ─────────────────────────────────────────────────────────────────────
# BUILD COMPANY LIST
# ─────────────────────────────────────────────────────────────────────
companies = {}
for rec in combined:
    t = rec.get('ticker', 'UNKNOWN')
    if t not in companies:
        companies[t] = {
            'ticker': t,
            'company': rec.get('company', t),
            'exchange': rec.get('exchange', ''),
            'country': rec.get('country', ''),
            'currency': rec.get('currency', ''),
            'sector': rec.get('sector', ''),
            'periods': []
        }
    companies[t]['periods'].append({
        'period_end_date': rec.get('period_end_date'),
        'period_type': rec.get('period_type'),
        'year': rec.get('year'),
        'revenue': rec.get('revenue'),
        'profit_after_tax': rec.get('profit_after_tax'),
        'profit_before_tax': rec.get('profit_before_tax'),
        'total_assets': rec.get('total_assets'),
        'total_equity': rec.get('total_equity'),
        'basic_eps': rec.get('basic_eps'),
        'dividend_per_share': rec.get('dividend_per_share'),
        'net_interest_income': rec.get('net_interest_income'),
        'customer_deposits': rec.get('customer_deposits'),
        'loans_and_advances': rec.get('loans_and_advances'),
    })

for t in companies:
    companies[t]['periods'].sort(key=lambda p: p.get('period_end_date') or '', reverse=True)

company_list = list(companies.values())
company_list.sort(key=lambda c: (c['exchange'], c['ticker']))
print(f'Unique companies: {len(company_list)}')

for t in ['KCB', 'EQTY', 'BHG', 'ANH', 'SCOM', 'FSR', 'MTN']:
    status = 'found' if t in companies else 'MISSING'
    print(f'  {t}: {status}')

# ─────────────────────────────────────────────────────────────────────
# GENERATE data.js
# ─────────────────────────────────────────────────────────────────────
data_js = f"""// Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Global Stocks Dashboard - NSE (Kenya) + JSE (South Africa)
// Total companies: {len(company_list)} | Kenya: {len(nse)} records | SA: {len(jse)} records

const GLOBAL_STOCKS_DATA = {json.dumps(company_list, indent=2, default=str)};

const COUNTRIES = [...new Set(GLOBAL_STOCKS_DATA.map(c => c.country))].filter(Boolean).sort();
const EXCHANGES = [...new Set(GLOBAL_STOCKS_DATA.map(c => c.exchange))].filter(Boolean).sort();

const companyByTicker = Object.fromEntries(GLOBAL_STOCKS_DATA.map(c => [c.ticker, c]));

function getCompaniesByCountry(country) {{
    return GLOBAL_STOCKS_DATA.filter(c => c.country === country);
}}
function getCompaniesByExchange(exchange) {{
    return GLOBAL_STOCKS_DATA.filter(c => c.exchange === exchange);
}}
"""

(FRONTEND / 'data.js').write_text(data_js, encoding='utf-8')
print(f'Generated: {FRONTEND}/data.js')

# ─────────────────────────────────────────────────────────────────────
# GENERATE index.html
# ─────────────────────────────────────────────────────────────────────
nse_count = len([c for c in company_list if c['exchange'] == 'NSE'])
jse_count = len([c for c in company_list if c['exchange'] == 'JSE'])

index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Global Stocks Dashboard - Africa</title>
  <script src="data.js?v=20260309-1"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; }}
    header {{ background: linear-gradient(135deg, #1a472a, #2d6a4f); color: white; padding: 20px 30px; }}
    header h1 {{ font-size: 1.8em; }}
    header p {{ opacity: 0.85; margin-top: 5px; font-size: 0.9em; }}
    .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
    .stats-row {{ display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap; }}
    .stat-card {{ background: white; border-radius: 8px; padding: 15px 20px; flex: 1; min-width: 150px;
                  box-shadow: 0 1px 4px rgba(0,0,0,0.1); border-left: 4px solid #2d6a4f; }}
    .stat-card .num {{ font-size: 2em; font-weight: bold; color: #2d6a4f; }}
    .stat-card .lbl {{ color: #888; font-size: 0.85em; margin-top: 3px; }}
    .filters {{ background: white; border-radius: 8px; padding: 15px 20px; margin-bottom: 15px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.1); display: flex; gap: 20px; flex-wrap: wrap; align-items: center; }}
    .filters label {{ font-weight: 600; font-size: 0.9em; }}
    .filters select {{ padding: 8px 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 0.9em; cursor: pointer; }}
    .filters input {{ padding: 8px 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 0.9em; width: 200px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px;
             overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }}
    thead tr {{ background: #1a472a; color: white; }}
    th {{ padding: 12px 15px; text-align: left; font-size: 0.85em; font-weight: 600; cursor: pointer; white-space: nowrap; }}
    th:hover {{ background: #2d6a4f; }}
    td {{ padding: 11px 15px; border-bottom: 1px solid #f0f0f0; font-size: 0.88em; }}
    tr:hover td {{ background: #f0f9f4; }}
    .tag {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.78em; font-weight: 600; }}
    .tag-NSE {{ background: #e8f5e9; color: #2e7d32; }}
    .tag-JSE {{ background: #e3f2fd; color: #1565c0; }}
    .num-col {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .ticker {{ font-weight: bold; color: #1a472a; font-family: monospace; font-size: 0.95em; }}
    .no-results {{ text-align: center; padding: 40px; color: #888; font-size: 1.1em; }}
    .result-count {{ color: #888; font-size: 0.85em; margin-bottom: 8px; }}
    footer {{ text-align: center; padding: 20px; color: #aaa; font-size: 0.8em; margin-top: 30px; }}
  </style>
</head>
<body>
  <header>
    <h1>🌍 Global Stocks Dashboard</h1>
    <p>African markets: NSE (Kenya) + JSE (South Africa) &mdash; {len(company_list)} companies tracked</p>
  </header>

  <div class="container">
    <div class="stats-row">
      <div class="stat-card">
        <div class="num" id="totalCount">{len(company_list)}</div>
        <div class="lbl">Total Companies</div>
      </div>
      <div class="stat-card">
        <div class="num" style="color:#2e7d32">{nse_count}</div>
        <div class="lbl">NSE Kenya</div>
      </div>
      <div class="stat-card">
        <div class="num" style="color:#1565c0">{jse_count}</div>
        <div class="lbl">JSE South Africa</div>
      </div>
      <div class="stat-card">
        <div class="num">2024</div>
        <div class="lbl">Data Year</div>
      </div>
    </div>

    <div class="filters">
      <div>
        <label>Country: </label>
        <select id="countryFilter" onchange="applyFilters()">
          <option value="">All Countries</option>
          <option value="Kenya">Kenya (NSE)</option>
          <option value="South Africa">South Africa (JSE)</option>
        </select>
      </div>
      <div>
        <label>Sector: </label>
        <select id="sectorFilter" onchange="applyFilters()">
          <option value="">All Sectors</option>
        </select>
      </div>
      <div>
        <label>Search: </label>
        <input type="text" id="searchInput" placeholder="Company or ticker..." oninput="applyFilters()">
      </div>
    </div>

    <div class="result-count" id="resultCount"></div>

    <table id="stocksTable">
      <thead>
        <tr>
          <th onclick="sortBy('ticker')">Ticker</th>
          <th onclick="sortBy('company')">Company</th>
          <th onclick="sortBy('sector')">Sector</th>
          <th>Exchange</th>
          <th class="num-col" onclick="sortByNum('revenue')">Revenue</th>
          <th class="num-col" onclick="sortByNum('profit_after_tax')">Net Profit</th>
          <th class="num-col" onclick="sortByNum('total_assets')">Assets</th>
          <th class="num-col" onclick="sortByNum('total_equity')">Equity</th>
          <th class="num-col" onclick="sortByNum('basic_eps')">EPS</th>
          <th class="num-col" onclick="sortByNum('dividend_per_share')">DPS</th>
          <th>Period</th>
        </tr>
      </thead>
      <tbody id="tableBody"></tbody>
    </table>

    <footer>
      Data: FY2023/2024 company reports &mdash; Generated {datetime.now().strftime('%Y-%m-%d')}
      &mdash; Values in company currency (KES/ZAR millions unless noted)
    </footer>
  </div>

  <script src="app.js?v=20260309-1"></script>
</body>
</html>"""

(FRONTEND / 'index.html').write_text(index_html, encoding='utf-8')
print(f'Generated: {FRONTEND}/index.html')

# ─────────────────────────────────────────────────────────────────────
# GENERATE app.js
# ─────────────────────────────────────────────────────────────────────
app_js = """// Global Stocks Dashboard - App Logic
// v=20260309-1

let sortField = 'ticker';
let sortAsc = true;
let currentData = GLOBAL_STOCKS_DATA;

function fmt(n, decimals) {
    if (n == null || n === undefined) return '-';
    if (typeof n !== 'number') return '-';
    if (n >= 1e9) return (n/1e9).toFixed(1) + 'B';
    if (n >= 1e6) return (n/1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n/1e3).toFixed(1) + 'K';
    return n.toFixed(decimals != null ? decimals : 2);
}

function fmtMillions(n) {
    // Input is already in millions
    if (n == null || n === undefined) return '-';
    if (typeof n !== 'number') return '-';
    if (n >= 1e6) return (n/1e6).toFixed(1) + 'T';
    if (n >= 1e3) return (n/1e3).toFixed(1) + 'B';
    return n.toFixed(0) + 'M';
}

function applyFilters() {
    const country = document.getElementById('countryFilter').value;
    const sector = document.getElementById('sectorFilter').value;
    const search = document.getElementById('searchInput').value.toLowerCase();
    
    currentData = GLOBAL_STOCKS_DATA.filter(c => {
        if (country && c.country !== country) return false;
        if (sector && c.sector !== sector) return false;
        if (search && !c.ticker.toLowerCase().includes(search) && 
            !c.company.toLowerCase().includes(search)) return false;
        return true;
    });
    
    renderTable(currentData);
}

function sortBy(field) {
    if (sortField === field) sortAsc = !sortAsc;
    else { sortField = field; sortAsc = true; }
    renderTable(currentData);
}

function sortByNum(field) {
    if (sortField === field) sortAsc = !sortAsc;
    else { sortField = field; sortAsc = false; }
    renderTable(currentData);
}

function renderTable(companies) {
    const sorted = [...companies].sort((a, b) => {
        let aVal, bVal;
        if (['revenue','profit_after_tax','total_assets','total_equity','basic_eps','dividend_per_share'].includes(sortField)) {
            aVal = a.periods[0] ? a.periods[0][sortField] : null;
            bVal = b.periods[0] ? b.periods[0][sortField] : null;
            aVal = aVal != null ? aVal : -Infinity;
            bVal = bVal != null ? bVal : -Infinity;
        } else {
            aVal = a[sortField] || '';
            bVal = b[sortField] || '';
        }
        if (typeof aVal === 'string') {
            return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        }
        return sortAsc ? aVal - bVal : bVal - aVal;
    });
    
    const tbody = document.getElementById('tableBody');
    const resultCount = document.getElementById('resultCount');
    resultCount.textContent = sorted.length + ' companies shown';
    
    if (sorted.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="no-results">No companies match your filters</td></tr>';
        return;
    }
    
    tbody.innerHTML = sorted.map(c => {
        const p = c.periods[0] || {};
        const tag = `<span class="tag tag-${c.exchange}">${c.exchange}</span>`;
        const period = p.period_end_date ? p.period_end_date.substring(0, 7) : '-';
        return `<tr>
            <td class="ticker">${c.ticker}</td>
            <td>${c.company}</td>
            <td>${c.sector || '-'}</td>
            <td>${tag}</td>
            <td class="num-col">${fmtMillions(p.revenue)}</td>
            <td class="num-col">${fmtMillions(p.profit_after_tax)}</td>
            <td class="num-col">${fmtMillions(p.total_assets)}</td>
            <td class="num-col">${fmtMillions(p.total_equity)}</td>
            <td class="num-col">${p.basic_eps != null ? p.basic_eps.toFixed(2) : '-'}</td>
            <td class="num-col">${p.dividend_per_share != null ? p.dividend_per_share.toFixed(2) : '-'}</td>
            <td>${period}</td>
        </tr>`;
    }).join('');
    
    document.getElementById('totalCount').textContent = companies.length;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Populate sector filter
    const sectors = [...new Set(GLOBAL_STOCKS_DATA.map(c => c.sector).filter(Boolean))].sort();
    const sFilter = document.getElementById('sectorFilter');
    sectors.forEach(s => sFilter.add(new Option(s, s)));
    
    renderTable(GLOBAL_STOCKS_DATA);
});
"""

(FRONTEND / 'app.js').write_text(app_js, encoding='utf-8')
print(f'Generated: {FRONTEND}/app.js')

# ─────────────────────────────────────────────────────────────────────
# SYNC TO DOCS
# ─────────────────────────────────────────────────────────────────────
for f in FRONTEND.glob('*'):
    if f.suffix in ('.html', '.js', '.css', '.json'):
        dest = DOCS / f.name
        shutil.copy2(f, dest)
        print(f'Copied to docs: {f.name}')

print(f'\nDone! {len(company_list)} companies across {len(nse)} Kenya + {len(jse)} SA records')
print(f'KCB: {"found" if "KCB" in companies else "MISSING"}')
print(f'EQTY: {"found" if "EQTY" in companies else "MISSING"}')
print(f'BHG: {"found" if "BHG" in companies else "MISSING"}')
print(f'ANH: {"found" if "ANH" in companies else "MISSING"}')
