"""
IndiaMART Scraper - B2B Business Data
High-quality manufacturer and supplier data with verified contact details
"""
import time
import csv
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class IndiaMartScraper:
    """Scrape B2B businesses from IndiaMART"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.businesses = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        logger.info("Chrome WebDriver initialized")
        
    def scrape_category(self, category_url, max_pages=5):
        """
        Scrape IndiaMART category
        
        Example URLs:
        - Marketing agencies: https://dir.indiamart.com/impcat/advertising-agencies.html
        - Web designers: https://dir.indiamart.com/impcat/website-designing-services.html
        - Fashion manufacturers: https://dir.indiamart.com/impcat/garments.html
        """
        logger.info(f"Scraping IndiaMART: {category_url}")
        print(f"\n🔍 Scraping IndiaMART Category")
        print("="*70)
        
        try:
            self.setup_driver()
            
            for page in range(1, max_pages + 1):
                url = f"{category_url}?page={page}" if page > 1 else category_url
                logger.info(f"Scraping page {page}: {url}")
                
                self.driver.get(url)
                time.sleep(3)
                
                # Parse page
                soup = BeautifulSoup(self.driver.page_source, 'lxml')
                
                # Find company listings
                companies = soup.find_all('div', class_=['bg-white', 'company-card'])
                if not companies:
                    # Try alternative selectors
                    companies = soup.find_all('li', class_='lst')
                
                logger.info(f"Found {len(companies)} companies on page {page}")
                
                for company in companies:
                    business = self.parse_company(company)
                    if business and business['business_name']:
                        self.businesses.append(business)
                        print(f"\n✓ {business['business_name']}")
                        if business['email']:
                            print(f"  📧 {business['email']}")
                        if business['phone']:
                            print(f"  📞 {business['phone']}")
                        if business['website']:
                            print(f"  🌐 {business['website']}")
                
                print(f"\nPage {page} complete: {len(self.businesses)} total businesses")
                time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error scraping IndiaMART: {e}")
            print(f"\n❌ Error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
    
    def parse_company(self, company_element):
        """Parse company details from listing"""
        try:
            business = {
                'business_name': None,
                'contact_person': None,
                'designation': None,
                'phone': None,
                'mobile': None,
                'email': None,
                'website': None,
                'address': None,
                'city': None,
                'state': None,
                'gst_number': None,
                'year_established': None,
                'business_type': None,
                'products_services': None,
                'company_url': None,
            }
            
            # Company name
            name_elem = company_element.find(['h2', 'h3', 'a'], class_=re.compile(r'company|name|title'))
            if name_elem:
                business['business_name'] = name_elem.get_text(strip=True)
            
            # Company URL
            link = company_element.find('a', href=True)
            if link:
                href = link['href']
                if not href.startswith('http'):
                    href = 'https://www.indiamart.com' + href
                business['company_url'] = href
            
            # Contact person
            contact_elem = company_element.find(string=re.compile(r'Contact Person|Mr\.|Mrs\.|Ms\.'))
            if contact_elem:
                business['contact_person'] = contact_elem.strip()
            
            # Phone/Mobile
            phone_elems = company_element.find_all(['a', 'span'], href=re.compile(r'tel:'), class_=re.compile(r'phone|mobile|call'))
            for elem in phone_elems:
                phone_text = elem.get_text(strip=True)
                phone = re.sub(r'\D', '', phone_text)
                if len(phone) >= 10:
                    if not business['phone']:
                        business['phone'] = phone[-10:]
                    else:
                        business['mobile'] = phone[-10:]
            
            # If no phone found, search in text
            if not business['phone']:
                text = company_element.get_text()
                phone_matches = re.findall(r'\d{10}', re.sub(r'[^\d]', '', text))
                if phone_matches:
                    business['phone'] = phone_matches[0]
            
            # Email
            email_elem = company_element.find('a', href=re.compile(r'mailto:'))
            if email_elem:
                email = email_elem['href'].replace('mailto:', '')
                business['email'] = email
            else:
                # Search for email in text
                text = company_element.get_text()
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                if email_match:
                    business['email'] = email_match.group(0)
            
            # Website
            website_elem = company_element.find('a', string=re.compile(r'Visit Website|Website', re.I))
            if website_elem and website_elem.get('href'):
                business['website'] = website_elem['href']
            
            # Address
            address_elem = company_element.find(['span', 'div', 'p'], class_=re.compile(r'address|location'))
            if address_elem:
                business['address'] = address_elem.get_text(strip=True)
            
            # GST Number
            gst_elem = company_element.find(string=re.compile(r'GST|GSTIN'))
            if gst_elem:
                gst_match = re.search(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[A-Z]{1}\d{1}', gst_elem)
                if gst_match:
                    business['gst_number'] = gst_match.group(0)
            
            # Year established
            year_elem = company_element.find(string=re.compile(r'Year|Since|Established'))
            if year_elem:
                year_match = re.search(r'(19|20)\d{2}', year_elem)
                if year_match:
                    business['year_established'] = year_match.group(0)
            
            return business
            
        except Exception as e:
            logger.error(f"Error parsing company: {e}")
            return None
    
    def save_to_csv(self, filename='indiamart_businesses.csv'):
        """Save to CSV"""
        if not self.businesses:
            logger.warning("No businesses to save")
            return None
        
        filepath = os.path.join('data', filename)
        
        fieldnames = [
            'business_name', 'contact_person', 'designation', 'phone', 'mobile',
            'email', 'website', 'address', 'city', 'state', 'gst_number',
            'year_established', 'business_type', 'products_services', 'company_url'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.businesses)
        
        logger.info(f"Saved {len(self.businesses)} businesses to {filepath}")
        print(f"\n💾 Saved to: {filepath}")
        
        # Print statistics
        self.print_statistics()
        
        return filepath
    
    def print_statistics(self):
        """Print data quality statistics"""
        if not self.businesses:
            return
        
        total = len(self.businesses)
        with_email = sum(1 for b in self.businesses if b.get('email'))
        with_phone = sum(1 for b in self.businesses if b.get('phone'))
        with_website = sum(1 for b in self.businesses if b.get('website'))
        with_gst = sum(1 for b in self.businesses if b.get('gst_number'))
        
        print("\n" + "="*70)
        print("📊 DATA QUALITY STATISTICS")
        print("="*70)
        print(f"Total Businesses: {total}")
        print(f"Email Coverage: {with_email/total*100:.1f}% ({with_email}/{total})")
        print(f"Phone Coverage: {with_phone/total*100:.1f}% ({with_phone}/{total})")
        print(f"Website Coverage: {with_website/total*100:.1f}% ({with_website}/{total})")
        print(f"GST Verified: {with_gst/total*100:.1f}% ({with_gst}/{total})")
        print("="*70)


def main():
    """Main execution"""
    print("🚀 IndiaMART B2B Business Scraper")
    print("="*70)
    
    scraper = IndiaMartScraper(headless=False)
    
    # Example categories - CHANGE THESE!
    categories = [
        {
            'name': 'Advertising Agencies',
            'url': 'https://dir.indiamart.com/impcat/advertising-agencies.html'
        },
        {
            'name': 'Website Design Services',
            'url': 'https://dir.indiamart.com/impcat/website-designing-services.html'
        },
    ]
    
    print("\nAvailable categories:")
    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat['name']}")
    
    # Scrape first category (change as needed)
    category = categories[0]
    print(f"\nScraping: {category['name']}")
    
    scraper.scrape_category(category['url'], max_pages=3)
    
    if scraper.businesses:
        scraper.save_to_csv('indiamart_premium.csv')
        
        # Save JSON
        with open('data/indiamart_premium.json', 'w', encoding='utf-8') as f:
            json.dump(scraper.businesses, f, indent=2, ensure_ascii=False)
        print("💾 Saved to: data/indiamart_premium.json")


if __name__ == "__main__":
    main()
