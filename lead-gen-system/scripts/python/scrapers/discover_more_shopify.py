"""
Expanded Shopify Store Discovery
Tests more URL patterns and naming conventions
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.shopify_lead_scorer import ShopifyLeadScorer
import requests
import time
from typing import List
import pandas as pd


def generate_store_urls(max_urls: int = 100) -> List[str]:
    """Generate likely Shopify store URLs based on patterns."""
    
    # Base keywords
    products = [
        'fashion', 'clothing', 'apparel', 'style', 'wear', 'dress',
        'beauty', 'cosmetics', 'makeup', 'skincare', 'hair',
        'jewelry', 'accessories', 'watches', 'bags', 'shoes',
        'tech', 'gadget', 'electronics', 'mobile', 'audio',
        'home', 'decor', 'furniture', 'kitchen', 'living',
        'fitness', 'sports', 'yoga', 'wellness', 'health',
        'kids', 'baby', 'toys', 'children', 'mom',
        'art', 'craft', 'design', 'creative', 'gift'
    ]
    
    # Suffixes
    suffixes = [
        'store', 'shop', 'online', 'outlet', 'market', 'hub',
        'collection', 'boutique', 'emporium', 'co', 'world',
        'india', 'brand', 'studio', 'gallery', 'closet'
    ]
    
    # Prefixes
    prefixes = ['the', 'my', 'your', 'our', 'best', 'top', 'new', 'fresh']
    
    urls = []
    
    # Pattern 1: product + suffix
    for product in products:
        for suffix in suffixes[:8]:  # Limit combinations
            url = f"https://{product}{suffix}.myshopify.com"
            urls.append(url)
    
    # Pattern 2: prefix + product + suffix
    for prefix in prefixes[:3]:
        for product in products[:10]:
            for suffix in suffixes[:3]:
                url = f"https://{prefix}{product}{suffix}.myshopify.com"
                urls.append(url)
    
    # Pattern 3: product + online/store
    for product in products:
        urls.append(f"https://{product}online.myshopify.com")
        urls.append(f"https://{product}store.myshopify.com")
    
    return list(set(urls))[:max_urls]


def test_stores(urls: List[str], timeout: int = 3) -> List[str]:
    """Test which URLs are active Shopify stores."""
    
    print(f"\n🔍 Testing {len(urls)} potential store URLs...")
    print("(This may take a few minutes)")
    
    active_stores = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for i, url in enumerate(urls, 1):
        try:
            response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            # Active stores typically return 200 or redirect to custom domain
            if response.status_code in [200, 301, 302]:
                final_url = response.url if response.history else url
                active_stores.append(final_url)
                print(f"   [{i}/{len(urls)}] ✅ {url.split('//')[1].split('.')[0]}")
            
        except:
            pass
        
        # Progress update every 20 tests
        if i % 20 == 0:
            print(f"   ... tested {i}/{len(urls)}, found {len(active_stores)} stores")
        
        time.sleep(0.2)  # Be respectful
    
    print(f"\n✅ Found {len(active_stores)} active stores out of {len(urls)} tested")
    
    return active_stores


def main():
    """Discover and score many Shopify stores."""
    
    print(f"\n{'='*80}")
    print(f"EXPANDED SHOPIFY STORE DISCOVERY")
    print(f"{'='*80}")
    
    # Generate potential URLs
    candidate_urls = generate_store_urls(max_urls=150)
    
    # Test which ones are active
    active_stores = test_stores(candidate_urls, timeout=3)
    
    if not active_stores:
        print("\n⚠️  No active stores found")
        return
    
    # Analyze and score stores
    print(f"\n{'='*80}")
    print(f"ANALYZING & SCORING {len(active_stores)} STORES")
    print(f"{'='*80}")
    
    scorer = ShopifyLeadScorer(delay=1.5)
    results = []
    
    for i, url in enumerate(active_stores, 1):
        print(f"\n[{i}/{len(active_stores)}] {url}")
        
        # Extract metadata
        metadata = scorer.extract_metadata(url)
        
        if metadata.get('error'):
            print(f"   ⚠️  Skipped: {metadata['error']}")
            continue
        
        # Classify and score
        industry, confidence = scorer.classify_industry(metadata)
        metadata['industry'] = industry
        metadata['industry_confidence'] = confidence
        
        lead_data = scorer.score_leads(metadata)
        metadata.update(lead_data)
        
        # Show score
        quality_emoji = {'hot': '🔥', 'warm': '🌡️', 'cold': '❄️', 'poor': '💤'}
        emoji = quality_emoji.get(lead_data['lead_quality'], '•')
        
        print(f"   {emoji} Score: {lead_data['lead_score']} ({lead_data['lead_quality'].upper()}) - {industry}")
        
        if lead_data['lead_score'] >= 7:
            print(f"      Top weaknesses: {', '.join(lead_data['weaknesses'][:2])}")
        
        results.append(metadata)
        
        time.sleep(1.0)
    
    # Save results
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('lead_score', ascending=False)
        scorer.save_results(df, output_format='both')
        
        # Show high-quality leads
        hot_leads = df[df['lead_quality'] == 'hot']
        warm_leads = df[df['lead_quality'] == 'warm']
        
        print(f"\n{'='*80}")
        print(f"HIGH-QUALITY LEADS SUMMARY")
        print(f"{'='*80}")
        print(f"\n🔥 HOT LEADS: {len(hot_leads)}")
        print(f"🌡️  WARM LEADS: {len(warm_leads)}")
        print(f"📊 TOTAL HIGH-QUALITY: {len(hot_leads) + len(warm_leads)}")
    else:
        print("\n⚠️  No stores successfully analyzed")


if __name__ == '__main__':
    main()
