// Global Stocks Dashboard - App Logic
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
    const exchange = document.getElementById('exchangeFilter').value;
    const sector = document.getElementById('sectorFilter').value;
    const search = document.getElementById('searchInput').value.toLowerCase();
    
    currentData = GLOBAL_STOCKS_DATA.filter(c => {
        if (exchange && c.exchange !== exchange) return false;
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
