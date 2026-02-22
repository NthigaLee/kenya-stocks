# Kenya Stocks — PDF Audit Findings
_Generated: 2026-02-22_

---

## Summary

All three companies have PDFs on disk. The core problem is **the extractor is broken** — it picks up table section/line reference numbers instead of actual financial values in most cases.

---

## ABSA Bank Kenya

**PDFs:** 9 | **JSON entries:** 9 | **1:1 match ✅**

### PDF Coverage (all in `data/nse/`)
| Period | File | Consolidation |
|---|---|---|
| 30-Jun-2020 | 2020/ABSA_Bank_Kenya_Plc_30_Jun_2020_financials.pdf | Unknown (probably Company) |
| 30-Sep-2020 | 2020/ABSA_Bank_Kenya_Plc_30_Sep_2020_financials.pdf | Group (Consolidated) ✅ |
| 31-Dec-2021 | 2022/ABSA_Bank_Kenya_Plc_31_Dec_2021_audited.pdf | Group (Consolidated) ✅ |
| 31-Mar-2022 | 2022/ABSA_Bank_Kenya_Plc_31_Mar_2022_financials.pdf | Unknown |
| 30-Jun-2023 | 2023/ABSA_Bank_Kenya_Plc_30_Jun_2023_financials.pdf | Group (Consolidated) ✅ |
| 30-Jun-2024 | 2024/ABSA_Bank_Kenya_Plc_30_Jun_2024_financials.pdf | Group (Consolidated) ✅ |
| 31-Dec-2023 | 2024/ABSA_Bank_Kenya_Plc_31_Dec_2023_audited.pdf | Group (Consolidated) ✅ |
| 31-Mar-2024 | 2024/ABSA_Bank_Kenya_Plc_31_Mar_2024_financials.pdf | Group (Consolidated) ✅ |
| 30-Sep-2025 | 2025/ABSA_Bank_Kenya_Plc_30_Sep_2025_financials.pdf | Group (Consolidated) ✅ |

### What the PDFs contain (structure)
ABSA PDFs show both Group and Company columns side by side. Table rows are numbered (e.g. "5 Total operating income", "9 Loans and advances", "21 Total assets", "35 Paid up capital"). 

Key metrics visible in source lines:
- `total_income`: Line 5 — "Total operating income [H1 current] [FY prior] [H1 prior] [FY prior-2]"  
- `total_assets`: Line 21 — "Total assets [Group] [Company] [Group prior]"
- `loans_and_advances`: Line 9
- `profit_before_tax`: Line 7 — "Profit before tax and exceptional items"
- `basic_eps`: "Earnings per share (Shs) [H1] [FY] [H1 prior] [FY prior]"
- `dividend_per_share`: "Dividends per share (Shs)"

### Extractor bugs found
1. **Line reference numbers taken as values**: `total_assets = 21`, `total_income = 5`, `total_equity = 35` — these are table row numbers, not financial values
2. **Multi-column confusion**: ABSA tables have 4 columns (Group H1, Group FY, Company H1, Company FY). Parser grabs the first number = row reference
3. **Number concatenation**: `2020/ABSA_30_Jun_2020` PDF has numbers running together without proper line breaks → massive numbers like `568015490128`

### JSON data quality
- `total_assets`: mostly correct (568,015 for Jun-2020 = KES 568bn ✅)
- `profit_after_tax`: mostly wrong (picking up retained earnings row number)
- `basic_eps`: ALWAYS null — never extracted correctly
- `total_income/revenue`: mostly wrong (picking up section numbers)

---

## Standard Chartered Bank Kenya

**PDFs:** 8 | **JSON entries:** 8 | **Note: 2 PDFs have no JSON match**

### PDF Coverage
| Period | File | Consolidation |
|---|---|---|
| 30-Jun-2019 | 2019/Standard_Chartered_Bank_Kenya_Ltd_30_Jun_2019_financials.pdf | Group (Consolidated) ✅ |
| 30-Jun-2020 | 2020/Standard_Chartered_Bank_Kenya_Ltd_30_Jun_2020_audited.pdf | Unknown |
| 30-Sep-2020 | 2020/Standard_Chartered_Bank_Kenya_Ltd_30_Sep_2020_financials.pdf | Group (Consolidated) ✅ |
| 31-Mar-2020 | 2020/Standard_Chartered_Bank_Kenya_Ltd_31_Mar_2020_audited.pdf | Unknown |
| 30-Jun-2022 | 2022/Standard_Chartered_Bank_Kenya_Ltd_30_Jun_2022_financials.pdf | Group (Consolidated) ✅ |
| 31-Dec-2023 | 2024/Standard_Chartered_Bank_Kenya_Ltd_31_Dec_2023_financials.pdf | Group + Company ✅✅ |
| H1 2025 | 2025/Standard_Chartered_Bank_Kenya_Ltd_00_1_51_financials.pdf | Group + Company ✅✅ |
| 31-Dec-2024 | 2025/Standard_Chartered_Bank_Ltd_31_Dec_2024_financials.pdf | Group + Company ✅✅ |

### What the PDFs contain (structure)
StanChart uses the SAME tabular format as ABSA, with numbered rows ("3 NET INTEREST INCOME", "5 TOTAL OPERATING INCOME", "21. TOTAL ASSETS", "35. Paid up/Assigned Capital"). The post-2022 reports show both Group and Company columns.

Notable: "Profit for the year - - - 9,043,839" — dashes indicate zero/interim periods; extractor wrongly reads these as negative signs.

### Extractor bugs found
1. **Negative values for profit**: `profit_after_tax = -9,043,839` when real value is `+9,043,839`. The table format "- - - 9,043,839" gets parsed with dash as negative sign
2. **Same line reference issue**: `total_assets = 21`, `total_equity = 35` (row numbers)
3. **Number concatenation in non-grouped PDFs**: `31-Mar-2020` and `30-Jun-2020` PDFs have all 5 quarterly values on one line → parser concatenates all into one giant number

### JSON data quality
- `total_assets`: Some correct (327,214,126 KES thousands for Jun-2020 ✅)
- `profit_after_tax`: Sign is wrong — stored as positive but extractor reads negative
- **Missing JSON entries**: `H1 2025` and `31-Dec-2024` PDFs → need to add

---

## Safaricom PLC

**PDFs:** 4 | **JSON entries:** 3 | **Note: 2024 extract PDF not in JSON**

### PDF Coverage
| Period | File | Consolidation |
|---|---|---|
| 30-Sep-2019 | 2019/Safaricom_PLC_30_Sep_2019_financials.pdf | Unknown |
| 31-Mar-2019 | 2019/Safaricom_PLC_31_March_2019_audited.pdf | Unknown |
| 31-Mar-2020 | 2020/Safaricom_Plc_31_Mar_2020_audited.pdf | Group (Consolidated) ✅ |
| 31-Mar-2024 | 2024/extracts_from_the_financial_books_of_Safaricom_PLC_31_Mar_2024_audited.pdf | Unknown |

### What the PDFs contain (structure)
Safaricom is a telco, NOT a bank. Structure is completely different:
- Revenue is "Service revenue" in KES Billions (not millions like banks)
- Unique metrics: M-PESA revenue, subscribers, EBITDA
- Year-end is **31 March** (not 31 December like most companies)
- 2020 PDF: values in KES billions (251.22 = KES 251bn service revenue ✅)
- 2024 PDF: values in KES millions (335,353 = KES 335bn ✅) — different unit!

### Extractor bugs found
1. **2019 PDFs: extract NOTHING** — likely scanned image PDFs without text layer (no OCR)
2. **Unit inconsistency**: 2020 = KES billions, 2024 = KES millions → can't compare directly without normalisation
3. **EBITDA wrong**: 2020 PDF shows "113388..0044" = PDF text corruption (doubled digits)
4. **2024 PDF not in JSON**: The "extracts" document from NSE was not picked up by the original scraper

### JSON data quality  
- 2019 periods: all null ❌
- 2020 period: `revenue=251` (correct ✅), `total_equity=114,433` (probably wrong — likely assets not equity)
- **Missing**: 31-Mar-2024 entirely absent from JSON

---

## What Needs To Be Fixed

### Priority 1 — Extractor rewrite
The current extractor is fundamentally broken for tabular PDFs:
- Must skip row reference numbers (1-40 at start of line)
- Must handle multi-column tables (Group vs Company, H1 vs FY)
- Must fix negative sign parsing from dash-formatted tables
- Must normalise units (KES billions vs KES millions vs KES thousands)

### Priority 2 — Missing JSON entries
| Company | Missing Period |
|---|---|
| StanChart | H1 2025 (00_1_51 file) |
| StanChart | 31-Dec-2024 |
| Safaricom | 31-Mar-2024 |

### Priority 3 — Scanned PDFs
The 2019 Safaricom PDFs appear to be image-only (no text layer). Would need OCR to extract.

### What is confirmed correct in current data
- Most `total_assets` values where the PDF doesn't have number-concatenation issues
- `profit_after_tax` values where the diff shows 0.0% (many ABSA entries)
- `basic_eps` from PDF audit (never stored in JSON — always null)

---

## Notes on Group vs Company

- **ABSA**: Reports both Group and Company in same table. Group = ABSA Bank Kenya PLC consolidated. Company = the bank entity alone (minimal subsidiaries). Values are very close.
- **StanChart**: Same format — Group and Company side by side. Post-2022 filings clearly label both.
- **Safaricom**: Group = Safaricom PLC + M-PESA Africa + other subsidiaries. Important for 2024+ as the Ethiopia expansion adds significant assets but different profitability profile.

**Recommendation**: Store Group figures as primary, flag Company figures as secondary.
