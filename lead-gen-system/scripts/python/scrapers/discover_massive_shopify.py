"""
Aggressive Shopify Store Discovery
Tests 500+ URL patterns with expanded keywords
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.shopify_lead_scorer import ShopifyLeadScorer
import requests
import time
from typing import List
import pandas as pd
from itertools import product


def generate_massive_url_list(max_urls: int = 500) -> List[str]:
    """Generate comprehensive list of Shopify store URLs."""
    
    # Expanded product categories
    products = [
        # Fashion & Apparel
        'fashion', 'clothing', 'apparel', 'style', 'wear', 'dress', 'shirt', 'tshirt',
        'jeans', 'pants', 'shorts', 'jacket', 'coat', 'sweater', 'hoodie', 'socks',
        'shoes', 'sneakers', 'boots', 'sandals', 'heels', 'flats',
        
        # Accessories
        'jewelry', 'accessories', 'watches', 'bags', 'handbags', 'wallet', 'belt',
        'scarf', 'hat', 'cap', 'sunglasses', 'eyewear',
        
        # Beauty & Personal Care
        'beauty', 'cosmetics', 'makeup', 'skincare', 'haircare', 'perfume', 'fragrance',
        'nails', 'spa', 'bath', 'soap', 'shampoo', 'lotion',
        
        # Electronics & Tech
        'tech', 'gadget', 'electronics', 'mobile', 'phone', 'tablet', 'laptop',
        'computer', 'gaming', 'audio', 'headphones', 'speakers', 'camera',
        'smartwatch', 'fitness', 'tracker',
        
        # Home & Living
        'home', 'decor', 'furniture', 'interior', 'kitchen', 'dining', 'bedroom',
        'living', 'lighting', 'candle', 'art', 'print', 'poster',
        
        # Lifestyle
        'gift', 'craft', 'handmade', 'vintage', 'organic', 'eco', 'green',
        'baby', 'kids', 'toys', 'pet', 'dog', 'cat',
        'sports', 'fitness', 'yoga', 'gym', 'outdoor', 'camping',
        'book', 'stationery', 'office', 'supplies',
        
        # Food & Beverage
        'food', 'snacks', 'coffee', 'tea', 'juice', 'beverage', 'wine',
        
        # Niche
        'wedding', 'party', 'event', 'travel', 'luxury', 'designer', 'custom'
    ]
    
    # Store types
    suffixes = [
        'store', 'shop', 'outlet', 'market', 'hub', 'emporium',
        'boutique', 'collection', 'closet', 'warehouse', 'plaza',
        'online', 'direct', 'world', 'express', 'central',
        'gallery', 'studio', 'house', 'room', 'corner',
        'co', 'goods', 'finds', 'depot', 'mart'
    ]
    
    # Prefixes
    prefixes = [
        '', 'the', 'my', 'your', 'our', 'best', 'top', 'new', 'fresh',
        'modern', 'urban', 'classic', 'vintage', 'premium', 'luxury',
        'smart', 'eco', 'green', 'pure', 'natural', 'organic'
    ]
    
    urls = set()
    
    # Pattern 1: product + suffix
    for prod, suf in product(products[:60], suffixes[:15]):
        urls.add(f"https://{prod}{suf}.myshopify.com")
    
    # Pattern 2: prefix + product
    for pre, prod in product(prefixes[:10], products[:40]):
        if pre:
            urls.add(f"https://{pre}{prod}.myshopify.com")
            urls.add(f"https://{pre}{prod}store.myshopify.com")
            urls.add(f"https://{pre}{prod}shop.myshopify.com")
    
    # Pattern 3: product + numbers (common pattern)
    for prod in products[:20]:
        for num in ['24', '365', '247', '360', 'hq', 'hub', 'co']:
            urls.add(f"https://{prod}{num}.myshopify.com")
    
    # Pattern 4: two-word combinations
    combos = [
        ('style', 'hub'), ('fashion', 'house'), ('beauty', 'box'), ('gift', 'shop'),
        ('tech', 'zone'), ('home', 'decor'), ('kids', 'corner'), ('pet', 'store'),
        ('shoe', 'store'), ('bag', 'shop'), ('watch', 'collection'), ('jewelry', 'box')
    ]
    for word1, word2 in combos:
        urls.add(f"https://{word1}{word2}.myshopify.com")
    
    return list(urls)[:max_urls]


def test_stores_batch(urls: List[str], batch_size: int = 50, timeout: int = 3) -> List[str]:
    """Test stores in batches with progress updates."""
    
    print(f"\n🔍 Testing {len(urls)} potential store URLs in batches of {batch_size}...")
    
    active_stores = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for i, url in enumerate(urls, 1):
        try:
            response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            if response.status_code in [200, 301, 302]:
                final_url = response.url if response.history else url
                
                # Avoid duplicates
                if final_url not in active_stores:
                    active_stores.append(final_url)
                    store_name = final_url.split('//')[1].split('.')[0]
                    print(f"   [{len(active_stores)}] ✅ {store_name}")
            
        except:
            pass
        
        # Progress updates
        if i % batch_size == 0:
            print(f"   ... tested {i}/{len(urls)}, found {len(active_stores)} active stores")
        
        # Rate limiting
        time.sleep(0.15)
    
    print(f"\n✅ Discovery complete: {len(active_stores)} active stores from {len(urls)} tested")
    
    return active_stores


def main():
    """Run massive Shopify discovery."""
    
    print(f"\n{'='*80}")
    print(f"AGGRESSIVE SHOPIFY STORE DISCOVERY")
    print(f"{'='*80}")
    print("\nGenerating 500+ potential store URLs...")
    
    # Generate URLs
    candidate_urls = generate_massive_url_list(max_urls=500)
    print(f"Generated {len(candidate_urls)} unique URL patterns")
    
    # Test in batches
    active_stores = test_stores_batch(candidate_urls, batch_size=50, timeout=3)
    
    if not active_stores:
        print("\n⚠️  No new stores found")
        return
    
    # Limit to 30 stores for analysis to save time
    stores_to_analyze = active_stores[:30]
    
    if len(active_stores) > 30:
        print(f"\n📊 Analyzing top 30 stores (found {len(active_stores)} total)")
        print(f"   Remaining {len(active_stores) - 30} stores saved for future analysis")
    
    # Analyze and score
    print(f"\n{'='*80}")
    print(f"ANALYZING & SCORING {len(stores_to_analyze)} STORES")
    print(f"{'='*80}")
    
    scorer = ShopifyLeadScorer(delay=1.0)
    results = []
    
    for i, url in enumerate(stores_to_analyze, 1):
        print(f"\n[{i}/{len(stores_to_analyze)}] {url}")
        
        metadata = scorer.extract_metadata(url)
        
        if metadata.get('error'):
            print(f"   ⚠️  Skipped: {metadata['error']}")
            continue
        
        industry, confidence = scorer.classify_industry(metadata)
        metadata['industry'] = industry
        metadata['industry_confidence'] = confidence
        
        lead_data = scorer.score_leads(metadata)
        metadata.update(lead_data)
        
        quality_emoji = {'hot': '🔥', 'warm': '🌡️', 'cold': '❄️', 'poor': '💤'}
        emoji = quality_emoji.get(lead_data['lead_quality'], '•')
        
        print(f"   {emoji} Score: {lead_data['lead_score']} ({lead_data['lead_quality'].upper()}) - {industry}")
        
        results.append(metadata)
        
        time.sleep(0.8)
    
    # Save results
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('lead_score', ascending=False)
        scorer.save_results(df, output_format='both')
        
        # Summary
        hot = df[df['lead_quality'] == 'hot']
        warm = df[df['lead_quality'] == 'warm']
        
        print(f"\n{'='*80}")
        print(f"FINAL RESULTS")
        print(f"{'='*80}")
        print(f"\n🔥 HOT LEADS: {len(hot)}")
        print(f"🌡️  WARM LEADS: {len(warm)}")
        print(f"📊 TOTAL HIGH-QUALITY: {len(hot) + len(warm)}")
        print(f"💎 TOTAL ANALYZED: {len(results)}")
        
        if len(active_stores) > 30:
            print(f"\n💡 TIP: {len(active_stores) - 30} more stores available for analysis")
            print(f"   Re-run script or manually analyze remaining stores")


if __name__ == '__main__':
    main()
