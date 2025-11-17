import csv
import glob
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
PRIOR_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'leads_prioritized.csv')

def latest_yc_csv():
    files = glob.glob(os.path.join(DATA_DIR, 'yc_startups_*.csv'))
    if not files:
        raise FileNotFoundError('No YC startups CSV files found in data/')
    files.sort()
    return files[-1]

def compute_priority(row: dict) -> int:
    # Base on YC 'score' (0-9) plus bonus for missing website
    try:
        base = int(row.get('score') or 0)
    except Exception:
        base = 0
    if not row.get('website'):
        base += 10  # emphasize lack of website
    # Cap at 100
    return min(base, 100)

def append_prioritized(csv_path: str) -> int:
    with open(PRIOR_PATH, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        existing = list(reader)
        existing_names = { (r.get('name') or '').strip().lower() for r in existing if r.get('name') }

    header_set = set(header)
    def put(out, k, v):
        if k in header_set:
            out[k] = v

    with open(csv_path, 'r', encoding='utf-8', newline='') as yf:
        yreader = csv.DictReader(yf)
        yc_rows = list(yreader)

    # Filter: lacking proper branding OR no website
    candidates = [r for r in yc_rows if (not r.get('website')) or int(r.get('score') or 0) >= 8]

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_rows = []
    appended = 0
    for r in candidates:
        name = (r.get('name') or '').strip()
        if not name or name.lower() in existing_names:
            continue
        out = {h: '' for h in header}
        put(out, 'lead_type', 'yc_startup_scored')
        put(out, 'name', name)
        put(out, 'source', 'yc_directory')
        put(out, 'collected_at', now)
        put(out, 'industry', r.get('industry',''))
        put(out, 'location', r.get('location',''))
        put(out, 'website', r.get('website',''))
        put(out, 'employees', r.get('team_size',''))
        put(out, 'source_url', r.get('detail_url',''))
        score = compute_priority(r)
        put(out, 'priority_score', str(score))
        new_rows.append(out)
        existing_names.add(name.lower())
        appended += 1

    # Merge & sort
    def score_of(row):
        try:
            return float(row.get('priority_score') or 0)
        except Exception:
            return 0.0
    all_rows = existing + new_rows
    all_rows.sort(key=score_of, reverse=True)

    tmp_path = PRIOR_PATH + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8', newline='') as wf:
        writer = csv.DictWriter(wf, fieldnames=header)
        writer.writeheader()
        writer.writerows(all_rows)
    os.replace(tmp_path, PRIOR_PATH)
    return appended

if __name__ == '__main__':
    yc_csv = latest_yc_csv()
    appended = append_prioritized(yc_csv)
    print(f"Appended {appended} YC prioritized rows from {os.path.basename(yc_csv)} to {os.path.basename(PRIOR_PATH)}")