"""
Instagram Brand Analyzer
Analyzes Instagram influencer profiles to extract brand mentions from captions, hashtags, and tagged accounts.
"""

import re
import json
import instaloader
import pandas as pd
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
from pathlib import Path


class InstagramBrandAnalyzer:
    """
    Analyzes Instagram profiles to extract brand mentions and engagement metrics.
    
    Usage:
        analyzer = InstagramBrandAnalyzer(username='khalidwalb')
        analyzer.load_profile()
        analyzer.analyze_posts(max_posts=50)
        df = analyzer.get_dataframe()
        analyzer.export_results('khalidwalb_analysis.csv')
    """
    
    # Default fashion brands list - can be customized
    DEFAULT_BRANDS = [
        'Nike', 'Adidas', 'Gucci', 'Zara', 'Louis Vuitton', 'Puma',
        'H&M', 'Forever 21', 'Chanel', 'Dior', 'Prada', 'Versace',
        'Balenciaga', 'Off-White', 'Supreme', 'Vans', 'Converse',
        'Reebok', 'Under Armour', 'Levi\'s', 'Calvin Klein', 'Tommy Hilfiger',
        'Ralph Lauren', 'Burberry', 'Armani', 'Dolce & Gabbana',
        'Fendi', 'Givenchy', 'Hermès', 'Valentino', 'YSL', 'Saint Laurent',
        'Bottega Veneta', 'Celine', 'Moncler', 'Stone Island', 'Polo',
        'Lacoste', 'Boss', 'Hugo Boss', 'Diesel', 'G-Star', 'Uniqlo',
        'Gap', 'Old Navy', 'American Eagle', 'Hollister', 'Abercrombie',
        'Fitch', 'Urban Outfitters', 'Topshop', 'Asos', 'Boohoo',
        'Missguided', 'Pretty Little Thing', 'Fashion Nova', 'Shein',
        'Zaful', 'Romwe', 'Yesstyle', 'Aritzia', 'Lululemon', 'Athleta',
        'Gymshark', 'Fabletics', 'Outdoor Voices', 'Allbirds', 'Everlane',
        'Reformation', 'Revolve', 'Nasty Gal', 'Free People', 'Anthropologie',
        'Madewell', 'J.Crew', 'Banana Republic', 'Express', 'The North Face',
        'Patagonia', 'Columbia', 'Arc\'teryx', 'Canada Goose', 'Moncler',
        'Carhartt', 'Dickies', 'Dr. Martens', 'Timberland', 'UGG',
        'Crocs', 'Birkenstock', 'Clarks', 'Skechers', 'New Balance',
        'Asics', 'Mizuno', 'Salomon', 'Hoka', 'Brooks', 'Saucony',
        'On Running', 'APL', 'Jordan', 'Yeezy', 'Fear of God'
    ]
    
    def __init__(self, username: str, brands: Optional[List[str]] = None, 
                 session_file: Optional[str] = None):
        """
        Initialize the Instagram Brand Analyzer.
        
        Args:
            username: Instagram username to analyze
            brands: Custom list of brands to search for (uses DEFAULT_BRANDS if None)
            session_file: Path to saved session file for authentication
        """
        self.username = username
        self.brands = brands if brands else self.DEFAULT_BRANDS
        self.session_file = session_file
        
        # Normalize brands to lowercase for case-insensitive matching
        self.brands_lower = [brand.lower() for brand in self.brands]
        
        # Create brand name mapping for display
        self.brand_mapping = {brand.lower(): brand for brand in self.brands}
        
        # Initialize instaloader
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern='',
        )
        
        # Storage for results
        self.profile = None
        self.posts_data = []
        self.brand_mentions = {}  # {brand: [post_shortcodes]}
        self.post_details = {}    # {shortcode: post_info}
        
    def login(self, username: str, password: str):
        """
        Login to Instagram for accessing profiles.
        
        Args:
            username: Instagram username
            password: Instagram password
        """
        try:
            self.loader.login(username, password)
            print(f"✅ Logged in as {username}")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            raise
    
    def load_session(self, session_file: str):
        """
        Load a saved session to avoid repeated logins.
        
        Args:
            session_file: Path to session file
        """
        try:
            self.loader.load_session_from_file(session_file)
            print(f"✅ Loaded session from {session_file}")
        except Exception as e:
            print(f"❌ Failed to load session: {e}")
            raise
    
    def load_profile(self):
        """
        Load the Instagram profile to analyze.
        """
        try:
            self.profile = instaloader.Profile.from_username(
                self.loader.context, 
                self.username
            )
            print(f"✅ Loaded profile: @{self.username}")
            print(f"   Followers: {self.profile.followers:,}")
            print(f"   Following: {self.profile.followees:,}")
            print(f"   Posts: {self.profile.mediacount:,}")
        except Exception as e:
            print(f"❌ Failed to load profile: {e}")
            raise
    
    def get_captions(self, max_posts: int = 50) -> List[Tuple[str, str]]:
        """
        Extract captions from recent posts.
        
        Args:
            max_posts: Maximum number of posts to analyze
            
        Returns:
            List of (shortcode, caption) tuples
        """
        if not self.profile:
            raise ValueError("Profile not loaded. Call load_profile() first.")
        
        captions = []
        
        try:
            for i, post in enumerate(self.profile.get_posts()):
                if i >= max_posts:
                    break
                
                caption = post.caption if post.caption else ""
                captions.append((post.shortcode, caption))
                
        except Exception as e:
            print(f"⚠️ Error fetching captions: {e}")
        
        return captions
    
    def extract_brands(self, text: str) -> Set[str]:
        """
        Extract brand mentions from text using case-insensitive matching.
        
        Args:
            text: Text to search (caption, hashtags, etc.)
            
        Returns:
            Set of brand names found (in original case)
        """
        if not text:
            return set()
        
        text_lower = text.lower()
        brands_found = set()
        
        # Use word boundaries for more accurate matching
        for brand_lower, brand_original in self.brand_mapping.items():
            # Create regex pattern with word boundaries
            pattern = r'\b' + re.escape(brand_lower) + r'\b'
            
            if re.search(pattern, text_lower):
                brands_found.add(brand_original)
        
        return brands_found
    
    def analyze_posts(self, max_posts: int = 50, include_engagement: bool = True):
        """
        Analyze posts to extract brand mentions and engagement metrics.
        
        Args:
            max_posts: Maximum number of posts to analyze
            include_engagement: Whether to include engagement metrics
        """
        if not self.profile:
            raise ValueError("Profile not loaded. Call load_profile() first.")
        
        print(f"\n🔍 Analyzing up to {max_posts} posts from @{self.username}...")
        
        # Reset storage
        self.posts_data = []
        self.brand_mentions = {brand: [] for brand in self.brands}
        self.post_details = {}
        
        try:
            for i, post in enumerate(self.profile.get_posts()):
                if i >= max_posts:
                    break
                
                # Extract post data
                shortcode = post.shortcode
                caption = post.caption if post.caption else ""
                
                # Get hashtags
                hashtags = []
                if caption:
                    hashtags = re.findall(r'#(\w+)', caption)
                
                # Get tagged accounts
                tagged_users = []
                try:
                    tagged_users = [user.username for user in post.tagged_users]
                except Exception:
                    pass
                
                # Extract brands from all sources
                brands_in_caption = self.extract_brands(caption)
                brands_in_hashtags = self.extract_brands(' '.join(hashtags))
                brands_in_tagged = self.extract_brands(' '.join(tagged_users))
                
                all_brands = brands_in_caption | brands_in_hashtags | brands_in_tagged
                
                # Store post details
                post_info = {
                    'shortcode': shortcode,
                    'url': f'https://www.instagram.com/p/{shortcode}/',
                    'date': post.date_utc.strftime('%Y-%m-%d %H:%M:%S'),
                    'caption': caption[:200] + '...' if len(caption) > 200 else caption,
                    'hashtags': hashtags,
                    'tagged_users': tagged_users,
                    'brands_mentioned': list(all_brands),
                    'brands_count': len(all_brands)
                }
                
                if include_engagement:
                    post_info.update({
                        'likes': post.likes,
                        'comments': post.comments,
                        'engagement': post.likes + post.comments,
                        'engagement_rate': ((post.likes + post.comments) / self.profile.followers * 100) 
                                         if self.profile.followers > 0 else 0
                    })
                
                self.posts_data.append(post_info)
                self.post_details[shortcode] = post_info
                
                # Update brand mentions mapping
                for brand in all_brands:
                    self.brand_mentions[brand].append(shortcode)
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"   Processed {i + 1}/{max_posts} posts...")
        
        except Exception as e:
            print(f"⚠️ Error during analysis: {e}")
        
        # Clean up brand_mentions (remove brands with no mentions)
        self.brand_mentions = {
            brand: shortcodes 
            for brand, shortcodes in self.brand_mentions.items() 
            if shortcodes
        }
        
        print(f"\n✅ Analysis complete!")
        print(f"   Total posts analyzed: {len(self.posts_data)}")
        print(f"   Brands mentioned: {len(self.brand_mentions)}")
        print(f"   Total brand mentions: {sum(len(codes) for codes in self.brand_mentions.values())}")
    
    def get_brand_summary(self) -> pd.DataFrame:
        """
        Get a summary of brand mentions.
        
        Returns:
            DataFrame with brand mention counts and post shortcodes
        """
        if not self.brand_mentions:
            return pd.DataFrame()
        
        summary_data = []
        
        for brand, shortcodes in sorted(
            self.brand_mentions.items(), 
            key=lambda x: len(x[1]), 
            reverse=True
        ):
            # Calculate total engagement for this brand
            total_likes = sum(
                self.post_details[sc]['likes'] 
                for sc in shortcodes 
                if 'likes' in self.post_details[sc]
            )
            total_comments = sum(
                self.post_details[sc]['comments'] 
                for sc in shortcodes 
                if 'comments' in self.post_details[sc]
            )
            
            summary_data.append({
                'influencer_handle': self.username,
                'brand': brand,
                'mentions': len(shortcodes),
                'post_shortcodes': ', '.join(shortcodes),
                'total_likes': total_likes,
                'total_comments': total_comments,
                'total_engagement': total_likes + total_comments,
                'avg_engagement_per_post': (total_likes + total_comments) / len(shortcodes) if shortcodes else 0
            })
        
        return pd.DataFrame(summary_data)
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Convert post analysis results to a pandas DataFrame.
        
        Returns:
            DataFrame with all post details
        """
        if not self.posts_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.posts_data)
        
        # Add influencer username column
        df.insert(0, 'influencer_handle', self.username)
        
        # Convert lists to strings for better CSV export
        if 'hashtags' in df.columns:
            df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x) if x else '')
        if 'tagged_users' in df.columns:
            df['tagged_users'] = df['tagged_users'].apply(lambda x: ', '.join(x) if x else '')
        if 'brands_mentioned' in df.columns:
            df['brands_mentioned'] = df['brands_mentioned'].apply(lambda x: ', '.join(x) if x else '')
        
        return df
    
    def export_results(self, output_file: str, format: str = 'csv', 
                      include_brand_summary: bool = True):
        """
        Export analysis results to file.
        
        Args:
            output_file: Output file path (without extension)
            format: Export format ('csv', 'json', 'excel')
            include_brand_summary: Whether to include brand summary sheet/file
        """
        output_path = Path(output_file)
        base_name = output_path.stem
        output_dir = output_path.parent if output_path.parent != Path('.') else Path('data')
        output_dir.mkdir(exist_ok=True)
        
        df = self.get_dataframe()
        brand_df = self.get_brand_summary()
        
        if format == 'csv':
            posts_file = output_dir / f'{base_name}_posts.csv'
            df.to_csv(posts_file, index=False)
            print(f"✅ Saved posts data to {posts_file}")
            
            if include_brand_summary and not brand_df.empty:
                brands_file = output_dir / f'{base_name}_brands.csv'
                brand_df.to_csv(brands_file, index=False)
                print(f"✅ Saved brand summary to {brands_file}")
        
        elif format == 'json':
            posts_file = output_dir / f'{base_name}_posts.json'
            df.to_json(posts_file, orient='records', indent=2)
            print(f"✅ Saved posts data to {posts_file}")
            
            if include_brand_summary and not brand_df.empty:
                brands_file = output_dir / f'{base_name}_brands.json'
                brand_df.to_json(brands_file, orient='records', indent=2)
                print(f"✅ Saved brand summary to {brands_file}")
            
            # Also save the brand_mentions dictionary
            mentions_file = output_dir / f'{base_name}_brand_mentions.json'
            with open(mentions_file, 'w') as f:
                json.dump(self.brand_mentions, f, indent=2)
            print(f"✅ Saved brand mentions map to {mentions_file}")
        
        elif format == 'excel':
            excel_file = output_dir / f'{base_name}.xlsx'
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Posts', index=False)
                if include_brand_summary and not brand_df.empty:
                    brand_df.to_excel(writer, sheet_name='Brand_Summary', index=False)
            print(f"✅ Saved Excel file to {excel_file}")
        
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv', 'json', or 'excel'")
    
    def print_summary(self):
        """
        Print a summary of the analysis results.
        """
        if not self.posts_data:
            print("No analysis data available. Run analyze_posts() first.")
            return
        
        print("\n" + "="*70)
        print(f"INSTAGRAM BRAND ANALYSIS - @{self.username}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        print(f"\n📊 PROFILE STATS")
        if self.profile:
            print(f"   Followers: {self.profile.followers:,}")
            print(f"   Following: {self.profile.followees:,}")
            print(f"   Total Posts: {self.profile.mediacount:,}")
        
        print(f"\n📈 ANALYSIS SUMMARY")
        print(f"   Posts Analyzed: {len(self.posts_data)}")
        print(f"   Brands Mentioned: {len(self.brand_mentions)}")
        print(f"   Total Brand Mentions: {sum(len(codes) for codes in self.brand_mentions.values())}")
        
        if self.brand_mentions:
            print(f"\n🏆 TOP BRANDS MENTIONED")
            brand_df = self.get_brand_summary()
            top_brands = brand_df.head(10)
            
            for _, row in top_brands.iterrows():
                print(f"   {row['brand']}: {row['mentions']} mentions "
                      f"({row['total_engagement']:,} total engagement)")
        
        if self.posts_data and 'likes' in self.posts_data[0]:
            total_likes = sum(p['likes'] for p in self.posts_data)
            total_comments = sum(p['comments'] for p in self.posts_data)
            avg_engagement = (total_likes + total_comments) / len(self.posts_data)
            
            print(f"\n💬 ENGAGEMENT METRICS")
            print(f"   Total Likes: {total_likes:,}")
            print(f"   Total Comments: {total_comments:,}")
            print(f"   Avg Engagement/Post: {avg_engagement:,.0f}")
        
        print("\n" + "="*70)


def analyze_influencer(username: str, max_posts: int = 50, 
                       brands: Optional[List[str]] = None,
                       output_format: str = 'csv',
                       login_required: bool = False) -> InstagramBrandAnalyzer:
    """
    Quick function to analyze an influencer profile.
    
    Args:
        username: Instagram username to analyze
        max_posts: Maximum number of posts to analyze
        brands: Custom list of brands (uses defaults if None)
        output_format: Export format ('csv', 'json', 'excel')
        login_required: Whether login is required
        
    Returns:
        InstagramBrandAnalyzer instance with results
    """
    analyzer = InstagramBrandAnalyzer(username=username, brands=brands)
    
    if login_required:
        print("⚠️ Login required. Please use the analyzer directly with login() method.")
        return analyzer
    
    analyzer.load_profile()
    analyzer.analyze_posts(max_posts=max_posts)
    analyzer.print_summary()
    analyzer.export_results(username, format=output_format)
    
    return analyzer


if __name__ == '__main__':
    # Example usage
    print("Instagram Brand Analyzer")
    print("=" * 50)
    
    # Analyze khalidwalb profile
    analyzer = analyze_influencer(
        username='khalidwalb',
        max_posts=50,
        output_format='csv'
    )
