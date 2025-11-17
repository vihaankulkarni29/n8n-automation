"""
Manually add seed brands to the system while waiting for Instagram rate limit.
Creates initial brand records that can be enriched later.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'

# Seed brands to add
SEED_BRANDS = [
    {
        'brand_username': 'dotcombubble',
        'brand_instagram_url': 'https://instagram.com/dotcombubble',
        'brand_full_name': 'DOTCOMBUBBLE',
        'brand_bio': 'Indian streetwear brand',
        'source': 'instagram_brand_network',
        'status': 'pending_enrichment',
        'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        'brand_username': 'killhouse',
        'brand_instagram_url': 'https://instagram.com/killhouse',
        'brand_full_name': 'KILLHOUSE',
        'brand_bio': 'Indian streetwear brand',
        'source': 'instagram_brand_network',
        'status': 'pending_enrichment',
        'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        'brand_username': 'infectedclo',
        'brand_instagram_url': 'https://instagram.com/infectedclo',
        'brand_full_name': 'INFECTED',
        'brand_bio': 'Indian streetwear brand',
        'source': 'instagram_brand_network',
        'status': 'pending_enrichment',
        'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        'brand_username': 'nvmbr',
        'brand_instagram_url': 'https://instagram.com/nvmbr',
        'brand_full_name': 'NVMBR',
        'brand_bio': 'Indian streetwear brand',
        'source': 'instagram_brand_network',
        'status': 'pending_enrichment',
        'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    },
]


def main():
    print("="*80)
    print("ADDING SEED BRANDS TO SYSTEM")
    print("="*80)
    
    # Create DataFrame
    df = pd.DataFrame(SEED_BRANDS)
    
    # Save
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = DATA_DIR / f'seed_brands_{timestamp}.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ Added {len(SEED_BRANDS)} seed brands:")
    for brand in SEED_BRANDS:
        print(f"   - @{brand['brand_username']}: {brand['brand_instagram_url']}")
    
    print(f"\n📁 Saved to: {output_file}")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Wait 15-30 minutes for Instagram rate limit to reset")
    print("2. Run brand_network_crawler.py to enrich profiles and discover network")
    print("3. Or manually enrich using enrich_brand_profiles.py")
    print("="*80)


if __name__ == '__main__':
    main()
