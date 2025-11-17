import os
import re
import glob
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# Unified schema (keep headers clean and consistent)
SCHEMA = [
    'name',              # Company/Business name
    'venture_type',      # Restaurants, FinTech, Fashion, Services, Tech, B2B, Healthcare, Education, Retail, Hospitality, Other
    'company_role',      # Refined role e.g., FinTech - Payments, Food Delivery, EdTech
    'services',          # Human-readable service/offering summary
    'industry',          # Raw/derived industry/category tags
    'location',          # Raw location text
    'city',
    'state',
    'country',
    'website',
    'email',
    'phone',
    'employees',
    'funding_usd',       # Integer USD if available
    'hiring',            # True/False if jobs available
    'jobs_link',
    'rating',            # Float if available
    'reviews',           # Int if available
    'price_level',       # e.g., $, $$, $$$ (if available)
    'source',            # google_maps | topstartups | indiamart | justdial | manual
    'source_url',        # Source URL if known
    'collected_at',      # Timestamp when merged
]

INDIA_DEFAULT = 'India'


def _clean_phone(value: Optional[str]) -> Optional[str]:
    if not value or not isinstance(value, str):
        return None
    digits = re.sub(r'[^0-9+]', '', value)
    return digits if digits else None


def _to_int(value) -> Optional[int]:
    try:
        if pd.isna(value):
            return None
        return int(float(value))
    except Exception:
        return None


def _derive_venture_type_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    t = text.lower()
    # Restaurants / Hospitality
    if any(k in t for k in ['restaurant', 'cafe', 'coffee', 'bistro', 'bar', 'diner', 'food court']):
        return 'Restaurants'
    if any(k in t for k in ['hotel', 'resort', 'hostel', 'homestay']):
        return 'Hospitality'
    # Fashion / Retail
    if any(k in t for k in ['fashion', 'boutique', 'apparel', 'clothing', 'garment', 'jewellery', 'jewelry', 'cosmetic', 'beauty']):
        return 'Fashion'
    if any(k in t for k in ['retail', 'store', 'shop', 'e-commerce', 'ecommerce']):
        return 'Retail'
    # Tech / Services
    if any(k in t for k in ['software', 'it services', 'web design', 'web development', 'digital marketing', 'seo', 'agency', 'saas']):
        return 'Services'
    if any(k in t for k in ['ai', 'ml', 'data', 'cloud', 'cybersecurity', 'devops', 'platform']):
        return 'Tech'
    # Finance
    if any(k in t for k in ['fintech', 'payments', 'lending', 'neo bank', 'neobank', 'credit', 'insurance']):
        return 'FinTech'
    # Healthcare / Education
    if any(k in t for k in ['health', 'clinic', 'hospital', 'care', 'pharma', 'wellness']):
        return 'Healthcare'
    if any(k in t for k in ['education', 'edtech', 'coaching', 'training', 'school', 'college', 'tuition']):
        return 'Education'
    # Automotive
    if any(k in t for k in ['automobile', 'auto', 'car', 'bike', 'showroom', 'dealership']):
        return 'Automotive'
    return None


def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in SCHEMA:
        if col not in df.columns:
            df[col] = None
    return df[SCHEMA]


from typing import Tuple


def _classify_role_services(name: Optional[str], industry: Optional[str], website: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Infer company_role and services from available text signals"""
    text = ' '.join([
        str(name or ''),
        str(industry or ''),
        str(website or ''),
    ]).lower()

    def any_kw(keys):
        return any(k in text for k in keys)

    # Specific brand-based hints
    if any_kw(['razorpay', 'innoviti', 'paytm', 'cashfree']):
        return 'FinTech - Payments', 'Payment gateway / digital payments'
    if any_kw(['scripbox', 'groww', 'zerodha', 'wealth']):
        return 'WealthTech', 'Investing / wealth management platform'
    if any_kw(['coinswitch', 'coin dcx', 'crypto']):
        return 'Crypto Exchange', 'Digital asset trading platform'
    if any_kw(['byju', 'cuemath', 'unacademy', 'vedantu', 'edtech', 'learn', 'education']):
        return 'EdTech', 'Online learning / education technology'
    if any_kw(['pristyn', 'health', 'clinic', 'care', 'med', 'wellness', 'telemed']):
        return 'HealthTech', 'Healthcare services / benefits / telemedicine'
    if any_kw(['swiggy', 'zomato', 'food delivery', 'deliveries']):
        return 'Food Delivery', 'Online food ordering & delivery'
    if any_kw(['livspace', 'interior']):
        return 'Interiors/Design', 'Home interior design & installation'
    if any_kw(['fashinza', 'apparel', 'garment', 'fashion', 'boutique']):
        return 'Fashion Supply Chain', 'B2B fashion/manufacturing platform'
    if any_kw(['rentomojo', 'rento', 'rent', 'furniture']):
        return 'Rental/PropTech', 'Furniture & appliance rentals'
    if any_kw(['bluestone', 'jewel', 'jewellery', 'jewelry']):
        return 'Jewelry E-commerce', 'Online D2C jewelry brand'
    if any_kw(['myglamm', 'beauty', 'makeup', 'cosmetic']):
        return 'Beauty D2C', 'Beauty & personal care D2C'
    if any_kw(['perfios', 'credit analytics', 'bureau']):
        return 'FinTech - Credit Analytics', 'Credit decisioning & analytics SaaS'
    if any_kw(['increff', 'supply chain', 'inventory', 'warehouse']):
        return 'B2B SaaS - Supply Chain', 'Inventory/fulfillment optimization SaaS'

    # Generic heuristics
    if any_kw(['payment', 'upi', 'wallet', 'lending', 'neobank', 'insurance', 'insurtech', 'credit']):
        return 'FinTech', 'Financial technology services'
    if any_kw(['saas', 'crm', 'erp', 'platform', 'analytics', 'billing', 'pos', 'hrms', 'ats']):
        return 'B2B SaaS', 'Software platform / SaaS'
    if any_kw(['ecommerce', 'e-commerce', 'marketplace', 'store', 'shop']):
        return 'E-commerce', 'Online commerce / marketplace'
    if any_kw(['restaurant', 'cafe', 'bistro', 'kitchen', 'diner']):
        return 'Restaurants', 'Dine-in / QSR / cloud kitchen'
    if any_kw(['logistics', 'delivery', 'courier', 'freight']):
        return 'Logistics', 'Logistics & delivery services'

    return None, None


def map_topstartups(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out['name'] = df.get('company_name')
    out['industry'] = df.get('industry')
    out['location'] = df.get('hq_location')
    out['website'] = df.get('website_url')
    out['email'] = None
    out['phone'] = df['phone'].apply(_clean_phone) if 'phone' in df.columns else pd.Series([None]*len(df))
    out['employees'] = df.get('employees')
    out['funding_usd'] = df['funding_amount'].apply(_to_int) if 'funding_amount' in df.columns else pd.Series([None]*len(df))
    out['hiring'] = df.get('jobs_available')
    out['jobs_link'] = df.get('jobs_link')
    out['rating'] = None
    out['reviews'] = None
    out['price_level'] = None
    out['source'] = 'topstartups'
    out['source_url'] = 'https://topstartups.io/?hq_location=India'
    out['collected_at'] = datetime.now().isoformat(timespec='seconds')

    # venture_type from industry
    venture_type = []
    roles, svc_list = [], []
    for _, row in out.iterrows():
        vt = _derive_venture_type_from_text(str(row.get('industry') or ''))
        if not vt and isinstance(row.get('name'), str):
            vt = _derive_venture_type_from_text(row['name'])
        venture_type.append(vt or 'Tech')  # default to Tech for startups
        role, svc = _classify_role_services(row.get('name'), row.get('industry'), row.get('website'))
        roles.append(role)
        svc_list.append(svc)
    out['venture_type'] = venture_type
    out['company_role'] = roles
    out['services'] = svc_list

    out['city'] = None
    out['state'] = None
    out['country'] = INDIA_DEFAULT
    return _ensure_columns(out)


def map_googlemaps(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    # Try common column names from google_maps_premium
    out['name'] = df.get('name') or df.get('business_name')
    out['industry'] = df.get('category') or df.get('types')
    out['location'] = df.get('address')
    out['website'] = df.get('website')
    out['email'] = df.get('email') if 'email' in df.columns else None
    out['phone'] = df['phone'].apply(_clean_phone) if 'phone' in df.columns else pd.Series([None]*len(df))
    out['employees'] = None
    out['funding_usd'] = None
    out['hiring'] = None
    out['jobs_link'] = None
    out['rating'] = df.get('rating')
    out['reviews'] = df.get('reviews') or df.get('reviews_count')
    out['price_level'] = df.get('price_level')
    out['source'] = 'google_maps'
    out['source_url'] = df.get('google_maps_url') if 'google_maps_url' in df.columns else None
    out['collected_at'] = datetime.now().isoformat(timespec='seconds')

    # venture_type from category
    venture_type = []
    roles, svc_list = [], []
    for _, row in out.iterrows():
        vt = _derive_venture_type_from_text(str(row.get('industry') or ''))
        if not vt and isinstance(row.get('name'), str):
            vt = _derive_venture_type_from_text(row['name'])
        venture_type.append(vt or 'Services')
        role, svc = _classify_role_services(row.get('name'), row.get('industry'), row.get('website'))
        roles.append(role)
        svc_list.append(svc)
    out['venture_type'] = venture_type
    out['company_role'] = roles
    out['services'] = svc_list

    # City/State/Country if present
    out['city'] = df.get('city') if 'city' in df.columns else None
    out['state'] = df.get('state') if 'state' in df.columns else None
    out['country'] = INDIA_DEFAULT
    return _ensure_columns(out)


def map_indiamart(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out['name'] = df.get('company_name') or df.get('name')
    out['industry'] = df.get('business_type') or df.get('products')
    out['location'] = df.get('address')
    out['website'] = df.get('website')
    out['email'] = df.get('email') if 'email' in df.columns else None
    out['phone'] = df['phone'].apply(_clean_phone) if 'phone' in df.columns else pd.Series([None]*len(df))
    out['employees'] = df.get('employees') if 'employees' in df.columns else None
    out['funding_usd'] = None
    out['hiring'] = None
    out['jobs_link'] = None
    out['rating'] = None
    out['reviews'] = None
    out['price_level'] = None
    out['source'] = 'indiamart'
    out['source_url'] = df.get('company_url') if 'company_url' in df.columns else None
    out['collected_at'] = datetime.now().isoformat(timespec='seconds')

    # venture_type: B2B Services or derive from industry
    venture_type = []
    roles, svc_list = [], []
    for _, row in out.iterrows():
        vt = _derive_venture_type_from_text(str(row.get('industry') or ''))
        venture_type.append(vt or 'B2B')
        role, svc = _classify_role_services(row.get('name'), row.get('industry'), row.get('website'))
        roles.append(role)
        svc_list.append(svc)
    out['venture_type'] = venture_type
    out['company_role'] = roles
    out['services'] = svc_list

    out['city'] = df.get('city') if 'city' in df.columns else None
    out['state'] = df.get('state') if 'state' in df.columns else None
    out['country'] = INDIA_DEFAULT
    return _ensure_columns(out)


def map_justdial(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out['name'] = df.get('name') or df.get('business_name')
    out['industry'] = df.get('cuisines') if 'cuisines' in df.columns else df.get('category')
    out['location'] = df.get('address')
    out['website'] = df.get('website') if 'website' in df.columns else None
    out['email'] = None
    out['phone'] = df['phone'].apply(_clean_phone) if 'phone' in df.columns else pd.Series([None]*len(df))
    out['employees'] = None
    out['funding_usd'] = None
    out['hiring'] = None
    out['jobs_link'] = None
    out['rating'] = df.get('rating') if 'rating' in df.columns else None
    out['reviews'] = df.get('reviews_count') if 'reviews_count' in df.columns else None
    out['price_level'] = df.get('cost_for_two') if 'cost_for_two' in df.columns else None
    out['source'] = 'justdial'
    out['source_url'] = df.get('detail_url') if 'detail_url' in df.columns else None
    out['collected_at'] = datetime.now().isoformat(timespec='seconds')

    # venture_type: Restaurants likely
    venture_type = []
    roles, svc_list = [], []
    for _, row in out.iterrows():
        vt = _derive_venture_type_from_text(str(row.get('industry') or ''))
        venture_type.append(vt or 'Restaurants')
        role, svc = _classify_role_services(row.get('name'), row.get('industry'), row.get('website'))
        roles.append(role)
        svc_list.append(svc)
    out['venture_type'] = venture_type
    out['company_role'] = roles
    out['services'] = svc_list

    out['city'] = df.get('city') if 'city' in df.columns else None
    out['state'] = df.get('state') if 'state' in df.columns else None
    out['country'] = INDIA_DEFAULT
    return _ensure_columns(out)


def load_and_map_files() -> pd.DataFrame:
    frames: List[pd.DataFrame] = []

    # TopStartups
    for path in glob.glob(os.path.join(DATA_DIR, 'topstartups_india_*.csv')):
        try:
            df = pd.read_csv(path)
            frames.append(map_topstartups(df))
        except Exception as e:
            print(f"Warning: failed to load {path}: {e}")

    # Google Maps
    for path in glob.glob(os.path.join(DATA_DIR, 'google_maps_premium_*.csv')):
        try:
            df = pd.read_csv(path)
            frames.append(map_googlemaps(df))
        except Exception as e:
            print(f"Warning: failed to load {path}: {e}")

    # IndiaMART
    for path in glob.glob(os.path.join(DATA_DIR, 'indiamart_**.csv')):
        try:
            df = pd.read_csv(path)
            frames.append(map_indiamart(df))
        except Exception as e:
            print(f"Warning: failed to load {path}: {e}")

    # JustDial - detailed coffee shops
    for path in glob.glob(os.path.join(DATA_DIR, 'detailed_*coffee*shops*.csv')):
        try:
            df = pd.read_csv(path)
            frames.append(map_justdial(df))
        except Exception as e:
            print(f"Warning: failed to load {path}: {e}")

    if not frames:
        return pd.DataFrame(columns=SCHEMA)

    merged = pd.concat(frames, ignore_index=True)

    # Prefer rows with better names when deduplicating
    name_series = merged['name'].fillna('').astype(str)
    merged['name_quality'] = (~name_series.str.contains('see who works here', case=False)) & (name_series.str.len() > 3)

    # Deduplicate carefully: avoid collapsing rows where keys are null
    # 1) By website (only non-null websites)
    if 'website' in merged.columns:
        has_site = merged['website'].notna()
        dedup_site = merged.loc[has_site].sort_values(by=['website', 'name_quality', 'source'], ascending=[True, False, True], na_position='last')\
            .drop_duplicates(subset=['website'], keep='first')
        no_site = merged.loc[~has_site]
        merged = pd.concat([dedup_site, no_site], ignore_index=True)

    # 2) By phone (only non-null phones)
    if 'phone' in merged.columns:
        has_phone = merged['phone'].notna()
        dedup_phone = merged.loc[has_phone].sort_values(by=['phone', 'source'], na_position='last')\
            .drop_duplicates(subset=['phone'], keep='first')
        no_phone = merged.loc[~has_phone]
        merged = pd.concat([dedup_phone, no_phone], ignore_index=True)

    # 3) By name+city (only rows where both exist)
    if all(c in merged.columns for c in ['name', 'city']):
        both = merged['name'].notna() & merged['city'].notna()
        dedup_name_city = merged.loc[both].sort_values(by=['name', 'city', 'source'], na_position='last')\
            .drop_duplicates(subset=['name', 'city'], keep='first')
        rest = merged.loc[~both]
        merged = pd.concat([dedup_name_city, rest], ignore_index=True)

    # Ensure schema and tidy types
    merged = _ensure_columns(merged)

    # Normalize booleans
    if 'hiring' in merged.columns:
        merged['hiring'] = merged['hiring'].apply(lambda x: bool(x) if pd.notna(x) else None)

    # Convert rating to float, reviews to int
    if 'rating' in merged.columns:
        merged['rating'] = pd.to_numeric(merged['rating'], errors='coerce')
    if 'reviews' in merged.columns:
        merged['reviews'] = pd.to_numeric(merged['reviews'], errors='coerce').astype('Int64')

    # Drop helper column
    if 'name_quality' in merged.columns:
        merged = merged.drop(columns=['name_quality'])

    return merged


def save_outputs(df: pd.DataFrame) -> Dict[str, str]:
    os.makedirs(DATA_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # CSV
    csv_path = os.path.join(DATA_DIR, 'leads.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8')

    # Excel with sheets per venture type
    xlsx_path = os.path.join(DATA_DIR, 'leads.xlsx')
    # Use openpyxl (present in environment). If missing, user will still get CSV.
    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        # Overall sheet
        df.to_excel(writer, sheet_name='All_Leads', index=False)
        # Per venture_type sheets
        vt_values = sorted([v for v in df['venture_type'].dropna().unique().tolist() if v])
        for vt in vt_values:
            sub = df[df['venture_type'] == vt]
            safe_name = re.sub(r'[^A-Za-z0-9_]', '_', vt)[:28]  # Excel sheet name limit
            sheet_name = f'{safe_name}'
            sub.to_excel(writer, sheet_name=sheet_name, index=False)

    return {'csv': csv_path, 'xlsx': xlsx_path}


def summary(df: pd.DataFrame) -> str:
    lines = []
    lines.append(f'Total leads: {len(df)}')
    if 'venture_type' in df.columns:
        counts = df['venture_type'].fillna('Other').value_counts()
        for vt, cnt in counts.items():
            lines.append(f'- {vt}: {cnt}')
    # Coverage
    website_cov = int(df['website'].notna().sum()) if 'website' in df.columns else 0
    email_cov = int(df['email'].notna().sum()) if 'email' in df.columns else 0
    phone_cov = int(df['phone'].notna().sum()) if 'phone' in df.columns else 0
    lines.append(f'Coverage: websites={website_cov}, emails={email_cov}, phones={phone_cov}')
    return '\n'.join(lines)


def main():
    df = load_and_map_files()
    if df.empty:
        print('No source CSVs found in data/. Run the scrapers first.')
        return
    paths = save_outputs(df)
    print('Saved outputs:')
    print(f"- CSV: {paths['csv']}")
    print(f"- XLSX: {paths['xlsx']}")
    print('\nSummary:')
    print(summary(df))


if __name__ == '__main__':
    main()
