import pandas as pd

# Update posts CSV to include influencer handle
posts_df = pd.read_csv('data/khalidwalb_posts.csv')
if 'influencer_handle' not in posts_df.columns:
    posts_df.insert(0, 'influencer_handle', 'khalidwalb')
    posts_df.to_csv('data/khalidwalb_posts.csv', index=False)
    print("✅ Updated khalidwalb_posts.csv with influencer_handle column")

# Update brand mentions CSV
mentions_df = pd.read_csv('data/khalidwalb_brand_mentions.csv')
if 'influencer_handle' in mentions_df.columns:
    mentions_df['influencer_handle'] = 'khalidwalb'
    mentions_df.to_csv('data/khalidwalb_brand_mentions.csv', index=False)
    print("✅ Updated khalidwalb_brand_mentions.csv with correct influencer_handle")

# Update brand summary CSV
try:
    summary_df = pd.read_csv('data/khalidwalb_brands.csv')
    if 'influencer_handle' not in summary_df.columns:
        summary_df.insert(0, 'influencer_handle', 'khalidwalb')
    else:
        summary_df['influencer_handle'] = 'khalidwalb'
    summary_df.to_csv('data/khalidwalb_brands.csv', index=False)
    print("✅ Updated khalidwalb_brands.csv with influencer_handle column")
except:
    pass

print("\n" + "="*70)
print("All CSV files now include 'influencer_handle' = 'khalidwalb'")
print("="*70)

# Show sample
print("\nSample from khalidwalb_brand_mentions.csv:")
print(mentions_df[['influencer_handle', 'brand', 'product', 'engagement']].head(5).to_string(index=False))
