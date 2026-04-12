You are working on the NSE Insights (kenya-stocks) project. The goal is to replace the TradingView embed with **self-hosted price charts** using Wanjawa’s Mendeley datasets (all NSE stocks, 2013–2025) and add a range selector: Max / 1Y / 1M / 1W / 1D.

## DATASETS TO USE (ALL DAILY PRICES, ALL NSE STOCKS)
Use these five Mendeley datasets as the canonical source of daily OHLC data:

- 2013–2020: `Nairobi Securities Exchange (NSE) All Stocks Prices 2013-2020`  (DOI: 10.17632/73rb78pmzw.2)
- 2021: `Nairobi Securities Exchange (NSE) Kenya - All Stocks Prices 2021` (DOI: 10.17632/97hkwn5y3x.3)
- 2022: `Kenya Nairobi Securities Exchange (NSE) All Stocks Prices 2022` (DOI: 10.17632/jmcdmnyh2s.2)
- 2023–2024: `Kenya Nairobi Securities Exchange (NSE) All Stocks Prices 2023-2024` (DOI: 10.17632/ss5pfw8xnk.3)
- 2025: `Kenya Nairobi Securities Exchange (NSE) All Stocks Prices 2025` (DOI: 10.17632/2b63rx67xt.1)

All of them share the same schema:
- Columns (CSV): Date, Stock Code, Stock Name, 12‑month Low, 12‑month High, Day Low, Day High, Day Final Price, Previous Price, Change Value, Change %, Volume, Adjusted Price.
- There is also a sectors CSV: `NSE_data_stock_market_sectors_YYYY.csv` (Market Sector, Stock Code, Stock Name).

## TARGET

1. Build a **single per-ticker daily history** covering 2013–2025 for all NSE stocks we care about.
2. Store price series locally in `data/prices/{TICKER}.json`.
3. Update the frontend (index.html/app.js) to render a Chart.js price chart per company based on that local data.
4. Add a time range selector with buttons: Max, 1Y, 1M, 1W, 1D.
5. Keep an "Open on TradingView" link as a secondary option.

---

## STEP 1: Add a prices/ module (backend)

Create a new module under `backend/prices/`:
- `backend/prices/download_mendeley.py` — for now, assume the CSV files have been manually downloaded into `data/prices/raw/`. Do **not** implement HTTP download; just read from disk.
- `backend/prices/build_price_history.py` — main script to merge and normalize.

### build_price_history.py responsibilities

Inputs (assume these CSVs are present in `data/prices/raw/`):
- `NSE_data_all_stocks_2013_2020.csv`
- `NSE_data_all_stocks_2021.csv`
- `NSE_data_all_stocks_2022.csv`
- `NSE_data_all_stocks_2023.csv`
- `NSE_data_all_stocks_2024.csv`
- `NSE_data_all_stocks_2025.csv`

Output:
- `data/prices/{TICKER}.json` for each NSE ticker

Each JSON file should have this structure:
```json
{
  "ticker": "KCB",
  "name": "KCB Group PLC",
  "sector": "Finance",  // optional, when available
  "prices": [
    { "date": "2013-01-02", "close": 27.5, "high": 28.0, "low": 27.0, "volume": 123456, "adj": 27.5 },
    ...
  ]
}
```

Rules:
- Parse the Date column and normalize to ISO `YYYY-MM-DD`.
- Use **Stock Code** for `ticker` (e.g. KCB, EQTY, SCBK, SCOM, etc.).
- Use `Day's Final Price` as `close` and `Adjusted Price` as `adj`.
- Merge all years; if duplicates exist (same ticker+date), keep the latest row.
- Sort `prices` by date ascending.
- Use the sectors CSVs (where present) to populate the `sector` field.

---

## STEP 2: Wire Chart.js price chart in frontend

### index.html

- Replace the TradingView iframe section with a new `<canvas id="price-chart"></canvas>` and a range selector bar:
  ```html
  <div class="price-chart-container">
    <div class="price-chart-header">
      <span>Share Price</span>
      <div class="price-range-buttons">
        <button data-range="max" class="active">Max</button>
        <button data-range="1y">1Y</button>
        <button data-range="1m">1M</button>
        <button data-range="1w">1W</button>
        <button data-range="1d">1D</button>
      </div>
    </div>
    <canvas id="price-chart"></canvas>
    <div class="price-chart-footer">
      <a id="tv-link" href="#" target="_blank" rel="noopener">Open on TradingView ↗</a>
    </div>
  </div>
  ```
- Keep styling light; add minimal CSS in `styles.css` to make this look decent.

### app.js

- Add a new module or section to:
  - Load `data/prices/{TICKER}.json` via fetch when a company is selected.
  - Initialize a Chart.js line chart in `#price-chart`.
  - Handle range selector buttons.

Pseudo‑logic for range filtering:
```js
function filterByRange(prices, range) {
  if (range === 'max') return prices;
  const end = new Date(prices[prices.length - 1].date);
  let start;
  switch (range) {
    case '1y': start = new Date(end); start.setFullYear(end.getFullYear() - 1); break;
    case '1m': start = new Date(end); start.setMonth(end.getMonth() - 1); break;
    case '1w': start = new Date(end); start.setDate(end.getDate() - 7); break;
    case '1d': start = new Date(end); start.setDate(end.getDate() - 1); break;
  }
  return prices.filter(p => new Date(p.date) >= start);
}
```

- On company selection (`loadCompany()`), do:
  - Map the selected TV ticker/internal ticker to Mendeley ticker (they should match Stock Code, e.g. KCB, EQTY, SCBK, SCOM, etc.; reuse existing TV↔internal map where needed).
  - Fetch `/data/prices/{TICKER}.json`.
  - Create/Update the Chart.js instance with Max range by default.
  - Wire up click handlers on range buttons to re‑filter the data and update the chart.
  - Update `#tv-link` to the correct TradingView URL (e.g. `https://www.tradingview.com/chart/?symbol=NSEKE%3AKCB`).

---

## STEP 3: Edge cases

- If a ticker has **no price file** (e.g. very illiquid or not in Mendeley data), hide the chart and show a message: "Price history not available for this stock."
- For companies with financial data but no NSE listing (like TCL if missing a Stock Code), keep the financial charts and hide the price chart.

---

## STEP 4: Test

Test on at least these tickers:
- KCB (bank, long history)
- EQTY
- SCBK
- SCOM
- EABL

Check each range button and confirm that:
- Max shows 2013–2025.
- 1Y shows only the last ~12 months.
- 1M shows last ~30 days.
- 1W shows last week.
- 1D shows last ~1–2 days.

---

## STEP 5: Commit + push

- Commit including:
  - `backend/prices/*.py`
  - `data/prices/*.json` (if not too large; if huge, we can discuss ignoring them, but for now assume we commit them)
  - `frontend/index.html`
  - `frontend/app.js`
  - `frontend/styles.css`

Commit message: `feat: add self-hosted NSE price charts using Wanjawa 2013-2025 datasets`

Push to `origin master`.

When completely finished, run:
openclaw system event --text "Done: NSE Insights now uses self-hosted price charts (2013-2025) with Max/1Y/1M/1W/1D ranges" --mode now
