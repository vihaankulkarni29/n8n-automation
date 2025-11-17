import pandas as pd

print("="*80)
print("INSTAGRAM INFLUENCER BRAND ANALYSIS - FINAL SUMMARY")
print("="*80)

# Load all data
posts_df = pd.read_csv('data/khalidwalb_posts.csv')
mentions_df = pd.read_csv('data/khalidwalb_brand_mentions.csv')
brands_df = pd.read_csv('data/khalidwalb_brands.csv')

influencer = posts_df['influencer_handle'].iloc[0]

print(f"\nINFLUENCER: @{influencer}")
print(f"Profile: https://instagram.com/{influencer}")

print(f"\nDATA COLLECTED:")
print(f"  Posts analyzed: {len(posts_df)}")
print(f"  Brand mentions found: {len(mentions_df)}")
print(f"  Unique brands: {len(brands_df)}")

print(f"\nFILES CREATED:")
print(f"  1. khalidwalb_posts.csv")
print(f"     - {len(posts_df)} posts with full details")
print(f"     - Columns: influencer_handle, shortcode, url, date, caption, hashtags,")
print(f"                tagged_users, brands_mentioned, likes, comments, engagement")
print(f"  ")
print(f"  2. khalidwalb_brand_mentions.csv")
print(f"     - {len(mentions_df)} product-brand mentions")
print(f"     - Columns: influencer_handle, brand, product, context, pattern_type,")
print(f"                post_shortcode, post_url, date, likes, comments, engagement")
print(f"  ")
print(f"  3. khalidwalb_brands.csv")
print(f"     - {len(brands_df)} unique brands summary")
print(f"     - Columns: influencer_handle, brand_account, products_mentioned,")
print(f"                total_mentions, total_engagement, total_likes,")
print(f"                total_comments, avg_engagement")

print(f"\nBRAND BREAKDOWN:")
print("-"*80)
for _, row in brands_df.iterrows():
    print(f"  @{row['brand_account']:<20} | {row['products_mentioned']:<20} | {row['total_mentions']} mentions | {row['total_engagement']:,} engagement")

print(f"\nQUALITY METRICS:")
print(f"  Avg engagement per post: {posts_df['engagement'].mean():,.0f}")
print(f"  Avg engagement per brand mention: {mentions_df['engagement'].mean():,.0f}")
print(f"  Success rate: {len(mentions_df)/len(posts_df)*100:.1f}% of posts have brand mentions")

print(f"\nSCALABILITY:")
print(f"  Current: 50 posts analyzed")
print(f"  Potential: 178 total posts on profile")
print(f"  Estimated: ~24-25 total brand mentions possible")

print("\n" + "="*80)
print("SYSTEM READY FOR ANY INFLUENCER ANALYSIS!")
print("="*80)
print("\nNext steps:")
print("  1. Analyze more posts from @khalidwalb (wait for rate limit reset)")
print("  2. Or analyze a different influencer")
print("  3. Use the same pipeline for any Instagram profile")
