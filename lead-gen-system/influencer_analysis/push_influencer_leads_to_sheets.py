"""
Build and push Instagram influencer leads to Google Sheets.
- Consolidates enriched brand data into data/influencer_leads.csv
- Pushes to worksheet 'Instagram_Influencer_Leads' in the main spreadsheet
"""

import os
import glob
from datetime import datetime
import pandas as pd

import sys
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from integration.sheets_writer import write_df_to_specific_worksheet
from utils.config import config

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
OUTPUT_CSV = os.path.join(DATA_DIR, 'influencer_leads.csv')
WORKSHEET_TITLE = 'Instagram_Influencer_Leads'

REQUIRED_COLS = [
    'influencer_handle',
    'brand_account',
    'brand_instagram_url',
    'brand_full_name',
    'brand_followers',
    'brand_is_verified',
    'brand_is_business',
    'products_mentioned',
    'total_mentions',
    'total_engagement'
]


def load_enriched_brand_files() -> pd.DataFrame:
    """Load all enriched brand CSVs and return a consolidated DataFrame."""
    pattern = os.path.join(DATA_DIR, '*_brands_enriched.csv')
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No enriched brand files found matching {pattern}")

    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            frames.append(df)
        except Exception:
            continue

    if not frames:
        raise RuntimeError('No enriched brand CSVs could be loaded')

    combined = pd.concat(frames, ignore_index=True).drop_duplicates(subset=['influencer_handle','brand_account'])
    return combined


def build_influencer_leads_df(enriched_df: pd.DataFrame) -> pd.DataFrame:
    """Map enriched brands to a clean influencer leads schema and add metadata."""
    # Ensure required columns exist
    for col in REQUIRED_COLS:
        if col not in enriched_df.columns:
            enriched_df[col] = ''

    leads = enriched_df[REQUIRED_COLS].copy()
    leads.insert(0, 'source', 'instagram')
    leads.insert(1, 'collected_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return leads


def save_and_push(leads_df: pd.DataFrame) -> dict:
    """Save consolidated CSV and push to Google Sheets worksheet."""
    # Save locally
    leads_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

    # Push to Sheets
    res = write_df_to_specific_worksheet(
        leads_df,
        worksheet_title=WORKSHEET_TITLE,
        sheet_id=config.GOOGLE_SHEET_ID or None,
        credentials_file=config.GOOGLE_SERVICE_ACCOUNT_JSON or None
    )
    return res


def main():
    enriched_df = load_enriched_brand_files()
    leads_df = build_influencer_leads_df(enriched_df)
    res = save_and_push(leads_df)

    print(f"Saved consolidated influencer leads CSV: {OUTPUT_CSV}")
    if res.get('success'):
        print(f"Pushed to Google Sheets -> {res['sheet_url']} [{WORKSHEET_TITLE}]")
    else:
        print('Failed to push to Google Sheets:', res.get('error'))


if __name__ == '__main__':
    main()
