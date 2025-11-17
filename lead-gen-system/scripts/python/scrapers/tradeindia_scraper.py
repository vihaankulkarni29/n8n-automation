"""
TradeIndia Scraper
Scrapes business listings from TradeIndia.com
Focus on manufacturers, exporters, and B2B companies
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import time
from pathlib import Path
import re


class TradeIndiaScraper:
    """
    Scrape business listings from TradeIndia.
    """
    
    BASE_URL = "https://www.tradeindia.com"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    # Categories relevant for RFRNCS clients
    CATEGORIES = {
        'fashion': 'apparel-garments',
        'beauty': 'cosmetics-toiletries',
        'food': 'food-beverages',
        'packaging': 'packaging-supplies',
        'textiles': 'textiles-yarn',
        'furniture': 'furniture-furnishings',
        'electronics': 'consumer-electronics',
        'jewelry': 'fashion-jewelry',
    }
    
    def __init__(self, delay: float = 2.0):
        """Initialize scraper."""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def search_companies(self, query: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """
        Search for companies by keyword.
        
        Args:
            query: Search keyword (e.g., 'clothing manufacturer', 'packaging company')
            location: City/state filter
            max_results: Maximum results to fetch
            
        Returns:
            List of company dicts
        """
        print(f"\n{'='*80}")
        print(f"TRADEINDIA SEARCH")
        print(f"{'='*80}")
        print(f"\nQuery: {query}")
        if location:
            print(f"Location: {location}")
        print(f"Max results: {max_results}")
        
        companies = []
        page = 1
        
        while len(companies) < max_results:
            search_url = f"{self.BASE_URL}/search.html"
            
            params = {
                'q': query,
                'page': page
            }
            if location:
                params['city'] = location
            
            print(f"\n🔍 Page {page}: {search_url}")
            
            try:
                response = self.session.get(search_url, params=params, timeout=15)
                
                if response.status_code != 200:
                    print(f"   ❌ Failed: Status {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find company listings
                company_cards = (
                    soup.find_all('div', class_=re.compile(r'company|seller|supplier', re.I)) or
                    soup.find_all('div', {'data-type': 'company'}) or
                    soup.find_all('div', class_='search-card')
                )
                
                print(f"   Found {len(company_cards)} listings")
                
                if not company_cards:
                    print("   No more results")
                    break
                
                for card in company_cards:
                    if len(companies) >= max_results:
                        break
                    
                    try:
                        company_data = self._extract_company_data(card)
                        if company_data and company_data.get('name'):
                            companies.append(company_data)
                    except Exception:
                        continue
                
                print(f"   ✅ Extracted {len(companies)} total companies so far")
                
                page += 1
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                break
        
        print(f"\n✅ Total companies found: {len(companies)}")
        return companies
    
    def _extract_company_data(self, element) -> Dict:
        """Extract company data from HTML element."""
        try:
            data = {
                'name': None,
                'description': None,
                'location': None,
                'phone': None,
                'email': None,
                'website': None,
                'tradeindia_url': None,
                'company_type': None,
                'products': [],
            }
            
            # Extract name
            name_elem = (
                element.find('h2') or
                element.find('h3') or
                element.find(class_=re.compile(r'company.*name|title', re.I)) or
                element.find('a', class_=re.compile(r'company', re.I))
            )
            if name_elem:
                data['name'] = name_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = element.find(class_=re.compile(r'desc|about|detail', re.I))
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)[:300]
            
            # Extract location
            location_elem = (
                element.find(class_=re.compile(r'location|city|address', re.I)) or
                element.find('span', {'itemprop': 'addressLocality'})
            )
            if location_elem:
                data['location'] = location_elem.get_text(strip=True)
            
            # Extract phone
            phone_elem = (
                element.find(class_=re.compile(r'phone|mobile|contact', re.I)) or
                element.find('a', href=re.compile(r'tel:'))
            )
            if phone_elem:
                phone_text = phone_elem.get_text(strip=True)
                phone_match = re.search(r'[\d\s\-\+\(\)]{10,}', phone_text)
                if phone_match:
                    data['phone'] = phone_match.group(0).strip()
            
            # Extract company URL
            link = element.find('a', href=re.compile(r'/company/'))
            if link:
                href = link.get('href', '')
                if href.startswith('/'):
                    data['tradeindia_url'] = self.BASE_URL + href
                else:
                    data['tradeindia_url'] = href
            
            # Extract company type
            type_elem = element.find(class_=re.compile(r'type|category', re.I))
            if type_elem:
                data['company_type'] = type_elem.get_text(strip=True)
            
            return data
            
        except Exception:
            return {}
    
    def scrape_category(self, category: str, max_results: int = 50) -> pd.DataFrame:
        """
        Scrape companies from a specific category.
        
        Args:
            category: Category key from CATEGORIES dict
            max_results: Maximum results
            
        Returns:
            DataFrame with companies
        """
        if category not in self.CATEGORIES:
            print(f"❌ Unknown category: {category}")
            print(f"Available: {list(self.CATEGORIES.keys())}")
            return pd.DataFrame()
        
        category_slug = self.CATEGORIES[category]
        companies = []
        page = 1
        
        print(f"\n{'='*80}")
        print(f"TRADEINDIA CATEGORY SCRAPER")
        print(f"{'='*80}")
        print(f"\nCategory: {category} ({category_slug})")
        print(f"Max results: {max_results}")
        
        while len(companies) < max_results:
            url = f"{self.BASE_URL}/category/{category_slug}/?page={page}"
            
            print(f"\n🔍 Page {page}: {url}")
            
            try:
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    print(f"   ❌ Failed: Status {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                company_cards = soup.find_all('div', class_=re.compile(r'company|listing', re.I))
                
                print(f"   Found {len(company_cards)} listings")
                
                if not company_cards:
                    break
                
                for card in company_cards:
                    if len(companies) >= max_results:
                        break
                    
                    try:
                        company_data = self._extract_company_data(card)
                        if company_data and company_data.get('name'):
                            company_data['category'] = category
                            companies.append(company_data)
                    except Exception:
                        continue
                
                print(f"   ✅ Extracted {len(companies)} total companies")
                
                page += 1
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                break
        
        if not companies:
            return pd.DataFrame()
        
        df = pd.DataFrame(companies)
        df = df.drop_duplicates(subset=['name'], keep='first')
        df['source'] = 'tradeindia'
        df['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return df
    
    def save_results(self, df: pd.DataFrame, category: str = 'general') -> str:
        """Save results to CSV."""
        if df.empty:
            print("\n⚠️  No data to save")
            return ""
        
        output_dir = Path('data')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'tradeindia_{category}_{timestamp}.csv'
        
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Saved to: {output_file}")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total companies: {len(df)}")
        print(f"With phone: {df['phone'].notna().sum() if 'phone' in df.columns else 0}")
        print(f"With location: {df['location'].notna().sum() if 'location' in df.columns else 0}")
        
        if 'location' in df.columns:
            print(f"\n📍 TOP LOCATIONS:")
            top_locations = df['location'].value_counts().head(5)
            for loc, count in top_locations.items():
                print(f"   {loc}: {count} companies")
        
        return str(output_file)


def main():
    """Main function to scrape TradeIndia."""
    scraper = TradeIndiaScraper(delay=2.0)
    
    # Try searching for specific queries first
    queries = [
        'clothing manufacturer',
        'packaging company',
        'textile exporter'
    ]
    
    all_companies = []
    
    for query in queries:
        companies = scraper.search_companies(query, location='', max_results=20)
        all_companies.extend(companies)
        time.sleep(2)
    
    if all_companies:
        df = pd.DataFrame(all_companies)
        df = df.drop_duplicates(subset=['name'], keep='first')
        df['source'] = 'tradeindia'
        df['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        scraper.save_results(df, 'manufacturers')
    else:
        print("\n⚠️  TradeIndia scraping failed.")
        print("They may have changed their structure or require login.")


if __name__ == '__main__':
    main()
