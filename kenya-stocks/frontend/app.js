// ============================================================
//  NSE Insights — App Logic
//  Qualtrim-style dashboard for Kenya NSE stocks
// ============================================================

let activeCompany = null;
let chartInstances = {};

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
  const sel = document.getElementById('company-select').value;
  if (!sel || !NSE_COMPANIES[sel]) {
    alert('Please select a company first.');
    return;
  }
  const co = NSE_COMPANIES[sel];
  activeCompany = co;
  _currentCompany = co;
  _currentPeriod = 'annual';
  // Reset toggle to annual
  document.getElementById('toggle-annual').classList.add('active');
  document.getElementById('toggle-quarterly').classList.remove('active');

  // Show dashboard, hide empty state
  document.getElementById('dashboard').classList.remove('hidden');
  document.getElementById('empty-state').classList.add('hidden');

  // Update breadcrumb
  document.getElementById('breadcrumb-company').textContent = `${co.ticker} | NSE`;

  // -- Company Header --
  document.getElementById('company-logo').textContent = co.logo;
  document.getElementById('company-name').textContent = co.name;
  document.getElementById('company-meta').textContent = `${co.ticker} | ${co.exchange} · ${co.sector}`;
  document.getElementById('company-price').textContent = fmtPrice(co.latestPrice);

  // Latest period (may be quarterly — more up-to-date than last annual)
  const latest = co.latestPeriod || co.annuals[co.annuals.length - 1];
  const latestLabel = latest.period || latest.year;
  document.getElementById('company-eps-pill').textContent = `EPS (${latestLabel}): ${fmtEPS(latest.eps)}`;
  document.getElementById('company-latest-year').textContent =
    `Units: KES ${co.units} · Last period: ${latestLabel}`;

  // -- Stock Price Chart --
  _activePriceRange = '1Y';
  loadStockPrice(co.ticker, '1Y');

  // -- Stats Grid --
  renderStatsGrid(co);

  // -- Charts --
  renderCharts(co, 'annual');
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
  
  // Sort by period/year to ensure chronological order
  dataPoints.sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year;
    return (a.period || '').localeCompare(b.period || '');
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
  const yfTicker = encodeURIComponent(ticker + '.NR');
  const direct = `https://query1.finance.yahoo.com/v8/finance/chart/${yfTicker}?interval=${interval}&range=${range}`;
  const proxy  = `https://corsproxy.io/?url=${encodeURIComponent(direct)}`;

  for (const url of [direct, proxy]) {
    try {
      const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
      if (!res.ok) continue;
      const json = await res.json();
      const result = json?.chart?.result?.[0];
      if (!result) continue;
      const timestamps = result.timestamp;
      const closes     = result.indicators?.quote?.[0]?.close;
      if (!timestamps || !closes) continue;
      return timestamps
        .map((t, i) => ({ t: t * 1000, v: closes[i] }))
        .filter(p => p.v !== null && p.v !== undefined);
    } catch (_) { /* try next */ }
  }
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
    return d.toLocaleDateString('en-KE', { month: 'short', day: 'numeric', year: rangeKey === '5Y' ? 'numeric' : undefined });
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
      datasets: [{
        label: 'Price (KES)',
        data: values,
        borderColor: color,
        backgroundColor: bgColor,
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
        fill: true,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 300 },
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: '#1e293b',
          borderColor: '#334155',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: (item) => ` KES ${item.raw?.toFixed(2)}`,
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 9 },
            maxTicksLimit: 8,
            maxRotation: 0,
          }
        },
        y: {
          position: 'right',
          grid: { color: 'rgba(51,65,85,0.4)', drawTicks: false },
          border: { display: false },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            callback: (v) => 'KES ' + v.toFixed(1),
          }
        }
      }
    }
  });
}

async function loadStockPrice(ticker, rangeKey) {
  rangeKey = rangeKey || _activePriceRange;
  _activePriceRange = rangeKey;

  // Highlight active button
  document.querySelectorAll('.price-range-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.range === rangeKey);
  });

  const priceSection = document.getElementById('price-chart-section');
  const loadingEl    = document.getElementById('price-chart-loading');
  const errorEl      = document.getElementById('price-chart-error');
  priceSection.classList.remove('hidden');
  loadingEl.classList.remove('hidden');
  errorEl.classList.add('hidden');

  const { interval, range } = PRICE_RANGES[rangeKey];
  const points = await fetchYahooChart(ticker, interval, range);

  loadingEl.classList.add('hidden');
  if (!points || points.length === 0) {
    errorEl.classList.remove('hidden');
    return;
  }

  // Update price change pill
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

// ---- Populate dropdown from NSE_COMPANIES (grouped by sector) ----
function populateDropdown() {
  const sel = document.getElementById('company-select');

  // Group tickers by sector
  const sectors = {};
  for (const [ticker, co] of Object.entries(NSE_COMPANIES)) {
    const sec = co.sector || 'Other';
    if (!sectors[sec]) sectors[sec] = [];
    sectors[sec].push({ ticker, name: co.name });
  }

  // Sort sectors, put Banking first
  const sectorOrder = ['Banking', 'Telecoms', 'FMCG', 'Insurance', 'Energy', 'Construction', 'Media', 'Agriculture', 'Manufacturing', 'Other'];
  const sortedSectors = Object.keys(sectors).sort((a, b) => {
    const ai = sectorOrder.indexOf(a);
    const bi = sectorOrder.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  for (const sector of sortedSectors) {
    const grp = document.createElement('optgroup');
    grp.label = sector;
    for (const { ticker, name } of sectors[sector].sort((a, b) => a.name.localeCompare(b.name))) {
      const opt = document.createElement('option');
      opt.value = ticker;
      opt.textContent = `${ticker} — ${name}`;
      grp.appendChild(opt);
    }
    sel.appendChild(grp);
  }
}

// ---- Enter key on select ----
document.addEventListener('DOMContentLoaded', () => {
  populateDropdown();
  document.getElementById('company-select').addEventListener('keydown', e => {
    if (e.key === 'Enter') loadCompany();
  });
});
