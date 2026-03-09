"""
IFRS Financial Statements Extractor
Works for both Kenya NSE and South Africa JSE (both use IFRS).
Extracts key metrics from annual and interim reports.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, List
import pypdf
from decimal import Decimal

class IFRSExtractor:
    """Extract financial metrics from IFRS-compliant PDFs (Kenya + SA)."""
    
    def __init__(self, exchange: str = "NSE"):
        self.exchange = exchange  # "NSE" or "JSE"
        self.currency = "KES" if exchange == "NSE" else "ZAR"
    
    def extract_pdf(self, pdf_path: str, ticker: str) -> Optional[Dict]:
        """
        Extract financials from a PDF file.
        
        Returns:
        {
            "url": "...",
            "year": 2024,
            "title": "...",
            "company": "...",
            "ticker": "...",
            "period": "Dec 2024",
            "period_type": "annual",
            "period_end_date": "2024-12-31",
            "currency": "KES" or "ZAR",
            "scale": "millions",   # NEW: detected number scale
            "net_interest_income": 123456789,
            "revenue": 234567890,
            "profit_before_tax": 45678901,
            "profit_after_tax": 34567890,
            "basic_eps": 1.23,
            "dividend_per_share": 0.45,
            "total_assets": 1234567890,
            "total_equity": 234567890,
            "customer_deposits": 123456789,
            "loans_and_advances": 987654321,
        }
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf = pypdf.PdfReader(f)
                text = ""
                for page in pdf.pages[:20]:  # Read first 20 pages
                    text += page.extract_text()
            
            # Extract basics
            title = Path(pdf_path).stem
            year = self._extract_year(text, title)
            period_type = self._detect_period_type(text, title)
            period_end_date = self._extract_period_end_date(text, title, period_type)

            # FIX #2: Detect scale (thousands / millions / single)
            scale = self._detect_scale(text)

            # Extract EPS raw values (may be in cents)
            raw_eps = self._extract_eps_raw(text)
            eps_normalized = self._normalize_eps(raw_eps, self.currency, text)

            # FIX #3: DPS — try tabular first, then narrative
            dps_tabular = self._extract_dps(text)
            dps_narrative = self._extract_dps_narrative(text, self.currency)
            dps = dps_tabular if dps_tabular is not None else dps_narrative

            # Normalize DPS from cents if narrative extraction detected cents
            if dps is not None and dps > 50 and self.exchange == "JSE":
                # JSE DPS > 50 is almost certainly cents (e.g. 70c → 0.70 ZAR)
                # Conservative: only convert if unit hint is in text
                if self._text_has_cents_unit(text, "dividend"):
                    dps = dps / 100

            metrics = {
                "url": "",
                "year": year,
                "title": title,
                "company": None,
                "ticker": ticker,
                "period": self._format_period(period_end_date),
                "period_type": period_type,
                "period_end_date": period_end_date,
                "currency": self.currency,
                "scale": scale,
                "net_interest_income": self._extract_nii(text),
                "revenue": self._extract_revenue(text),
                "profit_before_tax": self._extract_pbt(text),
                "profit_after_tax": self._extract_pat(text),
                "basic_eps": eps_normalized,
                "dividend_per_share": dps,
                "total_assets": self._extract_assets(text),
                "total_equity": self._extract_equity(text),
                "customer_deposits": self._extract_deposits(text),
                "loans_and_advances": self._extract_loans(text),
                "ebitda": None,
                "operating_expenses": None,
                "impairment_charges": None,
                "mpesa_revenue": None,
            }
            
            return metrics
        
        except Exception as e:
            print(f"  ❌ Extraction failed for {pdf_path}: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # FIX #2: SCALE DETECTION
    # ─────────────────────────────────────────────────────────────────────────

    def _detect_scale(self, text: str) -> str:
        """
        Detect the numeric scale used in the document.
        Returns: "thousands" | "millions" | "single"

        Searches for explicit disclosure phrases common in IFRS reports.
        Conservative: returns "single" if no clear signal found.
        """
        # Normalise for matching (collapse whitespace, lower)
        sample = " ".join(text[:3000].split()).lower()

        # ── Thousands patterns ─────────────────────────────────────────────
        thousands_patterns = [
            r"in thousands of rand",
            r"expressed in.*?thousands",
            r"r\s*['\u2019]000",        # R'000 or R'000
            r"zar\s*['\u2019]000",
            r"r000",
            r"in r 000",
            r"\(r\s*thousands\)",
            r"all amounts.*?thousands",
            r"figures.*?in thousands",
        ]
        for p in thousands_patterns:
            if re.search(p, sample):
                return "thousands"

        # ── Millions patterns ──────────────────────────────────────────────
        millions_patterns = [
            r"in millions of rand",
            r"expressed in.*?millions",
            r"zar millions",
            r"usd millions",
            r"r millions",
            r"in r million",
            r"\(r\s*millions\)",
            r"all amounts.*?millions",
            r"figures.*?in millions",
            r"in millions",
        ]
        for p in millions_patterns:
            if re.search(p, sample):
                return "millions"

        # ── Fallback: infer from revenue magnitude ─────────────────────────
        # If we can find a revenue-like number and it's in the 6-digit range,
        # that's probably thousands (real value would be ~billions).
        # This is heuristic — only used when no explicit disclosure found.
        revenue_match = re.search(
            r'(?:total revenue|revenue|turnover)[:\s]+(\d{1,3}(?:,\d{3})+)',
            text[:5000], re.IGNORECASE
        )
        if revenue_match:
            raw = revenue_match.group(1).replace(',', '')
            try:
                val = float(raw)
                if 10_000 < val < 100_000_000:
                    # Likely thousands (R100k – R100bn in thousands)
                    return "thousands"
                elif val >= 100_000_000:
                    # Already in actual units (rare)
                    return "single"
            except ValueError:
                pass

        # ── JSE Heuristic: check for space-separated large numbers ────────
        # SA reports commonly omit unit header but use space as thousands sep
        # e.g. "Revenue  122 615 986" = 122,615,986 ZAR thousands = R122.6bn
        if self.exchange == "JSE":
            space_num = re.search(r'(?:revenue|total assets)\s+(\d{1,3}(?:\s\d{3})+)', text[:8000], re.IGNORECASE)
            if space_num:
                raw = space_num.group(1).replace(' ', '')
                try:
                    val = float(raw)
                    if val > 5_000_000:  # > 5M ZAR in thousands = > R5B
                        return "thousands"
                except ValueError:
                    pass

        return "single"  # Conservative default

    # ─────────────────────────────────────────────────────────────────────────
    # FIX #3: DPS NARRATIVE EXTRACTION
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_dps_narrative(self, text: str, currency: str) -> Optional[float]:
        """
        Extract dividend per share from narrative text.
        JSE reports often state: "70.0 cents per share" rather than a table.

        Returns value in currency units (already divided by 100 if cents).
        Returns None if no clear match.
        """
        # Collapse whitespace for easier matching
        flat = " ".join(text.split())

        # Pattern set: capture numeric value + optional unit
        patterns = [
            # "dividend per share of 70.0 cents"
            r'dividend\s+per\s+share\s+of\s+([\d]+(?:[.,]\d+)?)\s*(cents?|c\b|zar|usd|r\b)?',
            # "dividend per share: 70.0 cents"
            r'dividend\s+per\s+share[:\s]+([\d]+(?:[.,]\d+)?)\s*(cents?|c\b|zar|usd|r\b)?',
            # "proposed dividend of 70.0 cents per share"
            r'proposed\s+(?:final\s+)?dividend\s+of\s+([\d]+(?:[.,]\d+)?)\s*(cents?|c\b|zar|usd|r\b)?\s*per\s+share',
            # "total dividend 70.0 cents per share"
            r'total\s+dividend\s+([\d]+(?:[.,]\d+)?)\s*(cents?|c\b|zar|usd|r\b)?\s*per\s+share',
            # "dividend payment of 70.0 cents per share"
            r'dividend\s+payment\s+of\s+([\d]+(?:[.,]\d+)?)\s*(cents?|c\b|zar|usd|r\b)?\s*per\s+share',
            # "total dividends: 140 cents" (full-year might be combined)
            r'total\s+dividends?[:\s]+([\d]+(?:[.,]\d+)?)\s*(cents?|c\b)',
            # "final dividend 35.0 cents per share"
            r'final\s+dividend\s+([\d]+(?:[.,]\d+)?)\s*(cents?|c\b|zar|usd|r\b)?\s*per\s+share',
            # "interim dividend 35.0 cents per share"
            r'interim\s+dividend\s+([\d]+(?:[.,]\d+)?)\s*(cents?|c\b|zar|usd|r\b)?\s*per\s+share',
        ]

        for pattern in patterns:
            match = re.search(pattern, flat, re.IGNORECASE)
            if match:
                raw_val = match.group(1).replace(',', '.')
                try:
                    value = float(raw_val)
                except ValueError:
                    continue

                # Sanity check: DPS should be positive and not absurdly large
                if value <= 0 or value > 50_000:
                    continue

                unit = (match.group(2) or "").lower().strip()

                # Convert cents to currency units
                if unit in ('cents', 'cent', 'c'):
                    return value / 100

                # Explicit currency — return as-is
                if unit in ('zar', 'usd', 'r'):
                    return value

                # No unit stated: if value looks like cents (> 5 and currency is ZAR),
                # convert conservatively only if > 10 (below 10 could be ZAR/USD)
                if not unit and value > 10 and currency in ('ZAR', 'KES'):
                    return value / 100

                return value  # Best guess: already in currency

        return None

    def _text_has_cents_unit(self, text: str, context_keyword: str) -> bool:
        """Return True if 'cents' appears near context_keyword in text."""
        pattern = rf'{context_keyword}.{{0,100}}cents'
        return bool(re.search(pattern, text, re.IGNORECASE))

    # ─────────────────────────────────────────────────────────────────────────
    # FIX #4: EPS UNIT CONVERSION
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_eps_raw(self, text: str) -> Optional[float]:
        """Extract raw EPS value (may be in cents)."""
        keywords = [
            'basic earnings per share',
            'basic eps',
            'earnings per share',
            'eps',
        ]
        value = self._extract_number(text, *keywords)
        if value and abs(value) < 100_000:
            return value
        return None

    def _normalize_eps(self, raw_eps: Optional[float], currency: str, text: str) -> Optional[float]:
        """
        Normalize EPS to currency units.
        JSE often reports EPS in cents; this converts to ZAR/USD.

        Logic:
        - If nearby text says "cents", divide by 100
        - If value > 50 and JSE, conservatively assume cents → divide by 100
        - NSE/KES EPS is typically already in KES (larger numbers normal)
        """
        if raw_eps is None:
            return None

        if self.exchange == "NSE":
            # KES EPS not in cents — return as-is
            return raw_eps

        # JSE: check for explicit cents disclosure near EPS
        if self._text_has_cents_unit(text, r'earnings\s+per\s+share'):
            return raw_eps / 100

        # JSE heuristic: EPS > 50 is almost certainly in cents
        if raw_eps > 50:
            return raw_eps / 100

        return raw_eps

    # ─────────────────────────────────────────────────────────────────────────
    # PERIOD DETECTION — improved
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_year(self, text: str, filename: str) -> Optional[int]:
        """Extract year from text or filename."""
        # Try filename first
        year_match = re.search(r'\b(20\d{2})\b', filename)
        if year_match:
            return int(year_match.group(1))
        
        # Try text — "year ended 31 December 2024"
        year_match = re.search(
            r'(?:year\s+ended|as\s+at)\s+[0-9]{1,2}\s+'
            r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+(20\d{2})',
            text, re.IGNORECASE
        )
        if year_match:
            return int(year_match.group(1))
        
        return None
    
    def _detect_period_type(self, text: str, filename: str) -> str:
        """
        Detect if annual, interim, or quarterly.

        FIX #4: Improved — searches for actual date phrases before falling
        back to keyword matching. "year ended" takes priority over filename
        keywords.
        """
        combined = (text[:3000] + " " + filename).lower()

        # ── 1. Explicit date phrases (highest confidence) ──────────────────
        # "year ended 31 December 2024" or "for the year ended"
        if re.search(r'\b(?:for\s+the\s+)?year\s+ended\b', combined):
            return "annual"

        # "six months ended" / "six-month period ended"
        if re.search(r'six[\s-]months?\s+ended', combined):
            return "half_year"

        # "three months ended" / "quarter ended"
        if re.search(r'(?:three[\s-]months?\s+ended|quarter(?:ly)?\s+ended)', combined):
            return "quarter"

        # ── 2. Keyword fallbacks ───────────────────────────────────────────
        if re.search(r'\b(annual\s+report|fy\d{2,4}|full[\s-]year)\b', combined):
            return "annual"
        if re.search(r'\b(h1|h2|half[\s-]?year(?:ly)?|interim\s+report|six\s+months)\b', combined):
            return "half_year"
        if re.search(r'\b(q[1-4]|quarter(?:ly)?)\b', combined):
            return "quarter"

        # ── 3. Conservative default — do NOT default to half_year ─────────
        return "annual"
    
    def _extract_period_end_date(self, text: str, filename: str, period_type: str) -> Optional[str]:
        """Extract period end date (ISO format YYYY-MM-DD)."""
        # Try filename (e.g., "2024-12-31" or "31_Dec_2024")
        date_match = re.search(r'(\d{4})[_-](\d{1,2})[_-](\d{1,2})', filename)
        if date_match:
            try:
                return f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
            except:
                pass
        
        months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }

        # FIX #4: broader patterns — "(year|period|six months) ended DD Month YYYY"
        for month_name, month_num in months.items():
            pattern = (
                rf'(?:year|period|six\s+months?)\s+ended\s+(\d{{1,2}})\s+{month_name}\s+(20\d{{2}})'
            )
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = int(match.group(1))
                year = match.group(2)
                return f"{year}-{month_num}-{day:02d}"

        # Legacy patterns: "as at DD Month YYYY"
        for month_name, month_num in months.items():
            pattern = rf'(?:as\s+at)\s+(\d{{1,2}})\s+{month_name}\s+(20\d{{2}})'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = int(match.group(1))
                year = match.group(2)
                return f"{year}-{month_num}-{day:02d}"
        
        # Fallback: assume period type
        year = self._extract_year(text, filename)
        if year:
            if period_type == "annual":
                return f"{year}-12-31"
            elif period_type == "half_year":
                return f"{year}-06-30"
            elif period_type == "quarter":
                return f"{year}-03-31"
        
        return None
    
    def _format_period(self, date_str: Optional[str]) -> Optional[str]:
        """Convert YYYY-MM-DD to readable period (e.g., 'Dec2024', 'Q1 2025')."""
        if not date_str:
            return None
        
        try:
            parts = date_str.split('-')
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            
            months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month_name = months[month]
            
            # Infer quarter
            quarter = (month - 1) // 3 + 1
            
            # If it looks like a quarter end (month = 3, 6, 9, 12)
            if month in [3, 6, 9, 12]:
                return f"Q{quarter} {year}"
            
            return f"{month_name}{year}"
        except:
            return None
    
    # ─────────────────────────────────────────────────────────────────────────
    # GENERIC NUMBER EXTRACTOR
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_number(self, text: str, *keywords: str) -> Optional[float]:
        """
        Generic number extractor.
        Searches for pattern like:
            Keyword: X,XXX,XXX or X XXX XXX (space-separated) or X.XXX (European format)
        """
        for keyword in keywords:
            # Pattern 1: Keyword followed by numbers (comma or period separated)
            pattern = rf'{keyword}[:\s]+(-?\d{{1,3}}(?:[,\.]\d{{3}})*(?:[,\.]\d{{2}})?)'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                value_str = match.group(1).replace(',', '').replace('.', '')
                try:
                    value = float(value_str)
                    if abs(value) > 1000:  # Ignore trivial numbers
                        return value
                except:
                    pass
            
            # Pattern 2: Space-separated numbers (common in SA/JSE reports)
            # e.g. "Revenue  122 615 986  114 911 518"
            pattern2 = rf'{keyword}\s+(-?\d{{1,3}}(?:\s\d{{3}})+)'
            matches2 = re.finditer(pattern2, text, re.IGNORECASE)
            
            for match in matches2:
                value_str = match.group(1).replace(' ', '')
                try:
                    value = float(value_str)
                    if abs(value) > 1000:
                        return value
                except:
                    pass
        
        return None
    
    # ─────────────────────────────────────────────────────────────────────────
    # INDIVIDUAL METRIC EXTRACTORS
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_nii(self, text: str) -> Optional[float]:
        """Extract Net Interest Income."""
        return self._extract_number(
            text,
            'net interest income',
            'interest income net of expense',
            'net interest revenue',
        )
    
    def _extract_revenue(self, text: str) -> Optional[float]:
        """Extract Total Revenue."""
        return self._extract_number(
            text,
            'total revenue',
            'operating revenue',
            'revenue',
            'operating income',
        )
    
    def _extract_pbt(self, text: str) -> Optional[float]:
        """Extract Profit Before Tax."""
        return self._extract_number(
            text,
            'profit before taxation',
            'profit before tax',
            'earnings before tax',
            'income before tax',
        )
    
    def _extract_pat(self, text: str) -> Optional[float]:
        """Extract Profit After Tax (Net Income)."""
        return self._extract_number(
            text,
            'profit for the year',
            'net profit',
            'profit after tax',
            'net income',
            'net earnings',
        )
    
    def _extract_eps(self, text: str) -> Optional[float]:
        """Extract and normalize EPS (backward-compat wrapper)."""
        raw = self._extract_eps_raw(text)
        return self._normalize_eps(raw, self.currency, text)
    
    def _extract_dps(self, text: str) -> Optional[float]:
        """Extract Dividend Per Share (tabular format)."""
        keywords = [
            'dividend per share',
            'dps',
            'proposed dividend',
        ]
        value = self._extract_number(text, *keywords)
        if value and abs(value) < 10_000:
            return value
        return None
    
    def _extract_assets(self, text: str) -> Optional[float]:
        """Extract Total Assets."""
        return self._extract_number(text, 'total assets')
    
    def _extract_equity(self, text: str) -> Optional[float]:
        """Extract Total Equity / Shareholders' Equity."""
        return self._extract_number(
            text,
            'total equity',
            'shareholders equity',
            "shareholders' equity",
            'equity attributable to owners',
        )
    
    def _extract_deposits(self, text: str) -> Optional[float]:
        """Extract Customer Deposits (banking sector)."""
        return self._extract_number(
            text,
            'customer deposits',
            'deposits from customers',
            'deposits',
        )
    
    def _extract_loans(self, text: str) -> Optional[float]:
        """Extract Loans and Advances (banking sector)."""
        return self._extract_number(
            text,
            'loans and advances',
            'loans and advancements',
            'net loans',
        )


if __name__ == "__main__":
    # Test: Extract from a Kenya sample
    extractor = IFRSExtractor(exchange="NSE")
    
    sample_pdf = "kenya-stocks/data/nse/KCB/KCB_Group_Plc_31_Dec_2024_financials.pdf"
    if Path(sample_pdf).exists():
        result = extractor.extract_pdf(sample_pdf, "KCB")
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Sample PDF not found: {sample_pdf}")
