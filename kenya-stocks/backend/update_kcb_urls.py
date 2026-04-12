import requests
from bs4 import BeautifulSoup
import re

# URLs for KCB financial statements
KCB_IR_PAGE = "https://kcbgroup.com/financial-statements"

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

def get_kcb_financial_statement_links():
    """Scrape KCB's financial statements page to get the latest URLs."""
    try:
        response = requests.get(KCB_IR_PAGE, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links to PDF files
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.pdf') and 'download-report' in href:
                # Get the full URL
                if href.startswith('/'):
                    full_url = f"https://kcbgroup.com{href}"
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://kcbgroup.com/{href}"
                    
                pdf_links.append(full_url)
        
        return pdf_links
        
    except Exception as e:
        print(f"Error fetching KCB financial statements: {e}")
        return []

def main():
    print("Fetching KCB financial statement links...")
    links = get_kcb_financial_statement_links()
    
    print(f"Found {len(links)} PDF links:")
    for link in links:
        print(f"  {link}")
    
    # Generate the updated KNOWN_PDFS entries
    print("\nUpdated KNOWN_PDFS entries for ir_downloader.py:")
    for link in links:
        # Extract the filename to determine the quarter/year
        filename = link.split('/')[-1]
        print(f'    ("KCB", "{link}"),')

if __name__ == "__main__":
    main()