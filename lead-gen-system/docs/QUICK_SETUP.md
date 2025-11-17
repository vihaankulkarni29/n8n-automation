# Quick Setup Guide - 12 Hour Sprint

## ✅ What's Already Done

1. ✓ Project structure created
2. ✓ Website checker module (failure-proof)
3. ✓ Google Sheets integration (failure-proof)
4. ✓ Main pipeline script (failure-proof)

## 🚀 What You Need To Do Now

### Step 1: Get Google Sheets Credentials (15 minutes)

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable "Google Sheets API" and "Google Drive API"
4. Create Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name it "lead-gen-bot"
   - Grant role: "Editor"
   - Click "Done"
5. Create Key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create New Key"
   - Choose "JSON"
   - Download the JSON file
6. Save the JSON file as `credentials.json` in your project folder

### Step 2: Create Google Sheet (2 minutes)

1. Go to https://sheets.google.com
2. Create a new blank spreadsheet
3. Name it "Lead Gen Data"
4. Copy the Sheet ID from URL (the long string between /d/ and /edit)
   - Example: `https://docs.google.com/spreadsheets/d/ABC123XYZ/edit`
   - Sheet ID is: `ABC123XYZ`
5. **IMPORTANT**: Share the sheet with the service account email
   - The email is in the credentials.json file (looks like: `lead-gen-bot@project-id.iam.gserviceaccount.com`)
   - Give "Editor" permissions

### Step 3: Configure Environment (2 minutes)

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` file and add:
   ```
   GOOGLE_SHEET_ID=your_sheet_id_here
   GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
   MIN_SCORE_THRESHOLD=40
   ```

### Step 4: Get Business Data (CRITICAL - Choose ONE Option)

**Option A: Manual Collection (Recommended for reliability)**

1. Go to Justdial/Google manually:
   - https://www.justdial.com/Mumbai/Restaurants/nct-10408936
   - https://www.justdial.com/Delhi/Food-Companies
   - https://www.justdial.com/Bangalore/Fashion-Companies

2. For each business, copy:
   - Business Name
   - Phone Number
   - Address
   - Website (if available)

3. Create a JSON file `data/manual_leads.json`:
   ```json
   [
     {
       "business_name": "Restaurant Name",
       "phone": "9876543210",
       "address": "Address here",
       "website": "https://example.com",
       "category": "Restaurants",
       "location": "Mumbai",
       "source": "manual"
     }
   ]
   ```

4. Repeat for 100-200 businesses

**Option B: Use Existing Data**

The system already has some JSON files in `data/` folder. You can use those:
- `data/up_and_coming_restaurants_Mumbai.json`
- `data/food_companies_Delhi.json`
- `data/fashion_companies_Bangalore.json`

**Option C: Data Entry Services (Fast but costs money)**

Use services like:
- Fiverr (search "data entry Justdial")
- Upwork
- Local data entry freelancers

Give them this template and ask for 500 entries ($10-50)

### Step 5: Run the Pipeline (2 minutes)

```powershell
# Process all JSON files in data/ folder
python main.py

# Or process a specific file
python main.py --input data/manual_leads.json

# With custom settings
python main.py --batch-size 200 --min-score 30 --sheet-id YOUR_SHEET_ID
```

### Step 6: Verify Results

1. Check the Google Sheet - you should see leads populated
2. Check `data/status.txt` for statistics
3. Check `logs/main.log` for detailed logs

## ⚡ Fastest Path to 500 Leads by Tuesday

**Day 1 (Today - 4 hours):**
- ✓ Setup complete (already done!)
- Get Google credentials (15 min)
- Collect 100 businesses manually from Justdial (2 hours)
- Test pipeline (30 min)
- Fix any issues (1 hour)

**Day 2 (Tomorrow - 4 hours):**
- Collect another 200 businesses (3 hours)
- Run pipeline, verify quality (1 hour)

**Day 3 (Monday - 4 hours):**
- Collect final 200 businesses (3 hours)
- Final pipeline run (30 min)
- Review and clean data (30 min)

**Tuesday Morning:**
- Submit the Google Sheet! ✓

## 🆘 Troubleshooting

### Pipeline runs but no data in Sheet
- Check if credentials.json exists
- Verify Sheet ID in .env file
- Confirm service account email has access to the sheet

### No qualified leads found
- Lower the min_score threshold: `--min-score 20`
- Check if JSON files have website data
- Some businesses might not have websites (expected)

### Import errors
```powershell
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

## 📊 Expected Results

With 500 businesses:
- ~300-400 will have websites
- ~150-250 will be "qualified" (score > 40)
- ~100-150 will have high scores (score > 60)

This is NORMAL and expected!

## 🎯 Success Checklist

- [ ] Google Service Account created
- [ ] Credentials.json downloaded
- [ ] Google Sheet created and shared
- [ ] .env file configured
- [ ] At least 100 businesses in data/ folder
- [ ] Pipeline runs successfully
- [ ] Data appears in Google Sheet
- [ ] Can continue collecting data and re-running

---

**Questions? Check logs/main.log for detailed error messages**
