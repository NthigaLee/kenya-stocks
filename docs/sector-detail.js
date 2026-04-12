// ═══════════════════════════════════════════════════════════════
// Sector Detail Dashboard — Banking-first, template for others
// ═══════════════════════════════════════════════════════════════

(function () {
  'use strict';

  let _activeTab = 'overview';
  let _yearView = '2024';
  let _sectorCompanies = [];
  let _charts = {};

  // ── Public entry point ──────────────────────────────────────
  window.renderSectorDetail = function (sectorName) {
    const wrap = document.getElementById('sector-detail');
    if (!wrap) return;

    // Gather sector companies
    _sectorCompanies = Object.entries(NSE_COMPANIES)
      .filter(([, co]) => normalizeSector(co.sector) === sectorName)
      .map(([ticker, co]) => ({ ticker, ...co }));

    // Show the detail panel, hide grid, old table & heatmap
    document.getElementById('sector-grid').style.display = 'none';
    document.getElementById('sector-table-wrap').classList.add('hidden');
    const heatmap = document.querySelector('.sector-heatmap-wrap');
    if (heatmap) heatmap.style.display = 'none';
    wrap.classList.remove('hidden');

    // Set hero
    document.getElementById('sd-hero-title').textContent =
      sectorName + ' Sector: The Full Story';
    document.getElementById('sd-hero-subtitle').textContent =
      `${_sectorCompanies.length} NSE-listed companies — FY 2024 vs FY 2023`;

    // Wire tabs
    wrap.querySelectorAll('.sd-tab').forEach(btn => {
      btn.onclick = () => switchTab(btn.dataset.tab);
    });

    // Wire year radio
    wrap.querySelectorAll('input[name="sd-year"]').forEach(r => {
      r.onchange = () => { _yearView = r.value; renderActiveTab(); };
    });

    // Wire back button
    document.getElementById('sd-back-btn').onclick = () => {
      wrap.classList.add('hidden');
      document.getElementById('sector-grid').style.display = '';
      const heatmap = document.querySelector('.sector-heatmap-wrap');
      if (heatmap) heatmap.style.display = '';
      destroyCharts();
    };

    // Wire profitability metric radio
    wrap.querySelectorAll('input[name="sd-profit-metric"]').forEach(r => {
      r.onchange = () => { if (_activeTab === 'profitability') renderProfitability(); };
    });

    // Wire deep-dive bank selector
    const sel = document.getElementById('sd-bank-select');
    if (sel) {
      sel.innerHTML = _sectorCompanies
        .sort((a, b) => getAnnual(b, 'pat') - getAnnual(a, 'pat'))
        .map(c => `<option value="${c.ticker}">${c.name}</option>`)
        .join('');
      sel.onchange = () => renderDeepDive();
    }

    switchTab('overview');
  };

  window.hideSectorDetail = function () {
    const wrap = document.getElementById('sector-detail');
    if (wrap) wrap.classList.add('hidden');
    const heatmap = document.querySelector('.sector-heatmap-wrap');
    if (heatmap) heatmap.style.display = '';
    destroyCharts();
  };

  // ── Helpers ─────────────────────────────────────────────────
  function getAnnual(co, field, year) {
    const yr = year || (_yearView === 'both' ? 2024 : parseInt(_yearView));
    const a = (co.annuals || []).find(a => a.year === yr);
    return a ? (a[field] || 0) : 0;
  }

  function getLatest(co, field) {
    return co.latestPeriod ? (co.latestPeriod[field] || 0) : getAnnual(co, field, 2024);
  }

  function fmt(n, decimals) {
    if (n === 0 || n == null) return '-';
    const abs = Math.abs(n);
    const d = decimals != null ? decimals : 1;
    if (abs >= 1e9) return 'Shs ' + (n / 1e9).toFixed(d) + 'Tn';
    if (abs >= 1e6) return 'Shs ' + (n / 1e6).toFixed(d) + 'Bn';
    if (abs >= 1e3) return 'Shs ' + (n / 1e3).toFixed(d) + 'Mn';
    return n.toFixed(d);
  }

  // KShs'000 to Shs Bn display
  function fmtBn(n) {
    if (!n) return '-';
    const bn = n / 1e6; // KShs'000 → billions
    return 'Shs ' + bn.toFixed(1) + 'Bn';
  }

  function fmtPct(n) {
    if (n == null || isNaN(n)) return '-';
    return n.toFixed(1) + '%';
  }

  function yoyChange(co, field) {
    const v24 = getAnnual(co, field, 2024);
    const v23 = getAnnual(co, field, 2023);
    if (!v23 || !v24) return null;
    return ((v24 - v23) / Math.abs(v23)) * 100;
  }

  function sectorSum(field, year) {
    return _sectorCompanies.reduce((s, c) => s + getAnnual(c, field, year), 0);
  }

  function sectorAvg(field, year) {
    const vals = _sectorCompanies
      .map(c => getAnnual(c, field, year))
      .filter(v => v !== 0);
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
  }

  function computeROE(co, year) {
    const pat = getAnnual(co, 'pat', year);
    const eq = getAnnual(co, 'totalEquity', year);
    return eq ? (pat / eq) * 100 : 0;
  }

  function computeROA(co, year) {
    const pat = getAnnual(co, 'pat', year);
    const ta = getAnnual(co, 'totalAssets', year);
    return ta ? (pat / ta) * 100 : 0;
  }

  function computeNIM(co, year) {
    const nii = getAnnual(co, 'nii', year);
    const ta = getAnnual(co, 'totalAssets', year);
    return ta ? (nii / ta) * 100 : 0;
  }

  function computeCIR(co, year) {
    const cir = getAnnual(co, 'costToIncomeRatio', year);
    if (cir) return cir;
    const opex = getAnnual(co, 'totalOpex', year);
    const rev = getAnnual(co, 'revenue', year);
    return rev ? (opex / rev) * 100 : 0;
  }

  function shortName(name) {
    return name.replace(/ (Holdings|Group|Plc|Ltd|Limited|Kenya|Bank of Kenya)/gi, '').trim();
  }

  // ── Chart management ────────────────────────────────────────
  function destroyCharts() {
    Object.values(_charts).forEach(c => { try { c.destroy(); } catch (e) {} });
    _charts = {};
  }

  function makeChart(canvasId, config) {
    if (_charts[canvasId]) { try { _charts[canvasId].destroy(); } catch (e) {} }
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    _charts[canvasId] = new Chart(ctx, config);
    return _charts[canvasId];
  }

  // Chart.js defaults for dark theme
  const COLORS = {
    bars2024: '#0d5c63',
    bars2023: '#7ec8c8',
    accent: '#00e676',
    grid: 'rgba(255,255,255,0.06)',
    text: '#909090',
  };

  const BANK_COLORS = [
    '#0d3b66', '#1b6b93', '#4fc0d0', '#a2d5ab', '#ffd93d',
    '#ff8a5c', '#ea5455', '#6c5ce7', '#00b894', '#e17055',
    '#74b9ff', '#a29bfe', '#fd79a8',
  ];

  function chartDefaults() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: COLORS.text, font: { size: 11 } } },
      },
      scales: {
        x: { ticks: { color: COLORS.text, font: { size: 10 } }, grid: { color: COLORS.grid } },
        y: { ticks: { color: COLORS.text, font: { size: 10 } }, grid: { color: COLORS.grid } },
      },
    };
  }

  // ── Tab switching ───────────────────────────────────────────
  function switchTab(tab) {
    _activeTab = tab;
    document.querySelectorAll('.sd-tab').forEach(b =>
      b.classList.toggle('active', b.dataset.tab === tab)
    );
    document.querySelectorAll('.sd-panel').forEach(p =>
      p.classList.toggle('hidden', p.id !== 'sd-tab-' + tab)
    );
    renderActiveTab();
  }

  function renderActiveTab() {
    destroyCharts();
    switch (_activeTab) {
      case 'overview': renderOverview(); break;
      case 'profitability': renderProfitability(); break;
      case 'efficiency': renderEfficiency(); break;
      case 'deep-dive': renderDeepDive(); break;
    }
  }

  // ═══════════════════════════════════════════════════════════
  // TAB 1: OVERVIEW
  // ═══════════════════════════════════════════════════════════
  function renderOverview() {
    const yr = _yearView === 'both' ? 2024 : parseInt(_yearView);
    const yr2 = yr === 2024 ? 2023 : 2022;

    // KPI calculations
    const totalPAT = sectorSum('pat', yr);
    const totalPATPrev = sectorSum('pat', yr2);
    const patYoY = totalPATPrev ? ((totalPAT - totalPATPrev) / Math.abs(totalPATPrev)) * 100 : 0;

    const totalAssets = sectorSum('totalAssets', yr);
    const totalAssetsPrev = sectorSum('totalAssets', yr2);
    const assetsYoY = totalAssetsPrev ? ((totalAssets - totalAssetsPrev) / Math.abs(totalAssetsPrev)) * 100 : 0;

    const totalDeposits = sectorSum('deposits', yr);
    const totalLoans = sectorSum('loans', yr);

    const roeVals = _sectorCompanies.map(c => computeROE(c, yr)).filter(v => v > 0);
    const avgROE = roeVals.length ? roeVals.reduce((a, b) => a + b, 0) / roeVals.length : 0;

    const nimVals = _sectorCompanies.map(c => computeNIM(c, yr)).filter(v => v > 0);
    const avgNIM = nimVals.length ? nimVals.reduce((a, b) => a + b, 0) / nimVals.length : 0;

    const cirVals = _sectorCompanies.map(c => computeCIR(c, yr)).filter(v => v > 0);
    const avgCIR = cirVals.length ? cirVals.reduce((a, b) => a + b, 0) / cirVals.length : 0;

    // Render KPI cards
    const kpi1 = document.getElementById('sd-kpi-row-1');
    kpi1.innerHTML = kpiCard('SECTOR PAT', fmtBn(totalPAT), patYoY, `FY ${yr} combined`) +
      kpiCard('TOTAL ASSETS', fmtBn(totalAssets), assetsYoY, `${_sectorCompanies.length} banks`) +
      kpiCard('CUSTOMER DEPOSITS', fmtBn(totalDeposits), null, 'Total sector') +
      kpiCard('TOTAL LOANS', fmtBn(totalLoans), null, 'Net advances');

    const kpi2 = document.getElementById('sd-kpi-row-2');
    kpi2.innerHTML = kpiCard('AVG RETURN ON EQUITY', fmtPct(avgROE), null, 'Sector average') +
      kpiCard('AVG NET INTEREST MARGIN', fmtPct(avgNIM), null, 'Sector average') +
      kpiCard('AVG COST-TO-INCOME', fmtPct(avgCIR), null, 'Lower = better') +
      kpiCard('COMPANIES', String(_sectorCompanies.length), null, 'NSE-listed');

    // PAT Ranking chart
    const sorted = [..._sectorCompanies]
      .sort((a, b) => getAnnual(b, 'pat', yr) - getAnnual(a, 'pat', yr));

    makeChart('sd-chart-pat-ranking', {
      type: 'bar',
      data: {
        labels: sorted.map(c => shortName(c.name)),
        datasets: [{
          label: `PAT FY ${yr} (Shs Mn)`,
          data: sorted.map(c => getAnnual(c, 'pat', yr) / 1000), // KShs'000 → millions
          backgroundColor: sorted.map((_, i) => BANK_COLORS[i % BANK_COLORS.length]),
          borderRadius: 3,
        }],
      },
      options: {
        ...chartDefaults(),
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => 'Shs ' + (ctx.raw / 1000).toFixed(1) + 'Bn',
            },
          },
        },
        scales: {
          x: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, title: { display: true, text: 'Shs Millions', color: COLORS.text } },
          y: { ticks: { color: '#f0f0f0', font: { size: 11 } }, grid: { display: false } },
        },
      },
    });

    // Top Earners callout
    const topEl = document.getElementById('sd-top-earners');
    if (topEl) {
      const top3 = sorted.slice(0, 3);
      topEl.innerHTML = '<h4>Top Earners</h4>' + top3.map((c, i) =>
        `<p><strong>${i + 1}. ${shortName(c.name)}</strong> — ${fmtBn(getAnnual(c, 'pat', yr))}</p>`
      ).join('');
    }

    // Asset treemap (simplified as stacked bar since Chart.js doesn't have treemap by default)
    const assetSorted = [..._sectorCompanies]
      .sort((a, b) => getAnnual(b, 'totalAssets', yr) - getAnnual(a, 'totalAssets', yr))
      .filter(c => getAnnual(c, 'totalAssets', yr) > 0);

    const treemapEl = document.getElementById('sd-asset-treemap');
    if (treemapEl) {
      treemapEl.innerHTML = assetSorted.map((c, i) => {
        const assets = getAnnual(c, 'totalAssets', yr);
        const pct = (assets / totalAssets) * 100;
        const roe = computeROE(c, yr);
        const opacity = Math.min(0.3 + (roe / 30) * 0.7, 1);
        return `<div class="sd-treemap-tile" style="flex:${Math.max(pct, 3)};opacity:${opacity.toFixed(2)}">
          <span class="sd-treemap-name">${shortName(c.name)}</span>
          <span class="sd-treemap-val">${(assets / 1e6).toFixed(0)}Bn</span>
          <span class="sd-treemap-roe">ROE ${roe.toFixed(1)}%</span>
        </div>`;
      }).join('');
    }
  }

  function kpiCard(label, value, yoy, sublabel) {
    const yoyHtml = yoy != null
      ? `<span class="sd-kpi-yoy ${yoy >= 0 ? 'pos' : 'neg'}">${yoy >= 0 ? '&#9650;' : '&#9660;'} ${Math.abs(yoy).toFixed(1)}% YoY</span>`
      : '';
    return `<div class="sd-kpi-card">
      <div class="sd-kpi-label">${label}</div>
      <div class="sd-kpi-value">${value}</div>
      ${yoyHtml}
      <div class="sd-kpi-sub">${sublabel || ''}</div>
    </div>`;
  }

  // ═══════════════════════════════════════════════════════════
  // TAB 2: PROFITABILITY LEAGUE
  // ═══════════════════════════════════════════════════════════
  function renderProfitability() {
    const yr = _yearView === 'both' ? 2024 : parseInt(_yearView);
    const yr2 = yr === 2024 ? 2023 : 2022;

    // Get selected metric from radio
    const metricRadio = document.querySelector('input[name="sd-profit-metric"]:checked');
    const metric = metricRadio ? metricRadio.value : 'pat';

    const metricLabels = { pat: 'Profit After Tax', pbt: 'Profit Before Tax', revenue: 'Total Revenue', nii: 'Net Interest Income' };

    const sorted = [..._sectorCompanies]
      .sort((a, b) => getAnnual(b, metric, yr) - getAnnual(a, metric, yr));

    // Grouped bar: 2024 vs 2023
    makeChart('sd-chart-profitability', {
      type: 'bar',
      data: {
        labels: sorted.map(c => shortName(c.name)),
        datasets: [
          {
            label: `${yr}`,
            data: sorted.map(c => getAnnual(c, metric, yr) / 1000),
            backgroundColor: COLORS.bars2024,
            borderRadius: 3,
          },
          {
            label: `${yr2}`,
            data: sorted.map(c => getAnnual(c, metric, yr2) / 1000),
            backgroundColor: COLORS.bars2023,
            borderRadius: 3,
          },
        ],
      },
      options: {
        ...chartDefaults(),
        plugins: {
          title: { display: true, text: `${metricLabels[metric]} — ${yr} vs ${yr2} (Shs Mn)`, color: '#7ec8c8', font: { size: 14 } },
          legend: { labels: { color: COLORS.text } },
          tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': Shs ' + (ctx.raw / 1000).toFixed(1) + 'Bn' } },
        },
        scales: {
          x: { ticks: { color: COLORS.text, maxRotation: 45 }, grid: { color: COLORS.grid } },
          y: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, title: { display: true, text: 'Shs Millions', color: COLORS.text } },
        },
      },
    });

    // YoY Growth charts side-by-side
    const patGrowth = sorted.map(c => ({
      name: shortName(c.name),
      growth: yoyChange(c, 'pat'),
    })).filter(g => g.growth != null).sort((a, b) => b.growth - a.growth);

    makeChart('sd-chart-pat-growth', {
      type: 'bar',
      data: {
        labels: patGrowth.map(g => g.name),
        datasets: [{
          label: 'PAT Growth %',
          data: patGrowth.map(g => g.growth),
          backgroundColor: patGrowth.map(g => g.growth >= 0 ? COLORS.bars2024 : '#ea5455'),
          borderRadius: 3,
        }],
      },
      options: {
        ...chartDefaults(),
        indexAxis: 'y',
        plugins: {
          title: { display: true, text: `PAT Growth — YoY %`, color: '#7ec8c8', font: { size: 13 } },
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => (ctx.raw >= 0 ? '+' : '') + ctx.raw.toFixed(1) + '%' } },
        },
        scales: {
          x: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, title: { display: true, text: '% Change', color: COLORS.text } },
          y: { ticks: { color: '#f0f0f0', font: { size: 11 } }, grid: { display: false } },
        },
      },
    });

    const revGrowth = sorted.map(c => ({
      name: shortName(c.name),
      growth: yoyChange(c, 'revenue'),
    })).filter(g => g.growth != null).sort((a, b) => b.growth - a.growth);

    makeChart('sd-chart-rev-growth', {
      type: 'bar',
      data: {
        labels: revGrowth.map(g => g.name),
        datasets: [{
          label: 'Revenue Growth %',
          data: revGrowth.map(g => g.growth),
          backgroundColor: revGrowth.map(g => g.growth >= 0 ? COLORS.bars2024 : '#ea5455'),
          borderRadius: 3,
        }],
      },
      options: {
        ...chartDefaults(),
        indexAxis: 'y',
        plugins: {
          title: { display: true, text: `Revenue Growth — YoY %`, color: '#7ec8c8', font: { size: 13 } },
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => (ctx.raw >= 0 ? '+' : '') + ctx.raw.toFixed(1) + '%' } },
        },
        scales: {
          x: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, title: { display: true, text: '% Change', color: COLORS.text } },
          y: { ticks: { color: '#f0f0f0', font: { size: 11 } }, grid: { display: false } },
        },
      },
    });
  }

  // ═══════════════════════════════════════════════════════════
  // TAB 3: CORE EFFICIENCY
  // ═══════════════════════════════════════════════════════════
  function renderEfficiency() {
    const yr = _yearView === 'both' ? 2024 : parseInt(_yearView);

    // NIM ranking
    const nimData = _sectorCompanies
      .map(c => ({ name: shortName(c.name), val: computeNIM(c, yr) }))
      .filter(d => d.val > 0)
      .sort((a, b) => b.val - a.val);

    makeChart('sd-chart-nim', {
      type: 'bar',
      data: {
        labels: nimData.map(d => d.name),
        datasets: [{
          label: `NIM % (FY ${yr})`,
          data: nimData.map(d => d.val),
          backgroundColor: COLORS.bars2024,
          borderRadius: 3,
        }],
      },
      options: {
        ...chartDefaults(),
        indexAxis: 'y',
        plugins: {
          title: { display: true, text: `Net Interest Margin — Sector Ranking`, color: '#7ec8c8', font: { size: 13 } },
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => ctx.raw.toFixed(1) + '%' } },
        },
        scales: {
          x: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, title: { display: true, text: 'NIM %', color: COLORS.text } },
          y: { ticks: { color: '#f0f0f0', font: { size: 11 } }, grid: { display: false } },
        },
      },
    });

    // CIR ranking
    const cirData = _sectorCompanies
      .map(c => ({ name: shortName(c.name), val: computeCIR(c, yr) }))
      .filter(d => d.val > 0)
      .sort((a, b) => a.val - b.val); // lower is better

    makeChart('sd-chart-cir', {
      type: 'bar',
      data: {
        labels: cirData.map(d => d.name),
        datasets: [{
          label: `CIR % (FY ${yr})`,
          data: cirData.map(d => d.val),
          backgroundColor: cirData.map(d => d.val < 50 ? '#00b894' : d.val < 60 ? '#ffd93d' : '#ea5455'),
          borderRadius: 3,
        }],
      },
      options: {
        ...chartDefaults(),
        indexAxis: 'y',
        plugins: {
          title: { display: true, text: `Cost-to-Income Ratio — Lower is Better`, color: '#7ec8c8', font: { size: 13 } },
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => ctx.raw.toFixed(1) + '%' } },
        },
        scales: {
          x: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, title: { display: true, text: 'CIR %', color: COLORS.text } },
          y: { ticks: { color: '#f0f0f0', font: { size: 11 } }, grid: { display: false } },
        },
      },
    });

    // ROE ranking
    const roeData = _sectorCompanies
      .map(c => ({ name: shortName(c.name), val: computeROE(c, yr) }))
      .filter(d => d.val > 0)
      .sort((a, b) => b.val - a.val);

    makeChart('sd-chart-roe', {
      type: 'bar',
      data: {
        labels: roeData.map(d => d.name),
        datasets: [{
          label: `ROE % (FY ${yr})`,
          data: roeData.map(d => d.val),
          backgroundColor: COLORS.bars2024,
          borderRadius: 3,
        }],
      },
      options: {
        ...chartDefaults(),
        indexAxis: 'y',
        plugins: {
          title: { display: true, text: `Return on Equity — ${yr}`, color: '#7ec8c8', font: { size: 13 } },
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => ctx.raw.toFixed(1) + '%' } },
        },
        scales: {
          x: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, title: { display: true, text: 'ROE %', color: COLORS.text } },
          y: { ticks: { color: '#f0f0f0', font: { size: 11 } }, grid: { display: false } },
        },
      },
    });

    // ROA ranking
    const roaData = _sectorCompanies
      .map(c => ({ name: shortName(c.name), val: computeROA(c, yr) }))
      .filter(d => d.val > 0)
      .sort((a, b) => b.val - a.val);

    makeChart('sd-chart-roa', {
      type: 'bar',
      data: {
        labels: roaData.map(d => d.name),
        datasets: [{
          label: `ROA % (FY ${yr})`,
          data: roaData.map(d => d.val),
          backgroundColor: COLORS.bars2023,
          borderRadius: 3,
        }],
      },
      options: {
        ...chartDefaults(),
        indexAxis: 'y',
        plugins: {
          title: { display: true, text: `Return on Assets — ${yr}`, color: '#7ec8c8', font: { size: 13 } },
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => ctx.raw.toFixed(1) + '%' } },
        },
        scales: {
          x: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, title: { display: true, text: 'ROA %', color: COLORS.text } },
          y: { ticks: { color: '#f0f0f0', font: { size: 11 } }, grid: { display: false } },
        },
      },
    });
  }

  // ═══════════════════════════════════════════════════════════
  // TAB 4: BANK DEEP DIVE
  // ═══════════════════════════════════════════════════════════
  function renderDeepDive() {
    const sel = document.getElementById('sd-bank-select');
    const ticker = sel ? sel.value : _sectorCompanies[0]?.ticker;
    const co = _sectorCompanies.find(c => c.ticker === ticker);
    if (!co) return;

    const yr = _yearView === 'both' ? 2024 : parseInt(_yearView);
    const yr2 = yr === 2024 ? 2023 : 2022;

    // Header
    document.getElementById('sd-dd-name').textContent = co.name;
    document.getElementById('sd-dd-subtitle').textContent =
      `NSE Ticker: ${co.ticker} · FY ${yr} Performance Review`;

    // KPI cards
    const pat = getAnnual(co, 'pat', yr);
    const rev = getAnnual(co, 'revenue', yr);
    const ta = getAnnual(co, 'totalAssets', yr);
    const roe = computeROE(co, yr);
    const nim = computeNIM(co, yr);

    const patChg = yoyChange(co, 'pat');
    const revChg = yoyChange(co, 'revenue');
    const taChg = yoyChange(co, 'totalAssets');

    document.getElementById('sd-dd-kpis').innerHTML =
      kpiCard(`PAT ${yr}`, fmtBn(pat), patChg, '') +
      kpiCard(`REVENUE ${yr}`, fmtBn(rev), revChg, '') +
      kpiCard('TOTAL ASSETS', fmtBn(ta), taChg, '') +
      kpiCard('ROE', fmtPct(roe), null, '') +
      kpiCard('NIM', fmtPct(nim), null, '');

    // P&L Waterfall
    const nii = getAnnual(co, 'nii', yr);
    const nonInt = rev - nii;
    const opex = getAnnual(co, 'totalOpex', yr);
    const impairment = getAnnual(co, 'loanLossProvision', yr);
    const pbt = getAnnual(co, 'pbt', yr);
    const tax = pbt - pat;

    if (nii && opex) {
      // Waterfall as bar chart
      const labels = ['NII', 'Non-Int Income', 'Operating Expenses', 'Impairments', 'PBT', 'Tax', 'PAT'];
      const values = [nii, nonInt, -opex, -impairment, pbt, -tax, pat].map(v => v / 1000);
      const colors = values.map(v => v >= 0 ? '#0d5c63' : '#ea5455');
      colors[colors.length - 1] = '#1b6b93'; // PAT gets different color

      makeChart('sd-chart-waterfall', {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Shs Millions',
            data: values,
            backgroundColor: colors,
            borderRadius: 3,
          }],
        },
        options: {
          ...chartDefaults(),
          plugins: {
            title: { display: true, text: `${shortName(co.name)} — P&L Waterfall (Shs Mn)`, color: '#7ec8c8', font: { size: 13 } },
            legend: { display: false },
            tooltip: { callbacks: { label: ctx => 'Shs ' + (Math.abs(ctx.raw) / 1000).toFixed(1) + 'Bn' } },
          },
          scales: {
            x: { ticks: { color: COLORS.text }, grid: { display: false } },
            y: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, title: { display: true, text: 'Shs Millions', color: COLORS.text } },
          },
        },
      });
    } else {
      // No detailed data — show placeholder
      const ctx = document.getElementById('sd-chart-waterfall');
      if (ctx) {
        const parent = ctx.parentElement;
        parent.innerHTML = '<div class="sd-no-data">Detailed P&L breakdown not available for this bank.<br>Available for: ABSA, EQTY, SCBK, NCBA, KCB</div><canvas id="sd-chart-waterfall" style="display:none"></canvas>';
      }
    }

    // Balance sheet composition (doughnut)
    const deposits = getAnnual(co, 'deposits', yr);
    const equity = getAnnual(co, 'totalEquity', yr);
    const loans = getAnnual(co, 'loans', yr);
    const otherAssets = ta - loans;
    const otherLiab = ta - deposits - equity;

    if (ta > 0 && (deposits > 0 || equity > 0)) {
      makeChart('sd-chart-balance', {
        type: 'doughnut',
        data: {
          labels: ['Net Loans', 'Other Assets', 'Deposits', 'Equity', 'Other Liabilities'],
          datasets: [{
            data: [loans, otherAssets, deposits, equity, Math.max(otherLiab, 0)].map(v => v / 1e6),
            backgroundColor: ['#0d3b66', '#7ec8c8', '#1b6b93', '#4fc0d0', '#a2d5ab'],
            borderWidth: 1,
            borderColor: '#111111',
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '55%',
          plugins: {
            title: { display: true, text: `${shortName(co.name)} — Balance Sheet (Shs Bn)`, color: '#7ec8c8', font: { size: 13 } },
            legend: { position: 'right', labels: { color: COLORS.text, font: { size: 11 }, padding: 12 } },
            tooltip: { callbacks: { label: ctx => ctx.label + ': Shs ' + ctx.raw.toFixed(0) + 'Bn' } },
          },
        },
      });
    }

    // Radar chart: bank vs sector average
    const sectorAvgROE = _sectorCompanies.map(c => computeROE(c, yr)).filter(v => v > 0);
    const sectorAvgROA = _sectorCompanies.map(c => computeROA(c, yr)).filter(v => v > 0);
    const sectorAvgNIM = _sectorCompanies.map(c => computeNIM(c, yr)).filter(v => v > 0);
    const sectorAvgCIR = _sectorCompanies.map(c => computeCIR(c, yr)).filter(v => v > 0);

    const avg = arr => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;

    const bankROE = computeROE(co, yr);
    const bankROA = computeROA(co, yr);
    const bankNIM = computeNIM(co, yr);
    const bankCIR = computeCIR(co, yr);

    if (bankROE > 0 || bankNIM > 0) {
      makeChart('sd-chart-radar', {
        type: 'radar',
        data: {
          labels: ['ROE (%)', 'ROA (%)', 'NIM (%)', 'CIR (%)'],
          datasets: [
            {
              label: shortName(co.name),
              data: [bankROE, bankROA * 10, bankNIM, 100 - bankCIR], // Normalize: invert CIR so higher=better
              backgroundColor: 'rgba(13, 92, 99, 0.3)',
              borderColor: '#0d5c63',
              borderWidth: 2,
              pointBackgroundColor: '#0d5c63',
            },
            {
              label: 'Sector Average',
              data: [avg(sectorAvgROE), avg(sectorAvgROA) * 10, avg(sectorAvgNIM), 100 - avg(sectorAvgCIR)],
              backgroundColor: 'rgba(126, 200, 200, 0.15)',
              borderColor: '#7ec8c8',
              borderWidth: 2,
              borderDash: [5, 5],
              pointBackgroundColor: '#7ec8c8',
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: { display: true, text: 'Performance Scorecard vs Sector', color: '#7ec8c8', font: { size: 13 } },
            legend: { labels: { color: COLORS.text } },
          },
          scales: {
            r: {
              angleLines: { color: COLORS.grid },
              grid: { color: COLORS.grid },
              pointLabels: { color: '#f0f0f0', font: { size: 11 } },
              ticks: { display: false },
            },
          },
        },
      });
    }
  }

})();
