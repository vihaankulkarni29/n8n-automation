"""
Extract all brand mentions from Instagram captions
Identifies brands using capitalization patterns, @ mentions, and keywords
"""

import re
import pandas as pd
from pathlib import Path
from typing import List, Set, Dict


class BrandExtractor:
    """
    Extract brand names from Instagram captions using multiple strategies.
    """
    
    # Common non-brand words to filter out
    IGNORE_WORDS = {
        'I', 'LOVE', 'THE', 'NEW', 'THIS', 'THAT', 'VERY', 'MUCH', 'REALLY',
        'JUST', 'HERE', 'BOTH', 'MORE', 'BACK', 'WELL', 'BEST', 'MOST',
        'SOME', 'GOOD', 'MANY', 'FIRST', 'LAST', 'LONG', 'GREAT', 'LITTLE',
        'OWN', 'OTHER', 'OLD', 'RIGHT', 'BIG', 'HIGH', 'DIFFERENT', 'SMALL',
        'LARGE', 'NEXT', 'EARLY', 'YOUNG', 'IMPORTANT', 'FEW', 'PUBLIC',
        'BAD', 'SAME', 'ABLE', 'AD', 'BBG', 'IM', 'ID', 'ME', 'MY', 'WE',
        'YOU', 'YOUR', 'HE', 'HIM', 'HIS', 'SHE', 'HER', 'IT', 'ITS',
        'THEY', 'THEM', 'THEIR', 'AM', 'IS', 'ARE', 'WAS', 'WERE', 'BE',
        'BEEN', 'BEING', 'HAVE', 'HAS', 'HAD', 'DO', 'DOES', 'DID',
        'WILL', 'WOULD', 'SHOULD', 'COULD', 'MAY', 'MIGHT', 'MUST',
        'CAN', 'CANNOT', 'CANT', 'DONT', 'DOESNT', 'DIDNT', 'WONT',
        'ISNT', 'ARENT', 'WASNT', 'WERENT', 'HASNT', 'HAVENT', 'HADNT',
        'AND', 'OR', 'BUT', 'IF', 'THEN', 'THAN', 'SO', 'BECAUSE',
        'AS', 'WHILE', 'WHEN', 'WHERE', 'WHY', 'HOW', 'WHICH', 'WHO',
        'WHAT', 'WHOSE', 'WHOM', 'ALL', 'EACH', 'EVERY', 'BOTH', 'FEW',
        'MORE', 'MOST', 'SOME', 'ANY', 'NO', 'NOT', 'ONLY', 'ALSO',
        'VERY', 'TOO', 'AGAIN', 'NEVER', 'ALWAYS', 'OFTEN', 'REELS',
        'EXPLORE', 'EXPLOREPAGE', 'AESTHETIC', 'FORYOU', 'INSTAGRAM',
        'LITERALLY', 'ABSOLUTELY', 'EXACTLY', 'PROBABLY', 'DEFINITELY',
        'ACTUALLY', 'BASICALLY', 'HONESTLY', 'SERIOUSLY', 'CLEARLY',
        'HAPPY', 'EXCITED', 'BELIEVE', 'TRUST', 'GUESS', 'KNOW', 'KNEW',
        'THINK', 'THOUGHT', 'FEEL', 'FELT', 'WANT', 'WANTED', 'NEED',
        'NEEDED', 'LIKE', 'LIKED', 'LOVE', 'LOVED', 'HATE', 'HATED',
        'SEE', 'SAW', 'LOOK', 'LOOKED', 'SHOW', 'SHOWED', 'TELL', 'TOLD',
        'ASK', 'ASKED', 'GIVE', 'GAVE', 'GET', 'GOT', 'TAKE', 'TOOK',
        'MAKE', 'MADE', 'FIND', 'FOUND', 'USE', 'USED', 'WORK', 'WORKED',
        'CALL', 'CALLED', 'TRY', 'TRIED', 'KEEP', 'KEPT', 'LET', 'BEGIN',
        'BEGAN', 'SEEM', 'SEEMED', 'HELP', 'HELPED', 'TALK', 'TALKED',
        'TURN', 'TURNED', 'START', 'STARTED', 'MIGHT', 'SHOW', 'PART',
        'AGAINST', 'BETWEEN', 'DURING', 'BEFORE', 'AFTER', 'ABOVE',
        'BELOW', 'FROM', 'UP', 'DOWN', 'IN', 'OUT', 'ON', 'OFF', 'OVER',
        'UNDER', 'AGAIN', 'FURTHER', 'ONCE', 'HERE', 'THERE', 'ALL',
        'OUT', 'REALLY', 'SUPER', 'MUCH', 'AROUND', 'COLLECTION',
        'BEAUTIFUL', 'DETAILS', 'RELEASE', 'VIDEO', 'PICTURES', 'GUYS',
        'BHAI', 'YAAR', 'KEK', 'LOL', 'LMAO', 'OMG', 'BTW', 'TBH',
        'IMO', 'IMHO', 'FYI', 'ASAP', 'DIY', 'FAQ', 'RSVP', 'PS',
        'LIVE', 'NEW', 'BRAND', 'BRANDS', 'SEASON', 'WINTER', 'WINTERS',
        'SUMMER', 'SUMMERS', 'SPRING', 'FALL', 'AUTUMN', 'YEAR', 'YEARS',
        'MONTH', 'MONTHS', 'WEEK', 'WEEKS', 'DAY', 'DAYS', 'TODAY',
        'TOMORROW', 'YESTERDAY', 'NOW', 'THEN', 'SOON', 'LATER', 'NEVER',
        'EDITION', 'REVIEW', 'UNBOXING', 'HAUL', 'LOOKBOOK', 'OOTD',
        'OUTFIT', 'FIT', 'STYLE', 'FASHION', 'LOOK', 'LOOKS', 'WEAR',
        'WEARING', 'WORE', 'CLOTHES', 'CLOTHING', 'DRESS', 'DRESSED'
    }
    
    def __init__(self, posts_csv: str):
        """
        Initialize with path to posts CSV file.
        
        Args:
            posts_csv: Path to CSV file with Instagram posts
        """
        self.posts_csv = posts_csv
        self.df = pd.read_csv(posts_csv)
        self.brand_data = []
        
    def extract_at_mentions(self, text: str) -> Set[str]:
        """
        Extract @ mentions from text (e.g., @lenskart).
        
        Args:
            text: Caption text
            
        Returns:
            Set of brand mentions (without @)
        """
        if not text or pd.isna(text):
            return set()
        
        # Find all @ mentions
        mentions = re.findall(r'@(\w+)', text)
        return set(mentions)
    
    def extract_capitalized_words(self, text: str) -> Set[str]:
        """
        Extract capitalized words that might be brand names.
        
        Args:
            text: Caption text
            
        Returns:
            Set of potential brand names
        """
        if not text or pd.isna(text):
            return set()
        
        brands = set()
        
        # Only look for well-known brand patterns:
        # 1. Multi-word Title Case brands (e.g., Louis Vuitton, Tom Ford)
        multi_word = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', text)
        for match in multi_word:
            if match.upper() not in self.IGNORE_WORDS:
                brands.add(match)
        
        # 2. Short ALL CAPS that are likely brands (3-6 letters, appears in specific contexts)
        # Only include if it appears near fashion/product keywords
        fashion_context = re.findall(
            r'\b(LOTTO|GAP|HOP|ZARA|DKNY|FILA|NIKE|PUMA|ASOS|SHEIN)\b',
            text
        )
        brands.update(fashion_context)
        
        return brands
    
    def extract_branded_hashtags(self, hashtags: str) -> Set[str]:
        """
        Extract brand names from hashtags.
        
        Args:
            hashtags: Comma-separated hashtags
            
        Returns:
            Set of potential brand names
        """
        if not hashtags or pd.isna(hashtags):
            return set()
        
        brands = set()
        tags = hashtags.split(',')
        
        # Known brand-related hashtags
        brand_keywords = [
            'gap', 'levi', 'levis', 'fastrack', 'nike', 'adidas', 'puma',
            'gucci', 'dior', 'chanel', 'louis', 'vuitton', 'lenskart',
            'oneplus', 'msi', 'skechers', 'converse', 'jordan', 'yeezy',
            'zara', 'h&m', 'uniqlo', 'supreme', 'offwhite', 'balenciaga'
        ]
        
        for tag in tags:
            tag = tag.strip()
            
            # Check if tag contains any brand keyword
            tag_lower = tag.lower()
            for brand_word in brand_keywords:
                if brand_word in tag_lower:
                    brands.add(tag)
                    break
        
        return brands
    
    def analyze_all_posts(self) -> pd.DataFrame:
        """
        Analyze all posts to extract brand mentions.
        
        Returns:
            DataFrame with brand mentions per post
        """
        results = []
        
        for _, row in self.df.iterrows():
            shortcode = row.get('shortcode', '')
            url = row.get('url', '')
            date = row.get('date', '')
            caption = row.get('caption', '')
            hashtags = row.get('hashtags', '')
            
            # Extract brands using multiple methods
            at_mentions = self.extract_at_mentions(caption)
            cap_words = self.extract_capitalized_words(caption)
            hash_brands = self.extract_branded_hashtags(hashtags)
            
            # Combine all brands
            all_brands = at_mentions | cap_words | hash_brands
            
            # Store each brand mention separately
            if all_brands:
                for brand in all_brands:
                    results.append({
                        'brand': brand,
                        'shortcode': shortcode,
                        'url': url,
                        'date': date,
                        'caption_preview': caption[:100] + '...' if len(caption) > 100 else caption,
                        'source': self._get_source_type(brand, at_mentions, cap_words, hash_brands)
                    })
        
        return pd.DataFrame(results)
    
    def _get_source_type(self, brand: str, at_mentions: Set, 
                        cap_words: Set, hash_brands: Set) -> str:
        """
        Determine where the brand mention came from.
        
        Returns:
            Source type: 'at_mention', 'caption', or 'hashtag'
        """
        if brand in at_mentions:
            return 'at_mention'
        elif brand in hash_brands:
            return 'hashtag'
        else:
            return 'caption'
    
    def get_brand_summary(self, brand_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create summary of brand mentions.
        
        Args:
            brand_df: DataFrame from analyze_all_posts()
            
        Returns:
            Aggregated brand statistics
        """
        summary = brand_df.groupby('brand').agg({
            'shortcode': 'count',
            'url': lambda x: ', '.join(x.head(5))  # First 5 URLs
        }).reset_index()
        
        summary.columns = ['brand', 'mention_count', 'sample_posts']
        summary = summary.sort_values('mention_count', ascending=False)
        
        return summary
    
    def export_results(self, output_dir: str = 'data'):
        """
        Analyze and export brand mentions to CSV files.
        
        Args:
            output_dir: Directory to save output files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print("🔍 Extracting all brand mentions from captions...")
        
        # Analyze all posts
        brand_df = self.analyze_all_posts()
        
        if brand_df.empty:
            print("❌ No brands found in captions")
            return
        
        # Get summary
        summary_df = self.get_brand_summary(brand_df)
        
        # Save detailed brand mentions
        detailed_file = output_path / 'khalidwalb_all_brand_mentions.csv'
        brand_df.to_csv(detailed_file, index=False)
        print(f"✅ Saved detailed brand mentions to {detailed_file}")
        print(f"   Total mentions: {len(brand_df)}")
        
        # Save brand summary
        summary_file = output_path / 'khalidwalb_brand_summary.csv'
        summary_df.to_csv(summary_file, index=False)
        print(f"✅ Saved brand summary to {summary_file}")
        print(f"   Unique brands: {len(summary_df)}")
        
        # Print top brands
        print(f"\n📊 TOP 10 BRANDS MENTIONED:")
        for _, row in summary_df.head(10).iterrows():
            print(f"   {row['brand']}: {row['mention_count']} mentions")
        
        return brand_df, summary_df


def extract_brands_simple(posts_csv: str = 'data/khalidwalb_posts.csv') -> pd.DataFrame:
    """
    Simple function to extract just @mentions as brands.
    
    Args:
        posts_csv: Path to posts CSV file
        
    Returns:
        DataFrame with brand mentions
    """
    df = pd.read_csv(posts_csv)
    
    brand_mentions = []
    
    for _, row in df.iterrows():
        caption = row.get('caption', '')
        
        if not caption or pd.isna(caption):
            continue
        
        # Extract @mentions
        mentions = re.findall(r'@(\w+)', str(caption))
        
        for mention in mentions:
            brand_mentions.append({
                'brand_account': mention,
                'post_shortcode': row.get('shortcode', ''),
                'post_url': row.get('url', ''),
                'date': row.get('date', ''),
                'likes': row.get('likes', 0),
                'comments': row.get('comments', 0),
                'engagement': row.get('engagement', 0)
            })
    
    return pd.DataFrame(brand_mentions)


def main():
    """
    Main function to extract brands from khalidwalb posts.
    Focus on @mentions which are actual brand accounts.
    """
    posts_file = 'data/khalidwalb_posts.csv'
    
    if not Path(posts_file).exists():
        print(f"❌ Posts file not found: {posts_file}")
        print("   Run the Instagram analyzer first to generate posts data.")
        return
    
    print("🔍 Extracting brand @mentions from captions...")
    print("="*70)
    
    # Extract simple @mentions (most reliable)
    brand_df = extract_brands_simple(posts_file)
    
    if brand_df.empty:
        print("❌ No brand @mentions found")
        return
    
    # Calculate summary
    summary = brand_df.groupby('brand_account').agg({
        'post_shortcode': 'count',
        'engagement': 'sum',
        'likes': 'sum',
        'comments': 'sum'
    }).reset_index()
    
    summary.columns = ['brand_account', 'mentions', 'total_engagement', 'total_likes', 'total_comments']
    summary['avg_engagement'] = (summary['total_engagement'] / summary['mentions']).round(0)
    summary = summary.sort_values('mentions', ascending=False)
    
    # Save results
    output_dir = Path('data')
    
    # Detailed mentions
    detailed_file = output_dir / 'khalidwalb_brand_mentions.csv'
    brand_df.to_csv(detailed_file, index=False)
    print(f"✅ Saved detailed mentions to: {detailed_file}")
    print(f"   Total brand tags: {len(brand_df)}")
    
    # Summary
    summary_file = output_dir / 'khalidwalb_brands.csv'
    summary.to_csv(summary_file, index=False)
    print(f"✅ Saved brand summary to: {summary_file}")
    print(f"   Unique brands: {len(summary)}")
    
    # Print top brands
    print(f"\n📊 TOP BRANDS MENTIONED (@accounts):")
    print(f"{'Brand Account':<30} {'Mentions':<10} {'Total Engagement':<20} {'Avg Engagement':<15}")
    print("-"*75)
    for _, row in summary.head(15).iterrows():
        print(f"@{row['brand_account']:<29} {row['mentions']:<10} {row['total_engagement']:>10,}          {row['avg_engagement']:>10,.0f}")
    
    print("\n" + "="*70)
    print("BRAND EXTRACTION COMPLETE!")
    print("="*70)


if __name__ == '__main__':
    main()
