import csv
import json
import glob
import os
from datetime import datetime

JD_URL = "https://www.justdial.com/Mumbai/Japanese-Restaurants/nct-10279229"
ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(os.path.dirname(ROOT), 'data')
PRIOR_PATH = os.path.join(ROOT, 'data', 'leads_prioritized.csv')


def latest_jd_json():
    files = glob.glob(os.path.join(DATA_DIR, 'justdial_mumbai_*.json'))
    if not files:
        raise FileNotFoundError('No JD JSON files found in data/')
    files.sort()
    with open(files[-1], 'r', encoding='utf-8') as f:
        return json.load(f), files[-1]


def compute_priority_score(row: dict) -> int:
    # Higher for weaker digital presence: no website/email/phone
    website = bool(row.get('website'))
    email = bool(row.get('email'))
    phone = bool(row.get('phone'))
    score = 0
    score += 70 if not website else 30
    if not email:
        score += 15
    if not phone:
        score += 10
    if score > 100:
        score = 100
    return int(score)


def append_scored_rows(jd_rows):
    # Load existing prioritized file
    with open(PRIOR_PATH, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        header = [h.strip() for h in header]
        existing = list(reader)
        existing_names = { (r.get('name') or '').strip().lower() for r in existing if r.get('name') }

    header_set = set(header)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    new_rows = []
    appended = 0
    for r in jd_rows:
        name = (r.get('name') or '').strip()
        if not name or name.lower() in existing_names:
            continue
        out = {h: '' for h in header}
        def put(k, v):
            if k in header_set:
                out[k] = v
        put('lead_type', 'restaurant_scored')
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
        score = compute_priority_score(r)
        put('priority_score', str(score))
        new_rows.append(out)
        existing_names.add(name.lower())
        appended += 1

    # Merge and sort by priority_score desc (non-numeric or missing treated as 0)
    all_rows = existing + new_rows
    def score_of(row):
        try:
            return float(row.get('priority_score') or 0)
        except Exception:
            return 0.0
    all_rows.sort(key=score_of, reverse=True)

    tmp_path = PRIOR_PATH + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8', newline='') as wf:
        writer = csv.DictWriter(wf, fieldnames=header)
        writer.writeheader()
        writer.writerows(all_rows)
    os.replace(tmp_path, PRIOR_PATH)
    return appended


if __name__ == '__main__':
    jd_rows, src = latest_jd_json()
    appended = append_scored_rows(jd_rows)
    print(f"Appended {appended} JD rows to leads_prioritized.csv (from {os.path.basename(src)})")
