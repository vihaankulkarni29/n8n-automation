"""
Scan specific brands for mentions and discover their network.
Lighter version focused on just extracting mentions without full network crawl.
"""

import instaloader
import pandas as pd
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Set, List

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'


def extract_brand_mentions(username: str, max_posts: int = 30, delay: float = 2.0) -> dict:
    """
    Extract brand mentions from a single Instagram account.
    
    Args:
        username: Instagram username to scan
        max_posts: Number of recent posts to analyze
        delay: Delay between requests
        
    Returns:
        Dict with mentions and stats
    """
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
    )
    
    print(f"\n{'='*80}")
    print(f"SCANNING @{username}")
    print(f"{'='*80}")
    
    mentions = set()
    tagged = set()
    post_count = 0
    
    try:
        # Get profile
        profile = instaloader.Profile.from_username(loader.context, username)
        
        print(f"\n📊 Profile Info:")
        print(f"   Name: {profile.full_name or username}")
        print(f"   Followers: {profile.followers:,}")
        print(f"   Posts: {profile.mediacount}")
        print(f"   {'✓ Verified' if profile.is_verified else ''} {'✓ Business' if profile.is_business_account else ''}")
        
        # Scan posts
        print(f"\n🔍 Scanning {max_posts} recent posts...")
        
        for post in profile.get_posts():
            if post_count >= max_posts:
                break
            
            # Extract from caption
            if post.caption:
                found = re.findall(r'@([a-zA-Z0-9._]+)', post.caption)
                mentions.update(found)
            
            # Extract tagged users
            try:
                for user in post.tagged_users:
                    tagged.add(user.username)
            except:
                pass
            
            post_count += 1
            
            # Progress
            if post_count % 5 == 0:
                print(f"   Scanned {post_count} posts...")
                time.sleep(delay)
        
        # Filter common words
        exclude = {'instagram', 'explore', 'reels', 'igtv', 'p', 'tv', 
                  'the', 'them', 'you', 'your', 'our', 'my', 'me', 'i', username}
        mentions = {m for m in mentions if m.lower() not in exclude and len(m) > 2}
        tagged = {t for t in tagged if t.lower() not in exclude and len(t) > 2}
        
        all_brands = mentions.union(tagged)
        
        print(f"\n📌 RESULTS:")
        print(f"   Caption mentions: {len(mentions)}")
        print(f"   Tagged users: {len(tagged)}")
        print(f"   Total unique brands: {len(all_brands)}")
        
        if all_brands:
            print(f"\n   Discovered brands:")
            for brand in sorted(list(all_brands)[:20]):
                source = []
                if brand in mentions:
                    source.append("caption")
                if brand in tagged:
                    source.append("tagged")
                print(f"      @{brand} ({', '.join(source)})")
            if len(all_brands) > 20:
                print(f"      ... and {len(all_brands) - 20} more")
        
        return {
            'username': username,
            'profile_found': True,
            'followers': profile.followers,
            'posts_scanned': post_count,
            'caption_mentions': list(mentions),
            'tagged_users': list(tagged),
            'all_brands': list(all_brands),
            'total_brands': len(all_brands),
            'error': None
        }
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)[:100]}")
        return {
            'username': username,
            'profile_found': False,
            'followers': 0,
            'posts_scanned': 0,
            'caption_mentions': [],
            'tagged_users': [],
            'all_brands': [],
            'total_brands': 0,
            'error': str(e)[:200]
        }


def scan_multiple_brands(usernames: List[str], max_posts: int = 30) -> pd.DataFrame:
    """
    Scan multiple brands and compile results.
    
    Args:
        usernames: List of Instagram usernames
        max_posts: Posts to scan per brand
        
    Returns:
        DataFrame with all mentions
    """
    print(f"\n{'='*80}")
    print(f"BRAND MENTION SCANNER")
    print(f"{'='*80}")
    print(f"\nTarget brands: {len(usernames)}")
    for u in usernames:
        print(f"   - @{u}")
    
    all_mentions = []
    
    for username in usernames:
        result = extract_brand_mentions(username, max_posts, delay=2.5)
        
        # Create rows for each discovered brand
        for brand in result['all_brands']:
            all_mentions.append({
                'source_brand': username,
                'mentioned_brand': brand,
                'in_caption': brand in result['caption_mentions'],
                'in_tags': brand in result['tagged_users'],
                'source_followers': result['followers'],
                'discovered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        time.sleep(3)  # Longer delay between accounts
    
    if not all_mentions:
        print("\n⚠️  No brand mentions found in any scanned profiles")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_mentions)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = DATA_DIR / f'brand_mentions_scan_{timestamp}.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n{'='*80}")
    print(f"✅ SCAN COMPLETE")
    print(f"{'='*80}")
    print(f"\nTotal mentions discovered: {len(df)}")
    print(f"Unique brands mentioned: {df['mentioned_brand'].nunique()}")
    print(f"\n📁 Saved to: {output_file}")
    
    # Show top mentioned brands
    top_brands = df['mentioned_brand'].value_counts().head(10)
    if not top_brands.empty:
        print(f"\n🏆 TOP MENTIONED BRANDS:")
        for brand, count in top_brands.items():
            print(f"   @{brand} - mentioned by {count} source(s)")
    
    return df


def main():
    """Scan the 4 seed brands for mentions."""
    
    SEED_BRANDS = [
        'dotcombubble',
        'killhouse',
        'infected.clo',
        'nvmbr',
    ]
    
    df = scan_multiple_brands(SEED_BRANDS, max_posts=30)
    
    if not df.empty:
        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("="*80)
        print("1. Review discovered brands in the CSV file")
        print("2. Add interesting brands to your system with utils/add_single_brand.py")
        print("3. Or run brand_network_crawler.py on discovered brands")
        print("="*80)


if __name__ == '__main__':
    main()
