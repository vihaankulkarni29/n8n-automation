"""
Instagram Business Account Scraper by Hashtags
Discovers D2C brands, fashion labels, and businesses through Instagram hashtags
"""

import instaloader
import pandas as pd
from datetime import datetime
from typing import List, Dict, Set
import time
from pathlib import Path
import re


class InstagramBusinessScraper:
    """
    Scrape Instagram business accounts by hashtags.
    """
    
    # Target hashtags for different categories
    HASHTAGS = {
        'fashion': [
            'indianbrand',
            'madeinindiastartup',
            'd2cbrand',
            'indianfashionbrand',
            'indiastreetwear',
            'indiandesigner',
        ],
        'beauty': [
            'indianbeautybrand',
            'makeinindia',
            'organicbeautyindia',
            'indianskincare',
        ],
        'food': [
            'indianfoodbrand',
            'organicfoodindia',
            'homemadeindia',
        ],
        'lifestyle': [
            'indianstartup',
            'indiaentrepreneur',
            'smallbusinessindia',
        ]
    }
    
    def __init__(self, delay: float = 3.0):
        """
        Initialize scraper.
        
        Args:
            delay: Delay between requests in seconds
        """
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
        )
        self.delay = delay
        self.discovered_accounts = {}
    
    def login(self, username: str, password: str) -> bool:
        """
        Login to Instagram (optional but recommended for higher limits).
        
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
    
    def scrape_hashtag(self, hashtag: str, max_posts: int = 30) -> Set[str]:
        """
        Scrape business accounts from a hashtag.
        
        Args:
            hashtag: Hashtag to scrape (without #)
            max_posts: Maximum posts to analyze
            
        Returns:
            Set of discovered business account usernames
        """
        print(f"\n🔍 Scraping #{hashtag}")
        
        business_accounts = set()
        
        try:
            posts = instaloader.Hashtag.from_name(self.loader.context, hashtag).get_posts()
            
            post_count = 0
            for post in posts:
                if post_count >= max_posts:
                    break
                
                # Get post owner
                owner = post.owner_username
                
                # Check if it's a business account
                try:
                    profile = instaloader.Profile.from_username(self.loader.context, owner)
                    
                    # Filter criteria for business accounts
                    if (profile.is_business_account or 
                        profile.is_verified or
                        profile.followers > 500):
                        
                        business_accounts.add(owner)
                        
                        if len(business_accounts) % 10 == 0:
                            print(f"   Found {len(business_accounts)} business accounts...")
                
                except Exception:
                    pass
                
                post_count += 1
                
                # Rate limiting
                if post_count % 10 == 0:
                    time.sleep(self.delay)
            
            print(f"   ✅ Discovered {len(business_accounts)} business accounts")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
        
        return business_accounts
    
    def get_account_details(self, username: str) -> Dict:
        """
        Get detailed info for a business account.
        
        Args:
            username: Instagram username
            
        Returns:
            Dict with account details
        """
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            # Extract website/bio for contact info
            website = profile.external_url or ''
            bio = profile.biography or ''
            
            # Try to extract email from bio
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', bio)
            email = email_match.group(0) if email_match else None
            
            # Try to extract phone from bio
            phone_match = re.search(r'[\+\(]?[0-9][0-9\s\-\(\)]{7,}[0-9]', bio)
            phone = phone_match.group(0) if phone_match else None
            
            data = {
                'username': username,
                'instagram_url': f'https://instagram.com/{username}',
                'full_name': profile.full_name,
                'bio': bio[:500] if bio else '',
                'website': website,
                'email': email,
                'phone': phone,
                'followers': profile.followers,
                'following': profile.followees,
                'posts': profile.mediacount,
                'is_verified': profile.is_verified,
                'is_business': profile.is_business_account,
                'category': getattr(profile, 'category_name', ''),
                'discovered_at': datetime.now().isoformat(),
            }
            
            return data
            
        except Exception as e:
            return {
                'username': username,
                'instagram_url': f'https://instagram.com/{username}',
                'error': str(e)[:200]
            }
    
    def scrape_by_category(self, category: str = 'fashion', 
                          max_posts_per_hashtag: int = 30,
                          max_accounts: int = 100) -> pd.DataFrame:
        """
        Scrape business accounts by category.
        
        Args:
            category: Category to scrape ('fashion', 'beauty', 'food', 'lifestyle')
            max_posts_per_hashtag: Posts to analyze per hashtag
            max_accounts: Maximum accounts to discover
            
        Returns:
            DataFrame with business accounts
        """
        print(f"\n{'='*80}")
        print(f"INSTAGRAM BUSINESS SCRAPER - {category.upper()}")
        print(f"{'='*80}")
        
        hashtags = self.HASHTAGS.get(category, self.HASHTAGS['fashion'])
        print(f"\nTarget hashtags: {', '.join(['#' + h for h in hashtags])}")
        
        all_accounts = set()
        
        for hashtag in hashtags:
            if len(all_accounts) >= max_accounts:
                break
            
            accounts = self.scrape_hashtag(hashtag, max_posts_per_hashtag)
            all_accounts.update(accounts)
            
            time.sleep(self.delay)
        
        print(f"\n{'='*80}")
        print(f"📊 Total unique accounts discovered: {len(all_accounts)}")
        print(f"{'='*80}")
        
        # Get detailed info for each account
        print(f"\n🔍 Fetching detailed info for {min(len(all_accounts), max_accounts)} accounts...")
        
        accounts_data = []
        count = 0
        
        for username in list(all_accounts)[:max_accounts]:
            print(f"   [{count+1}/{min(len(all_accounts), max_accounts)}] @{username}")
            
            details = self.get_account_details(username)
            if details and not details.get('error'):
                accounts_data.append(details)
            
            count += 1
            time.sleep(self.delay)
            
            if count >= max_accounts:
                break
        
        df = pd.DataFrame(accounts_data)
        
        if not df.empty:
            # Add source and category
            df['source'] = 'instagram_business'
            df['category_scraped'] = category
            df['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return df
    
    def save_results(self, df: pd.DataFrame, category: str, output_dir: str = 'data') -> str:
        """
        Save results to CSV.
        
        Args:
            df: DataFrame with account data
            category: Category name
            output_dir: Output directory
            
        Returns:
            Output file path
        """
        if df.empty:
            print("⚠️  No data to save")
            return ""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_path / f'instagram_business_{category}_{timestamp}.csv'
        
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Saved to: {output_file}")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total accounts: {len(df)}")
        print(f"Business accounts: {df['is_business'].sum() if 'is_business' in df.columns else 0}")
        print(f"Verified accounts: {df['is_verified'].sum() if 'is_verified' in df.columns else 0}")
        print(f"With websites: {df['website'].notna().sum() if 'website' in df.columns else 0}")
        print(f"With emails: {df['email'].notna().sum() if 'email' in df.columns else 0}")
        print(f"Avg followers: {int(df['followers'].mean()) if 'followers' in df.columns else 0:,}")
        
        return str(output_file)


def main():
    """
    Main function to scrape Instagram business accounts.
    """
    import os
    
    scraper = InstagramBusinessScraper(delay=3.0)
    
    # Optional: Login for better rate limits
    ig_user = os.getenv('INSTAGRAM_USERNAME')
    ig_pass = os.getenv('INSTAGRAM_PASSWORD')
    if ig_user and ig_pass:
        scraper.login(ig_user, ig_pass)
    
    # Scrape fashion/D2C brands
    categories_to_scrape = ['fashion']  # Can add: 'beauty', 'food', 'lifestyle'
    
    for category in categories_to_scrape:
        df = scraper.scrape_by_category(
            category=category,
            max_posts_per_hashtag=20,  # Keep low to avoid rate limits
            max_accounts=50  # Adjust based on needs
        )
        
        if not df.empty:
            scraper.save_results(df, category)
        
        time.sleep(5)  # Delay between categories


if __name__ == '__main__':
    main()
