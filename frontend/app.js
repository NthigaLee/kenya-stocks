// ============================================================
//  NSE Insights — App Logic
//  Premium financial dashboard for Kenya NSE stocks
//  With SECTOR-SPECIFIC templates
// ============================================================

let activeCompany = null;
let chartInstances = {};
let NSE_PRICES = {};
let _priceChartType = 'line'; // 'line' | 'candle'

// ---- Sector Templates ----
// Each sector defines which charts to show, in which rows,
// and which stats to display. This way banks show loan books,
// insurance shows GWP, telecoms shows M-PESA, etc.

const SECTOR_TEMPLATES = {
  Banking: {
    label: 'Banking',
    statsRows: [
      { title: 'Income', rows: [
        { label: 'Total Income', key: 'revenue', fmt: 'num' },
        { label: 'Net Int. Income', key: 'nii', fmt: 'num' },
        { label: 'YoY Income', key: '_growth_revenue', fmt: 'growth' },
      ]},
      { title: 'Profitability', rows: [
        { label: 'Profit After Tax', key: 'pat', fmt: 'num' },
        { label: 'YoY PAT', key: '_growth_pat', fmt: 'growth' },
        { label: 'YoY NII', key: '_growth_nii', fmt: 'growth' },
      ]},
      { title: 'Per Share', rows: [
        { label: 'EPS', key: 'eps', fmt: 'eps' },
        { label: 'DPS', key: 'dps', fmt: 'eps' },
        { label: 'Price', key: '_price', fmt: 'price' },
      ]},
      { title: 'Valuation', rows: [
        { label: 'P/E (approx)', key: '_pe', fmt: 'raw' },
        { label: 'Div. Yield', key: '_divyield', fmt: 'raw' },
        { label: 'P/B (approx)', key: '_pb', fmt: 'raw' },
      ]},
      { title: 'Balance Sheet', rows: [
        { label: 'Total Assets', key: 'totalAssets', fmt: 'num' },
        { label: 'Deposits', key: 'deposits', fmt: 'num' },
        { label: 'Loan Book', key: 'loans', fmt: 'num' },
        { label: 'Equity', key: 'totalEquity', fmt: 'num' },
      ]},
      { title: 'Financial Health', rows: [
        { label: 'ROE %', key: '_roe', fmt: 'raw' },
        { label: 'ROA %', key: '_roa', fmt: 'raw' },
        { label: 'Net Margin %', key: '_profitmargin', fmt: 'raw' },
        { label: 'Debt/Equity', key: '_debtequity', fmt: 'raw' },
      ]},
      { title: 'Growth Trends', rows: [
        { label: 'EPS 5Y CAGR', key: '_eps5yrgrowth', fmt: 'raw' },
        { label: 'Revenue 5Y CAGR', key: '_revenue5yrgrowth', fmt: 'raw' },
      ]},
    ],
    chartRows: [
      { label: 'Income Statement', charts: [
        { id: 'revenue', title: 'Total Operating Income', key: 'revenue' },
        { id: 'nii', title: 'Net Interest Income', key: 'nii' },
        { id: 'pat', title: 'Profit After Tax', key: 'pat' },
        { id: 'eps', title: 'Earnings Per Share', key: 'eps', isCurrency: true },
        { id: 'dps', title: 'Dividends Per Share', key: 'dps', isCurrency: true },
      ]},
      { label: 'Balance Sheet', charts: [
        { id: 'assets', title: 'Total Assets', key: 'totalAssets' },
        { id: 'deposits', title: 'Customer Deposits', key: 'deposits' },
        { id: 'loans', title: 'Loans & Advances', key: 'loans' },
        { id: 'equity', title: 'Shareholders\' Equity', key: 'totalEquity' },
      ]},
    ],
  },

  Telecoms: {
    label: 'Telecoms',
    statsRows: [
      { title: 'Revenue', rows: [
        { label: 'Total Revenue', key: 'revenue', fmt: 'num' },
        { label: 'M-PESA Revenue', key: 'mpesa', fmt: 'num' },
        { label: 'YoY Revenue', key: '_growth_revenue', fmt: 'growth' },
      ]},
      { title: 'Profitability', rows: [
        { label: 'Profit Before Tax', key: 'pbt', fmt: 'num' },
        { label: 'Profit After Tax', key: 'pat', fmt: 'num' },
        { label: 'YoY PAT', key: '_growth_pat', fmt: 'growth' },
      ]},
      { title: 'Per Share', rows: [
        { label: 'EPS', key: 'eps', fmt: 'eps' },
        { label: 'DPS', key: 'dps', fmt: 'eps' },
        { label: 'Price', key: '_price', fmt: 'price' },
      ]},
      { title: 'Valuation', rows: [
        { label: 'P/E (approx)', key: '_pe', fmt: 'raw' },
        { label: 'Div. Yield', key: '_divyield', fmt: 'raw' },
        { label: 'Currency', key: '_currency', fmt: 'raw' },
      ]},
      { title: 'Data Coverage', rows: [
        { label: 'First Period', key: '_firstPeriod', fmt: 'raw' },
        { label: 'Last Period', key: '_lastPeriod', fmt: 'raw' },
        { label: 'Data Points', key: '_dataPoints', fmt: 'raw' },
      ]},
      { title: 'Financial Health', rows: [
        { label: 'ROE %', key: '_roe', fmt: 'raw' },
        { label: 'ROA %', key: '_roa', fmt: 'raw' },
        { label: 'Net Margin %', key: '_profitmargin', fmt: 'raw' },
        { label: 'Debt/Equity', key: '_debtequity', fmt: 'raw' },
      ]},
      { title: 'Growth Trends', rows: [
        { label: 'EPS 5Y CAGR', key: '_eps5yrgrowth', fmt: 'raw' },
        { label: 'Revenue 5Y CAGR', key: '_revenue5yrgrowth', fmt: 'raw' },
      ]},
    ],
    chartRows: [
      { label: 'Income Statement', charts: [
        { id: 'revenue', title: 'Total Revenue', key: 'revenue' },
        { id: 'mpesa', title: 'M-PESA Revenue', key: 'mpesa' },
        { id: 'pat', title: 'Profit After Tax', key: 'pat' },
        { id: 'eps', title: 'Earnings Per Share', key: 'eps', isCurrency: true },
        { id: 'dps', title: 'Dividends Per Share', key: 'dps', isCurrency: true },
      ]},
      { label: 'Balance Sheet & Cash Flow', charts: [
        { id: 'assets', title: 'Total Assets', key: 'totalAssets' },
        { id: 'equity', title: 'Shareholders\' Equity', key: 'totalEquity' },
      ]},
    ],
  },

  Insurance: {
    label: 'Insurance',
    statsRows: [
      { title: 'Underwriting', rows: [
        { label: 'Insurance Revenue', key: 'revenue', fmt: 'num' },
        { label: 'YoY Revenue', key: '_growth_revenue', fmt: 'growth' },
      ]},
      { title: 'Profitability', rows: [
        { label: 'Profit Before Tax', key: 'pbt', fmt: 'num' },
        { label: 'Profit After Tax', key: 'pat', fmt: 'num' },
        { label: 'YoY PAT', key: '_growth_pat', fmt: 'growth' },
      ]},
      { title: 'Per Share', rows: [
        { label: 'EPS', key: 'eps', fmt: 'eps' },
        { label: 'DPS', key: 'dps', fmt: 'eps' },
        { label: 'Price', key: '_price', fmt: 'price' },
      ]},
      { title: 'Valuation', rows: [
        { label: 'P/E (approx)', key: '_pe', fmt: 'raw' },
        { label: 'Div. Yield', key: '_divyield', fmt: 'raw' },
        { label: 'Currency', key: '_currency', fmt: 'raw' },
      ]},
      { title: 'Balance Sheet', rows: [
        { label: 'Total Assets', key: 'totalAssets', fmt: 'num' },
        { label: 'Total Equity', key: 'totalEquity', fmt: 'num' },
      ]},
      { title: 'Financial Health', rows: [
        { label: 'ROE %', key: '_roe', fmt: 'raw' },
        { label: 'ROA %', key: '_roa', fmt: 'raw' },
        { label: 'Net Margin %', key: '_profitmargin', fmt: 'raw' },
        { label: 'Debt/Equity', key: '_debtequity', fmt: 'raw' },
      ]},
      { title: 'Growth Trends', rows: [
        { label: 'EPS 5Y CAGR', key: '_eps5yrgrowth', fmt: 'raw' },
        { label: 'Revenue 5Y CAGR', key: '_revenue5yrgrowth', fmt: 'raw' },
      ]},
    ],
    chartRows: [
      { label: 'Income Statement', charts: [
        { id: 'revenue', title: 'Insurance Revenue / GWP', key: 'revenue' },
        { id: 'pat', title: 'Profit After Tax', key: 'pat' },
        { id: 'eps', title: 'Earnings Per Share', key: 'eps', isCurrency: true },
        { id: 'dps', title: 'Dividends Per Share', key: 'dps', isCurrency: true },
      ]},
      { label: 'Balance Sheet', charts: [
        { id: 'assets', title: 'Total Assets', key: 'totalAssets' },
        { id: 'equity', title: 'Shareholders\' Equity', key: 'totalEquity' },
      ]},
    ],
  },

  FMCG: {
    label: 'Consumer Goods',
    statsRows: [
      { title: 'Revenue', rows: [
        { label: 'Revenue', key: 'revenue', fmt: 'num' },
        { label: 'YoY Revenue', key: '_growth_revenue', fmt: 'growth' },
      ]},
      { title: 'Profitability', rows: [
        { label: 'Profit Before Tax', key: 'pbt', fmt: 'num' },
        { label: 'Profit After Tax', key: 'pat', fmt: 'num' },
        { label: 'YoY PAT', key: '_growth_pat', fmt: 'growth' },
      ]},
      { title: 'Per Share', rows: [
        { label: 'EPS', key: 'eps', fmt: 'eps' },
        { label: 'DPS', key: 'dps', fmt: 'eps' },
        { label: 'Price', key: '_price', fmt: 'price' },
      ]},
      { title: 'Valuation', rows: [
        { label: 'P/E (approx)', key: '_pe', fmt: 'raw' },
        { label: 'Div. Yield', key: '_divyield', fmt: 'raw' },
        { label: 'Currency', key: '_currency', fmt: 'raw' },
      ]},
      { title: 'Balance Sheet', rows: [
        { label: 'Total Assets', key: 'totalAssets', fmt: 'num' },
        { label: 'Total Equity', key: 'totalEquity', fmt: 'num' },
      ]},
    ],
    chartRows: [
      { label: 'Income Statement', charts: [
        { id: 'revenue', title: 'Revenue', key: 'revenue' },
        { id: 'pat', title: 'Profit After Tax', key: 'pat' },
        { id: 'eps', title: 'Earnings Per Share', key: 'eps', isCurrency: true },
        { id: 'dps', title: 'Dividends Per Share', key: 'dps', isCurrency: true },
      ]},
      { label: 'Balance Sheet', charts: [
        { id: 'assets', title: 'Total Assets', key: 'totalAssets' },
        { id: 'equity', title: 'Shareholders\' Equity', key: 'totalEquity' },
      ]},
    ],
  },

  Energy: {
    label: 'Energy & Utilities',
    statsRows: [
      { title: 'Revenue', rows: [
        { label: 'Revenue', key: 'revenue', fmt: 'num' },
        { label: 'YoY Revenue', key: '_growth_revenue', fmt: 'growth' },
      ]},
      { title: 'Profitability', rows: [
        { label: 'Profit After Tax', key: 'pat', fmt: 'num' },
        { label: 'YoY PAT', key: '_growth_pat', fmt: 'growth' },
      ]},
      { title: 'Per Share', rows: [
        { label: 'EPS', key: 'eps', fmt: 'eps' },
        { label: 'DPS', key: 'dps', fmt: 'eps' },
        { label: 'Price', key: '_price', fmt: 'price' },
      ]},
      { title: 'Valuation', rows: [
        { label: 'P/E (approx)', key: '_pe', fmt: 'raw' },
        { label: 'Div. Yield', key: '_divyield', fmt: 'raw' },
        { label: 'Currency', key: '_currency', fmt: 'raw' },
      ]},
      { title: 'Balance Sheet', rows: [
        { label: 'Total Assets', key: 'totalAssets', fmt: 'num' },
        { label: 'Total Equity', key: 'totalEquity', fmt: 'num' },
      ]},
    ],
    chartRows: [
      { label: 'Income Statement', charts: [
        { id: 'revenue', title: 'Revenue', key: 'revenue' },
        { id: 'pat', title: 'Profit After Tax', key: 'pat' },
        { id: 'eps', title: 'Earnings Per Share', key: 'eps', isCurrency: true },
        { id: 'dps', title: 'Dividends Per Share', key: 'dps', isCurrency: true },
      ]},
      { label: 'Balance Sheet', charts: [
        { id: 'assets', title: 'Total Assets', key: 'totalAssets' },
        { id: 'equity', title: 'Shareholders\' Equity', key: 'totalEquity' },
      ]},
    ],
  },
};

// Default template for sectors not explicitly defined
const DEFAULT_TEMPLATE = {
  label: 'General',
  statsRows: [
    { title: 'Revenue', rows: [
      { label: 'Revenue', key: 'revenue', fmt: 'num' },
      { label: 'YoY Revenue', key: '_growth_revenue', fmt: 'growth' },
    ]},
    { title: 'Profitability', rows: [
      { label: 'Profit After Tax', key: 'pat', fmt: 'num' },
      { label: 'YoY PAT', key: '_growth_pat', fmt: 'growth' },
    ]},
    { title: 'Per Share', rows: [
      { label: 'EPS', key: 'eps', fmt: 'eps' },
      { label: 'DPS', key: 'dps', fmt: 'eps' },
      { label: 'Price', key: '_price', fmt: 'price' },
    ]},
    { title: 'Valuation', rows: [
      { label: 'P/E (approx)', key: '_pe', fmt: 'raw' },
      { label: 'Div. Yield', key: '_divyield', fmt: 'raw' },
      { label: 'Currency', key: '_currency', fmt: 'raw' },
    ]},
    { title: 'Balance Sheet', rows: [
      { label: 'Total Assets', key: 'totalAssets', fmt: 'num' },
      { label: 'Total Equity', key: 'totalEquity', fmt: 'num' },
    ]},
  ],
  chartRows: [
    { label: 'Income Statement', charts: [
      { id: 'revenue', title: 'Revenue', key: 'revenue' },
      { id: 'pat', title: 'Profit After Tax', key: 'pat' },
      { id: 'eps', title: 'Earnings Per Share', key: 'eps', isCurrency: true },
      { id: 'dps', title: 'Dividends Per Share', key: 'dps', isCurrency: true },
    ]},
    { label: 'Balance Sheet', charts: [
      { id: 'assets', title: 'Total Assets', key: 'totalAssets' },
      { id: 'equity', title: 'Shareholders\' Equity', key: 'totalEquity' },
    ]},
  ],
};

function getTemplate(sector) {
  return SECTOR_TEMPLATES[sector] || DEFAULT_TEMPLATE;
}

// ---- Financial Ratio Calculations ----
// Helper functions for computing financial ratios from company data

function calcROE(latest, prev) {
  // Return on Equity = Net Income / Shareholders Equity
  if (!latest || !latest.pat || !latest.totalEquity || latest.totalEquity <= 0) return null;
  return ((latest.pat / latest.totalEquity) * 100).toFixed(1);
}

function calcROA(latest, prev) {
  // Return on Assets = Net Income / Total Assets
  if (!latest || !latest.pat || !latest.totalAssets || latest.totalAssets <= 0) return null;
  return ((latest.pat / latest.totalAssets) * 100).toFixed(1);
}

function calcDebtEquity(latest, prev) {
  // Debt-to-Equity Ratio = Total Debt / Shareholders Equity
  // Approximation: Total Liabilities = Total Assets - Shareholders Equity
  if (!latest || !latest.totalAssets || !latest.totalEquity || latest.totalEquity <= 0) return null;
  const debt = latest.totalAssets - latest.totalEquity;
  return (debt / latest.totalEquity).toFixed(2);
}

function calcAssetTurnover(latest, prev) {
  // Asset Turnover = Revenue / Total Assets
  if (!latest || !latest.revenue || !latest.totalAssets || latest.totalAssets <= 0) return null;
  return (latest.revenue / latest.totalAssets).toFixed(2);
}

function calcProfitMargin(latest, prev) {
  // Net Profit Margin = Net Income / Revenue
  if (!latest || !latest.pat || !latest.revenue || latest.revenue <= 0) return null;
  return ((latest.pat / latest.revenue) * 100).toFixed(1);
}

function calcGrossMargin(latest, prev) {
  // Gross Margin = (Revenue - COGS) / Revenue
  // Not all companies have COGS data, so this returns null if unavailable
  if (!latest || !latest.revenue || latest.revenue <= 0 || !latest.cogs) return null;
  return (((latest.revenue - latest.cogs) / latest.revenue) * 100).toFixed(1);
}

function calcCAGR(dataArray, periods) {
  // Compound Annual Growth Rate
  // dataArray: array of numeric values in chronological order (oldest first)
  // periods: number of years between first and last value
  if (!dataArray || dataArray.length < 2 || periods <= 0) return null;

  const first = dataArray[0];
  const last = dataArray[dataArray.length - 1];

  if (first <= 0 || last <= 0 || first === null || last === null) return null;

  const cagr = (Math.pow(last / first, 1 / periods) - 1) * 100;
  return cagr.toFixed(1);
}

function calcEPS5YrGrowth(company) {
  // 5-year EPS CAGR
  if (!company.annuals || company.annuals.length < 2) return null;
  const eps = company.annuals.slice(0, Math.min(5, company.annuals.length))
    .reverse() // newest first, reverse to oldest first
    .map(d => d.eps)
    .filter(e => e && e > 0);

  if (eps.length < 2) return null;
  const years = eps.length - 1;
  return calcCAGR(eps, years);
}

function calcRevenue5YrGrowth(company) {
  // 5-year Revenue CAGR
  if (!company.annuals || company.annuals.length < 2) return null;
  const rev = company.annuals.slice(0, Math.min(5, company.annuals.length))
    .reverse()
    .map(d => d.revenue)
    .filter(r => r && r > 0);

  if (rev.length < 2) return null;
  const years = rev.length - 1;
  return calcCAGR(rev, years);
}

function calcCurrentRatio(latest, prev) {
  // Current Ratio = Current Assets / Current Liabilities
  // Not all companies have this data, so returns null if unavailable
  if (!latest || !latest.currentAssets || !latest.currentLiabilities || latest.currentLiabilities <= 0) return null;
  return (latest.currentAssets / latest.currentLiabilities).toFixed(2);
}

// ---- Load Prices ----
// prices.json format: { "TICKER": { name, sector, prices: [[timestamp_ms, close], ...] } }
async function loadPrices() {
  try {
    const resp = await fetch('prices.json?v=4');
    if (resp.ok) NSE_PRICES = await resp.json();
  } catch (e) {
    NSE_PRICES = {};
  }

  for (const [ticker, pd] of Object.entries(NSE_PRICES)) {
    const prices = pd.prices;
    if (!prices || prices.length < 2) continue;

    const lastPrice = prices[prices.length - 1][1];
    const prevPrice = prices[prices.length - 2][1];
    const change = lastPrice - prevPrice;
    const changePct = prevPrice ? (change / prevPrice) * 100 : 0;

    // 52-week high/low
    const oneYearAgo = Date.now() - 365 * 24 * 3600 * 1000;
    const recent = prices.filter(p => p[0] >= oneYearAgo);
    const hi52 = recent.length > 0 ? Math.max(...recent.map(p => p[1])) : lastPrice;
    const lo52 = recent.length > 0 ? Math.min(...recent.map(p => p[1])) : lastPrice;

    if (NSE_COMPANIES[ticker]) {
      // Stock has financial data — enrich it
      NSE_COMPANIES[ticker].latestPrice = lastPrice;
      NSE_COMPANIES[ticker].priceChange = change;
      NSE_COMPANIES[ticker].priceChangePct = changePct;
      NSE_COMPANIES[ticker].hi52 = hi52;
      NSE_COMPANIES[ticker].lo52 = lo52;
    } else {
      // Price-only stock — create lightweight entry
      NSE_COMPANIES[ticker] = {
        name: pd.name,
        ticker: ticker,
        exchange: 'NSE',
        sector: pd.sector || 'Other',
        logo: sectorEmoji(pd.sector),
        currency: 'KES',
        units: 'thousands',
        latestPrice: lastPrice,
        priceChange: change,
        priceChangePct: changePct,
        hi52: hi52,
        lo52: lo52,
        annuals: [],
        quarters: [],
        priceOnly: true,
      };
    }
  }
}

function sectorEmoji(sector) {
  const map = {
    'Banking': '🏦', 'Agricultural': '🌾', 'Insurance': '🛡️',
    'Manufacturing': '🏭', 'Automobiles and Accessories': '🚗',
    'Commercial and Services': '🏢', 'Construction and Allied': '🏗️',
    'Energy and Petroleum': '⚡', 'Investment': '📊',
    'Investment Services': '📊', 'Telecommunication and Technology': '📱',
  };
  return map[sector] || '📈';
}

// ---- Chart.js Global Defaults ----
Chart.defaults.color = '#707070';
Chart.defaults.borderColor = 'rgba(0,230,118,0.08)';
// ---- Theme-aware chart grid colour ----
function chartGridColor() {
  return document.body.classList.contains('light')
    ? 'rgba(0, 0, 0, 0.22)'
    : 'rgba(255, 255, 255, 0.08)';
}
Chart.defaults.font.family = "'Inter', 'Segoe UI', system-ui, sans-serif";
Chart.defaults.font.size = 11;

// ---- Formatters ----
function fmtNum(val, units) {
  if (val === null || val === undefined || isNaN(val)) return '\u2014';
  if (units === 'thousands') {
    // Raw values are in KES thousands, so 1e6 = 1B KES, 1e9 = 1T KES
    if (Math.abs(val) >= 1e9) return (val / 1e9).toFixed(1) + 'T';
    if (Math.abs(val) >= 1e6) return (val / 1e6).toFixed(1) + 'B';
    if (Math.abs(val) >= 1e3) return (val / 1e3).toFixed(0) + 'M';
    return val.toFixed(0) + 'K';
  }
  if (units === 'millions') {
    // Raw values are in KES millions, so 1e3 = 1B KES, 1e6 = 1T KES
    if (Math.abs(val) >= 1e6) return (val / 1e6).toFixed(1) + 'T';
    if (Math.abs(val) >= 1e3) return (val / 1e3).toFixed(1) + 'B';
    return val.toFixed(0) + 'M';
  }
  return val.toFixed(2);
}

function fmtEPS(val) {
  if (val === null || val === undefined) return '\u2014';
  return 'KES ' + val.toFixed(2);
}
function fmtPrice(val) {
  if (val === null || val === undefined || val === 0) return '\u2014';
  return 'KES ' + val.toFixed(2);
}
function fmtChange(change, changePct) {
  if (change === null || change === undefined) return '';
  const sign = change >= 0 ? '+' : '';
  const cls = change >= 0 ? 'positive' : 'negative';
  return '<span class="' + cls + '">' + sign + change.toFixed(2) + ' (' + sign + changePct.toFixed(2) + '%)</span>';
}

// ---- CAGR ----
function calcCAGR(data, periods) {
  if (!data || data.length < 2) return null;
  const latest = data[data.length - 1];
  const startIdx = Math.max(0, data.length - 1 - periods);
  const start = data[startIdx];
  if (start === null || start === undefined || start <= 0 || latest <= 0) return null;
  const n = data.length - 1 - startIdx;
  if (n === 0) return null;
  return (Math.pow(latest / start, 1 / n) - 1) * 100;
}

// ---- Bar Chart Creator ----
function makeBarChart(canvasId, labels, datasets, opts = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (chartInstances[canvasId]) chartInstances[canvasId].destroy();

  // Apply sharp corners to all bar datasets
  datasets = datasets.map(ds => ({ borderRadius: 2, borderSkipped: false, ...ds }));
  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111111',
          borderColor: 'rgba(255,255,255,0.05)',
          borderWidth: 1,
          padding: 12,
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 12 },
          cornerRadius: 10,
          callbacks: {
            label: (item) => {
              const val = item.raw;
              const formatted = opts.isCurrency ? fmtEPS(val) : fmtNum(val, opts.units);
              return ' ' + item.dataset.label + ': ' + formatted;
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#5a6a7e', font: { size: 10, weight: 500 } } },
        y: {
          grid: { color: chartGridColor(), drawTicks: false },
          border: { display: false },
          ticks: {
            color: '#5a6a7e', font: { size: 10 },
            callback: (v) => {
              const u = opts.units;
              if (opts.isCurrency) {
                // EPS/DPS — raw KES per share, no unit conversion
                return 'KES ' + v.toFixed(v >= 100 ? 0 : 2);
              }
              if (u === 'thousands') {
                // Values in KES thousands: 1e6 = 1B, 1e9 = 1T
                if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(0) + 'T';
                if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(0) + 'B';
                if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(0) + "M";
                return v + 'K';
              }
              if (u === 'millions') {
                // Values in KES millions: 1e3 = 1B, 1e6 = 1T
                if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(0) + 'T';
                if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(0) + 'B';
                return v.toFixed(0) + 'M';
              }
              // Fallback (raw KES or ratio)
              if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(0) + 'B';
              if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(0) + 'M';
              if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(0) + 'K';
              return v;
            }
          }
        }
      }
    }
  });

  const card = ctx.closest('.chart-card');
  let gc = card.querySelector('.growth-pills');
  if (opts.showGrowth && datasets[0].data.length >= 2) {
    if (!gc) { gc = document.createElement('div'); gc.className = 'growth-pills'; card.appendChild(gc); }
    const data = datasets[0].data.filter(v => v !== null && v !== undefined);
    const c1 = calcCAGR(data, 1), c3 = calcCAGR(data, 3), c5 = calcCAGR(data, 5);
    const pill = (l, v) => '<div class="growth-pill"><span>' + l + ':</span><span class="' + (v >= 0 ? 'positive' : 'negative') + '">' + (v >= 0 ? '+' : '') + v.toFixed(1) + '%</span></div>';
    let h = '';
    if (c1 !== null) h += pill('1Y', c1);
    if (c3 !== null) h += pill('3Y', c3);
    if (c5 !== null) h += pill('5Y', c5);
    gc.innerHTML = h;
  } else if (gc) gc.innerHTML = '';
}

function barColors(n) {
  return Array.from({ length: n }, (_, i) => i === n - 1 ? '#00e676' : 'rgba(0,230,118,0.4)');
}

// ---- Build Dynamic Chart Grid ----
function buildChartGrid(template) {
  const container = document.getElementById('sector-charts-container');
  container.innerHTML = '';

  // Destroy existing chart instances
  for (const key in chartInstances) {
    if (chartInstances[key]) chartInstances[key].destroy();
  }
  chartInstances = {};

  template.chartRows.forEach((row, i) => {
    // Section header
    if (i > 0) {
      const controls = document.createElement('div');
      controls.className = 'chart-controls';
      controls.style.marginTop = '1.5rem';
      controls.innerHTML = '<span class="chart-section-label">' + row.label + '</span>';
      container.appendChild(controls);
    }

    // Charts grid
    const grid = document.createElement('div');
    grid.className = 'charts-grid';
    grid.id = 'charts-row' + (i + 1);

    row.charts.forEach(chart => {
      const card = document.createElement('div');
      card.className = 'chart-card';
      card.id = 'card-' + chart.id;
      card.innerHTML =
        '<div class="chart-card-header">' +
        '  <span class="chart-title">' + chart.title + '</span>' +
        '  <span class="chart-expand">\u2922</span>' +
        '</div>' +
        '<div class="chart-wrap"><canvas id="chart-' + chart.id + '"></canvas></div>';
      grid.appendChild(card);
    });

    container.appendChild(grid);
  });
}

// ---- Price Chart ----
let _priceChartInstance = null;
let _currentRange = '1Y';

// Aggregate weekly close prices into bi-weekly or monthly OHLC candles.
// NSE data is one close per week, so we need to group multiple weeks together
// to get meaningful open/high/low/close spread on each candle.
function aggregateToCandles(prices, range) {
  // Short ranges: group every 2 weeks → ~2–6 candles
  // Long ranges: group by calendar month → 6–60 candles
  const useBiWeekly = ['1M', '3M'].includes(range);
  const buckets = new Map();

  prices.forEach(([ts, close]) => {
    const d = new Date(ts);
    let key;
    if (useBiWeekly) {
      // Week-of-year floored to nearest even number
      const startOfYear = new Date(d.getFullYear(), 0, 1);
      const weekOfYear = Math.floor((d - startOfYear) / (7 * 24 * 3600 * 1000));
      key = d.getFullYear() * 1000 + Math.floor(weekOfYear / 2);
    } else {
      // Calendar month
      key = d.getFullYear() * 100 + d.getMonth();
    }
    if (!buckets.has(key)) buckets.set(key, { lastTs: ts, closes: [] });
    const b = buckets.get(key);
    b.closes.push(close);
    b.lastTs = ts;
  });

  return Array.from(buckets.values()).map(b => ({
    x: b.lastTs,
    o: b.closes[0],
    h: Math.max(...b.closes),
    l: Math.min(...b.closes),
    c: b.closes[b.closes.length - 1],
  }));
}

function setPriceChartType(type) {
  _priceChartType = type;
  document.getElementById('btn-chart-line')?.classList.toggle('active', type === 'line');
  document.getElementById('btn-chart-candle')?.classList.toggle('active', type === 'candle');
  if (activeCompany) renderPriceChart(activeCompany.ticker, _currentRange);
}

function renderPriceChart(ticker, range) {
  range = range || _currentRange;
  _currentRange = range;

  const pd = NSE_PRICES[ticker];
  if (!pd || !pd.prices || pd.prices.length < 2) {
    document.getElementById('price-chart-section').classList.add('hidden');
    return;
  }

  document.getElementById('price-chart-section').classList.remove('hidden');

  const allPrices = pd.prices;
  const now = allPrices[allPrices.length - 1][0];

  // Range filtering
  const rangeMs = {
    '1M': 30 * 24 * 3600 * 1000,
    '3M': 91 * 24 * 3600 * 1000,
    '6M': 182 * 24 * 3600 * 1000,
    '1Y': 365 * 24 * 3600 * 1000,
    '3Y': 3 * 365 * 24 * 3600 * 1000,
    '5Y': 5 * 365 * 24 * 3600 * 1000,
    'ALL': Infinity,
  };

  const cutoff = range === 'ALL' ? 0 : now - rangeMs[range];
  const filtered = allPrices.filter(p => p[0] >= cutoff);
  if (filtered.length < 2) return;

  const firstPrice = filtered[0][1];
  const lastPrice = filtered[filtered.length - 1][1];
  const isUp = lastPrice >= firstPrice;

  // Update range button UI
  document.querySelectorAll('.range-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.range === range);
  });

  // Update price summary
  const co = NSE_COMPANIES[ticker];
  if (co) {
    document.getElementById('price-value').textContent = 'KES ' + lastPrice.toFixed(2);
    const change = lastPrice - firstPrice;
    const changePct = firstPrice ? (change / firstPrice) * 100 : 0;
    const sign = change >= 0 ? '+' : '';
    const cls = change >= 0 ? 'positive' : 'negative';
    document.getElementById('price-change').className = 'price-change ' + cls;
    document.getElementById('price-change').textContent = sign + change.toFixed(2) + ' (' + sign + changePct.toFixed(1) + '%)';

    document.getElementById('price-52hi').textContent = co.hi52 ? 'KES ' + co.hi52.toFixed(2) : '—';
    document.getElementById('price-52lo').textContent = co.lo52 ? 'KES ' + co.lo52.toFixed(2) : '—';
    document.getElementById('price-vol').textContent = '—';
  }

  const ctx = document.getElementById('chart-price');
  if (_priceChartInstance) _priceChartInstance.destroy();

  // Shared scale config
  const sharedScales = {
    x: {
      type: 'time',
      time: {
        tooltipFormat: 'dd MMM yyyy',
        displayFormats: { day: 'dd MMM', week: 'dd MMM', month: 'MMM yy', quarter: 'MMM yy', year: 'yyyy' }
      },
      grid: { display: false },
      ticks: { color: '#5a6a7e', font: { size: 10, weight: 500 }, maxTicksLimit: 8 },
      border: { display: false },
    },
    y: {
      grid: { color: chartGridColor(), drawTicks: false },
      border: { display: false },
      ticks: { color: '#5a6a7e', font: { size: 10 }, callback: (v) => v.toFixed(v >= 100 ? 0 : 2) },
    }
  };

  const sharedTooltip = {
    backgroundColor: '#111111',
    borderColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    padding: 12,
    titleFont: { size: 12, weight: 'bold' },
    bodyFont: { size: 13 },
    cornerRadius: 10,
    displayColors: false,
  };

  if (_priceChartType === 'candle') {
    // Build OHLC candles from daily closes
    const candles = aggregateToCandles(filtered, range);

    _priceChartInstance = new Chart(ctx, {
      type: 'candlestick',
      data: {
        datasets: [{
          label: ticker,
          data: candles,
          color: { up: '#00e676', down: '#ff4444', unchanged: '#888888' },
          borderColor: { up: '#00c060', down: '#cc3333', unchanged: '#666666' },
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            ...sharedTooltip,
            callbacks: {
              title: (items) => {
                if (!items.length) return '';
                return new Date(items[0].parsed.x).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
              },
              label: (item) => {
                const raw = item.raw;
                return [
                  'O: KES ' + raw.o.toFixed(2),
                  'H: KES ' + raw.h.toFixed(2),
                  'L: KES ' + raw.l.toFixed(2),
                  'C: KES ' + raw.c.toFixed(2),
                ];
              }
            }
          }
        },
        scales: sharedScales,
      }
    });

  } else {
    // Line chart (default)
    const chartData = filtered.map(p => ({ x: p[0], y: p[1] }));

    const gradient = ctx.getContext('2d');
    const gradientFill = gradient.createLinearGradient(0, 0, 0, 320);
    if (isUp) {
      gradientFill.addColorStop(0, 'rgba(0, 230, 118, 0.2)');
      gradientFill.addColorStop(1, 'rgba(0, 230, 118, 0.0)');
    } else {
      gradientFill.addColorStop(0, 'rgba(255, 68, 68, 0.2)');
      gradientFill.addColorStop(1, 'rgba(255, 68, 68, 0.0)');
    }

    _priceChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [{
          data: chartData,
          borderColor: isUp ? '#00e676' : '#ff4444',
          borderWidth: 2,
          fill: true,
          backgroundColor: gradientFill,
          pointRadius: 0,
          pointHitRadius: 8,
          tension: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            ...sharedTooltip,
            callbacks: {
              title: (items) => {
                if (!items.length) return '';
                return new Date(items[0].parsed.x).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
              },
              label: (item) => 'KES ' + item.parsed.y.toFixed(2),
            }
          }
        },
        scales: sharedScales,
      }
    });
  }
}

function timeAgo(dateStr) {
  const d = new Date(dateStr);
  if (isNaN(d)) return '';
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
  return Math.floor(diff / 86400) + 'd ago';
}

function formatStaticDate(dateStr) {
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const parts = dateStr.split('-');
  if (parts.length !== 3) return dateStr;
  return parts[2] + ' ' + months[parseInt(parts[1], 10) - 1] + ' ' + parts[0];
}

async function fetchNews(ticker, companyName) {
  const grid = document.getElementById('news-grid');
  if (!grid) return;

  // Show static news immediately if available
  const co = NSE_COMPANIES[ticker];
  const staticNews = co && co.staticNews && co.staticNews.length ? co.staticNews : null;

  if (staticNews) {
    grid.innerHTML = staticNews.map(a => {
      const href = a.url ? 'href="' + a.url + '" target="_blank" rel="noopener"' : 'href="#" onclick="return false"';
      return '<a class="news-card static" ' + href + '><div class="news-card-source"><span>' + a.source + '</span><span class="news-date"> · ' + formatStaticDate(a.date) + '</span></div><div class="news-card-title">' + a.title + '</div></a>';
    }).join('');
  } else {
    grid.innerHTML = '<div class="news-loading">Loading news…</div>';
  }

  // Also fetch live RSS feeds and append any fresh articles found
  const feeds = [
    { url: 'https://businessdailyafrica.com/rss/39546-business-news', name: 'Business Daily', domain: 'businessdailyafrica.com' },
    { url: 'https://www.standardmedia.co.ke/rss/business.php', name: 'The Standard', domain: 'standardmedia.co.ke' },
    { url: 'https://www.capitalfm.co.ke/business/feed/', name: 'Capital FM', domain: 'capitalfm.co.ke' },
  ];
  const proxy = 'https://api.rss2json.com/v1/api.json?rss_url=';
  const keywords = [ticker.toLowerCase(), companyName.toLowerCase().split(' ').slice(0, 2).join(' ')];
  const results = await Promise.allSettled(
    feeds.map(f => fetch(proxy + encodeURIComponent(f.url)).then(r => r.json()).then(data => ({ feed: f, items: (data.items || []) })))
  );
  let articles = [];
  results.forEach(r => {
    if (r.status !== 'fulfilled') return;
    const { feed, items } = r.value;
    items.forEach(item => {
      const haystack = ((item.title || '') + ' ' + (item.description || '')).toLowerCase();
      if (keywords.some(k => k.length > 2 && haystack.includes(k))) articles.push({ ...item, _feed: feed });
    });
  });
  articles.sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate));
  articles = articles.slice(0, 5);
  if (articles.length === 0) {
    if (!staticNews) {
      grid.innerHTML = '<div class="news-empty">No recent news found for <strong>' + ticker + '</strong> &nbsp;·&nbsp; <a href="https://businessdailyafrica.com/search?q=' + encodeURIComponent(companyName) + '" target="_blank" rel="noopener">Search Business Daily ↗</a></div>';
    }
    return;
  }
  const dynamicHtml = articles.map(a => {
    const fav = 'https://www.google.com/s2/favicons?domain=' + a._feed.domain + '&sz=16';
    return '<a class="news-card" href="' + a.link + '" target="_blank" rel="noopener"><div class="news-card-source"><img class="news-favicon" src="' + fav + '" alt=""><span>' + a._feed.name + '</span><span class="news-date"> · ' + timeAgo(a.pubDate) + '</span></div><div class="news-card-title">' + a.title + '</div></a>';
  }).join('');
  if (staticNews) {
    grid.innerHTML += dynamicHtml;
  } else {
    grid.innerHTML = dynamicHtml;
  }
}

// ---- Load Company (shared core) ----
function loadCompanyByTicker(ticker) {
  if (!ticker || !NSE_COMPANIES[ticker]) return;
  const co = NSE_COMPANIES[ticker];
  activeCompany = co;
  _currentCompany = co;
  _currentPeriod = 'annual';

  document.getElementById('dashboard').classList.remove('hidden');
  document.getElementById('empty-state').classList.add('hidden');
  document.getElementById('market-summary').classList.add('hidden');
  const infoRow = document.getElementById('info-row');
  if (infoRow) infoRow.classList.remove('hidden');
  document.getElementById('sector-overview').classList.add('hidden');
  document.getElementById('btn-companies').classList.add('active');
  document.getElementById('btn-sectors').classList.remove('active');
  _currentView = 'companies';
  const bc = document.getElementById('breadcrumb-company');
  if (bc) bc.textContent = co.ticker + ' | NSE';
  document.getElementById('company-logo').textContent = co.logo || '📈';
  document.getElementById('company-name').textContent = co.name;
  const descEl = document.getElementById('company-desc-text');
  if (descEl) descEl.textContent = co.description || 'No description available.';
  fetchNews(co.ticker, co.name || co.ticker);
  document.getElementById('company-meta').textContent = co.ticker + ' | ' + co.exchange + ' \u00B7 ' + co.sector;
  document.getElementById('company-price').textContent = fmtPrice(co.latestPrice);

  const changeEl = document.getElementById('company-price-change');
  if (co.priceChange !== undefined && co.priceChange !== null) {
    changeEl.innerHTML = fmtChange(co.priceChange, co.priceChangePct);
  } else {
    changeEl.innerHTML = '';
  }

  // Always render price chart
  _currentRange = '1Y';
  renderPriceChart(ticker, '1Y');

  // Check if stock has financial data
  const hasFinancials = co.annuals && co.annuals.length > 0;
  const financialSections = ['stats-grid', 'sector-charts-container', 'valuation-panel'];
  const chartControls = document.querySelector('.chart-controls');

  if (hasFinancials) {
    document.getElementById('toggle-annual').classList.add('active');
    document.getElementById('toggle-quarterly').classList.remove('active');
    if (chartControls) chartControls.style.display = '';
    financialSections.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.remove('hidden');
    });

    const latest = co.latestPeriod || co.annuals[0];
    const latestLabel = latest.period || latest.year;
    document.getElementById('company-eps-pill').textContent = 'EPS (' + latestLabel + '): ' + fmtEPS(latest.eps);
    document.getElementById('company-latest-year').textContent = 'Units: KES ' + co.units + ' \u00B7 Last period: ' + latestLabel;

    const template = getTemplate(co.sector);
    renderStatsGrid(co, template);
    buildChartGrid(template);
    renderCharts(co, 'annual', template);
    renderValuation(co);
  } else {
    if (chartControls) chartControls.style.display = 'none';
    financialSections.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.add('hidden');
    });
    document.getElementById('company-eps-pill').textContent = 'Price only — no financial data yet';
    document.getElementById('company-latest-year').textContent = co.sector;
  }
}

// Legacy entry point (kept for any remaining callers)
function loadCompany() {
  const sel = document.getElementById('company-select');
  const ticker = sel ? sel.value : (document.getElementById('company-search-input') || {}).value;
  loadCompanyByTicker((ticker || '').trim().toUpperCase());
}

// ---- Stats Grid ----
function renderStatsGrid(co, template) {
  const latest = co.latestPeriod || (co.annuals && co.annuals.length > 0 ? co.annuals[0] : {});
  const latestLabel = latest.period || latest.year || '\u2014';
  const annualRows = co.annuals || [];
  const prev = annualRows.length >= 2 ? annualRows[1] : null;

  function growthLabel(curr, prev) {
    if (curr == null || prev == null || prev === 0) return { text: '\u2014', cls: '' };
    const g = ((curr - prev) / Math.abs(prev)) * 100;
    return { text: (g >= 0 ? '+' : '') + g.toFixed(1) + '%', cls: g >= 0 ? 'up' : 'down' };
  }

  // Build computed values map
  const computed = {};
  computed['_growth_revenue'] = growthLabel(latest.revenue, prev?.revenue);
  computed['_growth_pat'] = growthLabel(latest.pat, prev?.pat);
  computed['_growth_nii'] = growthLabel(latest.nii, prev?.nii);
  computed['_price'] = co.latestPrice;
  computed['_pe'] = (latest.eps && co.latestPrice) ? (co.latestPrice / latest.eps).toFixed(1) + 'x' : '\u2014';
  computed['_divyield'] = (latest.dps && co.latestPrice) ? ((latest.dps / co.latestPrice) * 100).toFixed(1) + '%' : '\u2014';
  computed['_pb'] = (latest.totalEquity && co.latestPrice) ? '---' : '\u2014';
  computed['_currency'] = co.currency || 'KES';
  computed['_firstPeriod'] = annualRows.length > 0 ? (annualRows[annualRows.length - 1].period || annualRows[annualRows.length - 1].year || '\u2014') : '\u2014';
  computed['_lastPeriod'] = latestLabel;
  computed['_dataPoints'] = String(annualRows.length);

  // Financial Ratios (calculated via utility functions)
  computed['_roe'] = calcROE(latest, prev);
  computed['_roa'] = calcROA(latest, prev);
  computed['_debtequity'] = calcDebtEquity(latest, prev);
  computed['_assetturnover'] = calcAssetTurnover(latest, prev);
  computed['_profitmargin'] = calcProfitMargin(latest, prev);
  computed['_grossmargin'] = calcGrossMargin(latest, prev);
  computed['_currentratio'] = calcCurrentRatio(latest, prev);
  computed['_eps5yrgrowth'] = calcEPS5YrGrowth(co);
  computed['_revenue5yrgrowth'] = calcRevenue5YrGrowth(co);

  function getVal(key) {
    if (key.startsWith('_growth_')) {
      const g = computed[key];
      return { text: g.text, cls: g.cls };
    }
    if (key.startsWith('_')) {
      const v = computed[key];
      if (v === null || v === undefined) return { text: '\u2014', cls: '' };

      // Format specific ratio types
      if (key.includes('roe') || key.includes('roa') || key.includes('margin') || key.includes('growth')) {
        // These are percentages
        const numVal = typeof v === 'number' ? v : parseFloat(v);
        if (isNaN(numVal)) return { text: '\u2014', cls: '' };
        const cls = numVal >= 0 ? 'positive' : 'negative';
        return { text: (numVal >= 0 ? '+' : '') + numVal.toFixed(1) + '%', cls };
      }
      if (key.includes('debtequity') || key.includes('assetturnover') || key.includes('currentratio')) {
        // These are pure ratios
        return { text: String(v), cls: '' };
      }
      // Default formatting
      return { text: typeof v === 'number' ? fmtPrice(v) : String(v || '\u2014'), cls: '' };
    }
    return null; // Will be formatted by fmt
  }

  const sections = template.statsRows.map(sec => {
    const rows = sec.rows.map(r => {
      let val, cls = '';

      if (r.key.startsWith('_')) {
        const cv = getVal(r.key);
        val = cv.text;
        cls = cv.cls;
      } else if (r.fmt === 'num') {
        val = fmtNum(latest[r.key], co.units);
      } else if (r.fmt === 'eps' || r.fmt === 'price') {
        val = fmtEPS(latest[r.key]);
      } else {
        val = latest[r.key] != null ? String(latest[r.key]) : '\u2014';
      }

      return { label: r.label, val, cls };
    });

    return { title: sec.title, rows };
  });

  // Group sections into pairs for carousel
  const slides = [];
  for (let i = 0; i < sections.length; i += 2) {
    slides.push(sections.slice(i, i + 2));
  }

  function buildSection(sec) {
    return '<div class="stat-section"><div class="stat-section-title">' + sec.title + '</div>' +
      sec.rows.map(r => '<div class="stat-row"><span class="stat-label">' + r.label + '</span><span class="stat-val ' + (r.cls || '') + '">' + r.val + '</span></div>').join('') +
      '</div>';
  }

  const totalSlides = slides.length;
  document.getElementById('stats-grid').innerHTML =
    '<div class="stats-carousel-wrap">' +
      '<button class="stats-nav stats-nav-prev" onclick="statsCarouselNav(-1)" aria-label="Previous">&#8249;</button>' +
      '<div class="stats-carousel" id="stats-carousel">' +
        slides.map((pair, idx) =>
          '<div class="stats-slide" data-slide="' + idx + '">' +
            pair.map(buildSection).join('') +
          '</div>'
        ).join('') +
      '</div>' +
      '<button class="stats-nav stats-nav-next" onclick="statsCarouselNav(1)" aria-label="Next">&#8250;</button>' +
    '</div>' +
    '<div class="stats-dots">' +
      slides.map((_, i) => '<span class="stats-dot' + (i === 0 ? ' active' : '') + '" onclick="statsCarouselGoTo(' + i + ')"></span>').join('') +
    '</div>';
}

let _statsSlide = 0;
function statsCarouselNav(dir) {
  const carousel = document.getElementById('stats-carousel');
  if (!carousel) return;
  const total = carousel.querySelectorAll('.stats-slide').length;
  _statsSlide = (_statsSlide + dir + total) % total;
  statsCarouselGoTo(_statsSlide);
}
function statsCarouselGoTo(idx) {
  const carousel = document.getElementById('stats-carousel');
  if (!carousel) return;
  _statsSlide = idx;
  const slide = carousel.querySelectorAll('.stats-slide')[idx];
  if (slide) slide.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
  document.querySelectorAll('.stats-dot').forEach((d, i) => d.classList.toggle('active', i === idx));
}

// ---- Render Charts ----
function renderCharts(co, period, template) {
  template = template || getTemplate(co.sector);
  period = period || 'annual';
  const hasQ = co.quarters && co.quarters.length > 0;
  let dp = (period === 'quarterly' && hasQ) ? [...co.quarters] : [...(co.annuals || [])];
  dp.sort((a, b) => a.year !== b.year ? a.year - b.year : (a.period || '').localeCompare(b.period || ''));

  const labels = dp.map(d => d.period || d.year);
  const n = dp.length;
  const colors = barColors(n);
  const opts = { showGrowth: period === 'annual', units: co.units };

  template.chartRows.forEach(row => {
    row.charts.forEach(chart => {
      const canvasId = 'chart-' + chart.id;
      makeBarChart(canvasId, labels,
        [{ label: chart.title, data: dp.map(d => d[chart.key]), backgroundColor: colors, borderRadius: 2 }],
        { ...opts, isCurrency: chart.isCurrency || false }
      );
    });
  });
}

// ---- Period Toggle ----
let _currentCompany = null;
let _currentPeriod = 'annual';

function setPeriod(period) {
  if (!_currentCompany) return;
  if (period === 'quarterly' && (!_currentCompany.quarters || _currentCompany.quarters.length === 0)) {
    period = 'annual';
    const btn = document.getElementById('toggle-quarterly');
    btn.textContent = 'No quarterly data';
    setTimeout(() => { btn.textContent = 'Quarterly'; }, 1500);
  }
  _currentPeriod = period;
  document.getElementById('toggle-annual').classList.toggle('active', period === 'annual');
  document.getElementById('toggle-quarterly').classList.toggle('active', period === 'quarterly');
  renderCharts(_currentCompany, period);
}

// ---- Chart Modal (Expand) ----
let _modalChartInstance = null;

function openChartModal(chartTitle, chartConfig, metadata) {
  const modal = document.getElementById('chart-modal');
  const titleEl = document.querySelector('.chart-modal-title');
  const metaEl = document.getElementById('chart-modal-meta');
  const canvas = document.getElementById('chart-modal-canvas');

  // Set title and metadata
  titleEl.textContent = chartTitle;
  metaEl.textContent = metadata || '';

  // Destroy old instance if exists
  if (_modalChartInstance) { _modalChartInstance.destroy(); _modalChartInstance = null; }

  // Show modal FIRST so canvas has proper dimensions for chart rendering
  modal.classList.remove('hidden');

  // Render chart — use config directly (it's the original _config with all functions intact)
  const ctx = canvas.getContext('2d');
  _modalChartInstance = new Chart(ctx, chartConfig);
}

function closeChartModal() {
  const modal = document.getElementById('chart-modal');
  modal.classList.add('hidden');
  if (_modalChartInstance) {
    _modalChartInstance.destroy();
    _modalChartInstance = null;
  }
}

function initChartModalHandlers() {
  // Close button
  document.getElementById('chart-modal-close').addEventListener('click', closeChartModal);

  // Overlay click to close
  document.querySelector('.chart-modal-overlay').addEventListener('click', closeChartModal);

  // ESC key to close
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !document.getElementById('chart-modal').classList.contains('hidden')) {
      closeChartModal();
    }
  });

  // Fullscreen button
  document.getElementById('chart-modal-fullscreen').addEventListener('click', () => {
    const canvas = document.getElementById('chart-modal-canvas');
    if (canvas && _modalChartInstance) {
      // Open in new tab with data
      const dataUrl = canvas.toDataURL('image/png');
      const newWin = window.open();
      newWin.document.write('<img src="' + dataUrl + '" style="max-width:100%;height:auto;">');
    }
  });

  // Expand icon click delegation
  document.getElementById('sector-charts-container').addEventListener('click', (e) => {
    const expandBtn = e.target.closest('.chart-expand');
    if (!expandBtn) return;

    const card = expandBtn.closest('.chart-card');
    const canvas = card.querySelector('canvas');
    if (!canvas) return;

    const chartId = canvas.id;
    const canvasInstance = chartInstances[chartId];
    if (!canvasInstance) return;

    const titleEl = card.querySelector('.chart-title');
    const chartTitle = titleEl ? titleEl.textContent.trim() : 'Chart';

    // Use the actual internal config (_config is the original object passed to new Chart())
    const config = canvasInstance.config._config || canvasInstance.config;
    const metadata = 'Company: ' + (_currentCompany?.ticker || '—') + ' | Period: ' + _currentPeriod;

    openChartModal(chartTitle, config, metadata);
  });
}

// ---- Company Search Autocomplete ----
let selectedSuggestionIndex = -1;

function filterCompanies(query) {
  const entries = Object.entries(NSE_COMPANIES);
  if (!query || query.length === 0) {
    // Return all companies grouped by sector when browsing
    return entries
      .sort((a, b) => (a[1].sector || '').localeCompare(b[1].sector || '') || a[0].localeCompare(b[0]))
      .map(([ticker, co]) => ({
        ticker,
        name: co.name,
        sector: co.sector,
        price: co.latestPrice,
        priceChange: co.priceChange,
        priceChangePct: co.priceChangePct
      }));
  }
  const q = query.toLowerCase();
  return entries
    .filter(([ticker, co]) => {
      const tickerMatch = ticker.toLowerCase().includes(q);
      const nameMatch = (co.name || '').toLowerCase().includes(q);
      return tickerMatch || nameMatch;
    })
    .slice(0, 12)
    .map(([ticker, co]) => ({
      ticker,
      name: co.name,
      sector: co.sector,
      price: co.latestPrice,
      priceChange: co.priceChange,
      priceChangePct: co.priceChangePct
    }));
}

function displaySuggestions(suggestions, grouped) {
  const dropdown = document.getElementById('company-suggestions');

  if (suggestions.length === 0) {
    dropdown.classList.remove('active');
    return;
  }

  if (grouped) {
    // Group by sector for browse mode
    const sectors = {};
    for (const s of suggestions) {
      const sec = s.sector || 'Other';
      if (!sectors[sec]) sectors[sec] = [];
      sectors[sec].push(s);
    }
    let html = '';
    for (const [sec, items] of Object.entries(sectors)) {
      html += `<div class="suggestion-group-header">${sec}</div>`;
      html += items.map(s => buildSuggestionItem(s)).join('');
    }
    dropdown.innerHTML = html;
  } else {
    dropdown.innerHTML = suggestions.map(s => buildSuggestionItem(s)).join('');
  }

  dropdown.classList.add('active');
  selectedSuggestionIndex = -1;
}

function buildSuggestionItem(s) {
  const priceStr = s.price ? fmtPrice(s.price) : '—';
  let changeHtml = '';
  if (s.priceChangePct !== undefined && s.priceChangePct !== null) {
    const cls = s.priceChangePct >= 0 ? 'up' : 'down';
    const sign = s.priceChangePct >= 0 ? '+' : '';
    changeHtml = `<span class="company-suggestion-change ${cls}">${sign}${s.priceChangePct.toFixed(1)}%</span>`;
  }
  return `<div class="company-suggestion-item" onclick="selectSuggestion('${s.ticker}')">
    <span class="company-suggestion-ticker">${s.ticker}</span>
    <span class="company-suggestion-name">${s.name}</span>
    <span class="company-suggestion-price">${priceStr}</span>
    ${changeHtml}
  </div>`;
}

function toggleSearchDropdown() {
  const dropdown = document.getElementById('company-suggestions');
  if (dropdown.classList.contains('active')) {
    dropdown.classList.remove('active');
    return;
  }
  const all = filterCompanies('');
  displaySuggestions(all, true);
}

function selectSuggestion(ticker) {
  const input = document.getElementById('company-search-input');
  const company = NSE_COMPANIES[ticker];
  if (company) {
    input.value = company.ticker;
    document.getElementById('company-suggestions').classList.remove('active');
    loadCompanyFromSearch();
  }
}

function loadCompanyFromSearch() {
  const input = document.getElementById('company-search-input');
  if (!input) return;
  const ticker = input.value.trim().toUpperCase();
  document.getElementById('company-suggestions').classList.remove('active');
  loadCompanyByTicker(ticker);
}

// ---- Populate dropdown with all stocks ----
function populateDropdown() {
  // Note: This function now serves for initialization of all companies
  // The autocomplete search handles the actual filtering
  const sel = document.getElementById('company-select');
  if (!sel) return; // Exit early if using autocomplete instead of select
  const sectors = {};

  for (const [ticker, co] of Object.entries(NSE_COMPANIES)) {
    // Normalize sector name for grouping
    let sec = co.sector || 'Other';
    // Map price-data sector names to our display names
    const sectorMap = {
      'Telecommunication and Technology': 'Telecoms',
      'Energy and Petroleum': 'Energy',
      'Construction and Allied': 'Construction',
      'Commercial and Services': 'Commercial & Services',
      'Automobiles and Accessories': 'Automobiles',
      'Investment Services': 'Investment',
      'Investment': 'Investment',
      'Agricultural': 'Agriculture',
      'Manufacturing and Allied': 'Manufacturing',
    };
    sec = sectorMap[sec] || sec;

    if (!sectors[sec]) sectors[sec] = [];
    let priceStr = '';
    if (co.latestPrice && co.latestPrice > 0) {
      const sign = (co.priceChangePct || 0) >= 0 ? '+' : '';
      priceStr = ' | KES ' + co.latestPrice.toFixed(2) + ' (' + sign + (co.priceChangePct || 0).toFixed(1) + '%)';
    }
    const hasFinancials = co.annuals && co.annuals.length > 0;
    sectors[sec].push({ ticker, name: co.name, priceStr, hasFinancials });
  }

  const order = ['Banking', 'Telecoms', 'FMCG', 'Insurance', 'Energy', 'Construction', 'Media', 'Agriculture', 'Manufacturing', 'Commercial & Services', 'Investment', 'Automobiles'];
  const sorted = Object.keys(sectors).sort((a, b) => {
    const ai = order.indexOf(a), bi = order.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  for (const sector of sorted) {
    const grp = document.createElement('optgroup');
    grp.label = sector + ' (' + sectors[sector].length + ')';
    for (const { ticker, name, priceStr, hasFinancials } of sectors[sector].sort((a, b) => a.name.localeCompare(b.name))) {
      const opt = document.createElement('option');
      opt.value = ticker;
      const indicator = hasFinancials ? '● ' : '○ ';
      opt.textContent = indicator + ticker + ' \u2014 ' + name + priceStr;
      grp.appendChild(opt);
    }
    sel.appendChild(grp);
  }
}

// ---- Valuation Engine ----
// Kenya market parameters (as of early 2026)
const KENYA_MARKET = {
  riskFreeRate: 0.16,       // ~16% Kenya 91-day T-bill rate
  equityRiskPremium: 0.055, // ~5.5% ERP for frontier markets
  costOfEquity: 0.215,      // Ke = Rf + ERP = 21.5%
  terminalGrowth: 0.05,     // 5% long-term nominal growth (GDP + inflation)
  discountRate: 0.18,       // Conservative discount rate for DCF
  sectorPE: {               // Approximate NSE sector average trailing P/E
    Banking: 5.5,
    Telecoms: 18.0,
    Insurance: 8.0,
    FMCG: 16.0,
    Energy: 8.0,
    Media: 10.0,
    Manufacturing: 10.0,
    Agriculture: 8.0,
    DEFAULT: 10.0,
  },
};

// ---- Sector Aggregation Functions ----
function calculateSectorAggregates(sectorName) {
  const allCos = Object.entries(NSE_COMPANIES)
    .filter(([, co]) => normalizeSector(co.sector) === sectorName)
    .map(([, co]) => co);
  const companies = allCos.filter(co => co.annuals && co.annuals.length > 0);

  if (companies.length === 0) {
    return { avgPE: null, avgROE: null, avgGrowth: 0, strength: 'mixed', companyCount: 0 };
  }

  const avg = arr => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null;
  const fmt1 = v => v != null ? parseFloat(v.toFixed(1)) : null;

  let peVals = [], roeVals = [], growthVals = [], revenueVals = [], patMarginVals = [];
  let niiVals = [], totalAssetsVals = [], divYieldVals = [], roaVals = [];
  let revenueGrowthVals = [], patGrowthVals = [];

  companies.forEach(co => {
    const latest = co.annuals[0];
    const prev = co.annuals[1];
    const price = co.latestPrice;

    // P/E
    if (price > 0 && latest.eps > 0) {
      const pe = price / latest.eps;
      if (pe > 0 && pe < 100) peVals.push(pe);
    }
    // ROE
    const roe = calcROE(latest);
    if (roe !== null) roeVals.push(parseFloat(roe));
    // ROA
    const roa = calcROA(latest);
    if (roa !== null) roaVals.push(parseFloat(roa));
    // Price change
    if (co.priceChangePct != null) growthVals.push(co.priceChangePct);
    // Revenue
    if (latest.revenue > 0) revenueVals.push(latest.revenue);
    // PAT margin
    if (latest.revenue > 0 && latest.pat > 0) patMarginVals.push((latest.pat / latest.revenue) * 100);
    // NII (banking)
    if (latest.nii > 0) niiVals.push(latest.nii);
    // Total assets
    if (latest.totalAssets > 0) totalAssetsVals.push(latest.totalAssets);
    // Dividend yield
    if (price > 0 && latest.dps > 0) divYieldVals.push((latest.dps / price) * 100);
    // Revenue YoY growth
    if (prev && prev.revenue > 0 && latest.revenue > 0) {
      revenueGrowthVals.push(((latest.revenue - prev.revenue) / prev.revenue) * 100);
    }
    // PAT YoY growth
    if (prev && prev.pat > 0 && latest.pat > 0) {
      patGrowthVals.push(((latest.pat - prev.pat) / prev.pat) * 100);
    }
  });

  const avgGrowth = fmt1(avg(growthVals)) || 0;
  let strength = 'mixed';
  if (avgGrowth > 5) strength = 'up';
  else if (avgGrowth < -5) strength = 'down';

  return {
    companyCount: companies.length,
    avgPE: peVals.length ? (avg(peVals).toFixed(1)) : null,
    avgROE: roeVals.length ? (avg(roeVals).toFixed(1)) : null,
    avgROA: roaVals.length ? (avg(roaVals).toFixed(1)) : null,
    avgGrowth,
    strength,
    totalRevenue: revenueVals.length ? revenueVals.reduce((a, b) => a + b, 0) : null,
    avgPATMargin: patMarginVals.length ? fmt1(avg(patMarginVals)) : null,
    avgNII: niiVals.length ? avg(niiVals) : null,
    totalAssets: totalAssetsVals.length ? totalAssetsVals.reduce((a, b) => a + b, 0) : null,
    avgDivYield: divYieldVals.length ? fmt1(avg(divYieldVals)) : null,
    avgRevenueGrowth: revenueGrowthVals.length ? fmt1(avg(revenueGrowthVals)) : null,
    avgPATGrowth: patGrowthVals.length ? fmt1(avg(patGrowthVals)) : null,
  };
}

function getNSEAverages() {
  // Calculate NSE-wide average metrics for comparison
  const allCompanies = Object.values(NSE_COMPANIES)
    .filter(co => co.annuals && co.annuals.length > 0);

  if (allCompanies.length === 0) return null;

  let peValues = [];
  let roeValues = [];
  let priceChangeValues = [];

  allCompanies.forEach(co => {
    if (co.latestPrice && co.latestPrice > 0) {
      const latest = co.annuals[0];
      if (latest && latest.eps && latest.eps > 0) {
        const pe = co.latestPrice / latest.eps;
        if (pe > 0 && pe < 100) peValues.push(pe);
      }

      const roe = calcROE(latest);
      if (roe !== null) roeValues.push(parseFloat(roe));

      if (co.priceChangePct !== undefined) {
        priceChangeValues.push(co.priceChangePct);
      }
    }
  });

  return {
    avgPE: peValues.length > 0 ? (peValues.reduce((a, b) => a + b, 0) / peValues.length).toFixed(1) : null,
    avgROE: roeValues.length > 0 ? (roeValues.reduce((a, b) => a + b, 0) / roeValues.length).toFixed(1) : null,
    avgGrowth: priceChangeValues.length > 0 ? (priceChangeValues.reduce((a, b) => a + b, 0) / priceChangeValues.length).toFixed(1) : null,
  };
}

function computeValuation(co) {
  const annuals = co.annuals || [];
  if (annuals.length < 2) return null;
  const latest = annuals[0];
  const price = co.latestPrice;
  if (!price || price <= 0) return null;

  const eps = latest.eps;
  const dps = latest.dps;
  const pat = latest.pat;
  const equity = latest.totalEquity;
  const revenue = latest.revenue;
  const units = co.units;

  // Calculate historical growth rates (EPS & DPS CAGR)
  const epsArr = annuals.map(a => a.eps).filter(v => v != null && v > 0);
  const dpsArr = annuals.map(a => a.dps).filter(v => v != null && v > 0);
  const patArr = annuals.map(a => a.pat).filter(v => v != null && v > 0);
  const revArr = annuals.map(a => a.revenue).filter(v => v != null && v > 0);

  function cagr(arr, maxPeriods) {
    if (arr.length < 2) return null;
    const n = Math.min(arr.length - 1, maxPeriods);
    const end = arr[0], start = arr[n];
    if (start <= 0 || end <= 0) return null;
    return Math.pow(end / start, 1 / n) - 1;
  }

  const epsGrowth5 = cagr(epsArr, 5);
  const epsGrowth3 = cagr(epsArr, 3);
  const dpsGrowth5 = cagr(dpsArr, 5);
  const patGrowth5 = cagr(patArr, 5);
  const revGrowth3 = cagr(revArr, 3);

  // Use best available growth estimate, capped at reasonable range
  const rawGrowth = epsGrowth3 || epsGrowth5 || patGrowth5 || revGrowth3 || 0.05;
  const earningsGrowth = Math.max(-0.10, Math.min(rawGrowth, 0.25)); // Cap -10% to +25%
  const divGrowth = dpsGrowth5 != null ? Math.max(0, Math.min(dpsGrowth5, 0.15)) : earningsGrowth * 0.7;

  const sectorPE = KENYA_MARKET.sectorPE[co.sector] || KENYA_MARKET.sectorPE.DEFAULT;
  const Ke = KENYA_MARKET.costOfEquity;
  const g_terminal = KENYA_MARKET.terminalGrowth;
  const r = KENYA_MARKET.discountRate;

  const models = [];

  // ── MODEL 1: Two-Stage Dividend Discount Model ──
  // Stage 1: dividends grow at divGrowth for 5 years
  // Stage 2: terminal value using long-term growth rate
  if (dps && dps > 0) {
    let ddmSum = 0;
    const g1 = Math.min(divGrowth, 0.15); // Cap stage-1 growth at 15%
    for (let yr = 1; yr <= 5; yr++) {
      ddmSum += (dps * Math.pow(1 + g1, yr)) / Math.pow(1 + Ke, yr);
    }
    const termDiv = dps * Math.pow(1 + g1, 5) * (1 + g_terminal);
    const termValue = termDiv / (Ke - g_terminal);
    const pvTerm = termValue / Math.pow(1 + Ke, 5);
    const ddmValue = ddmSum + pvTerm;
    if (ddmValue > 0 && isFinite(ddmValue)) {
      models.push({
        name: 'Dividend Discount',
        abbr: 'DDM',
        value: ddmValue,
        desc: '2-stage DDM: DPS ' + dps.toFixed(2) + ' growing ' + (g1 * 100).toFixed(1) + '% for 5 yrs, then ' + (g_terminal * 100).toFixed(0) + '% terminal. Cost of equity: ' + (Ke * 100).toFixed(1) + '%.',
      });
    }
  }

  // ── MODEL 2: Sector P/E Fair Value ──
  if (eps && eps > 0) {
    const peValue = eps * sectorPE;
    models.push({
      name: 'Sector P/E',
      abbr: 'P/E',
      value: peValue,
      desc: 'EPS ' + eps.toFixed(2) + ' × NSE ' + co.sector + ' avg P/E of ' + sectorPE.toFixed(1) + 'x.',
    });
  }

  // ── MODEL 3: Graham Number ──
  // Intrinsic Value = sqrt(22.5 × EPS × BVPS)
  // BVPS needs shares outstanding — estimate from PAT/EPS
  if (eps && eps > 0 && equity && equity > 0 && pat && pat > 0) {
    const sharesEst = (pat / eps); // in thousands (same unit as equity)
    const bvps = equity / sharesEst;
    if (bvps > 0) {
      const grahamVal = Math.sqrt(22.5 * eps * bvps);
      if (grahamVal > 0 && isFinite(grahamVal)) {
        models.push({
          name: 'Graham Number',
          abbr: 'Graham',
          value: grahamVal,
          desc: 'Conservative value: √(22.5 × EPS ' + eps.toFixed(2) + ' × BVPS ' + bvps.toFixed(2) + ').',
        });
      }
    }
  }

  // ── MODEL 4: Simplified DCF (5-year earnings projection) ──
  if (eps && eps > 0) {
    let dcfSum = 0;
    const projGrowth = Math.min(earningsGrowth, 0.15); // More conservative for DCF
    for (let yr = 1; yr <= 5; yr++) {
      const futureEPS = eps * Math.pow(1 + projGrowth, yr);
      dcfSum += futureEPS / Math.pow(1 + r, yr);
    }
    // Terminal value (earnings at year 5 growing at terminal rate)
    const terminalEPS = eps * Math.pow(1 + projGrowth, 5);
    const terminalValue = (terminalEPS * (1 + g_terminal)) / (r - g_terminal);
    const pvTerminal = terminalValue / Math.pow(1 + r, 5);
    const dcfValue = dcfSum + pvTerminal;
    if (dcfValue > 0 && isFinite(dcfValue)) {
      models.push({
        name: 'DCF (5-Year)',
        abbr: 'DCF',
        value: dcfValue,
        desc: 'EPS growing ' + (projGrowth * 100).toFixed(1) + '% for 5 yrs, then ' + (g_terminal * 100).toFixed(0) + '% terminal. Discount rate: ' + (r * 100).toFixed(0) + '%.',
      });
    }
  }

  if (models.length === 0) return null;

  // Compute weighted average (equal weight)
  const avgValue = models.reduce((s, m) => s + m.value, 0) / models.length;
  const upside = ((avgValue - price) / price) * 100;

  // Signal
  let signal, signalClass;
  if (upside > 20) { signal = 'Undervalued'; signalClass = 'undervalued'; }
  else if (upside > -10) { signal = 'Fairly Valued'; signalClass = 'fair'; }
  else { signal = 'Overvalued'; signalClass = 'overvalued'; }

  return {
    models,
    avgValue,
    upside,
    signal,
    signalClass,
    price,
    earningsGrowth,
    divGrowth,
    sectorPE,
  };
}

function renderValuation(co) {
  const panel = document.getElementById('valuation-panel');
  const grid = document.getElementById('valuation-grid');
  const summary = document.getElementById('valuation-summary');
  const assumptions = document.getElementById('valuation-assumptions');

  // Coming soon
  panel.classList.remove('hidden');
  grid.innerHTML = '<div class="valuation-coming-soon"><span class="valuation-cs-icon">🔬</span><div class="valuation-cs-text">Coming soon</div><div class="valuation-cs-sub">Advanced valuation models are being refined</div></div>';
  summary.innerHTML = '';
  if (assumptions) assumptions.innerHTML = '';
  return;

  const result = computeValuation(co);
  if (!result) {
    panel.classList.add('hidden');
    return;
  }
  panel.classList.remove('hidden');

  // Render model cards
  grid.innerHTML = result.models.map(m => {
    const upsideVal = ((m.value - result.price) / result.price) * 100;
    const upsideCls = upsideVal >= 0 ? 'positive' : 'negative';
    const badgeCls = upsideVal > 20 ? 'undervalued' : upsideVal > -10 ? 'fair' : 'overvalued';
    const badgeText = upsideVal > 20 ? 'Upside' : upsideVal > -10 ? 'Fair' : 'Downside';
    return '<div class="val-card">' +
      '<div class="val-card-header">' +
        '<span class="val-card-title">' + m.name + '</span>' +
        '<span class="val-card-badge ' + badgeCls + '">' + badgeText + '</span>' +
      '</div>' +
      '<div class="val-card-value">KES ' + m.value.toFixed(2) + '</div>' +
      '<div class="val-card-upside ' + upsideCls + '">' +
        (upsideVal >= 0 ? '▲' : '▼') + ' ' + Math.abs(upsideVal).toFixed(1) + '% vs KES ' + result.price.toFixed(2) +
      '</div>' +
      '<div class="val-card-desc">' + m.desc + '</div>' +
    '</div>';
  }).join('');

  // Render summary bar
  const barPct = Math.max(5, Math.min(95, 50 + result.upside * 0.5));
  const barColor = result.signalClass === 'undervalued' ? '#10b981' :
                   result.signalClass === 'overvalued' ? '#ff4444' : '#ffa000';

  summary.innerHTML =
    '<div class="val-summary-header">' +
      '<span class="val-summary-verdict">' +
        'Consensus: KES ' + result.avgValue.toFixed(2) +
      '</span>' +
      '<span class="val-card-badge ' + result.signalClass + '">' + result.signal + '</span>' +
    '</div>' +
    '<div class="val-summary-bar">' +
      '<div class="val-summary-bar-fill" style="width:' + barPct + '%;background:' + barColor + '"></div>' +
    '</div>' +
    '<div class="val-summary-bar-labels">' +
      '<span>Overvalued</span><span>Fair Value</span><span>Undervalued</span>' +
    '</div>' +
    '<div class="val-summary-detail" style="margin-top:0.6rem">' +
      'Average of ' + result.models.length + ' models suggests <strong>' +
      (result.upside >= 0 ? '+' : '') + result.upside.toFixed(1) + '% ' +
      (result.upside >= 0 ? 'upside' : 'downside') + '</strong> from current price of KES ' +
      result.price.toFixed(2) + '. ' +
      'Earnings growth (hist.): ' + (result.earningsGrowth * 100).toFixed(1) + '% CAGR. ' +
      (result.divGrowth > 0 ? 'Dividend growth: ' + (result.divGrowth * 100).toFixed(1) + '% CAGR.' : '') +
    '</div>';

  assumptions.innerHTML =
    '<strong>Assumptions:</strong> ' +
    'Risk-free rate: ' + (KENYA_MARKET.riskFreeRate * 100).toFixed(0) + '% (Kenya 91-day T-bill). ' +
    'Cost of equity: ' + (KENYA_MARKET.costOfEquity * 100).toFixed(1) + '%. ' +
    'DCF discount rate: ' + (KENYA_MARKET.discountRate * 100).toFixed(0) + '%. ' +
    'Terminal growth: ' + (KENYA_MARKET.terminalGrowth * 100).toFixed(0) + '%. ' +
    'Sector P/E (' + co.sector + '): ' + result.sectorPE.toFixed(1) + 'x. ' +
    'Past performance does not predict future results. These are rough estimates based on historical data and should not be used as the sole basis for investment decisions.';
}

// ---- Market Data ----
let NSE_MARKET = null;

async function loadMarketData() {
  try {
    const resp = await fetch('market.json?v=4');
    if (resp.ok) NSE_MARKET = await resp.json();
  } catch (e) {
    NSE_MARKET = null;
  }

  // Populate NSE index cards in market summary
  if (NSE_MARKET) {
    const nse20 = NSE_MARKET.nse20;
    const nseAll = NSE_MARKET.nseAllShare;
    if (nse20) {
      const valEl = document.getElementById('nse20-val');
      const chgEl = document.getElementById('nse20-chg');
      if (valEl) valEl.textContent = nse20.value.toLocaleString();
      if (chgEl) {
        chgEl.textContent = (nse20.change_pct >= 0 ? '+' : '') + nse20.change_pct.toFixed(2) + '%';
        chgEl.className = 'market-card-chg ' + (nse20.change_pct >= 0 ? 'positive' : 'negative');
      }
    }
    if (nseAll) {
      const valEl = document.getElementById('nseall-val');
      const chgEl = document.getElementById('nseall-chg');
      if (valEl) valEl.textContent = nseAll.value.toLocaleString();
      if (chgEl) {
        chgEl.textContent = (nseAll.change_pct >= 0 ? '+' : '') + nseAll.change_pct.toFixed(2) + '%';
        chgEl.className = 'market-card-chg ' + (nseAll.change_pct >= 0 ? 'positive' : 'negative');
      }
    }
  }
}

// ---- Market Summary ----
function renderMarketSummary() {
  const companies = Object.entries(NSE_COMPANIES);
  const withPrices = companies.filter(([, c]) => c.latestPrice && c.latestPrice > 0);

  // Stocks tracked (element may not exist in new layout)
  const msStocks = document.getElementById('ms-stocks');
  if (msStocks) msStocks.textContent = companies.length;

  // Top gainer & loser
  if (withPrices.length > 0) {
    const sorted = [...withPrices].sort((a, b) => (b[1].priceChangePct || 0) - (a[1].priceChangePct || 0));
    const gainer = sorted[0];
    const loser = sorted[sorted.length - 1];
    const gainerEl = document.getElementById('ms-gainer');
    const loserEl  = document.getElementById('ms-loser');
    if (gainerEl) gainerEl.textContent = gainer[0] + ' +' + (gainer[1].priceChangePct || 0).toFixed(1) + '%';
    if (loserEl)  loserEl.textContent  = loser[0]  + ' '  + (loser[1].priceChangePct  || 0).toFixed(1) + '%';
  }

  // Override with market.json data if available
  if (NSE_MARKET) {
    if (NSE_MARKET.topGainer) {
      const gEl = document.getElementById('ms-gainer');
      if (gEl) gEl.textContent = NSE_MARKET.topGainer.ticker + ' +' + NSE_MARKET.topGainer.change_pct.toFixed(1) + '%';
    }
    if (NSE_MARKET.topLoser) {
      const lEl = document.getElementById('ms-loser');
      if (lEl) lEl.textContent = NSE_MARKET.topLoser.ticker + ' ' + NSE_MARKET.topLoser.change_pct.toFixed(1) + '%';
    }
    if (NSE_MARKET.stocksTracked) {
      const sEl = document.getElementById('ms-stocks');
      if (sEl) sEl.textContent = NSE_MARKET.stocksTracked;
    }
  }

  // Avg P/E for banking
  const banks = companies.filter(([, c]) => c.sector === 'Banking' && c.annuals && c.annuals.length > 0 && c.latestPrice > 0);
  if (banks.length > 0) {
    const pes = banks.map(([, c]) => {
      const eps = c.annuals[0].eps;
      return (eps && eps > 0) ? c.latestPrice / eps : null;
    }).filter(v => v !== null);
    if (pes.length > 0) {
      const avgPE = pes.reduce((s, v) => s + v, 0) / pes.length;
      const peEl = document.getElementById('ms-pe');
      if (peEl) peEl.textContent = avgPE.toFixed(1) + 'x';
    }
  }

  // Avg dividend yield (all companies with DPS + price, excluding outliers >25%)
  const withDiv = companies.filter(([, c]) => c.annuals && c.annuals.length > 0 && c.annuals[0].dps > 0 && c.latestPrice > 0);
  if (withDiv.length > 0) {
    const yields = withDiv.map(([, c]) => (c.annuals[0].dps / c.latestPrice) * 100).filter(y => y <= 25);
    if (yields.length > 0) {
      const avgYield = yields.reduce((s, v) => s + v, 0) / yields.length;
      const dyEl = document.getElementById('ms-divyield');
      if (dyEl) dyEl.textContent = avgYield.toFixed(1) + '%';
    }
  }

  // Most active (element may not exist in new layout)
  const msActive = document.getElementById('ms-active');
  if (msActive) {
    const withData = companies.filter(([, c]) => c.annuals && c.annuals.length > 0);
    if (withData.length > 0) {
      const byData = [...withData].sort((a, b) => (b[1].annuals.length + (b[1].quarters || []).length) - (a[1].annuals.length + (a[1].quarters || []).length));
      msActive.textContent = byData[0][0];
    }
  }
}

// ---- View Toggle ----
let _currentView = 'companies';

function showView(view) {
  _currentView = view;
  document.getElementById('btn-companies').classList.toggle('active', view === 'companies');
  document.getElementById('btn-sectors').classList.toggle('active', view === 'sectors');
  // Sync center nav links
  const navDash = document.getElementById('nav-dashboard');
  const navSectors = document.getElementById('nav-sectors');
  if (navDash) navDash.classList.toggle('active', view === 'companies');
  if (navSectors) navSectors.classList.toggle('active', view === 'sectors');

  const dashboard = document.getElementById('dashboard');
  const emptyState = document.getElementById('empty-state');
  const sectorOverview = document.getElementById('sector-overview');
  const marketSummary = document.getElementById('market-summary');

  if (view === 'sectors') {
    dashboard.classList.add('hidden');
    emptyState.classList.add('hidden');
    if (marketSummary) marketSummary.classList.add('hidden');
    sectorOverview.classList.remove('hidden');
    renderSectorOverview();
  } else {
    sectorOverview.classList.add('hidden');
    if (activeCompany) {
      dashboard.classList.remove('hidden');
      if (marketSummary) marketSummary.classList.add('hidden'); // Hide when company is selected
    } else {
      emptyState.classList.remove('hidden');
      if (marketSummary) marketSummary.classList.remove('hidden'); // Show market summary on empty state
    }
  }
}

// ---- Sector Overview ----
const SECTOR_DISPLAY = {
  'Banking': { emoji: '🏦', label: 'Banking' },
  'Insurance': { emoji: '🛡️', label: 'Insurance' },
  'Telecoms & Technology': { emoji: '📱', label: 'Telecoms & Technology' },
  'Consumer Goods': { emoji: '🛒', label: 'Consumer Goods' },
  'Energy & Utilities': { emoji: '⚡', label: 'Energy & Utilities' },
  'Agriculture': { emoji: '🌾', label: 'Agriculture' },
  'Manufacturing': { emoji: '🏭', label: 'Manufacturing' },
  'Media & Services': { emoji: '📺', label: 'Media & Services' },
  'Diversified': { emoji: '📊', label: 'Diversified' },
  // Legacy mappings (still in some company records)
  'Telecommunication and Technology': { emoji: '📱', label: 'Telecoms & Technology' },
  'Telecoms': { emoji: '📱', label: 'Telecoms & Technology' },
  'FMCG': { emoji: '🛒', label: 'Consumer Goods' },
  'Energy': { emoji: '⚡', label: 'Energy & Utilities' },
  'Energy and Petroleum': { emoji: '⚡', label: 'Energy & Utilities' },
  'Construction and Allied': { emoji: '🏭', label: 'Manufacturing' },
  'Construction': { emoji: '🏭', label: 'Manufacturing' },
  'Agricultural': { emoji: '🌾', label: 'Agriculture' },
  'Agriculture': { emoji: '🌾', label: 'Agriculture' },
  'Manufacturing and Allied': { emoji: '🏭', label: 'Manufacturing' },
  'Media': { emoji: '📺', label: 'Media & Services' },
  'Hospitality': { emoji: '📺', label: 'Media & Services' },
  'Logistics': { emoji: '📺', label: 'Media & Services' },
  'Financial Services': { emoji: '🛡️', label: 'Insurance' },
  'Real Estate': { emoji: '📊', label: 'Diversified' },
  'Entertainment': { emoji: '📱', label: 'Telecoms & Technology' },
  'Infrastructure': { emoji: '🏭', label: 'Manufacturing' },
  'Commercial and Services': { emoji: '📺', label: 'Media & Services' },
  'Investment': { emoji: '📊', label: 'Diversified' },
  'Investment Services': { emoji: '📊', label: 'Diversified' },
};

function normalizeSector(sec) {
  const d = SECTOR_DISPLAY[sec];
  return d ? d.label : (sec || 'Other');
}

function getCompanyMarketCap(co) {
  // Derive shares outstanding from PAT / EPS, then multiply by current price
  const price = co.latestPrice;
  if (!price || price <= 0) return null;
  const latest = co.annuals && co.annuals[0];
  if (!latest || !latest.eps || latest.eps <= 0 || !latest.pat || latest.pat <= 0) return null;
  const shares = (latest.pat * 1000) / latest.eps; // pat in KES '000, eps in KES/share
  return price * shares; // market cap in KES
}

function renderSectorHeatmap() {
  const el = document.getElementById('sector-heatmap');
  if (!el) return;

  const SECTOR_ORDER = ['Banking', 'Telecoms & Technology', 'Consumer Goods', 'Insurance', 'Energy & Utilities', 'Agriculture', 'Manufacturing', 'Media & Services', 'Diversified'];

  // Build sector data
  const sectorData = SECTOR_ORDER.map(sec => {
    const cos = Object.values(NSE_COMPANIES).filter(co => normalizeSector(co.sector) === sec);
    let totalMcap = 0, priceChanges = [], companyCount = cos.length;
    cos.forEach(co => {
      const mc = getCompanyMarketCap(co);
      if (mc) totalMcap += mc;
      if (co.priceChangePct != null) priceChanges.push(co.priceChangePct);
    });
    const avgChange = priceChanges.length ? priceChanges.reduce((a, b) => a + b, 0) / priceChanges.length : 0;
    const display = SECTOR_DISPLAY[sec] || { emoji: '📈', label: sec };
    return { sec, label: display.label, emoji: display.emoji, totalMcap, avgChange, companyCount };
  }).filter(d => d.totalMcap > 0);

  const totalMcap = sectorData.reduce((s, d) => s + d.totalMcap, 0);
  sectorData.sort((a, b) => b.totalMcap - a.totalMcap);

  // Colour scale: dark red → neutral → dark green mapped to -10% → 0 → +10%
  function heatColour(pct) {
    const t = Math.max(-1, Math.min(1, pct / 10));
    if (t >= 0) {
      const g = Math.round(120 + 80 * t);
      const rb = Math.round(30 - 20 * t);
      return `rgb(${rb},${g},${rb})`;
    } else {
      const r = Math.round(150 + 80 * (-t));
      const gb = Math.round(30 - 20 * (-t));
      return `rgb(${r},${gb},${gb})`;
    }
  }

  function fmtMcap(v) {
    if (v >= 1e12) return (v / 1e12).toFixed(2) + 'T';
    if (v >= 1e9) return (v / 1e9).toFixed(0) + 'B';
    return (v / 1e6).toFixed(0) + 'M';
  }

  // Split into two rows: row1 gets sectors until ~60% of total, row2 gets rest
  let cumulative = 0, row1 = [], row2 = [];
  for (const d of sectorData) {
    if (cumulative / totalMcap < 0.60) {
      row1.push(d);
      cumulative += d.totalMcap;
    } else {
      row2.push(d);
    }
  }
  if (row1.length === 0) { row1 = sectorData.slice(0, 2); row2 = sectorData.slice(2); }

  function renderRow(items) {
    const rowTotal = items.reduce((s, d) => s + d.totalMcap, 0);
    return items.map(d => {
      const widthPct = (d.totalMcap / rowTotal * 100).toFixed(2);
      const bg = heatColour(d.avgChange);
      const changeStr = (d.avgChange >= 0 ? '+' : '') + d.avgChange.toFixed(1) + '%';
      return `<div class="heatmap-tile" style="width:${widthPct}%;background:${bg}" onclick="renderSectorTable('${d.sec.replace(/'/g,"\\'")}')">
        <div class="heatmap-tile-inner">
          <div class="heatmap-sector-name">${d.label}</div>
          <div class="heatmap-mcap">KES ${fmtMcap(d.totalMcap)}</div>
          <div class="heatmap-change">${changeStr}</div>
        </div>
      </div>`;
    }).join('');
  }

  el.innerHTML =
    `<div class="heatmap-row">${renderRow(row1)}</div>` +
    (row2.length ? `<div class="heatmap-row">${renderRow(row2)}</div>` : '');

  renderSectorMarketSummary(sectorData, totalMcap);
}

function renderSectorMarketSummary(sectorData, totalMcap) {
  const el = document.getElementById('sector-market-summary');
  if (!el) return;

  function fmtMcap(v) {
    if (v >= 1e12) return 'KES ' + (v / 1e12).toFixed(2) + 'T';
    if (v >= 1e9)  return 'KES ' + (v / 1e9).toFixed(0) + 'B';
    return 'KES ' + (v / 1e6).toFixed(0) + 'M';
  }

  // For each sector find top contributors and build a concise insight
  const items = sectorData.map(d => {
    const cos = Object.entries(NSE_COMPANIES)
      .filter(([, co]) => normalizeSector(co.sector) === d.sec)
      .map(([ticker, co]) => {
        const mc = getCompanyMarketCap(co);
        const latest = co.annuals && co.annuals[0];
        return { ticker, name: co.name, mc, latest, price: co.latestPrice, chg: co.priceChangePct };
      })
      .filter(c => c.mc)
      .sort((a, b) => b.mc - a.mc);

    if (!cos.length) return null;

    const top = cos[0];
    const top2 = cos[1];
    const topShare = ((top.mc / d.totalMcap) * 100).toFixed(0);
    const sectorShare = ((d.totalMcap / totalMcap) * 100).toFixed(1);

    // Build insight sentence
    let insight = '';
    const latest = top.latest || {};

    if (d.sec === 'Banking') {
      const nii = latest.nii ? fmtMcap(latest.nii * 1000) : null;
      insight = `<b>${top.name}</b> leads with ${fmtMcap(top.mc)} (${topShare}% of sector).` +
        (nii ? ` Net interest income of ${nii} underpins its valuation.` : '') +
        (top2 ? ` <b>${top2.name}</b> (${fmtMcap(top2.mc)}) follows closely.` : '');
    } else if (d.sec === 'Telecoms & Technology') {
      const rev = latest.revenue ? fmtMcap(latest.revenue * 1000) : null;
      insight = `<b>${top.name}</b> accounts for ${topShare}% of sector cap at ${fmtMcap(top.mc)}, making it the single largest stock on the NSE.` +
        (rev ? ` Annual revenue of ${rev} and dominant M-PESA market share justify the premium.` : '');
    } else if (d.sec === 'Consumer Goods') {
      const rev = latest.revenue ? fmtMcap(latest.revenue * 1000) : null;
      insight = `<b>${top.name}</b> dominates at ${fmtMcap(top.mc)} (${topShare}% of sector).` +
        (rev ? ` Revenue of ${rev} is driven by beer, spirits and non-alcoholic beverages across East Africa.` : '') +
        (top2 ? ` <b>${top2.name}</b> adds ${fmtMcap(top2.mc)}.` : '');
    } else if (d.sec === 'Insurance') {
      insight = `<b>${top.name}</b> leads at ${fmtMcap(top.mc)} (${topShare}% of sector), backed by a diversified insurance and financial services portfolio.` +
        (top2 ? ` <b>${top2.name}</b> (${fmtMcap(top2.mc)}) is the second largest with life and general insurance operations.` : '');
    } else if (d.sec === 'Energy & Utilities') {
      insight = `<b>${top.name}</b> is the primary contributor at ${fmtMcap(top.mc)} (${topShare}% of sector).` +
        (d.sec === 'Energy & Utilities' && top.ticker === 'KPLC' ? ' Kenya Power\'s regulated monopoly on electricity distribution underpins its value.' : ' KenGen\'s installed generation capacity of ~1,800 MW across hydro, geothermal and wind assets drives its valuation.') +
        (top2 ? ` <b>${top2.name}</b> contributes ${fmtMcap(top2.mc)}.` : '');
    } else if (d.sec === 'Agriculture') {
      insight = `<b>${top.name}</b> leads at ${fmtMcap(top.mc)} (${topShare}% of sector). Tea companies benefit from strong export demand but are exposed to weather and global commodity prices.` +
        (top2 ? ` <b>${top2.name}</b> adds ${fmtMcap(top2.mc)}.` : '');
    } else if (d.sec === 'Manufacturing') {
      const margin = latest.pat && latest.revenue ? ((latest.pat / latest.revenue) * 100).toFixed(1) : null;
      insight = `<b>${top.name}</b> leads at ${fmtMcap(top.mc)} (${topShare}% of sector).` +
        (margin ? ` Net margin of ${margin}% reflects tight industrial margins.` : '') +
        (top2 ? ` <b>${top2.name}</b> (${fmtMcap(top2.mc)}) follows.` : '');
    } else if (d.sec === 'Media & Services') {
      insight = `<b>${top.name}</b> is the largest contributor at ${fmtMcap(top.mc)} (${topShare}% of sector). The sector faces headwinds from digital disruption in traditional media and sluggish consumer spending.` +
        (top2 ? ` <b>${top2.name}</b> adds ${fmtMcap(top2.mc)}.` : '');
    } else {
      insight = `<b>${top.name}</b> is the primary contributor at ${fmtMcap(top.mc)} (${topShare}% of sector).` +
        (top2 ? ` <b>${top2.name}</b> accounts for ${fmtMcap(top2.mc)}.` : '');
    }

    const chgClass = d.avgChange >= 0 ? 'pos' : 'neg';
    const chgStr = (d.avgChange >= 0 ? '+' : '') + d.avgChange.toFixed(1) + '%';

    return `<div class="summary-sector-item">
      <div class="summary-sector-header">
        <span class="summary-sector-name">${d.emoji} ${d.label}</span>
        <span class="summary-sector-mcap">${fmtMcap(d.totalMcap)}</span>
        <span class="summary-sector-share">${sectorShare}% of market</span>
        <span class="summary-sector-chg ${chgClass}">${chgStr}</span>
      </div>
      <div class="summary-sector-insight">${insight}</div>
    </div>`;
  }).filter(Boolean);

  el.innerHTML = items.join('');
}

function renderSectorOverview() {
  const grid = document.getElementById('sector-grid');
  const tableWrap = document.getElementById('sector-table-wrap');
  grid.style.display = '';
  tableWrap.classList.add('hidden');
  renderSectorHeatmap();

  // Group companies by normalized sector
  const sectors = {};
  for (const [ticker, co] of Object.entries(NSE_COMPANIES)) {
    const sec = normalizeSector(co.sector);
    if (!sectors[sec]) sectors[sec] = [];
    sectors[sec].push({ ticker, ...co });
  }

  const SECTOR_ORDER = ['Banking', 'Insurance', 'Telecoms & Technology', 'Consumer Goods', 'Energy & Utilities', 'Agriculture', 'Manufacturing', 'Media & Services', 'Diversified'];

  const sectorMetrics = {
    'Banking':               (a) => [
      a.avgNII      ? fmtKES(a.avgNII) + ' avg NII'           : null,
      a.totalAssets ? fmtKES(a.totalAssets / (a.companyCount||1)) + ' avg assets' : null,
      a.avgROE      ? 'ROE ' + a.avgROE + '%'                 : null,
      a.avgPE       ? 'P/E ' + a.avgPE + 'x'                 : null,
    ],
    'Insurance':             (a) => [
      a.avgROE      ? 'ROE ' + a.avgROE + '%'                 : null,
      a.avgPE       ? 'P/E ' + a.avgPE + 'x'                 : null,
      a.avgDivYield ? 'Div ' + a.avgDivYield + '%'           : null,
      a.avgPATGrowth != null ? 'PAT growth ' + (a.avgPATGrowth >= 0 ? '+' : '') + a.avgPATGrowth + '%' : null,
    ],
    'Telecoms & Technology': (a) => [
      a.totalRevenue ? fmtKES(a.totalRevenue) + ' revenue'   : null,
      a.avgPATMargin ? a.avgPATMargin + '% net margin'        : null,
      a.avgPE        ? 'P/E ' + a.avgPE + 'x'                : null,
      a.avgDivYield  ? 'Div ' + a.avgDivYield + '%'          : null,
    ],
    'Consumer Goods':        (a) => [
      a.avgRevenueGrowth != null ? 'Rev growth ' + (a.avgRevenueGrowth >= 0 ? '+' : '') + a.avgRevenueGrowth + '%' : null,
      a.avgPATMargin ? a.avgPATMargin + '% net margin'        : null,
      a.avgPE        ? 'P/E ' + a.avgPE + 'x'                : null,
      a.avgDivYield  ? 'Div ' + a.avgDivYield + '%'          : null,
    ],
    'Energy & Utilities':    (a) => [
      a.totalRevenue ? fmtKES(a.totalRevenue) + ' revenue'   : null,
      a.avgROA       ? 'ROA ' + a.avgROA + '%'               : null,
      a.avgROE       ? 'ROE ' + a.avgROE + '%'               : null,
      a.avgPE        ? 'P/E ' + a.avgPE + 'x'               : null,
    ],
    'Agriculture':           (a) => [
      a.avgPATMargin ? a.avgPATMargin + '% net margin'        : null,
      a.avgROE       ? 'ROE ' + a.avgROE + '%'               : null,
      a.avgDivYield  ? 'Div ' + a.avgDivYield + '%'          : null,
      a.avgPE        ? 'P/E ' + a.avgPE + 'x'               : null,
    ],
    'Manufacturing':         (a) => [
      a.totalRevenue ? fmtKES(a.totalRevenue) + ' revenue'   : null,
      a.avgPATMargin ? a.avgPATMargin + '% net margin'        : null,
      a.avgROE       ? 'ROE ' + a.avgROE + '%'               : null,
      a.avgPE        ? 'P/E ' + a.avgPE + 'x'               : null,
    ],
    'Media & Services':      (a) => [
      a.avgRevenueGrowth != null ? 'Rev growth ' + (a.avgRevenueGrowth >= 0 ? '+' : '') + a.avgRevenueGrowth + '%' : null,
      a.avgPATMargin ? a.avgPATMargin + '% net margin'        : null,
      a.avgROE       ? 'ROE ' + a.avgROE + '%'               : null,
      a.avgPE        ? 'P/E ' + a.avgPE + 'x'               : null,
    ],
    'Diversified':           (a) => [
      a.totalRevenue ? fmtKES(a.totalRevenue) + ' revenue'   : null,
      a.avgROE       ? 'ROE ' + a.avgROE + '%'               : null,
      a.avgDivYield  ? 'Div ' + a.avgDivYield + '%'          : null,
      a.avgPE        ? 'P/E ' + a.avgPE + 'x'               : null,
    ],
  };

  function fmtKES(n) {
    if (!n) return '—';
    if (n >= 1e9) return 'KES ' + (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return 'KES ' + (n / 1e6).toFixed(0) + 'M';
    return 'KES ' + n.toFixed(0);
  }

  const sorted = SECTOR_ORDER.filter(s => sectors[s]);

  grid.innerHTML = sorted.map(sec => {
    const companies = sectors[sec];
    const withFinancials = companies.filter(c => c.annuals && c.annuals.length > 0).length;
    const display = SECTOR_DISPLAY[sec] || { emoji: '📈', label: sec };
    const agg = calculateSectorAggregates(sec);
    const strengthEmoji = agg.strength === 'up' ? '▲' : agg.strength === 'down' ? '▼' : '—';
    const strengthClass = agg.strength === 'up' ? 'pos' : agg.strength === 'down' ? 'neg' : 'neu';
    const metrics = (sectorMetrics[sec] ? sectorMetrics[sec](agg) : []).filter(Boolean);

    const metricsHtml = '<div class="sector-card-metrics">' +
      metrics.map(m => '<div class="sector-metric-item">' + m + '</div>').join('') +
    '</div>';

    const trendHtml = '<div class="sector-card-trend ' + strengthClass + '">' +
      strengthEmoji + ' ' + (agg.avgGrowth != null ? ((agg.avgGrowth >= 0 ? '+' : '') + agg.avgGrowth.toFixed(1) + '%') : '—') +
      ' avg price</div>';

    return '<div class="sector-card" onclick="renderSectorTable(\'' + sec.replace(/'/g, "\\'") + '\')">' +
      '<div class="sector-card-header">' +
        '<span class="sector-card-emoji">' + display.emoji + '</span>' +
        trendHtml +
      '</div>' +
      '<div class="sector-card-name">' + display.label + '</div>' +
      '<div class="sector-card-count">' + companies.length + ' co · ' + withFinancials + ' with data</div>' +
      metricsHtml +
    '</div>';
  }).join('');
}

function showSectorGrid() {
  document.getElementById('sector-grid').style.display = '';
  document.getElementById('sector-table-wrap').classList.add('hidden');
  // Also hide sector detail dashboard if open
  if (typeof window.hideSectorDetail === 'function') window.hideSectorDetail();
}

let _sectorSortCol = null;
let _sectorSortAsc = true;

function renderSectorTable(sectorName) {
  // Route all sectors to the rich sector detail dashboard
  if (typeof window.renderSectorDetail === 'function') {
    return window.renderSectorDetail(sectorName);
  }
  document.getElementById('sector-grid').style.display = 'none';
  document.getElementById('sector-table-wrap').classList.remove('hidden');
  document.getElementById('sector-table-title').textContent = sectorName;

  // Reset comparison view
  _showingComparison = false;
  document.getElementById('sector-snapshot').classList.remove('hidden');
  document.getElementById('sector-comparison').classList.add('hidden');

  const companies = Object.entries(NSE_COMPANIES)
    .filter(([, co]) => normalizeSector(co.sector) === sectorName)
    .map(([ticker, co]) => {
      const latest = co.annuals && co.annuals.length > 0 ? co.annuals[0] : {};
      return {
        ticker,
        company: co.name || '—',
        price: co.latestPrice || null,
        change: co.priceChangePct || null,
        pe: (latest.eps && latest.eps > 0 && co.latestPrice) ? co.latestPrice / latest.eps : null,
        eps: latest.eps || null,
        dps: latest.dps || null,
        revenue: latest.revenue || null,
        pat: latest.pat || null,
        units: co.units || 'thousands',
      };
    });

  const cols = [
    { key: 'ticker', label: 'Ticker' },
    { key: 'company', label: 'Company' },
    { key: 'price', label: 'Price (KES)', numeric: true },
    { key: 'change', label: 'Change %', numeric: true },
    { key: 'pe', label: 'P/E', numeric: true },
    { key: 'eps', label: 'EPS', numeric: true },
    { key: 'dps', label: 'DPS', numeric: true },
    { key: 'revenue', label: 'Revenue', numeric: true },
    { key: 'pat', label: 'PAT', numeric: true },
  ];

  // Sort
  if (_sectorSortCol) {
    const col = cols.find(c => c.key === _sectorSortCol);
    companies.sort((a, b) => {
      let va = a[_sectorSortCol], vb = b[_sectorSortCol];
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (col && col.numeric) return _sectorSortAsc ? va - vb : vb - va;
      return _sectorSortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
    });
  }

  const head = document.getElementById('sector-table-head');
  head.innerHTML = cols.map(c => {
    let cls = c.numeric ? 'num-col' : '';
    if (_sectorSortCol === c.key) cls += _sectorSortAsc ? ' sort-asc' : ' sort-desc';
    return '<th class="' + cls + '" onclick="sortSectorTable(\'' + c.key + '\', \'' + sectorName.replace(/'/g, "\\'") + '\')">' + c.label + '</th>';
  }).join('');

  const body = document.getElementById('sector-table-body');
  body.innerHTML = companies.map(c => {
    const chgCls = c.change != null ? (c.change >= 0 ? 'positive' : 'negative') : '';
    return '<tr onclick="selectFromSector(\'' + c.ticker + '\')">' +
      '<td>' + c.ticker + '</td>' +
      '<td>' + c.company + '</td>' +
      '<td class="num-col">' + (c.price ? c.price.toFixed(2) : '—') + '</td>' +
      '<td class="num-col ' + chgCls + '">' + (c.change != null ? (c.change >= 0 ? '+' : '') + c.change.toFixed(1) + '%' : '—') + '</td>' +
      '<td class="num-col">' + (c.pe ? c.pe.toFixed(1) + 'x' : '—') + '</td>' +
      '<td class="num-col">' + (c.eps ? c.eps.toFixed(2) : '—') + '</td>' +
      '<td class="num-col">' + (c.dps ? c.dps.toFixed(2) : '—') + '</td>' +
      '<td class="num-col">' + (c.revenue ? fmtNum(c.revenue, c.units) : '—') + '</td>' +
      '<td class="num-col">' + (c.pat ? fmtNum(c.pat, c.units) : '—') + '</td>' +
    '</tr>';
  }).join('');

  // Render snapshot
  renderSectorSnapshot(sectorName);
}

function sortSectorTable(col, sectorName) {
  if (_sectorSortCol === col) {
    _sectorSortAsc = !_sectorSortAsc;
  } else {
    _sectorSortCol = col;
    _sectorSortAsc = true;
  }
  renderSectorTable(sectorName);
  renderSectorSnapshot(sectorName);
}

// ---- Sector Snapshot & Comparison ----
let _showingComparison = false;

function renderSectorSnapshot(sectorName) {
  const agg = calculateSectorAggregates(sectorName);
  const snapshotGrid = document.getElementById('snapshot-grid');
  const snapshotDiv = document.getElementById('sector-snapshot');

  if (!agg || agg.companyCount === 0) {
    snapshotDiv.classList.add('hidden');
    return;
  }

  snapshotDiv.classList.remove('hidden');

  const cards = [];
  if (agg.companyCount) {
    cards.push({ label: 'Companies', value: agg.companyCount });
  }
  if (agg.avgPE) {
    cards.push({ label: 'Avg P/E', value: agg.avgPE + 'x' });
  }
  if (agg.avgROE) {
    cards.push({ label: 'Avg ROE', value: agg.avgROE + '%' });
  }
  if (agg.avgGrowth !== null) {
    cards.push({ label: 'Avg Growth', value: (agg.avgGrowth >= 0 ? '+' : '') + agg.avgGrowth.toFixed(1) + '%' });
  }

  snapshotGrid.innerHTML = cards.map(card => {
    return '<div class="snapshot-card">' +
      '<div class="snapshot-label-text">' + card.label + '</div>' +
      '<div class="snapshot-value">' + card.value + '</div>' +
    '</div>';
  }).join('');
}

function toggleSectorComparison() {
  const compDiv = document.getElementById('sector-comparison');
  const titleEl = document.getElementById('sector-table-title');
  const sectorName = titleEl ? titleEl.textContent : null;

  if (!sectorName) return;

  _showingComparison = !_showingComparison;

  if (_showingComparison) {
    renderSectorComparison(sectorName);
    compDiv.classList.remove('hidden');
  } else {
    compDiv.classList.add('hidden');
  }
}

function renderSectorComparison(sectorName) {
  const agg = calculateSectorAggregates(sectorName);
  const nseAvg = getNSEAverages();
  const compGrid = document.getElementById('comparison-grid');

  if (!agg || !nseAvg) {
    compGrid.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--text-muted)">Insufficient data</div>';
    return;
  }

  const comparisons = [];

  // P/E Comparison
  if (agg.avgPE && nseAvg.avgPE) {
    const sectorPE = parseFloat(agg.avgPE);
    const nsePE = parseFloat(nseAvg.avgPE);
    const better = sectorPE < nsePE;
    comparisons.push({
      label: 'P/E Ratio',
      sectorVal: agg.avgPE + 'x',
      nseVal: nseAvg.avgPE + 'x',
      better: better,
    });
  }

  // ROE Comparison
  if (agg.avgROE && nseAvg.avgROE) {
    const sectorROE = parseFloat(agg.avgROE);
    const nseROE = parseFloat(nseAvg.avgROE);
    const better = sectorROE > nseROE;
    comparisons.push({
      label: 'ROE %',
      sectorVal: agg.avgROE + '%',
      nseVal: nseAvg.avgROE + '%',
      better: better,
    });
  }

  // Growth Comparison
  if (agg.avgGrowth !== null && nseAvg.avgGrowth) {
    const sectorGrowth = agg.avgGrowth;
    const nseGrowth = parseFloat(nseAvg.avgGrowth);
    const better = sectorGrowth > nseGrowth;
    comparisons.push({
      label: 'Growth %',
      sectorVal: (sectorGrowth >= 0 ? '+' : '') + sectorGrowth.toFixed(1) + '%',
      nseVal: (nseGrowth >= 0 ? '+' : '') + nseGrowth.toFixed(1) + '%',
      better: better,
    });
  }

  compGrid.innerHTML = comparisons.map(comp => {
    const indicator = comp.better ? '▲' : '▼';
    const cls = comp.better ? 'better' : 'worse';
    return '<div class="comparison-card">' +
      '<div class="comparison-label-text">' + comp.label + '</div>' +
      '<div style="font-size:0.75rem;color:var(--text-muted);">' +
        '<div><span style="font-size:0.65rem;">Sector:</span> ' + comp.sectorVal + '</div>' +
        '<div><span style="font-size:0.65rem;">NSE Avg:</span> ' + comp.nseVal + '</div>' +
      '</div>' +
      '<div class="comparison-value ' + cls + '" style="font-size:0.8rem;">' + indicator + '</div>' +
    '</div>';
  }).join('');
}

function selectFromSector(ticker) {
  const searchInput = document.getElementById('company-search-input');
  if (searchInput) searchInput.value = ticker;
  showView('companies');
  loadCompanyByTicker(ticker);
}

// ---- Mobile Navigation ----
function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  const hamburger = document.getElementById('hamburger-menu');
  if (menu && hamburger) {
    menu.classList.toggle('hidden');
    hamburger.classList.toggle('active');
  }
}

function closeMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  const hamburger = document.getElementById('hamburger-menu');
  if (menu && hamburger) {
    menu.classList.add('hidden');
    hamburger.classList.remove('active');
  }
}

// Close mobile menu when clicking on the backdrop (outside the panel)
document.addEventListener('click', (e) => {
  const menu = document.getElementById('mobile-menu');
  const menuContent = document.querySelector('.mobile-menu-content');
  const hamburger = document.getElementById('hamburger-menu');
  if (menu && !menu.classList.contains('hidden') && menuContent && hamburger) {
    if (!menuContent.contains(e.target) && !hamburger.contains(e.target)) {
      closeMobileMenu();
    }
  }
});

// ---- Touch Gesture Handler (Swipe for charts) ----
let touchStartX = 0;
let touchStartY = 0;

function handleTouchStart(e) {
  touchStartX = e.touches[0].clientX;
  touchStartY = e.touches[0].clientY;
}

function handleTouchEnd(e) {
  const touchEndX = e.changedTouches[0].clientX;
  const touchEndY = e.changedTouches[0].clientY;
  const diffX = touchStartX - touchEndX;
  const diffY = touchStartY - touchEndY;

  // Only trigger if horizontal swipe is more prominent than vertical
  if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
    // Swiped left (next), or right (previous)
    if (diffX > 0) {
      // Next chart/view
      onChartSwipeNext();
    } else {
      // Previous chart/view
      onChartSwipePrev();
    }
  }
}

function onChartSwipeNext() {
  // Navigate to next chart or section (to be implemented per view)
  // For now, placeholder
}

function onChartSwipePrev() {
  // Navigate to previous chart or section (to be implemented per view)
  // For now, placeholder
}

// Add touch listeners to chart containers
document.addEventListener('DOMContentLoaded', () => {
  const chartContainer = document.getElementById('sector-charts-container');
  if (chartContainer) {
    chartContainer.addEventListener('touchstart', handleTouchStart, false);
    chartContainer.addEventListener('touchend', handleTouchEnd, false);
  }
});

// ---- Theme Toggle ----
function toggleTheme() {
  const isLight = document.body.classList.toggle('light');
  const btn = document.getElementById('theme-toggle');
  const mobileBtn = document.getElementById('theme-toggle-mobile');
  if (btn) btn.textContent = isLight ? '🌙' : '☀️';
  if (mobileBtn) mobileBtn.textContent = isLight ? '🌙' : '☀️';
  try { localStorage.setItem('nse-theme', isLight ? 'light' : 'dark'); } catch(e) {}

  // Update chart colors without losing company context
  if (activeCompany) {
    const ticker = activeCompany.ticker;
    // Destroy and recreate charts with new theme colors
    Object.keys(chartInstances).forEach(key => {
      if (chartInstances[key]) {
        chartInstances[key].destroy();
        delete chartInstances[key];
      }
    });
    // Re-render only the charts, not the full company load
    renderPriceChart(ticker, _currentRange || '1Y');
    const template = getTemplate(activeCompany.sector);
    renderCharts(activeCompany, _currentPeriod || 'annual', template);
  }
}

function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem('nse-theme'); } catch(e) {}
  if (saved === 'light') {
    document.body.classList.add('light');
    const btn = document.getElementById('theme-toggle');
    const mobileBtn = document.getElementById('theme-toggle-mobile');
    if (btn) btn.textContent = '🌙';
    if (mobileBtn) mobileBtn.textContent = '🌙';
  }
}

// ---- Init ----
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  await loadPrices();
  await loadMarketData();
  populateDropdown();
  renderMarketSummary();
  initChartModalHandlers();

  // Setup autocomplete search
  const searchInput = document.getElementById('company-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value;
      if (query.length > 0) {
        const suggestions = filterCompanies(query);
        displaySuggestions(suggestions, false);
      } else {
        document.getElementById('company-suggestions').classList.remove('active');
      }
    });

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        loadCompanyFromSearch();
      }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.company-search-container')) {
        document.getElementById('company-suggestions').classList.remove('active');
      }
    });
  }

  // Price chart range buttons
  document.getElementById('price-range-btns').addEventListener('click', (e) => {
    const btn = e.target.closest('.range-btn');
    if (!btn || !activeCompany) return;
    renderPriceChart(activeCompany.ticker, btn.dataset.range);
  });
});
