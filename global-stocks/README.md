# Global Stocks — Multi-Exchange Financial Data Extractor

Extract and visualize financial statements from stock exchanges across Africa and Europe.

**Live Demo:** https://nthigalee.github.io/kenya-stocks/

---

## Current Markets

- ✅ **Kenya (NSE)** — 50+ companies
- 🚀 **South Africa (JSE)** — Phase 1 in progress
- 🔜 **London (LSE)** — Phase 2
- 🔜 **Euronext (Paris, Amsterdam)** — Phase 3
- 🔜 **Frankfurt, Milan, Swiss** — Phase 4+

---

## Quick Start

### 1. Set Up

```bash
# Clone repo
git clone https://github.com/NthigaLee/global-stocks.git
cd global-stocks

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/{nse,jse,lse} data/global frontend docs
```

### 2. Extract Kenya (NSE) — Already Complete

Kenya financials are pre-extracted and live. See `data/nse/financials.json`.

### 3. Extract South Africa (JSE) — Phase 1

```bash
# Download JSE company PDFs
python backend/exchanges/jse.py

# Extract financials
python backend/extract_all.py --exchange JSE --limit 30

# Merge Kenya + SA
python backend/pipeline.py merge --input1 data/nse/financials.json --input2 data/jse/financials.json --output data/global/financials.json

# Update frontend
python backend/pipeline.py generate-frontend --input data/global/financials.json

# Deploy
cp frontend/*.{js,html,css} docs/
git add -A && git commit -m "feat: add JSE Phase 1" && git push
```

---

## Architecture

### Backend

```
backend/
├── exchanges/              # Per-exchange adapters
│   ├── __init__.py
│   ├── nse.py             # Kenya NSE (IFRS, English)
│   ├── jse.py             # South Africa JSE (IFRS, English)
│   ├── lse.py             # London LSE (IFRS/GAAP, English)
│   ├── euronext.py        # Euronext (IFRS, multi-language)
│   ├── frankfurt.py       # Frankfurt (IFRS, German)
│   ├── milan.py           # Milan (IFRS, Italian)
│   └── swiss.py           # SIX (IFRS, multi-language)
├── extractors/            # Per-format extractors
│   ├── ifrs_extractor.py  # IFRS standard extractor (Kenya + SA + Europe)
│   ├── uk_gaap.py         # UK-specific variant
│   └── multilang.py       # Multi-language OCR support
├── extract_all.py         # Master extraction script
├── pipeline.py            # Orchestrator (download → extract → merge → deploy)
├── dedup_and_clean.py     # Cleanup + validation
└── normalize.py           # Currency normalization
```

### Frontend

```
frontend/
├── index.html             # Multi-country dashboard
├── app.js                 # Interactive charts + filters
├── data.js                # Embedded company data (auto-generated)
└── styles.css             # Dark Bloomberg-style theme
```

### Data

```
data/
├── nse/                   # Kenya NSE
│   ├── financials.json    # Extracted + cleaned
│   └── *.pdf              # Original reports
├── jse/                   # South Africa JSE
│   ├── financials.json
│   └── *.pdf
├── lse/                   # London LSE (Phase 2)
├── euronext/              # Euronext venues (Phase 3)
└── global/
    └── financials.json    # Merged all markets
```

---

## How It Works

### 1. Company Discovery
```python
from backend.exchanges.jse import JSE

jse = JSE()
companies = jse.get_company_list()  # [(ticker, name, ir_url), ...]
```

### 2. PDF Download
```python
downloader = jse.download_all(limit=30)
# Output: data/jse/{ticker}/*.pdf
```

### 3. Financial Extraction
```python
from backend.extractors.ifrs_extractor import IFRSExtractor

extractor = IFRSExtractor(exchange="JSE")
metrics = extractor.extract_pdf("data/jse/BHG/annual_report_2024.pdf", "BHG")
# {revenue, pat, eps, dps, assets, equity, ...}
```

### 4. Cleanup & Merge
```python
from backend.dedup_and_clean import cleanup_financials

cleaned = cleanup_financials(extracted_records)
# Dedup, null out invalid fields, validate ranges
```

### 5. Frontend Generation
```python
from backend.pipeline import generate_frontend

generate_frontend(
    input_json="data/global/financials.json",
    output_js="frontend/data.js"
)
```

### 6. Deploy
```bash
cp frontend/*.{js,html,css} docs/
git push origin master  # GitHub Pages auto-deploys
```

---

## Configuration

### Add New Exchange

1. Create `backend/exchanges/newexchange.py`:
```python
class NewExchange:
    def __init__(self):
        self.code = "NEX"
        self.currency = "USD"
    
    def get_company_list(self) -> List[Tuple]:
        """Return [(ticker, name, ir_url), ...]"""
        pass
    
    def download_all(self, limit=None) -> dict:
        """Download PDFs, return {ticker: [files]}"""
        pass
```

2. Update `backend/extract_all.py` to recognize new exchange

3. Run extraction pipeline

### Add New Metric

1. Edit `backend/extractors/ifrs_extractor.py`
2. Add method `def _extract_mynewmetric(self, text: str)`
3. Call in `extract_pdf()`

### Currency Normalization

By default, metrics stored in local currency (KES, ZAR, GBP, EUR, CHF). Frontend can convert:

```javascript
// app.js
const EXCHANGE_RATES = {
    KES: 1,
    ZAR: 0.053,  // 1 ZAR = 0.053 KES
    GBP: 158.5,  // 1 GBP = 158.5 KES
    EUR: 112.3,
    CHF: 123.1,
};

function convertCurrency(amount, fromCurrency, toCurrency) {
    return amount * (EXCHANGE_RATES[toCurrency] / EXCHANGE_RATES[fromCurrency]);
}
```

---

## Testing

```bash
# Test JSE extraction on 5 companies
python backend/exchanges/jse.py --limit 5

# Test extraction pipeline
python backend/extract_all.py --exchange JSE --limit 5 --verbose

# Validate output
python -c "import json; data = json.load(open('data/jse/financials.json')); print(f'{len(data)} records, {sum(1 for r in data if r.get(\"profit_after_tax\"))} with PAT')"
```

---

## Troubleshooting

### Problem: "No PDFs found"
**Solution:** Check company IR URL, may use JavaScript rendering
```python
# Manual fallback
jse = JSE()
jse.companies[0] = ("BHG", "Bidvest", "https://correct-url.com/reports")
```

### Problem: "Extraction returns mostly nulls"
**Solution:** PDF may be scanned image (needs OCR)
```bash
pip install pytesseract
python backend/extract_all.py --exchange JSE --use-ocr
```

### Problem: "Currency mismatch or wrong values"
**Solution:** Check extraction regex in extractor, validate sample manually
```bash
# Extract single PDF for debugging
python backend/extractors/ifrs_extractor.py --pdf data/jse/BHG/report.pdf --verbose
```

---

## Contributing

### Report Issues
- Data extraction fails: Include PDF filename + error message
- Frontend bug: Browser + screenshot
- Missing company: Add to exchange's `get_company_list()`

### Submit Improvements
1. Fork repo
2. Create feature branch: `git checkout -b feature/jse-optimization`
3. Test locally: `python backend/test_suite.py`
4. Push + submit PR

---

## Performance

- **Download:** ~5 sec/PDF (serial) → ~1 sec/PDF (parallel, 10 workers)
- **Extraction:** ~2 sec/PDF (avg)
- **Total:** JSE Top 30 ≈ 3–5 mins for 100 PDFs
- **Frontend:** <1s load time (static data.js)

---

## Roadmap

| Phase | Timeline | Scope | Status |
|-------|----------|-------|--------|
| Kenya (NSE) | Weeks 1–4 | 50+ companies | ✅ Complete |
| SA (JSE) | Week 2–3 | Top 30 | 🚀 Phase 1 In Progress |
| London (LSE) | Week 3–4 | FTSE 100 | 🔜 Phase 2 |
| Euronext | Week 4–5 | CAC 40 + others | 🔜 Phase 3 |
| Frankfurt + Milan + Swiss | Week 5–6 | 40 each | 🔜 Phase 4 |
| Optimization + API | Week 6+ | Real-time updates | 🔜 Future |

---

## Tech Stack

- **Backend:** Python 3.9+
  - `pypdf` — PDF text extraction
  - `requests` — HTTP download
  - `pytesseract` — OCR (optional)
  - `pandas` — Data cleaning (optional)

- **Frontend:** Vanilla JS + Chart.js
  - No build step
  - Static site (GitHub Pages)
  - Responsive mobile design

- **Deployment:** GitHub Pages
  - Auto-deploy on push
  - CDN-delivered globally

---

## License

All code and data aggregation scripts are open source. Financial data rights belong to respective exchanges/companies.

---

## Contact

**Questions?** Open an issue or contact the project maintainer.

---

**Last Updated:** 2026-03-08  
**Current Maintainer:** Urbanbot (🌍)
