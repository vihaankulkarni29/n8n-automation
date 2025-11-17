"""
Shopify Store Directory Scraper
Scrapes D2C brands and e-commerce stores from various Shopify directories
Focus on Indian and global online stores
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from typing import List, Dict
import time
from pathlib import Path
import re


class ShopifyStoreScraper:
    """
    Scrape Shopify stores from public directories and lists.
    """
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    # Public Shopify directories
    DIRECTORIES = {
        'myip': 'https://myip.ms/browse/sites/1/own/376714',  # Shopify IP range
        'builtwith': 'https://trends.builtwith.com/shop/Shopify',
    }
    
    def __init__(self, delay: float = 2.0):
        """Initialize scraper."""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def detect_shopify_store(self, url: str) -> Dict:
        """
        Check if a URL is a Shopify store and extract basic info.
        
        Args:
            url: Store URL to check
            
        Returns:
            Dict with store info or empty dict
        """
        try:
            # Ensure proper URL format
            if not url.startswith('http'):
                url = 'https://' + url
            
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code != 200:
                return {}
            
            # Check for Shopify indicators
            content = response.text.lower()
            is_shopify = (
                'shopify' in content or
                'cdn.shopify.com' in content or
                'myshopify.com' in content or
                'shopify-analytics' in content
            )
            
            if not is_shopify:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = {
                'url': url,
                'name': None,
                'description': None,
                'email': None,
                'phone': None,
                'is_shopify': True,
            }
            
            # Extract store name
            title = soup.find('title')
            if title:
                data['name'] = title.get_text(strip=True)
            
            # Extract description
            desc_meta = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
            if desc_meta:
                data['description'] = desc_meta.get('content', '')[:300]
            
            # Look for contact info
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
            if email_match:
                data['email'] = email_match.group(0)
            
            phone_match = re.search(r'[\+\(]?[0-9][0-9\s\-\(\)]{8,}[0-9]', response.text)
            if phone_match:
                data['phone'] = phone_match.group(0).strip()
            
            return data
            
        except Exception:
            return {}
    
    def scrape_from_list(self, urls: List[str], max_stores: int = 50) -> List[Dict]:
        """
        Check a list of URLs for Shopify stores.
        
        Args:
            urls: List of URLs to check
            max_stores: Maximum stores to find
            
        Returns:
            List of store dicts
        """
        print(f"\n{'='*80}")
        print(f"SHOPIFY STORE DETECTOR")
        print(f"{'='*80}")
        print(f"\nChecking {len(urls)} URLs...")
        
        stores = []
        
        for i, url in enumerate(urls, 1):
            if len(stores) >= max_stores:
                break
            
            print(f"\n🔍 [{i}/{len(urls)}] Checking: {url}")
            
            store_data = self.detect_shopify_store(url)
            
            if store_data:
                stores.append(store_data)
                print(f"   ✅ Shopify store found: {store_data.get('name', 'Unknown')}")
            else:
                print(f"   ❌ Not a Shopify store")
            
            time.sleep(self.delay)
        
        print(f"\n✅ Found {len(stores)} Shopify stores")
        return stores
    
    def search_indian_shopify_stores(self) -> List[str]:
        """
        Generate list of potential Indian Shopify store URLs.
        This uses common patterns and known stores.
        
        Returns:
            List of URLs to check
        """
        # Known Indian D2C brands (many use Shopify)
        known_stores = [
            'bewakoof.com',
            'thesouledstore.com',
            'purplle.com',
            'nykaa.com',
            'lenskart.com',
            'myntra.com',
            'ajio.com',
            'blinkit.com',
            'mamaearth.in',
            'plum.in',
            'myglamm.com',
            'sugarcosmetics.com',
            'boat-lifestyle.com',
            'noise.com',
            'giva.co',
            'melorra.com',
            'bluestone.com',
            'caratlane.com',
            'foreo.com',
            'minimalist.co',
            'mcaffeine.com',
            'thedermaco.com',
            'littlebox.in',
            'themancompany.com',
            'bombayshavingcompany.com',
            'beardhood.com',
            'ustraa.com',
            'snitch.co.in',
            'beyoung.in',
            'cultfit.com',
            'healthifyme.com',
            'eatfit.in',
            'mfine.co',
            'pristyncare.com',
        ]
        
        return known_stores
    
    def scrape_indian_stores(self, max_stores: int = 30) -> pd.DataFrame:
        """
        Scrape known Indian D2C Shopify stores.
        
        Args:
            max_stores: Maximum stores to check
            
        Returns:
            DataFrame with stores
        """
        print(f"\n{'='*80}")
        print(f"INDIAN SHOPIFY STORES SCRAPER")
        print(f"{'='*80}")
        print(f"\nSearching for Indian D2C brands on Shopify...")
        
        potential_urls = self.search_indian_shopify_stores()
        stores = self.scrape_from_list(potential_urls[:max_stores], max_stores)
        
        if not stores:
            print("\n⚠️  No Shopify stores found")
            return pd.DataFrame()
        
        df = pd.DataFrame(stores)
        df['source'] = 'shopify_directory'
        df['country'] = 'India'
        df['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return df
    
    def save_results(self, df: pd.DataFrame) -> str:
        """Save results to CSV."""
        if df.empty:
            print("\n⚠️  No data to save")
            return ""
        
        output_dir = Path('data')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'shopify_stores_{timestamp}.csv'
        
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Saved to: {output_file}")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total Shopify stores: {len(df)}")
        print(f"With email: {df['email'].notna().sum() if 'email' in df.columns else 0}")
        print(f"With phone: {df['phone'].notna().sum() if 'phone' in df.columns else 0}")
        
        if 'name' in df.columns:
            print(f"\n🛍️  STORES FOUND:")
            for idx, row in df.head(15).iterrows():
                print(f"   {row['name']}")
                print(f"      URL: {row['url']}")
                if row.get('email'):
                    print(f"      Email: {row['email']}")
        
        return str(output_file)


def main():
    """Main function to scrape Shopify stores."""
    scraper = ShopifyStoreScraper(delay=1.5)
    
    # Scrape known Indian D2C brands
    df = scraper.scrape_indian_stores(max_stores=30)
    
    if not df.empty:
        scraper.save_results(df)
    else:
        print("\n⚠️  Shopify scraping completed with no results.")


if __name__ == '__main__':
    main()
