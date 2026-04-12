You are working on the NSE Kenya Stocks project. There are 62 PDFs in data/nse/2025/ and data/nse/2026/ that haven't been fully extracted yet. Extract all financial data from them and update the database.

## WHAT'S IN THERE (confirmed PDFs)
Key files including:
- ABSA Bank Kenya Sep 2025, BK Group Dec 2024 + May 2025, Carbacid Jul 2025
- CIC Insurance Dec 2024, COOP Sep 2025, Crown Paints Jun 2025
- DTB Dec 2024 + Jun 2025 + Sep 2025
- EABL Dec 2024, EQTY FY2024 + Q1/H1/Q3 2025
- Family Bank Dec 2023 + Mar 2024, HF Group Dec 2024
- I&M Group Sep 2025, Jubilee Dec 2024, Kapchorua, KCB Dec 2024 + Q1/H1/Q3 2025
- KenGen Jun 2025, Kenya Re Dec 2024, Liberty Kenya Jun 2025
- NCBA Mar 2025 + May 2025 + Sep 2025, Sanlam Dec 2024 + Jun 2025
- Stanbic Jun 2025, SCBK Dec 2024, KPLC Dec 2024 + Jun 2025
- TransCentury Jun 2024 + Dec 2023, Williamson Tea, I&M Sep 2025

## TASK

### 1. Run the extractor
```bash
python backend/extract_all.py
```
This should pick up all PDFs in data/nse/2025/ and data/nse/2026/. Watch for errors and fix any extraction failures.

### 2. Run quality fixes after extraction
```bash
python backend/normalize_companies.py
python backend/fix_kcb_metadata.py
```

### 3. Check for obvious bad data
- Any values that look like wrong units (e.g. total assets = 5 when it should be 5000)
- Any duplicate records for same company+period
- Any records with all nulls (useless, remove them)

### 4. Regenerate frontend/data.js
Run `populate.py` (or whatever generates frontend/data.js from financials.json). Make sure all new companies/periods are included.

### 5. Push to GitHub
Commit: "data: extract 2024-2025 quarterly reports for 25+ NSE companies"
Push to origin master.

## REPORT
Print summary:
- Records before vs after
- New tickers added
- New periods per ticker (especially quarterlies Q1/H1/Q3)
- Any extraction failures with reasons

## CRITICAL
- Push after every meaningful step so progress is visible on the live site
- No garbage data — if a value looks wrong, flag it rather than include it

When completely finished, run:
openclaw system event --text "Done: kenya-stocks quarterly extraction complete - 2024-2025 data for 25+ companies extracted and pushed" --mode now
