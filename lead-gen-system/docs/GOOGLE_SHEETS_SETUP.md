# 📊 Google Sheets Integration Setup Guide

## Overview

The system can automatically upload your leads to Google Sheets with:
- **All_Leads** sheet with complete dataset
- **Separate sheets per venture type** (Restaurants, FinTech, Tech, etc.)
- Automatic formatting and deduplication

---

## 🔧 Setup Steps (One-Time)

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"New Project"** (top left)
3. Name: `lead-gen-system`
4. Click **"CREATE"**

### Step 2: Enable APIs

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"** → Click → **"ENABLE"**
3. Search for **"Google Drive API"** → Click → **"ENABLE"**

### Step 3: Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** → **"Service Account"**
3. Name: `lead-gen-bot`
4. Click **"CREATE AND CONTINUE"**
5. Role: Select **"Editor"** → Click **"CONTINUE"**
6. Click **"DONE"**

### Step 4: Download Credentials JSON

1. Click on the service account you just created
2. Go to **"KEYS"** tab
3. Click **"ADD KEY"** → **"Create new key"**
4. Select **"JSON"**
5. Click **"CREATE"** (file downloads automatically)
6. **Save this file as `credentials.json`** in your project root:
   ```
   c:\Users\Vihaan\Desktop\references\n8n automation\lead-gen-system\credentials.json
   ```

### Step 5: Configure Environment

Edit `.env` file and add:

```bash
GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
```

**Optional**: If you want to use an existing Google Sheet instead of creating new ones:

```bash
GOOGLE_SHEET_ID=your_spreadsheet_id_here
```

(Get the ID from the URL: `https://docs.google.com/spreadsheets/d/YOUR_ID_HERE/edit`)

---

## 🚀 Usage

### Option 1: Automatic Upload After Merging

After running the merger, your data is in `data/leads.csv` and `data/leads.xlsx`.

Upload to Google Sheets:

```powershell
python -m integration.sheets_writer
```

**Output:**
```
Uploading data/leads.csv to Google Sheets...
Successfully authenticated with Google Sheets
Created spreadsheet: https://docs.google.com/spreadsheets/d/...
Finished writing DataFrame to Google Sheets: https://docs.google.com/spreadsheets/d/...
{'success': True, 'sheet_url': 'https://...', 'worksheets': ['All_Leads', 'Restaurants', 'Tech', ...]}
```

### Option 2: Upload in Code

```python
from integration.sheets_writer import write_dataframe_to_sheets
import pandas as pd

# Load your leads
df = pd.read_csv('data/leads.csv')

# Upload to Google Sheets
result = write_dataframe_to_sheets(
    df,
    sheet_id=None,  # Creates new sheet, or provide existing ID
    split_by_venture=True  # Creates separate sheets per venture type
)

print(f"Sheet URL: {result['sheet_url']}")
print(f"Worksheets: {result['worksheets']}")
```

---

## 📋 What Gets Uploaded

### All_Leads Sheet

Complete dataset with all columns:
- name, venture_type, company_role, services
- industry, location, city, state, country
- website, email, phone
- employees, funding_usd, hiring, jobs_link
- rating, reviews, price_level
- source, source_url, collected_at

### Per-Venture Sheets

Separate sheets for each venture type:
- **Restaurants** (69 leads currently)
- **Tech** (18 leads currently)
- **Healthcare** (2 leads currently)
- **FinTech**, **Fashion**, **Education**, etc. (as they appear)

Each sheet contains the same columns but filtered by venture type.

---

## 🔐 Sharing & Permissions

### To Share with Others:

1. Open the spreadsheet URL from the upload output
2. Click **"Share"** (top right)
3. Add email addresses of people who need access
4. Set permissions (Viewer, Commenter, or Editor)

### To Make Service Account Owner:

If you want the service account to have full control:

1. Open an existing Google Sheet
2. Click **"Share"**
3. Add the service account email (from `credentials.json`, looks like: `lead-gen-bot@project-id.iam.gserviceaccount.com`)
4. Grant **"Editor"** permission
5. Add the Sheet ID to `.env`:
   ```
   GOOGLE_SHEET_ID=your_sheet_id
   ```

---

## 🔄 Complete Workflow

### Daily/Weekly Data Collection:

```powershell
# 1. Run scrapers
python scrapers/google_maps_premium.py
python scrapers/topstartups_scraper.py
python scrapers/indiamart_scraper.py
python scrapers/detailed_justdial_scraper.py

# 2. Merge all data
python utils/merge_datasets.py

# 3. Upload to Google Sheets
python -m integration.sheets_writer
```

**Result**: Fresh data in Google Sheets with automatic deduplication!

---

## 🎨 Customization

### Change Sheet Name:

Edit `integration/sheets_writer.py` line 302:

```python
spreadsheet = client.create(f"My Custom Name {datetime.now().strftime('%Y-%m-%d')}")
```

### Add Formatting:

```python
# After uploading, format headers
from integration.sheets_writer import write_dataframe_to_sheets, authenticate_sheets
import pandas as pd

df = pd.read_csv('data/leads.csv')
result = write_dataframe_to_sheets(df)

# Get client and format
client = authenticate_sheets()
spreadsheet = client.open_by_url(result['sheet_url'])
worksheet = spreadsheet.worksheet('All_Leads')

# Bold headers
worksheet.format('A1:Z1', {
    'textFormat': {'bold': True},
    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
})
```

---

## 🚨 Troubleshooting

### Error: "Authentication failed"

**Check:**
- `credentials.json` file exists in project root
- `.env` has `GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json`
- File path is correct (relative to project root)

**Fix:**
```powershell
# Verify file exists
Test-Path credentials.json

# Check .env
Get-Content .env | Select-String "GOOGLE"
```

---

### Error: "Failed to get/create worksheet"

**Cause**: Service account doesn't have permission to the sheet.

**Fix:**
- If using existing sheet (GOOGLE_SHEET_ID set): Share the sheet with service account email
- If creating new sheet: Remove GOOGLE_SHEET_ID from `.env` to create fresh sheet

---

### Error: "Credentials file not found"

**Check path**:
```powershell
python -c "import os; print('Project root:', os.getcwd()); print('Creds exist:', os.path.exists('credentials.json'))"
```

**Fix**: Ensure `credentials.json` is in the project root, not in a subfolder.

---

### Warning: "FutureWarning: DataFrame concatenation"

This is a pandas warning, safe to ignore. Data is processed correctly.

---

### No Data in Sheets

**Check:**
1. `data/leads.csv` exists and has data:
   ```powershell
   python -c "import pandas as pd; print(len(pd.read_csv('data/leads.csv')), 'rows')"
   ```
2. Run merger first: `python utils/merge_datasets.py`
3. Then upload: `python -m integration.sheets_writer`

---

## 📊 Google Sheets Features You Can Use

### Filters & Sorting

1. Select header row (row 1)
2. Click **Data** → **Create a filter**
3. Filter by venture_type, funding_usd, hiring, etc.

### Pivot Tables

1. **Data** → **Pivot table**
2. Rows: venture_type
3. Values: COUNT of name, AVERAGE of funding_usd
4. Analyze leads by category!

### Conditional Formatting

Highlight high-value leads:
1. Select funding_usd column
2. **Format** → **Conditional formatting**
3. Color scale: red (low) to green (high)

### Charts

Create funding distribution chart:
1. Select venture_type and funding_usd columns
2. **Insert** → **Chart**
3. Chart type: Column chart

---

## 💡 Pro Tips

### Tip 1: Scheduled Updates

Create a batch file `update_sheets.bat`:

```batch
@echo off
cd "c:\Users\Vihaan\Desktop\references\n8n automation\lead-gen-system"
python utils/merge_datasets.py
python -m integration.sheets_writer
echo Done! Check Google Sheets for latest data.
pause
```

Double-click to update sheets anytime!

---

### Tip 2: Version Control

Keep historical snapshots:
- Don't set GOOGLE_SHEET_ID in `.env`
- Each upload creates a new sheet with date: "Leads 2025-11-14"
- Compare versions over time

---

### Tip 3: Collaborative Filtering

Share with team and create filtered views:
1. **Data** → **Filter views** → **Create new filter view**
2. Name: "High Priority (>$50M funding + Hiring)"
3. Filter: funding_usd > 50000000 AND hiring = TRUE
4. Share the view link with team

---

### Tip 4: Data Validation

Add dropdowns for manual fields:
1. Select a column (e.g., "Status")
2. **Data** → **Data validation**
3. Criteria: List of items: "Hot Lead, Contacted, Closed, Lost"
4. Track lead progress!

---

## 🎯 Quick Reference

| Action | Command |
|--------|---------|
| Upload leads to Sheets | `python -m integration.sheets_writer` |
| Create new spreadsheet | Remove `GOOGLE_SHEET_ID` from `.env` |
| Update existing sheet | Set `GOOGLE_SHEET_ID` in `.env` |
| Test credentials | `python -c "from integration.sheets_writer import authenticate_sheets; print(authenticate_sheets())"` |
| Check current data | `python -c "import pandas as pd; df=pd.read_csv('data/leads.csv'); print(f'{len(df)} rows, {df[\"venture_type\"].value_counts().to_dict()}')"` |

---

## 📚 Next Steps

1. **Set up credentials** (Steps 1-5 above) ✅
2. **Run scrapers** to collect 500+ leads
3. **Merge data** with `python utils/merge_datasets.py`
4. **Upload to Sheets** with `python -m integration.sheets_writer`
5. **Share with team** and start qualifying leads!

---

**Questions?** Check the logs: `logs/main.log`

**Need help?** The code is in `integration/sheets_writer.py` - fully documented and failure-proof!
