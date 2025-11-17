"""
Alternative scraper using BeautifulSoup and requests with better selectors
"""
import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import time
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SimpleJustDialScraper:
    def __init__(self):
        self.collected = []
        self.unique_phones = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def extract_phone(self, text):
        """Extract 10-digit phone number"""
        if not text:
            return ''
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', text)
        # Find 10-digit sequences
        matches = re.findall(r'\d{10}', digits)
        return matches[0] if matches else ''
    
    def scrape_page(self, url, page_num=1):
        """Scrape a single page"""
        try:
            if page_num > 1:
                url = f"{url}/page-{page_num}"
            
            logger.info(f"Scraping page {page_num}: {url}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Save HTML for debugging
            with open(f'data/page_{page_num}_debug.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            # Try multiple approaches to find listings
            listings = []
            
            # Approach 1: Find by class
            listings = soup.find_all('li', class_='cntanr')
            if not listings:
                listings = soup.find_all('div', class_='resultbox')
            if not listings:
                listings = soup.find_all('article')
            
            logger.info(f"Found {len(listings)} potential listings on page {page_num}")
            
            page_businesses = []
            
            for idx, listing in enumerate(listings):
                try:
                    business = {
                        'business_name': '',
                        'phone': '',
                        'address': '',
                        'website': '',
                        'instagram': '',
                        'facebook': '',
                        'rating': '',
                        'notes': f'Page {page_num}'
                    }
                    
                    # Extract all text for analysis
                    listing_text = listing.get_text(separator=' ', strip=True)
                    
                    # Find business name
                    name_tag = (listing.find('span', class_='jcn') or 
                               listing.find('a', class_='resultbox_title_anchor') or
                               listing.find('h2'))
                    if name_tag:
                        business['business_name'] = name_tag.get_text(strip=True)
                    
                    # Find phone
                    phone_tag = listing.find('p', class_='contact-info')
                    if not phone_tag:
                        phone_tag = listing.find('span', class_='mobilesv')
                    if phone_tag:
                        business['phone'] = self.extract_phone(phone_tag.get_text())
                    
                    # If no phone found, try searching in all text
                    if not business['phone']:
                        business['phone'] = self.extract_phone(listing_text)
                    
                    # Find address
                    addr_tag = listing.find('span', class_='mrehover')
                    if not addr_tag:
                        addr_tag = listing.find('p', class_='address')
                    if addr_tag:
                        business['address'] = addr_tag.get_text(strip=True)
                    
                    # Find all links
                    links = listing.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        if 'instagram.com' in href:
                            business['instagram'] = href
                        elif 'facebook.com' in href:
                            business['facebook'] = href
                        elif href.startswith('http') and 'justdial' not in href:
                            if not business['website']:
                                business['website'] = href
                    
                    # Find rating
                    rating_tag = listing.find('span', class_='green-box')
                    if rating_tag:
                        rating_text = rating_tag.get_text(strip=True)
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            business['rating'] = match.group(1)
                    
                    # Validate: need at least name
                    if business['business_name']:
                        # Use name as backup for uniqueness if no phone
                        unique_key = business['phone'] if business['phone'] else business['business_name']
                        
                        if unique_key not in self.unique_phones:
                            self.unique_phones.add(unique_key)
                            page_businesses.append(business)
                            logger.info(f"  [{len(self.collected) + len(page_businesses)}] {business['business_name']}")
                
                except Exception as e:
                    logger.error(f"Error extracting listing {idx}: {e}")
                    continue
            
            return page_businesses
            
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {e}")
            return []
    
    def scrape(self, base_url, target_count=100):
        """Scrape multiple pages until target reached"""
        logger.info(f"Starting scrape for {target_count} businesses")
        
        page = 1
        max_pages = 20
        
        while len(self.collected) < target_count and page <= max_pages:
            businesses = self.scrape_page(base_url, page)
            
            if not businesses:
                logger.warning(f"No businesses found on page {page}, stopping")
                break
            
            self.collected.extend(businesses)
            logger.info(f"Progress: {len(self.collected)}/{target_count}")
            
            if len(self.collected) >= target_count:
                self.collected = self.collected[:target_count]
                break
            
            page += 1
            time.sleep(2)  # Be respectful
        
        return self.collected
    
    def save_csv(self, filename='CoffeeShops_Mumbai_100.csv'):
        """Save to CSV"""
        if not self.collected:
            logger.warning("No data to save")
            return
        
        filepath = os.path.join('data', filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['business_name', 'phone', 'address', 'website', 'instagram', 'facebook', 'rating', 'notes'])
            writer.writeheader()
            writer.writerows(self.collected)
        
        logger.info(f"Saved {len(self.collected)} businesses to {filepath}")
        return filepath

def main():
    print("🔍 Starting Simple JustDial Scraper...")
    print("=" * 60)
    
    scraper = SimpleJustDialScraper()
    url = "https://www.justdial.com/Mumbai/Coffee-Shops/nct-10104727"
    
    businesses = scraper.scrape(url, target_count=100)
    
    if businesses:
        filepath = scraper.save_csv()
        
        # Also save JSON
        json_file = os.path.join('data', f'CoffeeShops_Mumbai_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(businesses, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ SUCCESS! Collected {len(businesses)} coffee shops")
        print(f"📁 CSV: {filepath}")
        print(f"📁 JSON: {json_file}")
        print("\n📊 Next: python quick_data_helper.py analyze data/CoffeeShops_Mumbai_100.csv")
    else:
        print("\n❌ No data collected. Check data/page_1_debug.html to see what was returned")

if __name__ == "__main__":
    main()
