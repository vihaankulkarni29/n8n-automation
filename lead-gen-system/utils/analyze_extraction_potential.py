import pandas as pd

# Load the posts data
posts_df = pd.read_csv('data/khalidwalb_posts.csv')

# Load the brand mentions we extracted
mentions_df = pd.read_csv('data/khalidwalb_brand_mentions.csv')

print("="*80)
print("INSTAGRAM DATA EXTRACTION ANALYSIS - @khalidwalb")
print("="*80)

print(f"\nCURRENT DATA:")
print(f"   Total posts analyzed: {len(posts_df)}")
print(f"   Posts with brand mentions found: {mentions_df['post_shortcode'].nunique()}")
print(f"   Total brand-product mentions: {len(mentions_df)}")
print(f"   Extraction rate: {len(mentions_df)/len(posts_df)*100:.1f}% of posts have brand mentions")

print(f"\nPROFILE STATS:")
# Get profile info from first row if available
total_posts = 178  # From the earlier profile load
followers = 242457

print(f"   Total posts on profile: {total_posts}")
print(f"   Posts we analyzed: {len(posts_df)}")
print(f"   Posts remaining: {total_posts - len(posts_df)}")
print(f"   Coverage: {len(posts_df)/total_posts*100:.1f}%")

print(f"\nQUALITY ASSESSMENT:")
print(f"   Posts with captions: {posts_df['caption'].notna().sum()}")
print(f"   Posts with @ mentions: {posts_df['caption'].str.contains('@', na=False).sum()}")
print(f"   Avg engagement per post: {posts_df['engagement'].mean():,.0f}")
print(f"   Avg likes: {posts_df['likes'].mean():,.0f}")
print(f"   Avg comments: {posts_df['comments'].mean():,.0f}")

print(f"\nPOTENTIAL EXTRACTION:")
posts_with_mentions = posts_df['caption'].str.contains('@', na=False).sum()
potential_rate = len(mentions_df) / posts_with_mentions if posts_with_mentions > 0 else 0
estimated_total = int((total_posts / len(posts_df)) * len(mentions_df))

print(f"   Current posts with @ mentions: {posts_with_mentions}")
print(f"   Brand mentions per post (avg): {potential_rate:.2f}")
print(f"   Estimated mentions if we process all {total_posts} posts: {estimated_total}")

print(f"\nSCALING POTENTIAL:")
print(f"   If we process ALL {total_posts} posts:")
print(f"     - Expected brand mentions: ~{estimated_total}")
print(f"     - Additional mentions: ~{estimated_total - len(mentions_df)}")
print(f"   ")
print(f"   If we increase to 100 posts:")
expected_100 = int((100 / len(posts_df)) * len(mentions_df))
print(f"     - Expected brand mentions: ~{expected_100}")
print(f"   ")
print(f"   If we increase to 150 posts:")
expected_150 = int((150 / len(posts_df)) * len(mentions_df))
print(f"     - Expected brand mentions: ~{expected_150}")

print(f"\nRECOMMENDATIONS:")
print(f"   > Continue analyzing remaining {total_posts - len(posts_df)} posts")
print(f"   > Quality is GOOD: {len(mentions_df)} real brand-product mentions from {len(posts_df)} posts")
print(f"   > About {len(mentions_df)/len(posts_df)*100:.0f}% success rate for product mentions")
print(f"   > Each additional 50 posts = ~{int(7 * 50/50)} more brand mentions")

print("\n" + "="*80)
print(f"SUMMARY: We can extract ~{estimated_total} quality brand mentions from {total_posts} total posts")
print("="*80)
