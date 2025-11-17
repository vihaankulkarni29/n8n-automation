"""
Merge traditional leads (leads.csv) with influencer leads (influencer_leads.csv)
into a single unified CSV with superset schema.

Output: data/leads_unified.csv
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

LEADS_CSV = DATA / 'leads.csv'
INFLUENCER_CSV = DATA / 'influencer_leads.csv'
OUTPUT_CSV = DATA / 'leads_unified.csv'

# Superset schema combining both sources
UNIFIED_SCHEMA = [
    # Common identifiers
    'lead_type',          # 'business' | 'influencer_brand'
    'name',               # Business name or brand account
    'source',
    'collected_at',
    
    # Business lead fields
    'venture_type',
    'company_role',
    'services',
    'industry',
    'location',
    'city',
    'state',
    'country',
    'website',
    'email',
    'phone',
    'employees',
    'funding_usd',
    'hiring',
    'jobs_link',
    'rating',
    'reviews',
    'price_level',
    'source_url',
    
    # Influencer brand fields
    'influencer_handle',
    'brand_account',
    'brand_instagram_url',
    'brand_full_name',
    'brand_followers',
    'brand_is_verified',
    'brand_is_business',
    'products_mentioned',
    'total_mentions',
    'total_engagement',
]


def load_traditional_leads() -> pd.DataFrame:
    """Load and map traditional business leads to unified schema."""
    if not LEADS_CSV.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(LEADS_CSV)
    
    # Add lead_type
    df['lead_type'] = 'business'
    
    # Ensure all unified columns exist
    for col in UNIFIED_SCHEMA:
        if col not in df.columns:
            df[col] = None
    
    return df[UNIFIED_SCHEMA]


def load_influencer_leads() -> pd.DataFrame:
    """Load and map influencer brand leads to unified schema."""
    frames = []
    shopify_count = 0
    
    # Load main influencer_leads.csv
    if INFLUENCER_CSV.exists():
        df = pd.read_csv(INFLUENCER_CSV)
        df['data_source'] = 'influencer_leads'
        frames.append(df)
    
    # Load brand network CSVs
    import glob
    for file in glob.glob(str(DATA / 'brand_network_brands_*.csv')):
        df = pd.read_csv(file)
        df['data_source'] = 'brand_network'
        frames.append(df)
    
    # Load basic Shopify stores
    for file in glob.glob(str(DATA / 'shopify_stores_*.csv')):
        shopify_df = pd.read_csv(file)
        shopify_count = len(shopify_df)
        print(f"   Loading Shopify file: {file} ({shopify_count} stores)")
        # Map Shopify columns to unified schema
        shopify_mapped = pd.DataFrame({
            'lead_type': ['ecommerce_d2c'] * len(shopify_df),
            'name': shopify_df['name'].values,
            'source': shopify_df['source'].values,
            'collected_at': shopify_df['collected_at'].values,
            'venture_type': ['E-commerce'] * len(shopify_df),
            'country': shopify_df['country'].values,
            'website': shopify_df['url'].values,
            'email': shopify_df['email'].values,
            'phone': shopify_df['phone'].values,
            'data_source': ['shopify'] * len(shopify_df)
        })
        print(f"   Mapped {len(shopify_mapped)} Shopify stores")
        frames.append(shopify_mapped)
    
    # Load scored Shopify leads
    for file in glob.glob(str(DATA / 'shopify_leads_scored_*.csv')):
        scored_df = pd.read_csv(file)
        print(f"   Loading scored Shopify leads: {file} ({len(scored_df)} stores)")
        # Map scored leads columns
        scored_mapped = pd.DataFrame({
            'lead_type': ['ecommerce_scored'] * len(scored_df),
            'name': scored_df['domain'].values,
            'source': ['shopify_lead_scorer'] * len(scored_df),
            'collected_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'venture_type': scored_df['industry'].values if 'industry' in scored_df.columns else 'E-commerce',
            'website': scored_df['url'].values,
            'rating': scored_df['lead_score'].values if 'lead_score' in scored_df.columns else None,
            'services': scored_df['weaknesses'].apply(lambda x: ', '.join(eval(x)) if isinstance(x, str) and x.startswith('[') else x) if 'weaknesses' in scored_df.columns else None,
            'data_source': ['shopify_scored'] * len(scored_df)
        })
        print(f"   Mapped {len(scored_mapped)} scored Shopify leads")
        frames.append(scored_mapped)
    
    if not frames:
        return pd.DataFrame()
    
    print(f"   Total frames to concat: {len(frames)}")
    for i, frame in enumerate(frames):
        print(f"     Frame {i}: {len(frame)} rows, columns: {frame.columns.tolist()[:5]}...")
    
    df = pd.concat(frames, ignore_index=True)
    print(f"   After concat: {len(df)} total rows")
    
    # Deduplicate only rows that have values in those columns
    if 'brand_username' in df.columns:
        before = len(df)
        # Only deduplicate rows with non-null brand_username
        has_brand_username = df['brand_username'].notna()
        df_with_username = df[has_brand_username].drop_duplicates(subset=['brand_username'], keep='first')
        df_without_username = df[~has_brand_username]
        df = pd.concat([df_with_username, df_without_username], ignore_index=True)
        print(f"   Deduplicated by brand_username: {before} -> {len(df)}")
    if 'url' in df.columns:
        before = len(df)
        # Only deduplicate rows with non-null url
        has_url = df['url'].notna()
        df_with_url = df[has_url].drop_duplicates(subset=['url'], keep='first')
        df_without_url = df[~has_url]
        df = pd.concat([df_with_url, df_without_url], ignore_index=True)
        print(f"   Deduplicated by url: {before} -> {len(df)}")
    
    # Map fields for influencer brands (only if not already set)
    if 'name' not in df.columns or df['name'].isna().all():
        if 'brand_account' in df.columns:
            df['name'] = df['brand_account']
    
    if 'website' not in df.columns or df['website'].isna().all():
        if 'brand_instagram_url' in df.columns:
            df['website'] = df['brand_instagram_url']
        elif 'url' in df.columns:
            df['website'] = df['url']
    
    # Set venture_type for influencer brands only (don't override Shopify)
    if 'venture_type' not in df.columns:
        df['venture_type'] = None
    df.loc[(df['lead_type'] == 'influencer_brand') & df['venture_type'].isna(), 'venture_type'] = 'Fashion'
    
    # Set company_role and services for influencer brands
    if 'company_role' not in df.columns:
        df['company_role'] = None
    df.loc[df['lead_type'] == 'influencer_brand', 'company_role'] = 'Influencer Partnership'
    
    if 'services' not in df.columns:
        df['services'] = None
    if 'products_mentioned' in df.columns:
        df.loc[df['lead_type'] == 'influencer_brand', 'services'] = df['products_mentioned']
    
    # Default country
    if 'country' not in df.columns:
        df['country'] = 'India'
    
    # Ensure all unified columns exist
    for col in UNIFIED_SCHEMA:
        if col not in df.columns:
            df[col] = None
    
    return df[UNIFIED_SCHEMA]


def merge_and_deduplicate(business_df: pd.DataFrame, influencer_df: pd.DataFrame) -> pd.DataFrame:
    """Merge both DataFrames and deduplicate by website/brand URL."""
    
    if business_df.empty and influencer_df.empty:
        return pd.DataFrame(columns=UNIFIED_SCHEMA)
    
    if business_df.empty:
        return influencer_df
    
    if influencer_df.empty:
        return business_df
    
    # Concatenate
    merged = pd.concat([business_df, influencer_df], ignore_index=True)
    
    # Deduplicate by website (keep first occurrence)
    # This ensures if same brand appears in both sources, we keep the first one
    merged = merged.sort_values(by=['lead_type', 'source'], ascending=[True, True])
    
    has_website = merged['website'].notna() & (merged['website'] != '')
    dedup_website = merged.loc[has_website].drop_duplicates(subset=['website'], keep='first')
    no_website = merged.loc[~has_website]
    
    merged = pd.concat([dedup_website, no_website], ignore_index=True)
    
    return merged


def main():
    print("="*80)
    print("MERGING TRADITIONAL LEADS + INFLUENCER LEADS")
    print("="*80)
    
    # Load both sources
    print("\n1. Loading traditional business leads...")
    business_df = load_traditional_leads()
    print(f"   Found {len(business_df)} business leads")
    
    print("\n2. Loading influencer brand leads...")
    influencer_df = load_influencer_leads()
    print(f"   Found {len(influencer_df)} influencer brand leads")
    
    # Merge
    print("\n3. Merging and deduplicating...")
    unified_df = merge_and_deduplicate(business_df, influencer_df)
    print(f"   Total unified leads: {len(unified_df)}")
    
    # Save
    print(f"\n4. Saving to {OUTPUT_CSV}...")
    unified_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    # Summary
    print("\n" + "="*80)
    print("✅ UNIFIED LEADS CREATED")
    print("="*80)
    
    if not unified_df.empty:
        print(f"\nTotal leads: {len(unified_df)}")
        
        lead_type_counts = unified_df['lead_type'].value_counts()
        print("\nBy lead type:")
        for lt, count in lead_type_counts.items():
            print(f"  - {lt}: {count}")
        
        if 'venture_type' in unified_df.columns:
            venture_counts = unified_df['venture_type'].fillna('Unknown').value_counts().head(10)
            print("\nTop 10 venture types:")
            for vt, count in venture_counts.items():
                print(f"  - {vt}: {count}")
        
        source_counts = unified_df['source'].value_counts()
        print("\nBy source:")
        for src, count in source_counts.items():
            print(f"  - {src}: {count}")
        
        # Coverage stats
        website_count = unified_df['website'].notna().sum()
        email_count = unified_df['email'].notna().sum()
        phone_count = unified_df['phone'].notna().sum()
        
        print(f"\nData coverage:")
        print(f"  - Websites: {website_count}")
        print(f"  - Emails: {email_count}")
        print(f"  - Phones: {phone_count}")
    
    print(f"\n📁 Output file: {OUTPUT_CSV}")
    print("="*80)


if __name__ == '__main__':
    main()
