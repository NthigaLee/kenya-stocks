# Phase 1: South Africa JSE — Task Specification
**Date Started:** 2026-03-08  
**Objective:** Extract financials for JSE Top 30 companies and create live dashboard  
**Timeline:** 5 days  

---

## Step 1: Download JSE PDFs (Est. 30 mins)

```bash
cd global-stocks
python backend/exchanges/jse.py
```

**What it does:**
- Scrapes JSE Top 30 companies
- Discovers financial statement PDFs on each company's IR page
- Downloads all PDFs to `data/jse/{ticker}/`
- Logs success/failures

**Expected Output:**
```
data/jse/
├── BHG/
│   ├── Bidvest_Annual_Report_2024.pdf
│   ├── Bidvest_H1_2024.pdf
│   └── ...
├── ANH/
├── BTI/
└── ... (30 companies)
```

**Troubleshooting:**
- If IR URLs are wrong, manually update in `backend/exchanges/jse.py` line ~30
- If no PDFs found, IR page might use JavaScript rendering (fallback: manual download)

---

## Step 2: Extract Financials (Est. 1 hour)

```bash
python backend/extract_all.py --exchange JSE --limit 30
```

**What it does:**
- Reads all PDFs from `data/jse/`
- Extracts financial metrics using IFRS templates
- Normalizes to ZAR thousands (like Kenya)
- Validates and deduplicates
- Writes to `data/jse/financials.json`

**Expected Output:**
```json
[
  {
    "ticker": "BHG",
    "company": "Bidvest Group Limited",
    "period": "Dec2024",
    "period_type": "annual",
    "period_end_date": "2024-12-31",
    "currency": "ZAR",
    "revenue": 123456789000,
    "profit_after_tax": 12345678000,
    "basic_eps": 4.56,
    ...
  },
  ...
]
```

**Validation Checklist:**
- ✅ At least 25/30 companies extracted
- ✅ All financials in ZAR thousands
- ✅ Period dates are valid (YYYY-MM-DD)
- ✅ Revenue/PAT reasonable (non-zero, not negative for healthy companies)
- ✅ No duplicate entries per company/period

---

## Step 3: Merge with Kenya (30 mins)

```python
# backend/pipeline.py
financials_ke = load_json("data/nse/financials.json")
financials_za = load_json("data/jse/financials.json")

# Add exchange/country fields
for rec in financials_ke:
    rec["exchange"] = "NSE"
    rec["country"] = "Kenya"

for rec in financials_za:
    rec["exchange"] = "JSE"
    rec["country"] = "South Africa"

# Merge
combined = financials_ke + financials_za

# Save
save_json("data/global/financials.json", combined)
```

---

## Step 4: Update Frontend (1 hour)

### Option A: Unified Frontend (Recommended)

**New structure:**
```
frontend/
├── index.html          # Multi-country selector
├── app.js              # Unified dashboard
├── data.js             # All companies (Kenya + SA)
└── styles.css
```

**Updates needed:**
1. Add country dropdown in `index.html`
2. Add exchange filter logic in `app.js`
3. Regenerate `data.js` with all companies

**Feature additions:**
- Country selector: Kenya | South Africa
- Exchange filter: NSE | JSE
- Separate data arrays per exchange
- Currency display: KES or ZAR (user preference)

### Option B: Separate Site (Alternative)

Keep Kenya separate, create new `sa-stocks/` site with same layout.

**Recommendation:** Go with **Option A** (unified) for scalability to Europe.

---

## Step 5: Deploy to GitHub Pages (15 mins)

```bash
# Copy frontend to docs/
cp frontend/*.{js,html,css} docs/

# Commit & push
git add -A
git commit -m "feat: add JSE South Africa Top 30 financials"
git push origin master
```

**Live site:** https://nthigalee.github.io/kenya-stocks/
(rename repo to `global-stocks` after this phase if desired)

---

## Testing Checklist

**Data Quality:**
- [ ] At least 20/30 companies have financials
- [ ] EPS/DPS values are reasonable (< 1000 ZAR)
- [ ] Revenue > Profit After Tax (sanity check)
- [ ] Period dates are chronological
- [ ] No unicode/encoding errors in company names

**Frontend:**
- [ ] Can load Kenya companies
- [ ] Can load JSE companies
- [ ] Charts render for both
- [ ] Country selector works
- [ ] Responsive on mobile

**Deployment:**
- [ ] Site is live on GitHub Pages
- [ ] Cache-buster working (append `?v=20260308`)
- [ ] No 404s in console

---

## Known Issues & Workarounds

### Issue 1: PDF not found on IR page
**Solution:** Check company website directly, add URL manually to `jse.py`

### Issue 2: Extraction gives null values
**Solution:** Extractor may not recognize column headers in local GAAP variant
- Workaround: Use OCR (Tesseract) if pypdf fails
- Or: Manually verify a few PDFs, adjust extraction regex

### Issue 3: GitHub Pages cache not refreshing
**Solution:** Use cache-busting query params in `index.html`
```html
<script src="data.js?v=20260308-1"></script>
```

### Issue 4: Duplicate entries in financials.json
**Solution:** Run dedup pipeline:
```bash
python backend/dedup_and_clean.py --input data/jse/financials.json
```

---

## Success Criteria

By end of Phase 1, the site should show:

✅ **Kenya (NSE):** 50+ companies, live historical data (existing)  
✅ **South Africa (JSE):** 25+ companies, latest financials  
✅ **Frontend:** Single unified dashboard, country selector  
✅ **Deployment:** Live on GitHub Pages, auto-deployable  

---

## Next: Phase 2 (LSE — London)

Once JSE is complete:
1. Reuse JSE templates for LSE (both IFRS, English)
2. Adapt for GBP currency
3. Add LSE Top 50 companies
4. Repeat extraction → merge → deploy

---

## Files Modified/Created

```
backend/
├── exchanges/
│   ├── jse.py              ✨ NEW
│   └── nse.py              (existing)
├── extractors/
│   ├── ifrs_extractor.py   ✨ NEW
│   └── kenya.py            (may be deprecated)
├── extract_all.py          (update to use IFRS extractor)
└── pipeline.py             ✨ NEW (orchestrator)

data/
├── jse/                    ✨ NEW
│   └── financials.json
├── nse/                    (existing)
│   └── financials.json
└── global/                 ✨ NEW
    └── financials.json

frontend/
├── index.html              (update: add country selector)
├── app.js                  (update: unified logic)
└── data.js                 (regenerate)

docs/                       (auto-sync from frontend)
```

---

## How to Iterate if Extraction Fails

**Scenario:** Only 15/30 companies extracted successfully

**Option 1: Improve regex** (30 mins)
- Examine failing PDFs manually
- Adjust `ifrs_extractor.py` patterns
- Re-run extraction

**Option 2: Use OCR** (1 hour)
- Install: `pip install pytesseract`
- Add OCR path in extractor
- Re-run with `--use-ocr` flag

**Option 3: Hybrid manual** (2 hours)
- Extract top 15 successfully
- Manually lookup 15 missing companies from annual reports
- Save to JSON manually
- Merge both

**Recommendation:** Start with Option 1 (regex tweaks), escalate if needed.

---

## Automation Plan (Beyond Phase 1)

Once Phase 1 is stable:

```yaml
# .github/workflows/update-jse.yml
name: Update JSE Data
on:
  schedule:
    - cron: '0 2 * * *'  # Daily 2 AM UTC

jobs:
  extract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python backend/extract_all.py --exchange JSE
      - run: git add data && git commit -m "auto: update JSE financials" && git push
```

This ensures financials refresh automatically each day.

---

**Ready to execute Phase 1?** 🚀
