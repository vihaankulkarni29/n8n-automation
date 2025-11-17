"""
Add single brand manually to the system.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def add_brand(username: str):
    """Add a single brand to brand network."""
    
    brand = {
        'brand_username': username,
        'brand_instagram_url': f'https://instagram.com/{username}',
        'brand_full_name': username.upper().replace('.', ''),
        'brand_bio': '',
        'brand_followers': 0,
        'brand_following': 0,
        'brand_posts': 0,
        'brand_is_verified': False,
        'brand_is_business': False,
        'brand_category': '',
        'discovered_at': datetime.now().isoformat(),
        'profile_found': False,
        'error': 'Added manually, needs enrichment',
        'source': 'instagram_brand_network',
        'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'pending_enrichment'
    }
    
    # Save to new CSV
    df = pd.DataFrame([brand])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output = DATA / f'brand_network_brands_{timestamp}.csv'
    df.to_csv(output, index=False, encoding='utf-8-sig')
    
    print(f"✅ Added @{username}")
    print(f"📁 Saved to: {output}")
    print(f"🔗 {brand['brand_instagram_url']}")
    
    return output

if __name__ == '__main__':
    username = sys.argv[1] if len(sys.argv) > 1 else 'infected.clo'
    add_brand(username)
