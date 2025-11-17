"""
Discover smaller Shopify stores using alternative methods
Since search engines block automation, use:
1. Shopify's public store directory patterns
2. Social media scraping (Instagram bios with .myshopify.com links)
3. Sitemap crawling of known Shopify aggregators
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.shopify_lead_scorer import ShopifyLeadScorer
import requests
from bs4 import BeautifulSoup
import re
from typing import List
import time


class ShopifyStoreFinder:
    """Find smaller/newer Shopify stores likely to need design services."""
    
    def __init__(self):
        self.scorer = ShopifyLeadScorer(delay=1.5)
    
    def find_stores_from_builtwith(self, max_stores: int = 20) -> List[str]:
        """
        Scrape Shopify stores from BuiltWith trends page.
        """
        print("\n🔍 Finding Shopify stores from BuiltWith...")
        
        stores = []
        url = "https://trends.builtwith.com/shop/Shopify"
        
        try:
            response = requests.get(url, headers=self.scorer.HEADERS, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find store links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Look for actual store URLs (not internal BuiltWith links)
                if re.match(r'https?://(?!.*builtwith)', href) and '.' in href:
                    domain = href.split('/')[2]
                    if domain not in [s.split('/')[2] for s in stores]:
                        stores.append(href)
                
                if len(stores) >= max_stores:
                    break
            
            print(f"   ✅ Found {len(stores)} stores from BuiltWith")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
        
        return stores
    
    def find_myshopify_stores(self, keywords: List[str] = None, max_stores: int = 20) -> List[str]:
        """
        Generate likely myshopify.com URLs based on common naming patterns.
        """
        if not keywords:
            keywords = [
                'fashion', 'style', 'clothing', 'apparel', 'boutique', 'shop',
                'beauty', 'cosmetics', 'jewelry', 'accessories', 'brand',
                'tech', 'gadget', 'store', 'online', 'collection'
            ]
        
        print(f"\n🔍 Testing myshopify.com URL patterns...")
        
        stores = []
        tested = 0
        
        # Common patterns
        patterns = [
            '{keyword}store',
            '{keyword}shop',
            '{keyword}online',
            '{keyword}india',
            '{keyword}brand',
            'the{keyword}store',
            '{keyword}collection',
            '{keyword}boutique',
        ]
        
        for keyword in keywords[:5]:  # Limit keywords to avoid too many requests
            for pattern in patterns:
                if len(stores) >= max_stores:
                    break
                
                store_name = pattern.format(keyword=keyword)
                url = f"https://{store_name}.myshopify.com"
                
                tested += 1
                
                try:
                    response = requests.head(url, timeout=5, allow_redirects=True)
                    
                    # If store exists, it usually redirects or returns 200
                    if response.status_code in [200, 301, 302]:
                        final_url = response.url if response.history else url
                        if final_url not in stores:
                            stores.append(final_url)
                            print(f"   ✅ Found: {final_url}")
                    
                except:
                    pass
                
                time.sleep(0.3)  # Be respectful
            
            if len(stores) >= max_stores:
                break
        
        print(f"\n   Tested {tested} URLs, found {len(stores)} active stores")
        
        return stores
    
    def analyze_and_score(self, store_urls: List[str]) -> None:
        """Analyze and score discovered stores."""
        if not store_urls:
            print("\n⚠️  No stores to analyze")
            return
        
        print(f"\n{'='*80}")
        print(f"ANALYZING {len(store_urls)} DISCOVERED STORES")
        print(f"{'='*80}")
        
        results = []
        
        for i, url in enumerate(store_urls, 1):
            print(f"\n[{i}/{len(store_urls)}] {url}")
            
            # Extract metadata
            metadata = self.scorer.extract_metadata(url)
            
            if metadata.get('error'):
                print(f"   ⚠️  Skipped: {metadata['error']}")
                continue
            
            # Classify and score
            industry, confidence = self.scorer.classify_industry(metadata)
            metadata['industry'] = industry
            metadata['industry_confidence'] = confidence
            
            lead_data = self.scorer.score_leads(metadata)
            metadata.update(lead_data)
            
            print(f"   Score: {lead_data['lead_score']} ({lead_data['lead_quality'].upper()})")
            
            if lead_data['lead_score'] >= 5:
                print(f"   🔥 HOT/WARM LEAD!")
                for weakness in lead_data['weaknesses']:
                    print(f"      - {weakness}")
            
            results.append(metadata)
            
            time.sleep(self.scorer.delay)
        
        # Save results
        if results:
            import pandas as pd
            df = pd.DataFrame(results)
            df = df.sort_values('lead_score', ascending=False)
            self.scorer.save_results(df, output_format='both')


def main():
    """Find and score small Shopify stores."""
    finder = ShopifyStoreFinder()
    
    print(f"\n{'='*80}")
    print(f"SHOPIFY STORE DISCOVERY & LEAD SCORING")
    print(f"{'='*80}")
    
    all_stores = []
    
    # Method 1: Test myshopify.com patterns (higher chance of finding smaller stores)
    myshopify_stores = finder.find_myshopify_stores(
        keywords=['fashion', 'beauty', 'jewelry', 'tech', 'gadget'],
        max_stores=15
    )
    all_stores.extend(myshopify_stores)
    
    # Method 2: Try BuiltWith (may be blocked)
    # builtwith_stores = finder.find_stores_from_builtwith(max_stores=10)
    # all_stores.extend(builtwith_stores)
    
    # Remove duplicates
    all_stores = list(set(all_stores))
    
    print(f"\n✅ Total unique stores found: {len(all_stores)}")
    
    if all_stores:
        # Analyze and score
        finder.analyze_and_score(all_stores)
    else:
        print("\n⚠️  No stores discovered.")
        print("Consider using manual seed URLs or Instagram/social media scraping.")


if __name__ == '__main__':
    main()
