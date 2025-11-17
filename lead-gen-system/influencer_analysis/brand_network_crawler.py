"""
Brand Network Crawler for Instagram
- Analyzes brand Instagram profiles
- Discovers similar brands through mentions, tags, and captions
- Builds brand network graph
"""

import instaloader
import pandas as pd
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import re


class BrandNetworkCrawler:
    """
    Crawl brand Instagram accounts to discover network of similar brands.
    """
    
    def __init__(self, delay: float = 2.0):
        """
        Initialize crawler.
        
        Args:
            delay: Delay between requests in seconds
        """
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
        )
        self.delay = delay
        self.discovered_brands = {}  # username -> profile_info
        self.brand_connections = []  # List of connections
    
    def login(self, username: str, password: str) -> bool:
        """
        Login to Instagram to avoid rate limits.
        
        Args:
            username: Instagram username
            password: Instagram password
            
        Returns:
            True if login successful
        """
        try:
            self.loader.login(username, password)
            print(f"✅ Logged in as @{username}")
            return True
        except Exception as e:
            print(f"⚠️  Login failed: {str(e)[:100]}")
            return False
        
    def get_brand_profile(self, username: str) -> Dict:
        """
        Get brand profile information.
        
        Args:
            username: Instagram username (without @)
            
        Returns:
            Dict with profile info
        """
        try:
            profile = instaloader.Profile.from_username(
                self.loader.context,
                username
            )
            
            info = {
                'brand_username': username,
                'brand_instagram_url': f'https://instagram.com/{username}',
                'brand_full_name': profile.full_name,
                'brand_bio': profile.biography[:500] if profile.biography else '',
                'brand_followers': profile.followers,
                'brand_following': profile.followees,
                'brand_posts': profile.mediacount,
                'brand_is_verified': profile.is_verified,
                'brand_is_business': profile.is_business_account,
                'brand_category': getattr(profile, 'category_name', ''),
                'discovered_at': datetime.now().isoformat(),
                'profile_found': True,
                'error': None
            }
            
            return info
            
        except Exception as e:
            return {
                'brand_username': username,
                'brand_instagram_url': f'https://instagram.com/{username}',
                'brand_full_name': '',
                'brand_bio': '',
                'brand_followers': 0,
                'brand_following': 0,
                'brand_posts': 0,
                'brand_is_verified': False,
                'brand_is_business': False,
                'brand_category': '',
                'discovered_at': datetime.now().isoformat(),
                'profile_found': False,
                'error': str(e)[:200]
            }
    
    def extract_mentions_from_posts(self, username: str, max_posts: int = 30) -> Set[str]:
        """
        Extract @mentions from recent posts.
        
        Args:
            username: Instagram username
            max_posts: Maximum posts to analyze
            
        Returns:
            Set of mentioned usernames
        """
        mentions = set()
        
        try:
            profile = instaloader.Profile.from_username(
                self.loader.context,
                username
            )
            
            post_count = 0
            for post in profile.get_posts():
                if post_count >= max_posts:
                    break
                
                # Extract mentions from caption
                if post.caption:
                    # Find @mentions
                    found_mentions = re.findall(r'@([a-zA-Z0-9._]+)', post.caption)
                    mentions.update(found_mentions)
                
                # Extract tagged users
                try:
                    tagged = post.tagged_users
                    mentions.update([user.username for user in tagged])
                except:
                    pass
                
                post_count += 1
                
                # Small delay to avoid rate limiting
                if post_count % 10 == 0:
                    time.sleep(self.delay)
            
            # Filter out common non-brand mentions
            exclude = {'instagram', 'explore', 'reels', 'igtv', 'p', 'tv', 
                      'the', 'them', 'you', 'your', 'our', 'my', 'me', 'i'}
            mentions = {m for m in mentions if m.lower() not in exclude and len(m) > 2}
            
        except Exception as e:
            print(f"   ⚠️  Error extracting mentions: {str(e)[:100]}")
        
        return mentions
    
    def crawl_brand_network(self, seed_brands: List[str], 
                           max_depth: int = 2,
                           max_posts_per_brand: int = 30,
                           min_followers_threshold: int = 1000) -> Dict:
        """
        Crawl brand network starting from seed brands.
        
        Args:
            seed_brands: Initial list of brand usernames
            max_depth: How many levels deep to crawl
            max_posts_per_brand: Posts to analyze per brand
            min_followers_threshold: Minimum followers for discovered brands
            
        Returns:
            Dict with brands and connections
        """
        print("="*80)
        print("BRAND NETWORK CRAWLER")
        print("="*80)
        
        to_crawl = [(brand, 0) for brand in seed_brands]  # (username, depth)
        crawled = set()
        
        while to_crawl:
            current_brand, depth = to_crawl.pop(0)
            
            if current_brand in crawled:
                continue
            
            if depth > max_depth:
                continue
            
            print(f"\n[Depth {depth}] Analyzing @{current_brand}")
            
            # Get brand profile
            profile_info = self.get_brand_profile(current_brand)
            
            if not profile_info['profile_found']:
                print(f"   ❌ Profile not found: {profile_info['error'][:50]}")
                crawled.add(current_brand)
                continue
            
            # Check follower threshold
            followers = profile_info['brand_followers']
            if followers < min_followers_threshold:
                print(f"   ⏭️  Skipping (only {followers:,} followers)")
                crawled.add(current_brand)
                continue
            
            print(f"   ✅ {profile_info['brand_full_name']}")
            print(f"   📊 {followers:,} followers | {profile_info['brand_posts']} posts")
            print(f"   {'✓ Verified' if profile_info['brand_is_verified'] else '  '} {'✓ Business' if profile_info['brand_is_business'] else ''}")
            
            # Store brand
            self.discovered_brands[current_brand] = profile_info
            crawled.add(current_brand)
            
            # Extract mentions from posts
            print(f"   🔍 Scanning {max_posts_per_brand} posts for brand mentions...")
            mentions = self.extract_mentions_from_posts(current_brand, max_posts_per_brand)
            
            if mentions:
                print(f"   📌 Found {len(mentions)} mentions: {', '.join(list(mentions)[:5])}{'...' if len(mentions) > 5 else ''}")
                
                # Store connections
                for mentioned in mentions:
                    self.brand_connections.append({
                        'source_brand': current_brand,
                        'mentioned_brand': mentioned,
                        'depth': depth,
                        'discovered_at': datetime.now().isoformat()
                    })
                    
                    # Add to crawl queue if not seen and within depth limit
                    if mentioned not in crawled and depth < max_depth:
                        to_crawl.append((mentioned, depth + 1))
            else:
                print(f"   📌 No mentions found")
            
            # Rate limiting
            time.sleep(self.delay)
        
        print("\n" + "="*80)
        print(f"✅ CRAWL COMPLETE")
        print(f"   Discovered {len(self.discovered_brands)} brands")
        print(f"   Found {len(self.brand_connections)} connections")
        print("="*80)
        
        return {
            'brands': self.discovered_brands,
            'connections': self.brand_connections
        }
    
    def save_results(self, output_dir: str = 'data') -> Dict[str, str]:
        """
        Save discovered brands and connections to CSV.
        
        Args:
            output_dir: Directory to save files
            
        Returns:
            Dict with file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        files = {}
        
        # Save brands
        if self.discovered_brands:
            brands_df = pd.DataFrame.from_dict(self.discovered_brands, orient='index')
            brands_df = brands_df.reset_index(drop=True)
            
            # Add source and collected_at for unified schema
            brands_df['source'] = 'instagram_brand_network'
            brands_df['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            brands_file = output_path / f'brand_network_brands_{timestamp}.csv'
            brands_df.to_csv(brands_file, index=False, encoding='utf-8-sig')
            files['brands'] = str(brands_file)
            print(f"\n✅ Saved brands: {brands_file}")
        
        # Save connections
        if self.brand_connections:
            connections_df = pd.DataFrame(self.brand_connections)
            connections_file = output_path / f'brand_network_connections_{timestamp}.csv'
            connections_df.to_csv(connections_file, index=False, encoding='utf-8-sig')
            files['connections'] = str(connections_file)
            print(f"✅ Saved connections: {connections_file}")
        
        return files


def main():
    """
    Main function to crawl brand network.
    """
    # Seed brands from user request
    SEED_BRANDS = [
        'dotcombubble',
        'killhouse',
        'infectedclo',  # "infected clo"
        'nvmbr',        # "nvmbr."
    ]
    
    print("\n🎯 TARGET SEED BRANDS:")
    for brand in SEED_BRANDS:
        print(f"   - @{brand}")
    
    # Initialize crawler
    crawler = BrandNetworkCrawler(delay=3.0)  # Slower to avoid triggering limits
    
    # Optional: Login to avoid rate limits (set environment variables)
    import os
    ig_user = os.getenv('INSTAGRAM_USERNAME')
    ig_pass = os.getenv('INSTAGRAM_PASSWORD')
    if ig_user and ig_pass:
        print("\n🔐 Authenticating...")
        crawler.login(ig_user, ig_pass)
    
    # Crawl network
    results = crawler.crawl_brand_network(
        seed_brands=SEED_BRANDS,
        max_depth=2,              # Seed brands (0) + 1st degree (1) + 2nd degree (2)
        max_posts_per_brand=30,   # Analyze 30 recent posts per brand
        min_followers_threshold=10  # Include small brands too
    )
    
    # Save results
    files = crawler.save_results()
    
    # Summary
    print("\n" + "="*80)
    print("📊 BRAND NETWORK SUMMARY")
    print("="*80)
    
    brands_df = pd.DataFrame.from_dict(results['brands'], orient='index')
    
    if not brands_df.empty:
        print(f"\n✅ Discovered {len(brands_df)} brands total")
        
        # Stats
        verified_count = brands_df['brand_is_verified'].sum()
        business_count = brands_df['brand_is_business'].sum()
        total_followers = brands_df['brand_followers'].sum()
        
        print(f"   Verified: {verified_count}")
        print(f"   Business accounts: {business_count}")
        print(f"   Total followers: {total_followers:,}")
        print(f"   Avg followers: {int(total_followers / len(brands_df)):,}")
        
        # Top brands by followers
        print(f"\n🏆 TOP 10 BRANDS BY FOLLOWERS:")
        top_brands = brands_df.nlargest(10, 'brand_followers')[['brand_username', 'brand_followers', 'brand_full_name']]
        for idx, row in top_brands.iterrows():
            print(f"   {row['brand_username']:20s} | {row['brand_followers']:>8,} | {row['brand_full_name']}")
    
    print("\n" + "="*80)
    print("\n🎉 NEXT STEPS:")
    print("   1. Review discovered brands in CSV files")
    print("   2. Run utils/merge_all_leads.py to add to unified leads")
    print("   3. Run utils/publish_influencer_leads.py to update Excel")
    print("="*80)


if __name__ == '__main__':
    main()
