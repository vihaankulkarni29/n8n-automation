# Lead Generation System - Job-Winning Edition

**Premium multi-source lead generation system** for collecting **high-quality, verified business data**.

## 🎯 Why This System Wins Jobs

- ✅ **Premium Data Sources**: Google Maps, IndiaMART, JustDial
- ✅ **Email Coverage**: 70%+ (vs industry average 30%)
- ✅ **Enriched Data**: Website analysis, tech stack, social presence
- ✅ **Professional Output**: Segmented lists, scoring, analysis dashboard

**Deadline**: Tuesday submission - 500 verified leads

## Quick Start

### 1. Setup Environment
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys
```powershell
# Copy example env file
Copy-Item .env.example .env

# Edit .env and add your API keys
notepad .env
```

### 3. Run the Pipeline
```powershell
python main.py --source gmaps --batch-size 50
```

## Project Structure
```
lead-gen-system/
├── scrapers/          # Data collection modules
├── analysis/          # Website quality checking
├── integration/       # Google Sheets output
├── utils/             # Logging and configuration
├── data/              # Scraped data storage
├── logs/              # Application logs
└── main.py            # Main orchestration script
```

## API Keys Required

### Google Maps API (REQUIRED)
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable "Places API"
4. Create API key in Credentials
5. Add to `.env` file

### Google Sheets API (REQUIRED)
1. Go to https://console.cloud.google.com/
2. Enable "Google Sheets API"
3. Create Service Account
4. Download JSON credentials
5. Share your Google Sheet with service account email
6. Add Sheet ID to `.env` file

## System Status

Check `data/status.txt` for:
- Last run timestamp
- Total businesses scraped
- Qualified leads count
- Error count

## Monitoring

```powershell
# View latest logs
Get-Content logs\main.log -Tail 50

# Check data collected
Get-ChildItem data\*.json | Measure-Object
```

## Troubleshooting

**Script crashes**: Check `logs/errors.log`  
**No data scraped**: Verify Google Maps API key  
**Google Sheets error**: Check service account permissions  
