"""
Run Shopify Lead Scorer with manual seed URLs
Since search engines block automated queries, use known Shopify stores
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.shopify_lead_scorer import ShopifyLeadScorer
import pandas as pd


def main():
    scraper = ShopifyLeadScorer(delay=1.5)
    
    # Seed list of Shopify stores to analyze
    # Mix of myshopify.com domains and custom domains
    seed_stores = [
        # Indian D2C brands on Shopify
        'https://sugarcosmetics.com',
        'https://boat-lifestyle.com',
        'https://giva.co',
        'https://mcaffeine.com',
        'https://themancompany.com',
        'https://bombayshavingcompany.com',
        'https://snitch.co.in',
        
        # Known Shopify stores (various industries)
        'https://www.allbirds.com',
        'https://www.gymshark.com',
        'https://www.fashionnova.com',
        'https://www.mvmt.com',
        'https://www.kylie cosmetics.com',
        'https://www.colourpop.com',
        
        # Smaller stores (may have weaknesses)
        'https://shop.tesla.com',
        'https://www.redbull.com/shop',
    ]
    
    print(f"\n{'='*80}")
    print(f"SHOPIFY LEAD SCORING - MANUAL MODE")
    print(f"{'='*80}")
    print(f"\nAnalyzing {len(seed_stores)} known Shopify stores...")
    
    results = []
    
    for i, url in enumerate(seed_stores, 1):
        print(f"\n[{i}/{len(seed_stores)}] Processing: {url}")
        
        # Extract metadata
        metadata = scraper.extract_metadata(url)
        
        # Skip if error
        if metadata.get('error'):
            print(f"   ⚠️  Skipping due to error: {metadata['error']}")
            continue
        
        # Classify industry
        industry, confidence = scraper.classify_industry(metadata)
        metadata['industry'] = industry
        metadata['industry_confidence'] = confidence
        
        # Score as lead
        lead_data = scraper.score_leads(metadata)
        metadata.update(lead_data)
        
        print(f"   Lead Score: {lead_data['lead_score']} ({lead_data['lead_quality'].upper()})")
        print(f"   Industry: {industry} ({confidence:.1%} confidence)")
        if lead_data['weaknesses']:
            print(f"   Weaknesses: {len(lead_data['weaknesses'])}")
            for weakness in lead_data['weaknesses'][:2]:
                print(f"      - {weakness}")
        
        results.append(metadata)
        
        scraper.session.close()
        scraper.session = scraper.session.__class__()
        scraper.session.headers.update(scraper.HEADERS)
    
    if not results:
        print("\n⚠️  No stores successfully analyzed")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Sort by lead score
    df = df.sort_values('lead_score', ascending=False)
    
    # Save results
    scraper.save_results(df, output_format='both')


if __name__ == '__main__':
    main()
