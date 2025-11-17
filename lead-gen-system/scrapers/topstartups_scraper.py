"""
Top Startups India Scraper
==========================
Scrapes startup data from topstartups.io for Indian companies.

Features:
- Extracts company details (name, location, employees, funding)
- Checks website availability and job listings
- Handles dynamic content with Selenium
- Modular and reusable for different filters
- Exports to CSV/JSON with pandas
"""

import time
import re
import json
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TopStartupsScr:
    """Scraper for topstartups.io startup data"""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the scraper with Selenium WebDriver
        
        Args:
            headless: Run browser in headless mode (no GUI)
        """
        self.headless = headless
        self.driver = None
        self.companies_data: List[Dict] = []
        self.base_url = "https://topstartups.io/?hq_location=India"
        
    def setup_driver(self):
        """Configure and initialize Chrome WebDriver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        logger.info("Chrome WebDriver initialized successfully")
        
    def load_page(self, url: str, scroll_times: int = 5):
        """
        Load page and scroll to trigger lazy loading
        
        Args:
            url: URL to load
            scroll_times: Number of times to scroll down
        """
        try:
            logger.info(f"Loading page: {url}")
            self.driver.get(url)
            
            # Wait for initial content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            
            # Scroll to load lazy content
            logger.info(f"Scrolling page {scroll_times} times to load all content...")
            for i in range(scroll_times):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                logger.info(f"Scroll {i+1}/{scroll_times} completed")
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            logger.info("Page loaded and scrolled successfully")
            
        except Exception as e:
            logger.error(f"Error loading page: {e}")
            raise
            
    def get_page_html(self) -> str:
        """Get the fully rendered HTML from Selenium"""
        return self.driver.page_source
    
    def parse_funding(self, funding_text: Optional[str]) -> Optional[int]:
        """
        Parse funding amount and normalize to integer
        
        Args:
            funding_text: Text like "$700M", "$1.2B", "$50K"
            
        Returns:
            Integer funding amount in dollars (e.g., 700000000 for $700M)
        """
        if not funding_text or funding_text.strip() == '':
            return None
            
        try:
            # Remove $ and whitespace
            text = funding_text.replace('$', '').replace(',', '').strip()
            
            # Extract number and unit
            match = re.match(r'([\d.]+)\s*([KMB]?)', text, re.IGNORECASE)
            if not match:
                return None
                
            number = float(match.group(1))
            unit = match.group(2).upper()
            
            # Convert to dollars
            multipliers = {
                'K': 1_000,
                'M': 1_000_000,
                'B': 1_000_000_000,
                '': 1
            }
            
            return int(number * multipliers.get(unit, 1))
            
        except Exception as e:
            logger.warning(f"Error parsing funding '{funding_text}': {e}")
            return None
    
    def parse_employees(self, employee_text: Optional[str]) -> Optional[str]:
        """
        Parse employee count text
        
        Args:
            employee_text: Text like "51–100", "1001–5000", "11-50"
            
        Returns:
            Normalized employee range string
        """
        if not employee_text:
            return None
            
        # Normalize dashes (em-dash to regular dash)
        normalized = employee_text.replace('–', '-').replace('—', '-').strip()
        
        # Validate format
        if re.match(r'\d+[-–]\d+', normalized):
            return normalized
        
        return employee_text.strip() if employee_text else None
    
    def extract_company_data(self, company_soup: BeautifulSoup) -> Dict:
        """
        Extract all data from a single company block
        
        Args:
            company_soup: BeautifulSoup object of company card/block
            
        Returns:
            Dictionary with company data
        """
        data = {
            'company_name': None,
            'hq_location': None,
            'website_available': None,
            'website_url': None,
            'phone': None,
            'employees': None,
            'funding_amount': None,
            'funding_raw': None,
            'jobs_available': None,
            'jobs_link': None,
            'description': None,
            'industry': None,
            'founded_year': None
        }
        
        try:
            # Company Name - try multiple strategies
            name_elem = None
            
            # Strategy 1: Look for heading tags (h1, h2, h3, h4)
            for tag in ['h1', 'h2', 'h3', 'h4']:
                name_elem = company_soup.find(tag)
                if name_elem:
                    text = name_elem.get_text(strip=True)
                    # Skip if it's the "See who works here" text
                    if text and 'see who works' not in text.lower() and len(text) > 2:
                        data['company_name'] = text
                        break
            
            # Strategy 2: Look for links with company names
            if not data['company_name']:
                # Find the main website link and extract domain as company name
                website_link = company_soup.find('a', href=re.compile(r'http'))
                if website_link and website_link.get('href'):
                    href = website_link.get('href')
                    # Extract domain name (e.g., "innoviti" from "innoviti.com")
                    domain_match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+)\.com', href)
                    if domain_match:
                        domain = domain_match.group(1)
                        # Capitalize first letter
                        data['company_name'] = domain.capitalize()
            
            # Strategy 3: Look for any link to company page
            if not data['company_name']:
                name_elem = company_soup.find('a', href=re.compile(r'/company/'))
                if name_elem:
                    text = name_elem.get_text(strip=True)
                    if text and 'see who works' not in text.lower():
                        data['company_name'] = text
            
            # HQ Location
            location_elem = company_soup.find(text=re.compile(r'location|headquarters', re.I))
            if location_elem:
                data['hq_location'] = location_elem.parent.get_text(strip=True)
            else:
                # Try finding by icon or common patterns
                loc = company_soup.find(['span', 'div'], class_=re.compile(r'location', re.I))
                if loc:
                    data['hq_location'] = loc.get_text(strip=True)
            
            # Website
            website_link = company_soup.find('a', text=re.compile(r'Check company site|Visit|Website', re.I))
            if not website_link:
                website_link = company_soup.find('a', href=re.compile(r'http|www'))
            
            if website_link:
                data['website_available'] = True
                data['website_url'] = website_link.get('href', None)
            else:
                data['website_available'] = False
            
            # Phone Number
            phone_elem = company_soup.find(text=re.compile(r'\+?\d{10,}'))
            if phone_elem:
                phone_text = phone_elem.strip()
                phone_match = re.search(r'\+?[\d\s\-()]{10,}', phone_text)
                if phone_match:
                    data['phone'] = phone_match.group(0).strip()
            
            # Employees
            emp_elem = company_soup.find(text=re.compile(r'\d+[-–]\d+|\d+\+'))
            if emp_elem:
                emp_text = emp_elem.strip()
                # Look for patterns like "51-100", "1001-5000"
                emp_match = re.search(r'\d+[-–]\d+', emp_text)
                if emp_match:
                    data['employees'] = self.parse_employees(emp_match.group(0))
            
            # Funding
            funding_elem = company_soup.find(text=re.compile(r'\$[\d.]+\s*[KMB]', re.I))
            if funding_elem:
                funding_text = funding_elem.strip()
                funding_match = re.search(r'\$[\d.]+\s*[KMB]?', funding_text, re.I)
                if funding_match:
                    data['funding_raw'] = funding_match.group(0)
                    data['funding_amount'] = self.parse_funding(data['funding_raw'])
            
            # Jobs Available
            jobs_link = company_soup.find('a', text=re.compile(r'View Jobs?|Careers?|Hiring', re.I))
            if not jobs_link:
                jobs_link = company_soup.find('a', href=re.compile(r'jobs|careers', re.I))
            
            if jobs_link:
                data['jobs_available'] = True
                data['jobs_link'] = jobs_link.get('href', None)
            else:
                data['jobs_available'] = False
            
            # Description
            desc_elem = company_soup.find(['p', 'div'], class_=re.compile(r'description|about', re.I))
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)[:200]  # Limit to 200 chars
            
            # Industry/Category
            industry_elem = company_soup.find(['span', 'div'], class_=re.compile(r'category|industry|tag', re.I))
            if industry_elem:
                data['industry'] = industry_elem.get_text(strip=True)
            
            # Founded Year
            year_elem = company_soup.find(text=re.compile(r'Founded|Est\.?\s*\d{4}', re.I))
            if year_elem:
                year_match = re.search(r'\d{4}', year_elem)
                if year_match:
                    data['founded_year'] = int(year_match.group(0))
            
        except Exception as e:
            logger.warning(f"Error extracting company data: {e}")
        
        return data
    
    def scrape_companies(self, html: str) -> List[Dict]:
        """
        Parse HTML and extract all company data
        
        Args:
            html: Rendered HTML from Selenium
            
        Returns:
            List of company dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        companies = []
        
        # Try multiple selectors for company cards
        selectors = [
            'div[class*="company"]',
            'div[class*="card"]',
            'div[class*="startup"]',
            'article',
            'li[class*="company"]'
        ]
        
        company_blocks = []
        for selector in selectors:
            blocks = soup.select(selector)
            if blocks and len(blocks) > 5:  # Found meaningful results
                company_blocks = blocks
                logger.info(f"Found {len(blocks)} company blocks using selector: {selector}")
                break
        
        if not company_blocks:
            logger.warning("No company blocks found with standard selectors, trying fallback...")
            # Fallback: find all divs with links to company pages
            all_divs = soup.find_all('div')
            company_blocks = [div for div in all_divs if div.find('a', href=re.compile(r'/company/'))]
        
        logger.info(f"Processing {len(company_blocks)} company blocks...")
        
        for idx, block in enumerate(company_blocks, 1):
            company_data = self.extract_company_data(block)
            
            # Only add if we got at least a company name
            if company_data.get('company_name'):
                companies.append(company_data)
                logger.info(f"Extracted company {idx}: {company_data['company_name']}")
            else:
                logger.debug(f"Skipped block {idx} - no company name found")
        
        return companies
    
    def scrape(self, url: Optional[str] = None, scroll_times: int = 5) -> List[Dict]:
        """
        Main scraping method
        
        Args:
            url: URL to scrape (defaults to base India startups page)
            scroll_times: Number of scroll iterations for lazy loading
            
        Returns:
            List of company dictionaries
        """
        try:
            self.setup_driver()
            
            target_url = url or self.base_url
            self.load_page(target_url, scroll_times=scroll_times)
            
            html = self.get_page_html()
            self.companies_data = self.scrape_companies(html)
            
            logger.info(f"Successfully scraped {len(self.companies_data)} companies")
            return self.companies_data
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert scraped data to pandas DataFrame"""
        if not self.companies_data:
            logger.warning("No data to convert. Run scrape() first.")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.companies_data)
        logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        return df
    
    def save_to_csv(self, filename: Optional[str] = None) -> str:
        """
        Save data to CSV file
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        df = self.to_dataframe()
        
        if df.empty:
            logger.warning("No data to save")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/topstartups_india_{timestamp}.csv'
        
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} companies to {filename}")
        return filename
    
    def save_to_json(self, filename: Optional[str] = None) -> str:
        """
        Save data to JSON file
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if not self.companies_data:
            logger.warning("No data to save")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/topstartups_india_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.companies_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.companies_data)} companies to {filename}")
        return filename
    
    def get_statistics(self) -> Dict:
        """Calculate statistics about scraped data"""
        if not self.companies_data:
            return {}
        
        df = self.to_dataframe()
        
        stats = {
            'total_companies': len(df),
            'with_website': df['website_available'].sum() if 'website_available' in df else 0,
            'with_phone': df['phone'].notna().sum() if 'phone' in df else 0,
            'with_funding': df['funding_amount'].notna().sum() if 'funding_amount' in df else 0,
            'with_jobs': df['jobs_available'].sum() if 'jobs_available' in df else 0,
            'with_employees': df['employees'].notna().sum() if 'employees' in df else 0,
            'total_funding': df['funding_amount'].sum() if 'funding_amount' in df else 0,
            'avg_funding': df['funding_amount'].mean() if 'funding_amount' in df else 0,
        }
        
        # Coverage percentages
        if stats['total_companies'] > 0:
            stats['website_coverage'] = f"{(stats['with_website'] / stats['total_companies'] * 100):.1f}%"
            stats['phone_coverage'] = f"{(stats['with_phone'] / stats['total_companies'] * 100):.1f}%"
            stats['funding_coverage'] = f"{(stats['with_funding'] / stats['total_companies'] * 100):.1f}%"
            stats['jobs_coverage'] = f"{(stats['with_jobs'] / stats['total_companies'] * 100):.1f}%"
        
        return stats
    
    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.get_statistics()
        
        if not stats:
            print("No statistics available. Run scrape() first.")
            return
        
        print("\n" + "="*60)
        print("TOP STARTUPS INDIA - SCRAPING STATISTICS")
        print("="*60)
        print(f"Total Companies Scraped: {stats['total_companies']}")
        print(f"\nData Coverage:")
        print(f"  - With Website: {stats['with_website']} ({stats.get('website_coverage', 'N/A')})")
        print(f"  - With Phone: {stats['with_phone']} ({stats.get('phone_coverage', 'N/A')})")
        print(f"  - With Funding Info: {stats['with_funding']} ({stats.get('funding_coverage', 'N/A')})")
        print(f"  - With Job Listings: {stats['with_jobs']} ({stats.get('jobs_coverage', 'N/A')})")
        print(f"  - With Employee Count: {stats['with_employees']}")
        
        if stats['total_funding'] > 0:
            print(f"\nFunding Stats:")
            print(f"  - Total Funding: ${stats['total_funding']:,.0f}")
            print(f"  - Average Funding: ${stats['avg_funding']:,.0f}")
        
        print("="*60 + "\n")


# Modular helper functions for reusability
def scrape_india_startups(headless: bool = True, scroll_times: int = 5) -> pd.DataFrame:
    """
    Quick function to scrape all Indian startups
    
    Args:
        headless: Run in headless mode
        scroll_times: Number of scrolls to load content
        
    Returns:
        DataFrame with startup data
    """
    scraper = TopStartupsScr(headless=headless)
    scraper.scrape(scroll_times=scroll_times)
    return scraper.to_dataframe()


def scrape_by_category(category: str, headless: bool = True) -> pd.DataFrame:
    """
    Scrape startups filtered by category
    
    Args:
        category: Category slug (e.g., 'ai', 'fintech', 'saas')
        headless: Run in headless mode
        
    Returns:
        DataFrame with filtered startup data
    """
    url = f"https://topstartups.io/?industry={category}&hq_location=India"
    scraper = TopStartupsScr(headless=headless)
    scraper.scrape(url=url)
    return scraper.to_dataframe()


def scrape_by_location(location: str, headless: bool = True) -> pd.DataFrame:
    """
    Scrape startups filtered by location
    
    Args:
        location: Location name (e.g., 'Bangalore', 'Mumbai')
        headless: Run in headless mode
        
    Returns:
        DataFrame with filtered startup data
    """
    url = f"https://topstartups.io/?hq_location={location}"
    scraper = TopStartupsScr(headless=headless)
    scraper.scrape(url=url)
    return scraper.to_dataframe()


if __name__ == "__main__":
    """Example usage"""
    
    print("Starting Top Startups India scraper...")
    print("This will take 2-3 minutes to load and scrape all startups...\n")
    
    # Initialize scraper
    scraper = TopStartupsScr(headless=True)  # Set to False to see browser
    
    # Scrape data
    companies = scraper.scrape(scroll_times=8)  # More scrolls = more companies
    
    # Print statistics
    scraper.print_statistics()
    
    # Convert to DataFrame
    df = scraper.to_dataframe()
    
    # Display sample
    print("Sample Data (first 5 companies):")
    print(df.head().to_string())
    print()
    
    # Save to files
    csv_file = scraper.save_to_csv()
    json_file = scraper.save_to_json()
    
    print(f"\n✅ Data saved to:")
    print(f"   - CSV: {csv_file}")
    print(f"   - JSON: {json_file}")
    
    # Example: Filter high-value leads
    print("\n" + "="*60)
    print("HIGH-VALUE LEADS ANALYSIS")
    print("="*60)
    
    if not df.empty:
        # Startups with funding > $1M
        if 'funding_amount' in df.columns:
            funded = df[df['funding_amount'] > 1_000_000].copy()
            print(f"\nStartups with >$1M funding: {len(funded)}")
            if len(funded) > 0:
                print(f"Average funding: ${funded['funding_amount'].mean():,.0f}")
        
        # Startups hiring (jobs available)
        if 'jobs_available' in df.columns:
            hiring = df[df['jobs_available'] == True]
            print(f"\nStartups currently hiring: {len(hiring)}")
        
        # Startups without website (URGENT leads!)
        if 'website_available' in df.columns:
            no_website = df[df['website_available'] == False]
            print(f"\nStartups without website (URGENT): {len(no_website)}")
    
    print("\n✅ Scraping completed successfully!")
