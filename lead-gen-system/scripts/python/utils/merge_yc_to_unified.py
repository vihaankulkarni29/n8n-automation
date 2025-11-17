import csv
import glob
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
UNIFIED_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'leads_unified.csv')

def latest_yc_csv():
    files = glob.glob(os.path.join(DATA_DIR, 'yc_startups_*.csv'))
    if not files:
        raise FileNotFoundError('No YC startups CSV files found in data/')
    files.sort()
    return files[-1]

US_STATES = { 'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY' }

def infer_country(location: str) -> str:
    if not location:
        return ''
    parts = [p.strip() for p in location.split(',') if p.strip()]
    if parts and parts[-1] in US_STATES:
        return 'USA'
    if 'India' in location:
        return 'India'
    return ''

def append_yc_to_unified(csv_path: str) -> int:
    with open(UNIFIED_PATH, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        existing = list(reader)
        existing_names = { (r.get('name') or '').strip().lower() for r in existing if r.get('name') }

    header_set = set(header)
    def put(out, k, v):
        if k in header_set:
            out[k] = v

    rows_added = 0
    now_iso = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    with open(csv_path, 'r', encoding='utf-8', newline='') as yf:
        yreader = csv.DictReader(yf)
        yc_rows = list(yreader)

    # Partition missing website first similar to JD ordering
    no_web = [r for r in yc_rows if not r.get('website')]
    has_web = [r for r in yc_rows if r.get('website')]
    ordered = no_web + has_web

    tmp_path = UNIFIED_PATH + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8', newline='') as wf:
        writer = csv.DictWriter(wf, fieldnames=header)
        writer.writeheader()
        for r in existing:
            writer.writerow(r)
        for r in ordered:
            name = (r.get('name') or '').strip()
            if not name or name.lower() in existing_names:
                continue
            out = {h: '' for h in header}
            put(out, 'lead_type', 'yc_startup')
            put(out, 'name', name)
            put(out, 'source', 'yc_directory')
            put(out, 'collected_at', now_iso)
            put(out, 'industry', r.get('industry',''))
            put(out, 'location', r.get('location',''))
            country = infer_country(r.get('location',''))
            if country:
                put(out, 'country', country)
            put(out, 'website', r.get('website',''))
            put(out, 'employees', r.get('team_size',''))
            put(out, 'source_url', r.get('detail_url',''))
            # Branding score (optional) - add if column exists
            branding_score = r.get('score')
            if branding_score and 'branding_score' in header_set:
                put(out, 'branding_score', branding_score)
            writer.writerow(out)
            existing_names.add(name.lower())
            rows_added += 1

    os.replace(tmp_path, UNIFIED_PATH)
    return rows_added

if __name__ == '__main__':
    yc_csv = latest_yc_csv()
    added = append_yc_to_unified(yc_csv)
    print(f"Appended {added} YC startup rows from {os.path.basename(yc_csv)} to {os.path.basename(UNIFIED_PATH)}")