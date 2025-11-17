"""
Extract product and brand mentions from Instagram captions
Identifies brands mentioned in natural language patterns like:
- "from @brand"
- "wearing X"
- "the shirt is from X"
- "pants from X"
- "shoes are X"
"""

import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional


class ProductBrandExtractor:
    """
    Extract product-specific brand mentions from Instagram captions.
    Focuses on outfit/product breakdowns like "the shoes from X", "wearing Y brand".
    """
    
    # Product categories to look for
    PRODUCT_KEYWORDS = [
        # Clothing
        'shirt', 'tshirt', 't-shirt', 'tee', 'top', 'jacket', 'coat', 'blazer',
        'hoodie', 'sweatshirt', 'sweater', 'cardigan', 'vest',
        'pants', 'jeans', 'trousers', 'shorts', 'joggers', 'cargo',
        'kurta', 'kurti', 'sherwani', 'dhoti',
        
        # Footwear
        'shoes', 'sneakers', 'sneaker', 'boots', 'sandals', 'slippers',
        'loafers', 'oxfords', 'trainers',
        
        # Accessories
        'watch', 'glasses', 'sunglasses', 'bag', 'backpack', 'wallet',
        'belt', 'hat', 'cap', 'beanie', 'scarf', 'tie', 'bowtie',
        'necklace', 'chain', 'bracelet', 'ring', 'earrings',
        
        # Grooming
        'fragrance', 'perfume', 'cologne', 'deodorant',
        
        # General
        'outfit', 'fit', 'look', 'collection', 'piece'
    ]
    
    def __init__(self, posts_csv: str):
        """
        Initialize with path to posts CSV file.
        
        Args:
            posts_csv: Path to CSV file with Instagram posts
        """
        self.posts_csv = posts_csv
        self.df = pd.read_csv(posts_csv)
        
    def extract_brand_patterns(self, text: str) -> List[Dict[str, str]]:
        """
        Extract brand mentions using natural language patterns.
        
        Patterns:
        - "from @brand"
        - "from brand's collection"
        - "wearing brand"
        - "the shoes from brand"
        - "shirt is brand"
        
        Args:
            text: Caption text
            
        Returns:
            List of dicts with {brand, product, context}
        """
        if not text or pd.isna(text):
            return []
        
        mentions = []
        text_lower = text.lower()
        
        # Pattern 1: "from @brand" or "from brand's"
        # Example: "glasses from @lenskart's HIP-HOP Collection"
        pattern1 = r'(?:from|by)\s+@?([a-zA-Z0-9_]+)(?:\'s|s)?'
        matches1 = re.finditer(pattern1, text, re.IGNORECASE)
        
        for match in matches1:
            brand = match.group(1)
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].strip()
            
            # Try to find product mentioned nearby
            product = self._find_nearby_product(text, match.start())
            
            mentions.append({
                'brand': brand,
                'product': product,
                'context': context,
                'pattern': 'from/by'
            })
        
        # Pattern 2: "@brand" followed by possessive or collection
        # Example: "@lenskart's HIP-HOP Collection"
        pattern2 = r'@([a-zA-Z0-9_]+)(?:\'s|s)?\s+([A-Z][A-Z\-\s]+(?:Collection|Edition|Series|Line))'
        matches2 = re.finditer(pattern2, text, re.IGNORECASE)
        
        for match in matches2:
            brand = match.group(1)
            collection = match.group(2).strip()
            
            mentions.append({
                'brand': brand,
                'product': collection,
                'context': match.group(0),
                'pattern': 'collection'
            })
        
        # Pattern 3: Product + "from/by/is" + Brand
        # Example: "the Zeenat Aman t-shirt from Brand"
        for product_keyword in self.PRODUCT_KEYWORDS:
            pattern3 = rf'(?:the\s+)?(?:\w+\s+)?{product_keyword}(?:\s+\w+)?\s+(?:from|by|is|are)\s+@?([a-zA-Z0-9_]+)'
            matches3 = re.finditer(pattern3, text_lower, re.IGNORECASE)
            
            for match in matches3:
                brand = match.group(1)
                start = max(0, match.start())
                end = min(len(text), match.end() + 20)
                context = text[start:end].strip()
                
                mentions.append({
                    'brand': brand,
                    'product': product_keyword,
                    'context': context,
                    'pattern': 'product_from'
                })
        
        # Pattern 4: "wearing Brand" or "wearing Brand's"
        pattern4 = r'wearing\s+@?([a-zA-Z0-9_]+)(?:\'s|s)?'
        matches4 = re.finditer(pattern4, text, re.IGNORECASE)
        
        for match in matches4:
            brand = match.group(1)
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 30)
            context = text[start:end].strip()
            
            product = self._find_nearby_product(text, match.start())
            
            mentions.append({
                'brand': brand,
                'product': product or 'clothing',
                'context': context,
                'pattern': 'wearing'
            })
        
        # Pattern 5: Direct @mention without "from" but near product words
        all_at_mentions = re.finditer(r'@([a-zA-Z0-9_]+)', text)
        
        for mention in all_at_mentions:
            brand = mention.group(1)
            
            # Check if near a product keyword
            window_start = max(0, mention.start() - 50)
            window_end = min(len(text), mention.end() + 50)
            window = text[window_start:window_end].lower()
            
            product_found = None
            for product_keyword in self.PRODUCT_KEYWORDS:
                if product_keyword in window:
                    product_found = product_keyword
                    break
            
            if product_found:
                start = max(0, mention.start() - 30)
                end = min(len(text), mention.end() + 30)
                context = text[start:end].strip()
                
                # Avoid duplicates from other patterns
                if not any(m['brand'].lower() == brand.lower() and m.get('product') == product_found 
                          for m in mentions):
                    mentions.append({
                        'brand': brand,
                        'product': product_found,
                        'context': context,
                        'pattern': 'proximity'
                    })
        
        return mentions
    
    def _find_nearby_product(self, text: str, position: int, window: int = 50) -> Optional[str]:
        """
        Find product keyword near a given position in text.
        
        Args:
            text: Caption text
            position: Position to search around
            window: Search window size
            
        Returns:
            Product keyword if found, None otherwise
        """
        start = max(0, position - window)
        end = min(len(text), position + window)
        window_text = text[start:end].lower()
        
        for product in self.PRODUCT_KEYWORDS:
            if product in window_text:
                return product
        
        return None
    
    def analyze_all_posts(self) -> pd.DataFrame:
        """
        Analyze all posts to extract product-brand mentions.
        
        Returns:
            DataFrame with detailed brand mentions
        """
        results = []
        
        # Get influencer handle from the CSV if available
        influencer_handle = self.df.get('influencer_handle', pd.Series(['unknown'] * len(self.df))).iloc[0] if len(self.df) > 0 else 'unknown'
        
        for _, row in self.df.iterrows():
            shortcode = row.get('shortcode', '')
            url = row.get('url', '')
            date = row.get('date', '')
            caption = row.get('caption', '')
            likes = row.get('likes', 0)
            comments = row.get('comments', 0)
            engagement = row.get('engagement', 0)
            
            # Extract brand mentions
            mentions = self.extract_brand_patterns(caption)
            
            for mention in mentions:
                results.append({
                    'influencer_handle': influencer_handle,
                    'brand': mention['brand'],
                    'product': mention.get('product', 'unknown'),
                    'context': mention['context'][:150],  # Limit context length
                    'pattern_type': mention['pattern'],
                    'post_shortcode': shortcode,
                    'post_url': url,
                    'date': date,
                    'likes': likes,
                    'comments': comments,
                    'engagement': engagement
                })
        
        return pd.DataFrame(results)
    
    def get_brand_summary(self, mentions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create summary of brand mentions with product breakdown.
        
        Args:
            mentions_df: DataFrame from analyze_all_posts()
            
        Returns:
            Aggregated brand statistics
        """
        if mentions_df.empty:
            return pd.DataFrame()
        
        # Get influencer handle
        influencer_handle = mentions_df['influencer_handle'].iloc[0] if 'influencer_handle' in mentions_df.columns and len(mentions_df) > 0 else 'unknown'
        
        # Group by brand
        summary = mentions_df.groupby('brand').agg({
            'post_shortcode': 'count',
            'product': lambda x: ', '.join(sorted(set(str(p) for p in x if pd.notna(p)))),
            'engagement': 'sum',
            'likes': 'sum',
            'comments': 'sum'
        }).reset_index()
        
        summary.columns = ['brand', 'mentions', 'products', 'total_engagement', 'total_likes', 'total_comments']
        summary.insert(0, 'influencer_handle', influencer_handle)
        summary['avg_engagement'] = (summary['total_engagement'] / summary['mentions']).round(0)
        summary = summary.sort_values('mentions', ascending=False)
        
        return summary
    
    def export_results(self, output_dir: str = 'data'):
        """
        Analyze and export brand-product mentions.
        
        Args:
            output_dir: Directory to save output files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print("🔍 Extracting product-brand mentions from captions...")
        print("   Looking for patterns like: 'from @brand', 'wearing X', 'shirt from Y'")
        print("="*70)
        
        # Analyze all posts
        mentions_df = self.analyze_all_posts()
        
        if mentions_df.empty:
            print("❌ No product-brand mentions found")
            return
        
        # Remove duplicates (same brand in same post)
        mentions_df = mentions_df.drop_duplicates(subset=['brand', 'post_shortcode', 'product'])
        
        # Get summary
        summary_df = self.get_brand_summary(mentions_df)
        
        # Save detailed mentions
        detailed_file = output_path / 'khalidwalb_all_brand_mentions.csv'
        mentions_df.to_csv(detailed_file, index=False, encoding='utf-8-sig')
        print(f"✅ Saved detailed mentions to: {detailed_file}")
        print(f"   Total product-brand mentions: {len(mentions_df)}")
        
        # Save summary
        summary_file = output_path / 'khalidwalb_brand_summary.csv'
        summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
        print(f"✅ Saved brand summary to: {summary_file}")
        print(f"   Unique brands: {len(summary_df)}")
        
        # Print detailed results
        print(f"\n📊 TOP BRANDS WITH PRODUCT MENTIONS:")
        print(f"{'Brand':<25} {'Mentions':<10} {'Products':<40} {'Engagement':<12}")
        print("-"*90)
        
        for _, row in summary_df.head(20).iterrows():
            products_display = row['products'][:35] + '...' if len(row['products']) > 35 else row['products']
            print(f"@{row['brand']:<24} {row['mentions']:<10} {products_display:<40} {row['total_engagement']:>10,}")
        
        # Show sample mentions
        print(f"\n📝 SAMPLE PRODUCT MENTIONS:")
        print("-"*90)
        for _, row in mentions_df.head(10).iterrows():
            print(f"\n• @{row['brand']} - {row['product']}")
            print(f"  Context: \"{row['context']}\"")
            print(f"  Post: {row['post_url']}")
        
        print("\n" + "="*70)
        print("EXTRACTION COMPLETE!")
        print("="*70)
        
        return mentions_df, summary_df


def main():
    """
    Main function to extract product-brand mentions from khalidwalb posts.
    """
    posts_file = 'data/khalidwalb_posts.csv'
    
    if not Path(posts_file).exists():
        print(f"❌ Posts file not found: {posts_file}")
        print("   Run the Instagram analyzer first to generate posts data.")
        return
    
    extractor = ProductBrandExtractor(posts_file)
    extractor.export_results()


if __name__ == '__main__':
    main()
