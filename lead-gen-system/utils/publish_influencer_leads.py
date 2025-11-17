"""
Publish Instagram influencer leads as:
- CSV 'worksheet' at data/leads_instagram_influencer_leads.csv
- Excel sheet 'Instagram_Influencer_Leads' inside data/leads.xlsx (created if missing)

Input: data/influencer_leads.csv (built by influencer_analysis/push_influencer_leads_to_sheets.py)
"""

import os
import sys
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
CSV_IN = DATA / 'influencer_leads.csv'
CSV_UNIFIED = DATA / 'leads_unified.csv'
CSV_OUT = DATA / 'leads_instagram_influencer_leads.csv'
XLSX_OUT = DATA / 'leads.xlsx'
SHEET_NAME = 'Instagram_Influencer_Leads'
UNIFIED_SHEET = 'All_Leads_Unified'


def main():
    if not CSV_IN.exists():
        print(f"❌ Missing input CSV: {CSV_IN}")
        print("Run influencer_analysis/push_influencer_leads_to_sheets.py first to build influencer_leads.csv")
        sys.exit(1)

    # Load influencer leads
    df = pd.read_csv(CSV_IN)

    # 1) Save the CSV 'worksheet'
    df.to_csv(CSV_OUT, index=False, encoding='utf-8-sig')
    print(f"✅ Wrote CSV worksheet: {CSV_OUT}")

    # 2) Add/replace sheet in leads.xlsx
    # If workbook exists, load and replace the sheet. Else, create anew and add All_Leads placeholder if desired.
    try:
        # Use openpyxl engine
        if XLSX_OUT.exists():
            # Load existing, remove sheet if present, then write back
            with pd.ExcelWriter(XLSX_OUT, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
            print(f"✅ Upserted sheet '{SHEET_NAME}' in {XLSX_OUT}")
        else:
            with pd.ExcelWriter(XLSX_OUT, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
            print(f"✅ Created workbook and added sheet '{SHEET_NAME}': {XLSX_OUT}")
    except Exception as e:
        print(f"❌ Failed to write Excel sheet: {e}")
        sys.exit(1)

    # 3) Add unified leads sheet if available
    if CSV_UNIFIED.exists():
        try:
            unified_df = pd.read_csv(CSV_UNIFIED)
            with pd.ExcelWriter(XLSX_OUT, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                unified_df.to_excel(writer, sheet_name=UNIFIED_SHEET, index=False)
            print(f"✅ Upserted sheet '{UNIFIED_SHEET}' with {len(unified_df)} unified leads")
        except Exception as e:
            print(f"⚠️  Failed to add unified sheet: {e}")

    print("🎉 Publish complete.")


if __name__ == '__main__':
    main()
