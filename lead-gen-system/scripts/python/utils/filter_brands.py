import pandas as pd

# Read the mentions
df = pd.read_csv('data/khalidwalb_all_brand_mentions.csv')

# Filter out common words that aren't brands
exclude_brands = ['the', 'them', 'something', 'myself', '2024', '2023', '2022', 'this', 'that']
real_brands = df[~df['brand'].str.lower().isin(exclude_brands)]

print("="*80)
print("REAL PRODUCT-BRAND MENTIONS FROM CAPTIONS")
print("="*80)
print(f"\nTotal real mentions: {len(real_brands)}")
print(f"Unique brands: {real_brands['brand'].nunique()}")

print("\nBRAND MENTIONS WITH PRODUCTS:")
print("-"*80)

for _, row in real_brands.iterrows():
    product = row['product'] if pd.notna(row['product']) else 'general'
    print(f"\n@{row['brand']}")
    print(f"  Product: {product}")
    print(f"  Context: {row['context'][:80]}")
    print(f"  Date: {row['date'][:10]}")
    print(f"  Engagement: {row['engagement']:,}")

# Save cleaned version
real_brands.to_csv('data/khalidwalb_brand_mentions.csv', index=False)
print("\n" + "="*80)
print("Saved cleaned brand mentions to: khalidwalb_brand_mentions.csv")
print("="*80)
