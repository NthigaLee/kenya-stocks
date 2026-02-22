# COMPANY_NOTES.md — Deep Financial Reference

_Last updated: 2026-02-22_
_Purpose: For each company, understand the PDF structure, data quality, what's available, where to find answers._

---

## ABSA BANK KENYA PLC (ABSA)

### Basic Info
- **Listed**: NSE, Banking sector
- **Fiscal Year End**: December 31
- **Reporting currency**: KES (thousands)
- **Formerly**: Barclays Bank of Kenya (rebranded ~2019)
- **ISIN**: KE0000000562

### PDF Coverage
| File | Period | Type | Consolidation | Notes |
|---|---|---|---|---|
| ABSA_Bank_Kenya_Plc_30_Jun_2020_financials.pdf | H1 FY2020 | Unaudited | Company only | Title says "Unaudited Company Results" |
| ABSA_Bank_Kenya_Plc_30_Sep_2020_financials.pdf | 9M FY2020 | Unaudited | Group (Consolidated) | Has 8-period comparison table |
| ABSA_Bank_Kenya_Plc_31_Dec_2021_audited.pdf | FY2021 | Audited | Group + Company | Side-by-side Group / Bank columns |
| ABSA_Bank_Kenya_Plc_31_Mar_2022_financials.pdf | Q1 FY2022 | Unaudited | Group + Company | |
| ABSA_Bank_Kenya_Plc_30_Jun_2023_financials.pdf | H1 FY2023 | Unaudited | Group (Consolidated) | |
| ABSA_Bank_Kenya_Plc_31_Dec_2023_audited.pdf | FY2023 | Audited | Group (Consolidated) | Full year — best data quality |
| ABSA_Bank_Kenya_Plc_30_Jun_2024_financials.pdf | H1 FY2024 | Unaudited | Group (Consolidated) | |
| ABSA_Bank_Kenya_Plc_31_Mar_2024_financials.pdf | Q1 FY2024 | Unaudited | Group (Consolidated) | |
| ABSA_Bank_Kenya_Plc_30_Sep_2025_financials.pdf | 9M FY2025 | Unaudited | Group (Consolidated) | Most recent available |

**Also available** (in `data/absa_ir/`):
- Annual Integrated Reports 2010–2024 (full IR, not just financials)
- These are richer — include narrative, sustainability, governance sections

### PDF Format Notes
- NSE compact format: note number + label + value(s) in same row
  - E.g.: `3.0 Net interest income 14,343,849 32,131,322` (note 3, H1, full year comparison)
- Multiple period columns side by side (Q1, H1, 9M, FY, prior year)
- Group and Company data in same document (separate columns, clearly labelled)
- Amounts in KES thousands

### Key Metrics Available (from PDFs)
- **Income Statement**: Net Interest Income, Total Operating Income, Operating Expenses, PBT, PAT
- **EPS & DPS**: Basic EPS (Shs), Dividends per Share (Shs)
- **Balance Sheet**: Total Assets, Loans & Advances (net), Customer Deposits
- **Equity**: Paid-up Capital, Retained Earnings, Shareholders' Funds
- **NOT in compact reports**: Capital Adequacy Ratio (in Integrated Reports only)

### EPS Progression (Basic EPS, Shs)
| Period | EPS |
|---|---|
| 9M FY2020 | 0.98 |
| FY2021 | 0.69 (Group), 0.77 (Bank) |
| Q1 FY2022 | 0.42 |
| H1 FY2023 | 1.09 (Group), 1.16 (Bank) |
| H1 FY2024 | 1.42 (Group), 1.53 (Bank) |
| FY2023 (audited) | 2.55 (Group), 2.69 (Bank) |
| 9M FY2025 | 2.54 (Group), 2.83 (Bank) |

### DPS Progression (Shs per share)
| Period | DPS |
|---|---|
| FY2021 | 1.10 |
| FY2022 | 1.10 |
| FY2023 | 1.35 |
| FY2024 | 1.55 |
| FY2025 (interim) | 0.20 (interim) |

### Total Assets Progression (KES thousands)
| Period | Total Assets |
|---|---|
| H1 FY2020 | 568,015,000 (approx — compact format) |
| FY2021 | 377,935,772 (Group) / 379,440,676 (Bank) |
| FY2023 | 477,290,548 (Group) / 477,233,937 (Bank) |
| Q1 FY2024 | 514,817,820 (Group) |

### Data Quality Issues (JSON vs PDF)
- The extractor picks up note reference numbers (3, 5, 21) instead of actual values
- Multi-column table format confuses the regex (concatenates adjacent numbers)
- `revenue` field in JSON maps to `total_income` for banks (correct concept, different label)
- Many `null` fields in JSON — need targeted extraction per company format

### Where to Find Specific Answers
- **"What was ABSA's profit in FY2023?"** → `ABSA_Bank_Kenya_Plc_31_Dec_2023_audited.pdf`, note 7 (PBT) or note 8 (PAT)
- **"What is ABSA's loan book?"** → note 9 in any compact report
- **"What was the dividend?"** → DPS line in any compact report, or Integrated Report
- **"What is ABSA's capital ratio?"** → Integrated Report (not in NSE compact format)

---

## STANDARD CHARTERED BANK KENYA LTD (STANCHART)

### Basic Info
- **Listed**: NSE, Banking sector
- **Fiscal Year End**: December 31
- **Reporting currency**: KES (thousands)
- **Parent**: Standard Chartered PLC (London)
- **Company name variant**: "Standard Chartered Bank Kenya Ltd" (main) and "Standard Chartered Bank Ltd" (2024 file)

### PDF Coverage
| File | Period | Type | Consolidation | Notes |
|---|---|---|---|---|
| STANDARD_CHARTERED_BANK_KENYA_LIMITED_69_1_69_financials.pdf | Unknown | Financials | Unknown | 2015 folder, filename garbled |
| Standard_Chartered_Bank_Kenya_Ltd_30_Jun_2019_financials.pdf | H1 FY2019 | Unaudited | Group (Consolidated) | |
| Standard_Chartered_Bank_Kenya_Ltd_30_Jun_2020_audited.pdf | H1 FY2020 | Audited | Unknown | Extraction issues — may be scanned |
| Standard_Chartered_Bank_Kenya_Ltd_30_Sep_2020_financials.pdf | 9M FY2020 | Unaudited | Group (Consolidated) | |
| Standard_Chartered_Bank_Kenya_Ltd_31_Mar_2020_audited.pdf | Q1 FY2020 | Audited | Unknown | Extraction issues — may be scanned |
| Standard_Chartered_Bank_Kenya_Ltd_30_Jun_2022_financials.pdf | H1 FY2022 | Unaudited | Group (Consolidated) | |
| Standard_Chartered_Bank_Kenya_Ltd_31_Dec_2023_financials.pdf | FY2023 | Financials | Group + Company | Best coverage year |
| Standard_Chartered_Bank_Kenya_Ltd_00_1_51_financials.pdf | H1 FY2025? | Financials | Group + Company | Filename garbled — likely H1 FY2025 |
| Standard_Chartered_Bank_Ltd_31_Dec_2024_financials.pdf | FY2024 | Financials | Group + Company | Most recent full year |

**GAPS IN COVERAGE:**
- No FY2020 full-year audited (only H1, Q1, 9M available)
- No FY2021 or FY2022 full-year audited
- FY2024 and H1 FY2025 present but NOT in financials.json yet (missing from extraction)

### PDF Format Notes
- Uses uppercase section headings: "NET INTEREST INCOME/(LOSS)", "TOTAL OPERATING INCOME"
- Note numbers alongside values (same as ABSA)
- Group + Company columns side by side in 2022+ reports
- Older reports (2019-2020): Group only
- Some PDFs (30-Jun-2020, 31-Mar-2020) have **scanning/encoding issues** — numbers being concatenated incorrectly
- Amounts in KES thousands

### Key Metrics Available (from PDFs)
- Note 3: Net Interest Income/(Loss)
- Note 5: Total Operating Income
- Note 6: Other Operating Expenses
- Note 9: Loans and Advances to Customers (net)
- Note 18: Earnings Per Share (Basic & Diluted)
- Note 19: Dividend Per Share — Declared
- Note 21: Total Assets
- Note 23: Customer Deposits
- Note 35: Paid-up/Assigned Capital
- Note 39: Statutory Loan Loss Reserves

### EPS Progression (Basic & Diluted EPS, KShs)
| Period | EPS |
|---|---|
| H1 FY2019 | 12.76 (Group) |
| Q1 FY2020 | 5.14 |
| H1 FY2020 | 8.26 |
| 9M FY2020 | 16.15 |
| H1 FY2022 | 12.69 |
| FY2023 | 31.47 (Group), 32.47 (Bank) |
| FY2024 | 36.17 (Group), 36.39 (Bank) |
| H1 FY2025 | 26.99 (Group) |

### DPS Progression (KShs per share)
| Period | DPS |
|---|---|
| FY2019 | 19.00 |
| FY2020 | 12.50 |
| FY2022 | 19.00 |
| FY2023 | 29.00 |
| FY2024 | 45.00 |

### Total Assets Progression (KES thousands)
| Period | Total Assets |
|---|---|
| H1 FY2019 | 295,955,246 |
| H1 FY2022 | 345,646,341 |
| FY2023 | 381,260,015 (Group) / 381,630,646 (Bank) |
| FY2024 | 428,962,175 (Group) / 429,278,578 (Bank) |
| H1 FY2025 | 377,283,638 (Group) |

### Data Quality Issues
- Two PDFs not in financials.json: `31_Dec_2024` and `00_1_51` — need to be added
- Profit after tax extraction flawed: picks up equity movement column (negative sign) not P&L
- Some PDFs (2020 era) have scanning issues causing number concatenation bugs
- No capital adequacy data in NSE compact reports

### Where to Find Specific Answers
- **"What was StanChart's profit in FY2024?"** → `Standard_Chartered_Bank_Ltd_31_Dec_2024_financials.pdf`, note 7 (PBT = 28,208,236), PAT = 20,060,587
- **"What is StanChart's loan book?"** → note 9 in any report
- **"What was the FY2024 dividend?"** → DPS = KShs 45.00 per share
- **"How does Group compare to Bank?"** → Side-by-side columns in FY2023 and FY2024 reports

---

## SAFARICOM PLC (SCOM)

### Basic Info
- **Listed**: NSE, Telco sector
- **Fiscal Year End**: March 31 (NOT December — different from banks)
- **Reporting currency**: KES (millions, not thousands)
- **Parent**: Safaricom is majority-owned by Vodacom/Vodafone
- **Key product**: M-Pesa (mobile money — often >50% of revenue)

### PDF Coverage
| File | Period | Type | Notes |
|---|---|---|---|
| Safaricom_PLC_31_March_2019_audited.pdf | FY2019 | Audited | Full year |
| Safaricom_PLC_30_Sep_2019_financials.pdf | H1 FY2020 | Unaudited | Sep = midyear for Safaricom |
| Safaricom_Plc_31_Mar_2020_audited.pdf | FY2020 | Audited | Full year |
| SAFARICOM_PLC_CONDENSED_AUDITED_RESULTS_FOR_THE_YE_31_Mar_2023_audited.pdf | FY2023 | Audited | |
| extracts_from_the_financial_books_of_Safaricom_PLC_31_Mar_2024_audited.pdf | FY2024 | Audited | "Extracts" — may be partial |
| SAFARICOM_PLC_CONDENSED_UNAUDITED_RESULTS_FOR_THE_30_September_2024_financials.pdf | H1 FY2025 | Unaudited | |

**IMPORTANT**: Safaricom FY runs April 1 → March 31.
- "Sep 2019 financials" = **H1 of FY2020** (not FY2019)
- "Sep 2024 financials" = **H1 of FY2025**
- "Mar 2024 audited" = **Full year FY2024**

**GAPS IN COVERAGE:**
- Missing: FY2021 (Mar 2021), FY2022 (Mar 2022)
- 2023 and 2024 look well-covered

### Notable: No "Group vs Company" complexity for Safaricom
Safaricom is primarily a single entity for Kenyan reporting. M-Pesa Africa is a separate entity but not in these NSE reports.

### Key Metrics to Extract (Telco-specific)
- Revenue by segment (Voice, Data, M-Pesa, Fixed, Other)
- EBITDA and EBITDA margin
- Operating Profit (EBIT)
- PAT
- EPS and DPS
- Capex (large — network rollout)
- M-Pesa revenue and active customers
- Total subscribers
- Free Cash Flow

### Data Quality Issues (JSON vs PDF)
- JSON has entries for 2019-2020 only (3 entries)
- All bank-specific extraction patterns don't apply — need telco patterns
- Amounts in KES millions (not thousands like banks — scale difference vs ABSA/StanChart)
- **2019 PDFs (both FY2019 and H1 FY2020)**: extraction fails completely — likely scanned/image-based
- **FY2020 PDF**: extraction partially works but text has doubled characters ("113388..0044" = 113,388.04) due to overlapping PDF text layer
- **FY2024 PDF**: extraction works well
- **CRITICAL BUG**: Audit script misses `SAFARICOM_PLC_...` (uppercase S) and `SAFARICOM_PLC_CONDENSED_UNAUDITED...` files — case-sensitive string match. Fix: use `.lower()` in filename search.

### Actual Financial Data (from FY2024 PDF — most reliable)
FY2024 (year ended 31 March 2024, KES millions):
- **Service Revenue**: 335,353.1 (Group) / 326,564.6 (Safaricom Kenya standalone)
- **Operating Profit (EBIT)**: 80,344.8 (Group) / 138,290.7 (Safaricom Kenya) — Group lower due to M-Pesa Africa startup losses
- **PAT**: 42,658.4 (Group) / 82,653.8 (Safaricom Kenya)
- **EPS**: 1.57 KShs (Group basic)
- **Total Assets**: 641,164.3 (Group) / 371,291.1 (Safaricom Kenya)
- Prior year (FY2023 Group): Revenue 295,692.3, PAT 52,482.8, Assets 509,207.0

FY2020 (year ended 31 March 2020, KES billions — different scale):
- Service Revenue: ~251.22 KES Bn
- EBITDA: ~113.4 KES Bn
- PAT: ~73.7 KES Bn
- Basic EPS: ~1.84 KShs
- DPS: 1.40 KShs

### Where to Find Specific Answers
- **"What was Safaricom's revenue in FY2024?"** → `extracts_from...31_Mar_2024_audited.pdf`, "Service revenue 335,353.1" (Group level)
- **"What is M-Pesa's revenue?"** → Look for "M-PESA" segment in breakdown; FY2024 document has segment detail
- **"What is subscriber count?"** → FY2020 doc: "M-PESA one month active customers increased 10.0% to 24 [million]"
- **"What was the dividend?"** → FY2020: DPS = 1.40 KShs; FY2024: not clearly extracted — check PDF directly
- **"Group vs Safaricom Kenya?"** → FY2024 doc has 4 columns: Current Group, Prior Group, Current Safaricom Kenya, Prior Safaricom Kenya
- **"Why is Group PAT lower than Kenya PAT?"** → M-Pesa Africa startup losses drag Group down

---

## COMMON ISSUES & EXTRACTION IMPROVEMENTS NEEDED

### Problem 1: Note Numbers Captured Instead of Values
NSE compact format: `"3.0 Net interest income 14,343,849 32,131,322"`
- Current extractor: finds "net interest income" → returns "3" (first number in line)
- Fix: Skip leading small integers (note numbers), parse the larger numbers that follow

### Problem 2: Multi-Column Table Concatenation
Format: `"Total assets 568,015 490,128"` (current period + prior period)
- Current extractor: concatenates → "568015490128" (a garbage number)
- Fix: Only take the FIRST valid large number from the line

### Problem 3: PAT Sign Error
StanChart format: `"Profit for the year - - - 12,057,935 - - - - 12,057,935"`
- Current extractor: finds first number after "profit for the year" → gets "-" (negative sign) then 0
- The actual PAT is always positive in P&L; negative appears in equity movement
- Fix: Skip equity movement sections when searching for PAT

### Problem 4: Banking vs Telco Revenue Terminology
- Banks: "Total Operating Income" = revenue concept (not "revenue" / "turnover")
- Safaricom: "Revenue" is correct term
- Fix: Already done partially — `total_income` pattern exists

### Problem 5: Amounts Scale
- Banks: KES thousands
- Safaricom: KES millions
- Fix: Store scale as metadata per company

---

## JSON DATA STATUS (financials.json)

### ABSA — 9 entries
All periods covered by PDFs are in JSON ✅
Most critical fields filled: revenue (partial), total_assets (partial), total_equity (partial)
Missing from JSON: profit_after_tax for most entries, basic_eps for all, dividend_per_share

### StanChart — 8 entries (but 2 PDFs not represented)
Missing from JSON: FY2024 (Dec 2024) and H1 FY2025 (00_1_51 PDF)
Field quality: similar to ABSA — many nulls

### Safaricom — 3 entries (FY2019, H1 FY2020, FY2020)
Severely under-represented: FY2023, FY2024, H1 FY2025 not in JSON
Need to run extractor against all Safaricom PDFs

---

## ABSA INVESTOR RELATIONS (data/absa_ir/)

Additional data source — richer than NSE compact reports.
Contains annual integrated reports going back to 2010.

| Year | Files |
|---|---|
| 2010-2015 | Barclays Kenya Annual Reports |
| 2017 | Barclays Kenya Annual Report (no 2016 file) |
| 2019-2025 | Absa Bank Kenya Integrated Reports + Quarterly PDFs |

These contain: strategic narrative, ESG metrics, capital adequacy, risk disclosures, governance — **much more than the NSE compact results**.
