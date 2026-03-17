// ============================================================
//  NSE Insights — App Logic
//  Premium financial dashboard for Kenya NSE stocks
//  With SECTOR-SPECIFIC templates
// ============================================================

let activeCompany = null;
let chartInstances = {};
let NSE_PRICES = {};

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

// ---- Load Prices ----
const API_BASE = 'https://kenya-stocks-1.onrender.com';

async function loadPrices() {
  try {
    const tickers = Object.keys(NSE_COMPANIES).join(',');
    const resp = await fetch(`${API_BASE}/prices?tickers=${tickers}`);
    if (resp.ok) {
      const data = await resp.json();
      NSE_PRICES = data.tickers || {};
    }
  } catch (e) {
    console.warn('Live prices unavailable, falling back to static:', e);
    NSE_PRICES = {};
  }
  for (const [ticker, priceData] of Object.entries(NSE_PRICES)) {
    if (NSE_COMPANIES[ticker]) {
      NSE_COMPANIES[ticker].latestPrice = priceData.price;
      NSE_COMPANIES[ticker].priceChange = priceData.change;
      NSE_COMPANIES[ticker].priceChangePct = priceData.change_pct;
    }
  }
}

// ---- Chart.js Global Defaults ----
Chart.defaults.color = '#8896a8';
Chart.defaults.borderColor = '#1e2d3d';
Chart.defaults.font.family = "'Inter', 'Segoe UI', system-ui, sans-serif";
Chart.defaults.font.size = 11;

// ---- Formatters ----
function fmtNum(val, units) {
  if (val === null || val === undefined || isNaN(val)) return '\u2014';
  if (units === 'thousands') {
    if (Math.abs(val) >= 1e6) return (val / 1e6).toFixed(1) + 'B';
    if (Math.abs(val) >= 1e3) return (val / 1e3).toFixed(1) + 'M';
    return val.toFixed(0);
  }
  if (units === 'millions') {
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

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1a2332',
          borderColor: '#2a3a4e',
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
          grid: { color: 'rgba(30, 45, 61, 0.6)', drawTicks: false },
          border: { display: false },
          ticks: {
            color: '#5a6a7e', font: { size: 10 },
            callback: (v) => {
              const u = opts.units;
              // Data stored in THOUSANDS of KES:
              //   1,000,000 thousands = 1 Billion KES  → threshold 1e6
              //   1,000 thousands     = 1 Million KES   → threshold 1e3
              if (u === 'thousands') {
                if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(1) + 'B';
                if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(1) + 'M';
                return v + 'K';
              }
              // Data stored in MILLIONS of KES:
              //   1,000 millions = 1 Billion KES → threshold 1e3
              if (u === 'millions') {
                if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(1) + 'B';
                return v.toFixed(0) + 'M';
              }
              // Raw values (EPS etc.)
              if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(1) + 'B';
              if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(1) + 'M';
              if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(1) + 'K';
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
  return Array.from({ length: n }, (_, i) => i === n - 1 ? '#f59e0b' : '#3b82f6');
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

// ---- Load Company ----
function loadCompany() {
  const sel = document.getElementById('company-select').value;
  if (!sel || !NSE_COMPANIES[sel]) return;
  const co = NSE_COMPANIES[sel];
  activeCompany = co;
  _currentCompany = co;
  _currentPeriod = 'annual';
  document.getElementById('toggle-annual').classList.add('active');
  document.getElementById('toggle-quarterly').classList.remove('active');
  document.getElementById('dashboard').classList.remove('hidden');
  document.getElementById('empty-state').classList.add('hidden');
  document.getElementById('breadcrumb-company').textContent = co.ticker + ' | NSE';
  document.getElementById('company-logo').textContent = co.logo;
  document.getElementById('company-name').textContent = co.name;
  document.getElementById('company-meta').textContent = co.ticker + ' | ' + co.exchange + ' \u00B7 ' + co.sector;
  document.getElementById('company-price').textContent = fmtPrice(co.latestPrice);

  const changeEl = document.getElementById('company-price-change');
  if (co.priceChange !== undefined && co.priceChange !== null) {
    changeEl.innerHTML = fmtChange(co.priceChange, co.priceChangePct);
  } else {
    changeEl.innerHTML = '';
  }

  const latest = co.latestPeriod || (co.annuals && co.annuals.length > 0 ? co.annuals[0] : null);
  if (!latest) return;
  const latestLabel = latest.period || latest.year;
  document.getElementById('company-eps-pill').textContent = 'EPS (' + latestLabel + '): ' + fmtEPS(latest.eps);
  document.getElementById('company-latest-year').textContent = 'Units: KES ' + co.units + ' \u00B7 Last period: ' + latestLabel;

  // Get sector template and build UI
  const template = getTemplate(co.sector);
  renderStatsGrid(co, template);
  buildChartGrid(template);
  renderCharts(co, 'annual', template);
  renderValuation(co);
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

  function getVal(key) {
    if (key.startsWith('_growth_')) {
      const g = computed[key];
      return { text: g.text, cls: g.cls };
    }
    if (key.startsWith('_')) {
      const v = computed[key];
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

  document.getElementById('stats-grid').innerHTML = sections.map(sec =>
    '<div class="stat-section"><div class="stat-section-title">' + sec.title + '</div>' +
    sec.rows.map(r => '<div class="stat-row"><span class="stat-label">' + r.label + '</span><span class="stat-val ' + (r.cls || '') + '">' + r.val + '</span></div>').join('') +
    '</div>'
  ).join('');
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
        [{ label: chart.title, data: dp.map(d => d[chart.key]), backgroundColor: colors, borderRadius: 6 }],
        { ...opts, isCurrency: chart.isCurrency || false }
      );
    });
  });
}


// ---- Stock Price Chart ----
const PRICE_RANGES = {
  '1D': { interval: '5m',  range: '1d'  },
  '1W': { interval: '30m', range: '5d'  },
  '1M': { interval: '1d',  range: '1mo' },
  '6M': { interval: '1d',  range: '6mo' },
  '1Y': { interval: '1d',  range: '1y'  },
  '5Y': { interval: '1wk', range: '5y'  },
};
let _activePriceRange = '1Y';

async function fetchYahooChart(ticker, interval, range) {
  // Route through our Render backend — Yahoo Finance has no NSE Kenya data
  try {
    const url = `${API_BASE}/history/${encodeURIComponent(ticker)}?range=${range}`;
    const res = await fetch(url, { signal: AbortSignal.timeout(12000) });
    if (!res.ok) return null;
    const json = await res.json();
    if (json.points && json.points.length > 0) return json.points;
  } catch (_) {}
  return null;
}

function makePriceLineChart(canvasId, points, rangeKey) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (chartInstances[canvasId]) chartInstances[canvasId].destroy();
  const labels = points.map(p => {
    const d = new Date(p.t);
    if (rangeKey === '1D') return d.toLocaleTimeString('en-KE', { hour: '2-digit', minute: '2-digit' });
    if (rangeKey === '1W') return d.toLocaleDateString('en-KE', { weekday: 'short', hour: '2-digit' });
    return d.toLocaleDateString('en-KE', { month: 'short', day: 'numeric', ...(rangeKey === '5Y' && { year: 'numeric' }) });
  });
  const values = points.map(p => p.v);
  const first  = values[0] || 0;
  const last   = values[values.length - 1] || 0;
  const color  = last >= first ? '#10b981' : '#ef4444';
  const bgColor = last >= first ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)';
  chartInstances[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{ label: 'Price (KES)', data: values, borderColor: color, backgroundColor: bgColor,
        borderWidth: 2, pointRadius: 0, tension: 0.3, fill: true }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false, backgroundColor: '#1e2d3d', borderColor: '#2a3f52',
          borderWidth: 1, padding: 10, cornerRadius: 8,
          callbacks: { label: (item) => ` KES ${item.raw?.toFixed(2)}` }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#5a6a7e', font: { size: 9 }, maxTicksLimit: 8, maxRotation: 0 } },
        y: { position: 'right', grid: { color: 'rgba(30,45,61,0.6)', drawTicks: false }, border: { display: false },
          ticks: { color: '#5a6a7e', font: { size: 10 }, callback: (v) => 'KES ' + v.toFixed(1) } }
      }
    }
  });
}

async function loadStockPrice(ticker, rangeKey) {
  if (!ticker) return;
  rangeKey = rangeKey || _activePriceRange;
  _activePriceRange = rangeKey;
  document.querySelectorAll('.price-range-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.range === rangeKey);
  });
  const section   = document.getElementById('price-chart-section');
  const loadingEl = document.getElementById('price-chart-loading');
  const errorEl   = document.getElementById('price-chart-error');
  section.classList.remove('hidden');
  loadingEl.classList.remove('hidden');
  errorEl.classList.add('hidden');
  const { interval, range } = PRICE_RANGES[rangeKey];
  const points = await fetchYahooChart(ticker, interval, range);
  loadingEl.classList.add('hidden');
  if (!points || points.length === 0) { errorEl.classList.remove('hidden'); return; }
  const first = points[0].v, last = points[points.length - 1].v;
  const chgPct = ((last - first) / first) * 100;
  const chgEl  = document.getElementById('price-change-pill');
  chgEl.textContent = `${chgPct >= 0 ? '+' : ''}${chgPct.toFixed(2)}% (${rangeKey})`;
  chgEl.className   = 'price-change-pill ' + (chgPct >= 0 ? 'positive' : 'negative');
  makePriceLineChart('chart-price', points, rangeKey);
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

// ---- Populate dropdown with prices ----
function populateDropdown() {
  const sel = document.getElementById('company-select');
  const sectors = {};
  for (const [ticker, co] of Object.entries(NSE_COMPANIES)) {
    const sec = co.sector || 'Other';
    if (!sectors[sec]) sectors[sec] = [];
    let priceStr = '';
    if (co.latestPrice && co.latestPrice > 0) {
      const sign = (co.priceChangePct || 0) >= 0 ? '+' : '';
      priceStr = ' | KES ' + co.latestPrice.toFixed(2) + ' (' + sign + (co.priceChangePct || 0).toFixed(1) + '%)';
    }
    sectors[sec].push({ ticker, name: co.name, priceStr });
  }

  const order = ['Banking', 'Telecoms', 'FMCG', 'Insurance', 'Energy', 'Construction', 'Media', 'Agriculture', 'Manufacturing'];
  const sorted = Object.keys(sectors).sort((a, b) => {
    const ai = order.indexOf(a), bi = order.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  for (const sector of sorted) {
    const grp = document.createElement('optgroup');
    grp.label = sector;
    for (const { ticker, name, priceStr } of sectors[sector].sort((a, b) => a.name.localeCompare(b.name))) {
      const opt = document.createElement('option');
      opt.value = ticker;
      opt.textContent = ticker + ' \u2014 ' + name + priceStr;
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

  const result = computeValuation(co);
  if (!result) {
    panel.style.display = 'none';
    return;
  }
  panel.style.display = 'block';

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
                   result.signalClass === 'overvalued' ? '#ef4444' : '#f59e0b';

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

// ---- Init ----
document.addEventListener('DOMContentLoaded', async () => {
  await loadPrices();
  populateDropdown();
  document.getElementById('company-select').addEventListener('keydown', e => {
    if (e.key === 'Enter') loadCompany();
  });
  document.getElementById('company-select').addEventListener('change', () => {
    loadCompany();
  });
});
