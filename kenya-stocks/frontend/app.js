// ============================================================
//  NSE Insights — App Logic
//  Qualtrim-style dashboard for Kenya NSE stocks
// ============================================================

let activeCompany = null;
let chartInstances = {};

// ---- Ticker Mappings ----
// TV ticker (NSE_ALL_STOCKS key / TradingView NSEKE symbol) → internal key (NSE_COMPANIES key)
// Only entries where they differ
const TV_TO_INTERNAL = {
  'DTK':  'DTB',    // Diamond Trust Bank
  'BAT':  'BATK',   // BAT Kenya
  'CRWN': 'CPKL',   // Crown Paints
  'PORT': 'EAPC',   // EA Portland Cement
  'KAPC': 'KAPA',   // Kapchorua Tea
};

// Reverse map: internal → TV ticker (for companies where they differ)
const INTERNAL_TO_TV = Object.fromEntries(
  Object.entries(TV_TO_INTERNAL)
    .filter(([tv, internal]) => tv !== internal)
    .map(([tv, internal]) => [internal, tv])
);

// Companies with financial data but no TradingView NSEKE ticker
const NO_TV_TICKER = new Set(['FMLY', 'HBZE', 'TCL']);

// Derive FINANCIAL_TICKERS as TV tickers from all NSE_COMPANIES entries
// (NSE_COMPANIES is defined in data.js, loaded before app.js)
const FINANCIAL_TICKERS = new Set(
  Object.keys(NSE_COMPANIES).map(internal => INTERNAL_TO_TV[internal] || internal)
);

// Get TradingView NSEKE symbol from TV ticker
function getTVSymbol(tvTicker) {
  return `NSEKE:${tvTicker}`;
}

// ---- Chart.js Global Defaults ----
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#2a3146';
Chart.defaults.font.family = "'Inter', 'Segoe UI', system-ui, sans-serif";
Chart.defaults.font.size = 11;

// ---- Formatters ----
function fmtNum(val, units) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  // Convert to billions or millions for display
  if (units === 'thousands') {
    if (Math.abs(val) >= 1e6)      return (val / 1e6).toFixed(1) + 'B';
    if (Math.abs(val) >= 1e3)      return (val / 1e3).toFixed(1) + 'M';
    return val.toFixed(0);
  }
  if (units === 'millions') {
    if (Math.abs(val) >= 1e3)      return (val / 1e3).toFixed(1) + 'B';
    return val.toFixed(0) + 'M';
  }
  return val.toFixed(2);
}

function fmtEPS(val) {
  if (val === null || val === undefined) return '—';
  return 'KES ' + val.toFixed(2);
}

function fmtDPS(val) {
  if (val === null || val === undefined) return '—';
  return 'KES ' + val.toFixed(2);
}

function fmtPrice(val) {
  if (val === null || val === undefined) return '—';
  return 'KES ' + val.toFixed(2);
}

// ---- Calculate Compound Annual Growth Rate ----
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

  // Destroy existing instance if any
  if (chartInstances[canvasId]) {
    chartInstances[canvasId].destroy();
  }

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          borderColor: '#334155',
          borderWidth: 1,
          padding: 10,
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 12 },
          cornerRadius: 8,
          callbacks: {
            label: (item) => {
              const val = item.raw;
              const formatted = opts.isCurrency ? fmtPrice(val) : fmtNum(val, opts.units);
              return ` ${item.dataset.label}: ${formatted}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#64748b', font: { size: 10 } }
        },
        y: {
          grid: { color: 'rgba(51, 65, 85, 0.5)', drawTicks: false },
          border: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            callback: (v) => {
              const u = opts.units;
              if (u === 'millions') {
                // data stored in KES millions
                if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(0) + 'T';
                if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(0) + 'B';
                return v.toFixed(0) + 'M';
              }
              if (u === 'thousands') {
                // data stored in KES thousands
                if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(0) + 'B';
                if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(0) + 'M';
                if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(0) + 'K';
                return v;
              }
              // raw / isCurrency (EPS, DPS, price)
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

  // Add growth pills if requested (Qualtrim style)
  const card = ctx.closest('.chart-card');
  let growthContainer = card.querySelector('.growth-pills');
  if (opts.showGrowth && datasets[0].data.length >= 2) {
    if (!growthContainer) {
      growthContainer = document.createElement('div');
      growthContainer.className = 'growth-pills';
      card.appendChild(growthContainer);
    }
    const data = datasets[0].data;
    const cagr1 = calcCAGR(data, 1);
    const cagr3 = calcCAGR(data, 3);
    const cagr5 = calcCAGR(data, 5);
    
    let html = '';
    if (cagr1 !== null) html += `<div class="growth-pill"><span>1Y:</span>${cagr1 >= 0 ? '+' : ''}${cagr1.toFixed(1)}%</div>`;
    if (cagr3 !== null) html += `<div class="growth-pill"><span>3Y:</span>${cagr3 >= 0 ? '+' : ''}${cagr3.toFixed(1)}%</div>`;
    if (cagr5 !== null) html += `<div class="growth-pill"><span>5Y:</span>${cagr5 >= 0 ? '+' : ''}${cagr5.toFixed(1)}%</div>`;
    growthContainer.innerHTML = html;
  } else if (growthContainer) {
    growthContainer.innerHTML = '';
  }
}

// ---- Build bar colors (Qualtrim style: Orange for latest, Blue for others) ----
function barColors(n) {
  return Array.from({ length: n }, (_, i) =>
    i === n - 1 ? '#f59e0b' : '#38bdf8'
  );
}

// ---- Load Company ----
function loadCompany() {
  const tvTicker = document.getElementById('company-select').value;
  if (!tvTicker) {
    alert('Please select a company first.');
    return;
  }

  const hasFinancials = FINANCIAL_TICKERS.has(tvTicker);
  const internalTicker = TV_TO_INTERNAL[tvTicker] || tvTicker;
  const co = hasFinancials ? NSE_COMPANIES[internalTicker] : null;
  const companyName = co ? co.name : (NSE_ALL_STOCKS[tvTicker] || tvTicker);

  activeCompany = co;
  _currentCompany = co;
  _currentPeriod = 'annual';

  // Show dashboard, hide empty state
  document.getElementById('dashboard').classList.remove('hidden');
  document.getElementById('empty-state').classList.add('hidden');

  // Update breadcrumb
  document.getElementById('breadcrumb-company').textContent = `${companyName} (${tvTicker})`;

  // -- Company Header --
  document.getElementById('company-logo').textContent = co ? co.logo : '🏢';
  document.getElementById('company-name').textContent = companyName;
  document.getElementById('company-meta').textContent =
    co ? `${tvTicker} | ${co.exchange} · ${co.sector}` : `NSE:${tvTicker} · NSE Kenya`;

  const priceEl = document.getElementById('company-price');
  const hasTVChart = !NO_TV_TICKER.has(internalTicker);
  if (hasTVChart) {
    priceEl.textContent = 'Live on chart ↓';
    priceEl.classList.add('tv-live-badge');
  } else {
    priceEl.textContent = co && co.latestPrice ? `KES ${co.latestPrice.toFixed(2)}` : '—';
    priceEl.classList.remove('tv-live-badge');
  }

  // -- TradingView Live Price Chart --
  // Skip for companies with no NSEKE ticker (FMLY, HBZE, TCL)
  if (hasTVChart) {
    initTradingViewChart(tvTicker, !hasFinancials);
  } else {
    const section   = document.getElementById('tv-chart-section');
    const container = document.getElementById('tradingview-chart-container');
    section.classList.remove('hidden');
    container.classList.remove('tv-chart-full');
    container.innerHTML = '<div class="tv-chart-error" style="padding:24px;text-align:center;color:#64748b;font-size:13px;">Live price chart not available for this stock on TradingView (NSEKE)</div>';
  }

  if (hasFinancials && co) {
    // Reset period toggle
    document.getElementById('toggle-annual').classList.add('active');
    document.getElementById('toggle-quarterly').classList.remove('active');

    // Latest period for header pills
    const latest = co.latestPeriod || co.annuals[co.annuals.length - 1];
    const latestLabel = latest.period || latest.year;
    document.getElementById('company-eps-pill').textContent = `EPS (${latestLabel}): ${fmtEPS(latest.eps)}`;
    document.getElementById('company-latest-year').textContent =
      `Units: KES ${co.units} · Last period: ${latestLabel}`;

    // Show financial sections, hide notice
    document.getElementById('financial-content').classList.remove('hidden');
    document.getElementById('no-data-notice').classList.add('hidden');

    // -- Stats Grid & Charts --
    renderStatsGrid(co);
    renderCharts(co, 'annual');
  } else {
    // Price-only stock
    document.getElementById('company-eps-pill').textContent = '';
    document.getElementById('company-latest-year').textContent = 'Live price shown in chart below';

    // Hide financial sections, show notice
    document.getElementById('financial-content').classList.add('hidden');
    document.getElementById('no-data-notice').classList.remove('hidden');
    document.getElementById('no-data-text').textContent =
      `📊 Financial statements for ${companyName} are not yet available. Price chart powered by TradingView.`;
  }
}

// ---- Stats Grid ----
function renderStatsGrid(co) {
  // Use latestPeriod (could be quarterly) for the stats card — more up-to-date
  const latest = co.latestPeriod || co.annuals[co.annuals.length - 1];
  const latestLabel = latest.period || latest.year;
  // For YoY comparison use second-to-last annual row
  const annualRows = co.annuals;
  const prev = annualRows.length >= 2 ? annualRows[annualRows.length - 2] : null;

  function growth(curr, prev) {
    if (curr === null || curr === undefined || prev === null || prev === undefined) return null;
    return ((curr - prev) / Math.abs(prev)) * 100;
  }

  function growthLabel(curr, prev) {
    const g = growth(curr, prev);
    if (g === null) return { text: '—', cls: '' };
    const sign = g >= 0 ? '+' : '';
    return { text: `${sign}${g.toFixed(1)}%`, cls: g >= 0 ? 'up' : 'down' };
  }

  const revGrowth = growthLabel(latest.revenue, prev?.revenue);
  const patGrowth = growthLabel(latest.pat,     prev?.pat);
  const niiGrowth = growthLabel(latest.nii,     prev?.nii);

  const sections = [
    {
      title: 'Revenue / NII',
      rows: [
        { label: 'Revenue',        val: fmtNum(latest.revenue, co.units) },
        { label: 'Net Int. Income',val: fmtNum(latest.nii, co.units) },
        { label: 'YoY Revenue',    val: revGrowth.text,  cls: revGrowth.cls },
      ]
    },
    {
      title: 'Profitability',
      rows: [
        { label: 'Net Income',     val: fmtNum(latest.pat, co.units) },
        { label: 'YoY Net Inc.',   val: patGrowth.text, cls: patGrowth.cls },
        { label: 'YoY NII',        val: niiGrowth.text, cls: niiGrowth.cls },
      ]
    },
    {
      title: 'Per Share',
      rows: [
        { label: 'EPS',            val: fmtEPS(latest.eps) },
        { label: 'DPS',            val: fmtDPS(latest.dps) },
        { label: 'Price',          val: fmtPrice(co.latestPrice) },
      ]
    },
    {
      title: 'Valuation',
      rows: [
        { label: 'P/E (approx)',
          val: (latest.eps && co.latestPrice) ? (co.latestPrice / latest.eps).toFixed(1) + 'x' : '—' },
        { label: 'Div. Yield',
          val: (latest.dps && co.latestPrice) ? ((latest.dps / co.latestPrice) * 100).toFixed(1) + '%' : '—' },
        { label: 'Currency',       val: co.currency },
      ]
    },
    {
      title: 'Data Coverage',
      rows: [
        { label: 'First Period', val: co.annuals[0].period || co.annuals[0].year },
        { label: 'Last Period',  val: latestLabel },
        { label: 'Period Type',  val: latest.periodType || '—' },
        { label: 'Data Points',  val: co.annuals.length },
      ]
    }
  ];

  const grid = document.getElementById('stats-grid');
  grid.innerHTML = sections.map(sec => `
    <div class="stat-section">
      <div class="stat-section-title">${sec.title}</div>
      ${sec.rows.map(r => `
        <div class="stat-row">
          <span class="stat-label">${r.label}</span>
          <span class="stat-val ${r.cls || ''}">${r.val}</span>
        </div>
      `).join('')}
    </div>
  `).join('');
}

// ---- Render Charts ----
function renderCharts(co, period) {
  period = period || 'annual';
  const hasQuarters = co.quarters && co.quarters.length > 0;
  
  // Data selection
  let dataPoints = (period === 'quarterly' && hasQuarters) ? [...co.quarters] : [...co.annuals];
  
  // Sort chronologically using dateKey (ISO date) if present, else year
  dataPoints.sort((a, b) => {
    const da = a.dateKey || String(a.year || '');
    const db = b.dateKey || String(b.year || '');
    return da.localeCompare(db);
  });

  const labels  = dataPoints.map(d => d.period || d.year);
  const n       = dataPoints.length;
  const colors  = barColors(n);
  const chartOpts = { showGrowth: period === 'annual', units: co.units };

  // Revenue / NII
  makeBarChart('chart-revenue', labels, [{
    label: 'Revenue/NII',
    data: dataPoints.map(d => d.revenue ?? d.nii),
    backgroundColor: colors,
    borderRadius: 4,
  }], chartOpts);

  // Net Income (PAT)
  makeBarChart('chart-pat', labels, [{
    label: 'Net Income',
    data: dataPoints.map(d => d.pat),
    backgroundColor: colors,
    borderRadius: 4,
  }], chartOpts);

  // EPS
  makeBarChart('chart-eps', labels, [{
    label: 'EPS',
    data: dataPoints.map(d => d.eps),
    backgroundColor: colors,
    borderRadius: 4,
  }], { ...chartOpts, isCurrency: true });

  // DPS
  makeBarChart('chart-dps', labels, [{
    label: 'DPS',
    data: dataPoints.map(d => d.dps),
    backgroundColor: colors,
    borderRadius: 4,
  }], { ...chartOpts, isCurrency: true });

  // NII
  makeBarChart('chart-nii', labels, [{
    label: 'NII',
    data: dataPoints.map(d => d.nii),
    backgroundColor: colors,
    borderRadius: 4,
  }], chartOpts);

  // Balance Sheet
  makeBarChart('chart-assets', labels, [{
    label: 'Total Assets',
    data: dataPoints.map(d => d.totalAssets),
    backgroundColor: colors,
    borderRadius: 4,
  }], chartOpts);

  makeBarChart('chart-equity', labels, [{
    label: 'Total Equity',
    data: dataPoints.map(d => d.totalEquity),
    backgroundColor: colors,
    borderRadius: 4,
  }], chartOpts);

  makeBarChart('chart-deposits', labels, [{
    label: 'Deposits',
    data: dataPoints.map(d => d.deposits),
    backgroundColor: colors,
    borderRadius: 4,
  }], chartOpts);

  makeBarChart('chart-loans', labels, [{
    label: 'Loans',
    data: dataPoints.map(d => d.loans),
    backgroundColor: colors,
    borderRadius: 4,
  }], chartOpts);

  const ebitdaData = dataPoints.map(d => d.mpesa ?? d.ebitda);
  makeBarChart('chart-ebitda', labels, [{
    label: co.ticker === 'SCOM' ? 'M-PESA Revenue' : 'EBITDA',
    data: ebitdaData,
    backgroundColor: colors,
    borderRadius: 4,
  }], chartOpts);
}

// ---- TradingView Live Price Chart ----
function initTradingViewChart(ticker, fullHeight) {
  const nsekeTicker = getTVSymbol(ticker);

  const section   = document.getElementById('tv-chart-section');
  const container = document.getElementById('tradingview-chart-container');
  const link      = document.getElementById('tv-open-link');

  section.classList.remove('hidden');
  container.classList.toggle('tv-chart-full', !!fullHeight);

  if (link) {
    link.href = `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(nsekeTicker)}`;
  }

  // Re-create inner div to force widget reset when switching companies
  container.innerHTML = '<div id="tradingview_widget_inner" style="height:100%"></div>';

  if (typeof TradingView === 'undefined') {
    container.innerHTML = '<div class="tv-chart-error">TradingView chart could not load. Check your internet connection.</div>';
    return;
  }

  new TradingView.widget({
    autosize:            true,
    symbol:              nsekeTicker,
    interval:            'D',
    timezone:            'Africa/Nairobi',
    theme:               'dark',
    style:               '1',
    locale:              'en',
    toolbar_bg:          '#1e293b',
    enable_publishing:   false,
    withdateranges:      true,
    hide_side_toolbar:   false,
    allow_symbol_change: false,
    save_image:          false,
    container_id:        'tradingview_widget_inner',
  });
}

// ---- Period Toggle (annual / quarterly) ----
let _currentCompany = null;
let _currentPeriod = 'annual';

function setPeriod(period) {
  if (!_currentCompany) return;
  const hasQuarters = _currentCompany.quarters && _currentCompany.quarters.length > 0;
  // If no quarterly data, stay on annual
  if (period === 'quarterly' && !hasQuarters) {
    period = 'annual';
    // Flash the quarterly button to indicate no data
    const btn = document.getElementById('toggle-quarterly');
    btn.textContent = 'No quarterly data';
    setTimeout(() => { btn.textContent = 'Quarterly'; }, 1500);
  }
  _currentPeriod = period;
  document.getElementById('toggle-annual').classList.toggle('active', period === 'annual');
  document.getElementById('toggle-quarterly').classList.toggle('active', period === 'quarterly');
  renderCharts(_currentCompany, period);
}

// ---- Populate dropdown from NSE_COMPANIES + NSE_ALL_STOCKS with two optgroups ----
// Group 1: Full Data (all NSE_COMPANIES) — Group 2: Price Chart Only (others)
function populateDropdown() {
  const sel = document.getElementById('company-select');

  // Build Full Data entries from NSE_COMPANIES (internal tickers → TV tickers)
  const fullDataEntries = Object.keys(NSE_COMPANIES).map(internal => {
    const tvTicker = INTERNAL_TO_TV[internal] || internal;
    const name = NSE_ALL_STOCKS[tvTicker] || NSE_COMPANIES[internal].name;
    return { value: tvTicker, display: `${tvTicker} — ${name}`, name };
  }).sort((a, b) => a.name.localeCompare(b.name));

  // Set of TV tickers covered by Full Data group (to exclude from Price Chart Only)
  const fullDataTVSet = new Set(fullDataEntries.map(e => e.value));

  // Full Data group
  const fullDataGrp = document.createElement('optgroup');
  fullDataGrp.label = '⭐ Full Data';
  for (const { value, display } of fullDataEntries) {
    const opt = document.createElement('option');
    opt.value = value;
    opt.textContent = display;
    fullDataGrp.appendChild(opt);
  }
  sel.appendChild(fullDataGrp);

  // Price Chart Only group (all NSE_ALL_STOCKS not covered by Full Data)
  const priceOnlyGrp = document.createElement('optgroup');
  priceOnlyGrp.label = '📈 Price Chart Only';
  const priceOnlyEntries = Object.entries(NSE_ALL_STOCKS)
    .filter(([ticker]) => !fullDataTVSet.has(ticker))
    .sort((a, b) => a[1].localeCompare(b[1]));
  for (const [ticker, name] of priceOnlyEntries) {
    const opt = document.createElement('option');
    opt.value = ticker;
    opt.textContent = `${ticker} — ${name}`;
    priceOnlyGrp.appendChild(opt);
  }
  sel.appendChild(priceOnlyGrp);
}

// ---- Enter key on select ----
document.addEventListener('DOMContentLoaded', () => {
  populateDropdown();
  document.getElementById('company-select').addEventListener('keydown', e => {
    if (e.key === 'Enter') loadCompany();
  });
});
