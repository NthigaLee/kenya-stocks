You are working on the NSE Insights frontend. The financial database (financials.json) now has data for 39 companies, but the frontend only shows "Full Data" for 7. Fix this.

## THE PROBLEM
In frontend/app.js line ~11:
```js
const FINANCIAL_TICKERS = new Set(['ABSA', 'COOP', 'DTK', 'EQTY', 'KCB', 'NCBA', 'SCBK']);
```
This hardcoded set needs to include all 39 companies that have data in financials.json / NSE_COMPANIES (data.js).

## CURRENT DATA (financials.json tickers and what they map to on TradingView)
Here are ALL 39 tickers in the DB and their TradingView NSEKE symbol equivalents:

| Internal ticker (financials.json) | TradingView ticker (NSEKE:) | Company |
|---|---|---|
| ABSA | ABSA | Absa Bank Kenya |
| BAMB | BAMB | Bamburi Cement |
| BATK | BAT | BAT Kenya ← DIFFERENT |
| BKG | BKG | BK Group |
| BOC | BOC | B.O.C Kenya |
| BRIT | BRIT | Britam Holdings |
| CARB | CARB | Carbacid Investments |
| COOP | COOP | Co-operative Bank |
| CPKL | CRWN | Crown Paints ← DIFFERENT (CPKL internal, CRWN on TV) |
| DTB | DTK | Diamond Trust Bank ← DIFFERENT |
| EABL | EABL | East African Breweries |
| EAPC | PORT | EA Portland Cement ← DIFFERENT (EAPC internal, PORT on TV) |
| EQTY | EQTY | Equity Group |
| FMLY | (not on TV) | Family Bank - no TradingView ticker, skip chart |
| FTGH | FTGH | Flame Tree Group |
| HAFR | HAFR | Home Afrika |
| HBZE | (not on TV) | Homeboyz Entertainment - no TradingView ticker, skip chart |
| HFCK | HFCK | HF Group |
| IMH | IMH | I&M Group |
| JUB | JUB | Jubilee Holdings |
| KAPA | KAPC | Kapchorua Tea ← DIFFERENT (KAPA internal, KAPC on TV) |
| KCB | KCB | KCB Group |
| KEGN | KEGN | KenGen |
| KPLC | KPLC | Kenya Power |
| NCBA | NCBA | NCBA Group |
| NMG | NMG | Nation Media Group |
| NSE | NSE | Nairobi Securities Exchange |
| SASN | SASN | Sasini |
| SBIC | SBIC | Stanbic Holdings |
| SCAN | SCAN | WPP Scangroup |
| SCBK | SCBK | Standard Chartered |
| SCOM | SCOM | Safaricom |
| SGL | SGL | Standard Group |
| SLAM | SLAM | Sanlam Allianz Kenya |
| TCL | (not on TV) | TransCentury - no TradingView ticker, skip chart |
| UMME | UMME | Umeme |
| UNGA | UNGA | Unga Group |
| WTK | WTK | Williamson Tea |
| XPRS | XPRS | Express Kenya |

## TASK

### 1. Regenerate frontend/data.js
Run `backend/extract_all.py` or whatever generates data.js to include ALL 39 tickers. If there's a `populate.py` script, use it. Check what generates `frontend/data.js` and make sure NSE_COMPANIES in data.js has all 39 companies.

### 2. Update app.js FINANCIAL_TICKERS
Replace the hardcoded 7-ticker set with all tickers that have data in NSE_COMPANIES. Best approach: derive it dynamically from NSE_COMPANIES keys at runtime rather than hardcoding:
```js
const FINANCIAL_TICKERS = new Set(Object.keys(NSE_COMPANIES));
```

### 3. Update TV_TO_INTERNAL mapping
Expand TV_TO_INTERNAL to cover all the ticker differences:
```js
const TV_TO_INTERNAL = {
  'DTK':  'DTB',    // Diamond Trust Bank
  'BAT':  'BATK',   // BAT Kenya
  'CRWN': 'CPKL',   // Crown Paints
  'PORT': 'EAPC',   // EA Portland Cement
  'KAPC': 'KAPA',   // Kapchorua Tea
};
// Reverse map also needed: internal → TV ticker
const INTERNAL_TO_TV = Object.fromEntries(
  Object.entries(TV_TO_INTERNAL).map(([tv, internal]) => [internal, tv])
);
```

### 4. Handle companies with no TradingView ticker
FMLY (Family Bank), HBZE (Homeboyz), TCL (TransCentury) have financial data but no NSEKE ticker on TradingView.
- For these, show the financial charts as normal
- Skip/hide the TradingView chart section (show a note: "Live price chart not available for this stock")
- Make sure the company still appears in the ⭐ Full Data group in the dropdown

### 5. Update the dropdown builder in app.js
The dropdown currently hardcodes the 7 full-data companies (line ~490). Update it to:
- Pull full-data companies from NSE_COMPANIES keys dynamically
- For companies not in NSE_ALL_STOCKS (FMLY, HBZE, TCL), add them to the ⭐ Full Data group using their name from NSE_COMPANIES
- Handle the ticker mapping correctly (internal ↔ TV)

### 6. Company header + breadcrumb
When loading a company, the breadcrumb and header should show the correct company name regardless of which ticker system is used.

### 7. Verify the financial charts still render
Make sure the existing Chart.js charts (EPS, total assets, NII, profit) still render for all the original 7 companies after the changes.

## IMPORTANT
- Push to GitHub (origin master) after completing — every iteration should be pushed
- Keep nse_tickers.js as-is (it's the TradingView symbol source of truth for the price chart)
- Do NOT break the TradingView chart for the 50 price-only companies

## COMMIT
"feat: expand full financial data to all 39 NSE companies, fix ticker mappings"
Push to origin master.

When completely finished, run:
openclaw system event --text "Done: kenya-stocks frontend now shows full financial data for all 39 NSE companies" --mode now
