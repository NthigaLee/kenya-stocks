"""
JSE (Johannesburg Stock Exchange) adapter.
Handles company discovery, PDF downloading, and JSE-specific rules.

FIX #1: Uses a curated PDF URL registry (backend/data/jse_pdf_registry.json)
         instead of fragile IR-page scraping. Falls back to IR-page scraping
         only when a ticker is not in the registry.
"""

import json
import os
import re
from typing import List, Tuple, Optional
from pathlib import Path
import requests

# Registry path (relative to this file's location)
_REGISTRY_PATH = Path(__file__).parent.parent / "data" / "jse_pdf_registry.json"


class JSE:
    """Johannesburg Stock Exchange adapter."""
    
    def __init__(self, output_dir: str = "data/jse"):
        self.code = "JSE"
        self.name = "Johannesburg Stock Exchange"
        self.currency = "ZAR"
        self.url = "https://www.jse.co.za"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load PDF registry
        self._registry: dict = {}
        if _REGISTRY_PATH.exists():
            with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Drop the _meta key
            self._registry = {k: v for k, v in raw.items() if not k.startswith("_")}
        else:
            print(f"  ⚠️ PDF registry not found at {_REGISTRY_PATH}; falling back to IR scraping")

    # ─────────────────────────────────────────────────────────────────────────
    # COMPANY LIST
    # ─────────────────────────────────────────────────────────────────────────

    def get_company_list(self) -> List[Tuple[str, str, str]]:
        """
        Return JSE Top 30 companies: (ticker, company_name, ir_page_url)

        Sourced from the PDF registry first; supplemented by hardcoded
        fallbacks for tickers not in the registry.
        """
        # Build from registry
        companies = []
        for ticker, info in self._registry.items():
            ir_page = info.get("ir_page", "")
            companies.append((ticker, info.get("company_name", ticker), ir_page))

        if companies:
            return companies

        # Hardcoded fallback (original list — kept for backward compat)
        return [
            ("BHG", "Bidvest Group Limited", "https://www.bidvest.co.za/investor-relations/"),
            ("APN", "Aspen Pharmacare Holdings Limited", "https://www.aspenpharma.com/investors/"),
            ("BTI", "British American Tobacco PLC", "https://www.bat.com/investors"),
            ("NTC", "NetCare Limited", "https://www.netcare.co.za/investors/"),
            ("PRX", "Prosus N.V.", "https://prosus.com/en/investors/"),
            ("FSR", "FirstRand Limited", "https://www.firstrand.co.za/investor-centre/"),
            ("SBK", "Standard Bank Group Limited", "https://www.standardbank.com/group/en/investor-relations.html"),
            ("NED", "Nedbank Group Limited", "https://www.nedbankgroup.co.za/investor-relations"),
            ("ABG", "Absa Group Limited", "https://www.absa.africa/absaafrica/investor-relations/"),
            ("SOL", "Sasol Limited", "https://www.sasol.com/investors"),
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # FIX #1: REGISTRY-BASED PDF DISCOVERY
    # ─────────────────────────────────────────────────────────────────────────

    def get_pdf_urls_from_registry(self, ticker: str) -> List[str]:
        """
        Return all known PDF URLs for a ticker from the curated registry.
        Order: latest_annual → latest_interim → fallbacks.
        """
        info = self._registry.get(ticker)
        if not info:
            return []

        urls = []
        for key in ("latest_annual_pdf_url", "latest_interim_pdf_url"):
            url = info.get(key)
            if url:
                urls.append(url)
        urls.extend(info.get("fallback_urls", []))
        return urls

    def get_registry_meta(self, ticker: str) -> dict:
        """Return registry metadata for a ticker (currency, scale, etc.)."""
        return self._registry.get(ticker, {})

    # ─────────────────────────────────────────────────────────────────────────
    # IR PAGE SCRAPING (legacy fallback)
    # ─────────────────────────────────────────────────────────────────────────

    def get_ir_page_pattern(self, company_name: str) -> str:
        """
        Given a company name, return a likely IR page URL pattern.
        Fallback if custom URL not in get_company_list.
        """
        safe_name = company_name.lower().replace(" ", "-").replace(".", "")
        return f"https://www.{safe_name}.co.za/investor-relations/"

    def discover_pdfs(self, ir_url: str, company_ticker: str) -> List[str]:
        """
        Discover financial statement PDFs on a company's IR page.
        Legacy method — only called when ticker is not in registry.
        """
        pdf_urls = []

        try:
            response = requests.get(ir_url, timeout=10)
            if response.status_code != 200:
                print(f"  ⚠️ IR page not found: {ir_url}")
                return []

            links = re.findall(r'href=["\'](https?://[^\s"\']+\.pdf)', response.text, re.IGNORECASE)

            patterns = [
                r'annual.*report',
                r'financial.*statements',
                r'interim.*report',
                r'h1\s+\d{4}',
                r'h2\s+\d{4}',
                r'q[1-4]\s+\d{4}',
                r'consolidated.*statement',
            ]

            for link in links:
                link_lower = link.lower()
                if any(re.search(p, link_lower) for p in patterns):
                    pdf_urls.append(link)

            return pdf_urls[:10]

        except Exception as e:
            print(f"  ❌ Error discovering PDFs for {company_ticker}: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────
    # DOWNLOAD
    # ─────────────────────────────────────────────────────────────────────────

    def download_pdf(self, url: str, ticker: str, filename: str) -> Optional[Path]:
        """Download a single PDF and save it locally."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            output_path = self.output_dir / ticker / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(response.content)

            print(f"  ✅ Downloaded: {output_path}")
            return output_path

        except requests.exceptions.Timeout:
            print(f"  ⏱️ Timeout: {url}")
            return None
        except Exception as e:
            print(f"  ❌ Error downloading {url}: {e}")
            return None

    def download_all(self, limit: int = 30) -> dict:
        """
        Download all PDFs for Top 30 companies.

        Strategy:
        1. Try registry URLs first (deterministic, no scraping)
        2. Fall back to IR page scraping if ticker not in registry

        Returns:
            {ticker: [list of downloaded file paths], ...}
        """
        companies = self.get_company_list()[:limit]
        results = {}

        print(f"\n🌍 JSE Phase 1: Downloading financial statements for {len(companies)} companies...")
        print(f"   Output: {self.output_dir}\n")

        for ticker, company_name, ir_url in companies:
            print(f"📥 {ticker} — {company_name}")

            # Try registry first
            pdf_urls = self.get_pdf_urls_from_registry(ticker)

            if pdf_urls:
                print(f"   📚 Using registry ({len(pdf_urls)} URL(s))")
            else:
                # Fallback: scrape IR page
                print(f"   🔍 Registry miss — scraping IR page: {ir_url}")
                pdf_urls = self.discover_pdfs(ir_url, ticker)

            if not pdf_urls:
                print(f"   No PDFs found")
                results[ticker] = []
                continue

            print(f"   Found {len(pdf_urls)} candidate PDFs")

            downloaded = []
            for url in pdf_urls:
                filename = url.split('/')[-1]
                if not filename.endswith('.pdf'):
                    filename += '.pdf'

                path = self.download_pdf(url, ticker, filename)
                if path:
                    downloaded.append(str(path))

            results[ticker] = downloaded

        total_downloaded = sum(len(files) for files in results.values())
        print(f"\n✨ Summary: Downloaded {total_downloaded} PDFs across "
              f"{len([t for t, f in results.items() if f])} companies\n")

        return results


if __name__ == "__main__":
    jse = JSE()
    results = jse.download_all(limit=5)

    for ticker, files in results.items():
        print(f"{ticker}: {len(files)} files")
