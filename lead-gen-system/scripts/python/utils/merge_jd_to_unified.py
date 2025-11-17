import csv
import json
import glob
import os
from datetime import datetime

JD_URL = "https://www.justdial.com/Mumbai/Japanese-Restaurants/nct-10279229"
UNIFIED_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'leads_unified.csv')
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def load_latest_jd_json():
    files = glob.glob(os.path.join(DATA_DIR, 'justdial_mumbai_*.json'))
    if not files:
        raise FileNotFoundError('No JD JSON files found in data/')
    files.sort()
    with open(files[-1], 'r', encoding='utf-8') as f:
        return json.load(f), files[-1]

def append_to_unified(jd_rows):
    # Partition: no-website first, then has website
    no_web = [r for r in jd_rows if not r.get('website')]
    has_web = [r for r in jd_rows if r.get('website')]
    ordered = no_web + has_web

    with open(UNIFIED_PATH, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        header = [h.strip() for h in header]
        existing = list(reader)
        existing_names = { (r.get('name') or '').strip().lower() for r in existing if r.get('name') }

    tmp_path = UNIFIED_PATH + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8', newline='') as wf:
        writer = csv.DictWriter(wf, fieldnames=header)
        writer.writeheader()
        for r in existing:
            writer.writerow(r)
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        appended = 0
        header_set = set(header)
        for r in ordered:
            name = (r.get('name') or '').strip()
            if not name or name.lower() in existing_names:
                continue
            out = {h: '' for h in header}
            # Assign only if column exists
            def put(k, v):
                if k in header_set:
                    out[k] = v
            put('lead_type', 'restaurant')
            put('name', name)
            put('source', 'justdial')
            put('collected_at', now)
            put('industry', 'Restaurants')
            put('location', r.get('address',''))
            put('city', 'Mumbai')
            put('country', 'India')
            put('website', r.get('website',''))
            put('email', r.get('email',''))
            put('phone', r.get('phone',''))
            put('rating', r.get('rating',''))
            put('reviews', r.get('reviews',''))
            put('price_level', r.get('pricing',''))
            put('source_url', JD_URL)
            writer.writerow(out)
            existing_names.add(name.lower())
            appended += 1
    os.replace(tmp_path, UNIFIED_PATH)
    return appended

if __name__ == '__main__':
    jd_rows, fp = load_latest_jd_json()
    appended = append_to_unified(jd_rows)
    print(f"Merged from {os.path.basename(fp)} -> {os.path.basename(UNIFIED_PATH)} | appended {appended}")
