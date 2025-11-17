"""
Generate status report for lead generation system
"""
import pandas as pd
import os
import glob
from datetime import datetime

def generate_report():
    df = pd.read_csv('data/leads.csv')
    
    print('='*70)
    print('LEAD GENERATION SYSTEM - STATUS REPORT')
    print(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*70)
    print()
    
    print('📊 OVERALL STATISTICS')
    print(f'Total Leads Collected: {len(df)}')
    print()
    
    print('🏢 BY VENTURE TYPE')
    for vt, count in df['venture_type'].value_counts().items():
        print(f'  {vt}: {count}')
    print()
    
    print('🎯 BY COMPANY ROLE (Top defined roles)')
    role_counts = df[df['company_role'].notna()]['company_role'].value_counts().head(10)
    for role, count in role_counts.items():
        print(f'  {role}: {count}')
    print()
    
    print('📈 DATA QUALITY')
    print(f'  With Website: {df["website"].notna().sum()} ({df["website"].notna().sum()/len(df)*100:.1f}%)')
    print(f'  With Email: {df["email"].notna().sum()} ({df["email"].notna().sum()/len(df)*100:.1f}%)')
    print(f'  With Phone: {df["phone"].notna().sum()} ({df["phone"].notna().sum()/len(df)*100:.1f}%)')
    print(f'  With Funding Data: {df["funding_usd"].notna().sum()} ({df["funding_usd"].notna().sum()/len(df)*100:.1f}%)')
    print(f'  Currently Hiring: {df["hiring"].sum() if "hiring" in df.columns else 0}')
    print()
    
    if df['funding_usd'].notna().sum() > 0:
        print('💰 FUNDING INSIGHTS')
        total_funding = df['funding_usd'].sum()
        avg_funding = df['funding_usd'].mean()
        print(f'  Total Funding: ${total_funding:,.0f}')
        print(f'  Average Funding: ${avg_funding:,.0f}')
        top_funded = df.nlargest(3, 'funding_usd')[['name', 'funding_usd', 'company_role']]
        print('  Top 3 Funded:')
        for _, row in top_funded.iterrows():
            print(f'    • {row["name"]}: ${row["funding_usd"]:,.0f} ({row["company_role"]})')
        print()
    
    print('📁 OUTPUT FILES')
    print(f'  ✅ data/leads.csv ({os.path.getsize("data/leads.csv")/1024:.1f} KB)')
    print(f'  ✅ data/leads.xlsx ({os.path.getsize("data/leads.xlsx")/1024:.1f} KB)')
    print()
    
    print('📂 SOURCE FILES PROCESSED')
    sources = {
        'TopStartups': glob.glob('data/topstartups_india_*.csv'),
        'JustDial': glob.glob('data/detailed_*coffee*.csv'),
        'Google Maps': glob.glob('data/google_maps_premium_*.csv'),
        'IndiaMART': glob.glob('data/indiamart_*.csv')
    }
    for source, files in sources.items():
        if files:
            print(f'  ✅ {source}: {len(files)} file(s)')
        else:
            print(f'  ⏳ {source}: Not yet run')
    print()
    
    print('🚀 NEXT STEPS TO REACH 500+ LEADS')
    current = len(df)
    target = 500
    remaining = target - current
    
    if remaining > 0:
        print(f'  Current: {current} leads')
        print(f'  Target: {target} leads')
        print(f'  Remaining: {remaining} leads needed')
        print()
        print('  Recommended actions:')
        print('  1. Run Google Maps scraper (150 leads): python scrapers/google_maps_premium.py')
        print('  2. Run IndiaMART scraper (50 leads): python scrapers/indiamart_scraper.py')
        print('  3. Run JustDial for more categories (100+ leads)')
        print('  4. Re-run TopStartups with more scrolls (200+ leads)')
    else:
        print(f'  ✅ TARGET ACHIEVED! {current}/{target} leads collected')
        print('  Next: Upload to Google Sheets with python -m integration.sheets_writer')
    
    print()
    print('='*70)

if __name__ == '__main__':
    generate_report()
