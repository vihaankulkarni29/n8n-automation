"""
Enrich brand data with Instagram profile information
"""

import pandas as pd
import instaloader
from pathlib import Path
import time


class BrandProfileEnricher:
    """
    Enrich brand mentions with Instagram profile information.
    """
    
    def __init__(self):
        """Initialize Instaloader."""
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
        )
    
    def get_profile_info(self, username: str) -> dict:
        """
        Get Instagram profile information for a brand.
        
        Args:
            username: Instagram username (without @)
            
        Returns:
            Dict with profile info or error
        """
        try:
            profile = instaloader.Profile.from_username(
                self.loader.context, 
                username
            )
            
            return {
                'brand_username': username,
                'brand_instagram_url': f'https://instagram.com/{username}',
                'brand_full_name': profile.full_name,
                'brand_bio': profile.biography[:200] if profile.biography else '',
                'brand_followers': profile.followers,
                'brand_following': profile.followees,
                'brand_posts': profile.mediacount,
                'brand_is_verified': profile.is_verified,
                'brand_is_business': profile.is_business_account,
                'brand_category': profile.category_name if hasattr(profile, 'category_name') else '',
                'profile_found': True,
                'error': None
            }
        
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
                'profile_found': False,
                'error': str(e)
            }
    
    def enrich_brands_csv(self, input_file: str = 'data/khalidwalb_brands.csv',
                         output_file: str = 'data/khalidwalb_brands_enriched.csv',
                         delay: float = 2.0):
        """
        Enrich brands CSV with Instagram profile information.
        
        Args:
            input_file: Input CSV with brands
            output_file: Output CSV with enriched data
            delay: Delay between requests (to avoid rate limiting)
        """
        print("="*80)
        print("ENRICHING BRANDS WITH INSTAGRAM PROFILE DATA")
        print("="*80)
        
        # Load brands
        df = pd.read_csv(input_file)
        
        print(f"\nProcessing {len(df)} brands...")
        print(f"Delay between requests: {delay} seconds")
        
        enriched_data = []
        
        for idx, row in df.iterrows():
            brand_account = row.get('brand_account', row.get('brand', ''))
            
            print(f"\n[{idx+1}/{len(df)}] Fetching profile: @{brand_account}")
            
            # Get profile info
            profile_info = self.get_profile_info(brand_account)
            
            # Combine original data with profile info
            enriched_row = row.to_dict()
            enriched_row.update(profile_info)
            enriched_data.append(enriched_row)
            
            if profile_info['profile_found']:
                print(f"   ✅ {profile_info['brand_full_name']}")
                print(f"   Followers: {profile_info['brand_followers']:,}")
                print(f"   Verified: {'Yes' if profile_info['brand_is_verified'] else 'No'}")
                print(f"   Business: {'Yes' if profile_info['brand_is_business'] else 'No'}")
            else:
                print(f"   ❌ Profile not found or error: {profile_info['error'][:50]}")
            
            # Delay to avoid rate limiting
            if idx < len(df) - 1:
                time.sleep(delay)
        
        # Create enriched DataFrame
        enriched_df = pd.DataFrame(enriched_data)
        
        # Reorder columns for better readability
        first_cols = ['influencer_handle', 'brand_account', 'brand_username', 
                     'brand_instagram_url', 'brand_full_name', 'brand_followers',
                     'brand_is_verified', 'brand_is_business']
        
        other_cols = [col for col in enriched_df.columns if col not in first_cols]
        enriched_df = enriched_df[first_cols + other_cols]
        
        # Save enriched data
        enriched_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*80)
        print(f"✅ Saved enriched data to: {output_file}")
        print("="*80)
        
        # Summary
        found_count = sum(1 for d in enriched_data if d['profile_found'])
        print(f"\nSUMMARY:")
        print(f"  Profiles found: {found_count}/{len(df)}")
        print(f"  Profiles not found: {len(df) - found_count}")
        
        if found_count > 0:
            verified_count = sum(1 for d in enriched_data if d['brand_is_verified'])
            business_count = sum(1 for d in enriched_data if d['brand_is_business'])
            total_followers = sum(d['brand_followers'] for d in enriched_data if d['profile_found'])
            
            print(f"  Verified accounts: {verified_count}")
            print(f"  Business accounts: {business_count}")
            print(f"  Total followers: {total_followers:,}")
            print(f"  Avg followers per brand: {total_followers//found_count:,}")
        
        print("\n" + "="*80)
        
        return enriched_df
    
    def enrich_mentions_csv(self, input_file: str = 'data/khalidwalb_brand_mentions.csv',
                           brands_enriched_file: str = 'data/khalidwalb_brands_enriched.csv',
                           output_file: str = 'data/khalidwalb_brand_mentions_enriched.csv'):
        """
        Enrich brand mentions with profile data from enriched brands file.
        
        Args:
            input_file: Input mentions CSV
            brands_enriched_file: Enriched brands CSV with profile data
            output_file: Output enriched mentions CSV
        """
        print("\n" + "="*80)
        print("ENRICHING BRAND MENTIONS WITH PROFILE DATA")
        print("="*80)
        
        # Load mentions and enriched brands
        mentions_df = pd.read_csv(input_file)
        brands_df = pd.read_csv(brands_enriched_file)
        
        # Create mapping of brand -> profile info
        brand_info_cols = ['brand_username', 'brand_instagram_url', 'brand_full_name', 
                          'brand_followers', 'brand_is_verified', 'brand_is_business', 
                          'brand_category']
        
        brand_info = brands_df.set_index('brand_account')[brand_info_cols].to_dict('index')
        
        # Add brand info to mentions
        for col in brand_info_cols:
            mentions_df[col] = mentions_df['brand'].map(
                lambda b: brand_info.get(b, {}).get(col, '')
            )
        
        # Save enriched mentions
        mentions_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ Saved enriched mentions to: {output_file}")
        print("="*80)
        
        return mentions_df


def main():
    """
    Main function to enrich brand data with Instagram profiles.
    """
    enricher = BrandProfileEnricher()
    
    # Check if files exist
    brands_file = 'data/khalidwalb_brands.csv'
    mentions_file = 'data/khalidwalb_brand_mentions.csv'
    
    if not Path(brands_file).exists():
        print(f"❌ File not found: {brands_file}")
        return
    
    # Enrich brands with profile data
    enriched_brands = enricher.enrich_brands_csv(
        input_file=brands_file,
        output_file='data/khalidwalb_brands_enriched.csv',
        delay=2.0
    )
    
    # Enrich mentions with profile data
    if Path(mentions_file).exists():
        enricher.enrich_mentions_csv(
            input_file=mentions_file,
            brands_enriched_file='data/khalidwalb_brands_enriched.csv',
            output_file='data/khalidwalb_brand_mentions_enriched.csv'
        )
    
    print("\n🎉 ENRICHMENT COMPLETE!")
    print("\nNew files created:")
    print("  1. khalidwalb_brands_enriched.csv - Brands with Instagram profile data")
    print("  2. khalidwalb_brand_mentions_enriched.csv - Mentions with brand profiles")


if __name__ == '__main__':
    main()
