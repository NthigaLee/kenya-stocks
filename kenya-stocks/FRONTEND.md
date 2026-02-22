# FRONTEND.md — Kenya Stocks Dashboard UI Reference

_Last updated: 2026-02-22_

---

## File Structure

```
frontend/
├── index.html    — Page structure / layout
├── styles.css    — All styling (dark theme)
└── app.js        — Data loading + DOM manipulation
```

---

## Current State (V0 Prototype)

Very basic. Two sections, both showing sample/scraped data via FastAPI on port 8000.

### Sections

| Section ID | What it shows | API endpoint |
|---|---|---|
| `#stocks-section` | Stock symbols, names, prices, change | `GET /stocks/sample` |
| `#announcements-section` | Company, title, date, URL | `GET /announcements/nse` |

### Theme (Dark)

| Variable | Value | Used for |
|---|---|---|
| Background | `#0b0c10` | Body |
| Card/Header | `#1f2833` | Header, table headers, even rows bg |
| Accent (teal) | `#45a29e` | Border, accent lines |
| Row odd | `#151820` | Table alternating row |
| Row even | `#1b1f2a` | Table alternating row |
| Text primary | `#f5f5f5` | Body text |
| Text muted | `#c5c6c7` | Status messages |

### Fonts
- System font stack: `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

---

## How to Make UI Changes

### Change the theme/colours
Edit `styles.css`. The five core colours are in `body`, `header`, `#stocks-table th`, and the two `tr:nth-child` rules.

### Add a chart
1. Include Chart.js in `index.html`: `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
2. Add a `<canvas id="revenue-chart"></canvas>` in the section you want
3. In `app.js`, call `new Chart(ctx, { type: 'line', data: {...}, options: {...} })`

### Add a new section
1. In `index.html`, add a `<section id="new-section">` block
2. Style it in `styles.css`
3. Fetch data and populate in `app.js`

### Change chart order / section order
Reorder the `<section>` blocks in `index.html`.

### Add a company filter / dropdown
1. Add `<select id="company-filter">` in `index.html`
2. In `app.js`, listen on `change` and re-filter the rendered data

---

## Planned/Needed Upgrades

- [ ] Real company data from `financials.json` (not sample)
- [ ] Chart.js charts: Revenue, PAT, EPS, Total Assets over time
- [ ] Company selector (dropdown or tabs)
- [ ] Group vs Company data toggle
- [ ] Period filter (Annual / H1 / Q3)
- [ ] Mobile-responsive layout
- [ ] Key metrics summary cards (like Bloomberg terminal style)

---

## Backend API (FastAPI on port 8000)

| Endpoint | Returns |
|---|---|
| `GET /stocks/sample` | `{ stocks: [{symbol, name, price, change}] }` |
| `GET /announcements/nse` | `{ announcements: [{company, title, url, date}], count }` |

Backend is in `backend/app.py`. To add a new endpoint, add a route there and call it from `app.js`.
