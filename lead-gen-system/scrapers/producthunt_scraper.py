"""
Product Hunt Scraper
Scrapes new product launches, startups, and makers from Product Hunt
Focus on Indian/global SaaS products
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import time
from pathlib import Path
import re


class ProductHuntScraper:
    """
    Scrape product launches from Product Hunt.
    """
    
    BASE_URL = "https://www.producthunt.com"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.producthunt.com/',
    }
    
    def __init__(self, delay: float = 2.0):
        """Initialize scraper."""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def scrape_daily_products(self, date: str = None, max_products: int = 20) -> List[Dict]:
        """
        Scrape products from a specific day.
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
            max_products: Maximum products to scrape
            
        Returns:
            List of product dicts
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.BASE_URL}/posts/{date}"
        
        print(f"\n🔍 Scraping Product Hunt for {date}")
        print(f"   URL: {url}")
        
        products = []
        
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"   ❌ Failed: Status {response.status_code}")
                return products
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Product Hunt uses dynamic class names, look for common patterns
            product_cards = (
                soup.find_all('div', class_=re.compile(r'post', re.I))[:max_products] or
                soup.find_all('article')[:max_products] or
                soup.find_all('a', href=re.compile(r'/posts/'))[:max_products]
            )
            
            print(f"   Found {len(product_cards)} product cards")
            
            for card in product_cards:
                try:
                    product_data = self._extract_product_data(card)
                    if product_data and product_data.get('name'):
                        products.append(product_data)
                except Exception as e:
                    continue
            
            print(f"   ✅ Extracted {len(products)} products")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
        
        return products
    
    def _extract_product_data(self, element) -> Dict:
        """Extract product data from HTML element."""
        try:
            data = {
                'name': None,
                'tagline': None,
                'description': None,
                'website': None,
                'product_hunt_url': None,
                'upvotes': 0,
                'topics': [],
                'maker': None,
            }
            
            # Extract name
            name_elem = (
                element.find('h3') or
                element.find('h2') or
                element.find(class_=re.compile(r'name|title', re.I))
            )
            if name_elem:
                data['name'] = name_elem.get_text(strip=True)
            
            # Extract tagline
            tagline_elem = element.find(class_=re.compile(r'tagline|subtitle', re.I))
            if tagline_elem:
                data['tagline'] = tagline_elem.get_text(strip=True)[:200]
            
            # Extract URL
            link = element.find('a', href=re.compile(r'/posts/'))
            if link:
                href = link.get('href', '')
                if href.startswith('/'):
                    data['product_hunt_url'] = self.BASE_URL + href
                else:
                    data['product_hunt_url'] = href
            
            # Extract upvotes
            upvote_elem = element.find(class_=re.compile(r'vote|upvote', re.I))
            if upvote_elem:
                upvote_text = upvote_elem.get_text(strip=True)
                upvote_match = re.search(r'(\d+)', upvote_text)
                if upvote_match:
                    data['upvotes'] = int(upvote_match.group(1))
            
            return data
            
        except Exception:
            return {}
    
    def get_product_details(self, product_url: str) -> Dict:
        """
        Get detailed information for a specific product.
        
        Args:
            product_url: Product Hunt product URL
            
        Returns:
            Dict with detailed product info
        """
        try:
            response = self.session.get(product_url, timeout=15)
            
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {}
            
            # Try to find website link
            website_link = soup.find('a', href=re.compile(r'^https?://(?!.*producthunt)'))
            if website_link:
                details['website'] = website_link.get('href')
            
            # Try to find maker info
            maker_elem = soup.find(class_=re.compile(r'maker|creator|hunter', re.I))
            if maker_elem:
                details['maker'] = maker_elem.get_text(strip=True)
            
            # Description
            desc_elem = soup.find('meta', {'name': 'description'})
            if desc_elem:
                details['description'] = desc_elem.get('content', '')[:500]
            
            return details
            
        except Exception:
            return {}
    
    def scrape_multiple_days(self, days: int = 7, max_products_per_day: int = 20) -> pd.DataFrame:
        """
        Scrape products from multiple days.
        
        Args:
            days: Number of days to scrape backwards from today
            max_products_per_day: Products per day
            
        Returns:
            DataFrame with all products
        """
        print(f"\n{'='*80}")
        print(f"PRODUCT HUNT SCRAPER")
        print(f"{'='*80}")
        print(f"\nScraping {days} days of product launches...")
        
        all_products = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            products = self.scrape_daily_products(date, max_products_per_day)
            all_products.extend(products)
            
            time.sleep(self.delay)
        
        if not all_products:
            print("\n⚠️  No products found")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_products)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['name'], keep='first')
        
        # Add metadata
        df['source'] = 'producthunt'
        df['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n✅ Total unique products: {len(df)}")
        
        return df
    
    def save_results(self, df: pd.DataFrame, output_dir: str = 'data') -> str:
        """Save results to CSV."""
        if df.empty:
            print("⚠️  No data to save")
            return ""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_path / f'producthunt_products_{timestamp}.csv'
        
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Saved to: {output_file}")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total products: {len(df)}")
        print(f"With websites: {df['website'].notna().sum() if 'website' in df.columns else 0}")
        print(f"Avg upvotes: {int(df['upvotes'].mean()) if 'upvotes' in df.columns and not df['upvotes'].empty else 0}")
        
        if 'name' in df.columns:
            print(f"\n🏆 TOP 10 PRODUCTS BY UPVOTES:")
            top_products = df.nlargest(10, 'upvotes') if 'upvotes' in df.columns else df.head(10)
            for idx, row in top_products.iterrows():
                upvotes = f" ({row.get('upvotes', 0)} upvotes)" if 'upvotes' in df.columns else ""
                print(f"   {row['name']}{upvotes}")
        
        return str(output_file)


def main():
    """Main function to scrape Product Hunt."""
    scraper = ProductHuntScraper(delay=2.0)
    
    # Scrape last 7 days of launches
    df = scraper.scrape_multiple_days(
        days=7,
        max_products_per_day=20
    )
    
    if not df.empty:
        scraper.save_results(df)
    else:
        print("\n⚠️  Product Hunt scraping failed.")
        print("They may have anti-scraping protection or changed their structure.")
        print("Consider using their official API: https://api.producthunt.com/v2/docs")


if __name__ == '__main__':
    main()
