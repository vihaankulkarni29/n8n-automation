import pandas as pd

# Read the cleaned mentions
df = pd.read_csv('data/khalidwalb_brand_mentions.csv')

# Create brand summary
summary = df.groupby('brand').agg({
    'product': lambda x: ', '.join(sorted(set(str(p) for p in x if pd.notna(p)))),
    'post_shortcode': 'count',
    'engagement': 'sum',
    'likes': 'sum',
    'comments': 'sum'
}).reset_index()

summary.columns = ['brand_account', 'products_mentioned', 'total_mentions', 'total_engagement', 'total_likes', 'total_comments']
summary['avg_engagement'] = (summary['total_engagement'] / summary['total_mentions']).round(0).astype(int)
summary = summary.sort_values('total_mentions', ascending=False)

# Save summary
summary.to_csv('data/khalidwalb_brands.csv', index=False)

print("="*80)
print("BRAND SUMMARY - Products Mentioned in Captions")
print("="*80)
print(f"\nTotal unique brands: {len(summary)}")
print(f"Total product mentions: {len(df)}")

print("\nBRAND BREAKDOWN:")
print("-"*80)
print(f"{'Brand':<25} {'Products':<30} {'Mentions':<10} {'Engagement':<12}")
print("-"*80)

for _, row in summary.iterrows():
    products_short = row['products_mentioned'][:28] + '..' if len(row['products_mentioned']) > 28 else row['products_mentioned']
    print(f"@{row['brand_account']:<24} {products_short:<30} {row['total_mentions']:<10} {row['total_engagement']:>10,}")

print("\n" + "="*80)
print("Files created:")
print("  - khalidwalb_brand_mentions.csv (detailed with context)")
print("  - khalidwalb_brands.csv (summary)")
print("="*80)
