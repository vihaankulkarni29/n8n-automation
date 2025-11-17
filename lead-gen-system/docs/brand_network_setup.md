# Brand Network Crawler - Setup Guide

## Instagram Rate Limit Encountered

Instagram has temporarily rate-limited API requests from this system due to multiple requests in a short period.

### What happened:
- Analyzed @khalidwalb earlier (50+ posts)
- Attempted to enrich 7 brand profiles
- Tried to crawl 4 new seed brands
- Instagram detected automated access and applied temporary rate limit (401 errors)

### When it will reset:
Typically **30-60 minutes** from last request attempt.

---

## How to Run Brand Network Crawler

### Option 1: Wait for Rate Limit Reset (Recommended)

**After 30-60 minutes**, run:

```powershell
cd "c:\Users\Vihaan\Desktop\references\n8n automation\lead-gen-system"
C:/Users/Vihaan/AppData/Local/Programs/Python/Python314/python.exe influencer_analysis/brand_network_crawler.py
```

### Option 2: Use Authentication (Better Rate Limits)

Set environment variables before running:

```powershell
$env:INSTAGRAM_USERNAME = "your_instagram_username"
$env:INSTAGRAM_PASSWORD = "your_instagram_password"

C:/Users/Vihaan/AppData/Local/Programs/Python/Python314/python.exe influencer_analysis/brand_network_crawler.py
```

**Or add to .env file:**
```
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
```

---

## What the Crawler Will Do

### Seed Brands (Already Added):
- @dotcombubble
- @killhouse
- @infectedclo
- @nvmbr

### Crawling Process:
1. **Depth 0**: Analyze seed brands
   - Get profile info (followers, verified, bio)
   - Scan last 30 posts for @mentions and tags
   
2. **Depth 1**: Analyze discovered brands
   - Follow @mentions from seed brands
   - Only include brands with 500+ followers
   
3. **Depth 2**: Analyze 2nd degree connections
   - Follow @mentions from 1st degree brands
   - Build complete network graph

### Output Files:
- `data/brand_network_brands_TIMESTAMP.csv` - All discovered brands with profiles
- `data/brand_network_connections_TIMESTAMP.csv` - Network graph (who mentions whom)

---

## Expected Results

Based on similar streetwear brand networks:
- **Seed brands**: 4
- **1st degree connections**: 15-30 brands (mentioned by seed brands)
- **2nd degree connections**: 50-150 brands (mentioned by 1st degree)
- **Total network**: 70-180+ brands

### What You'll Get:
- Full Instagram profiles (followers, verified status, business account)
- Product categories (from captions and mentions)
- Brand collaboration networks
- Influencer partnerships
- Similar/competitor brands

---

## After Crawling Completes

### 1. Review Discovered Brands
```powershell
# Open in Excel or check CSV
explorer data\brand_network_brands_*.csv
```

### 2. Merge into Unified Leads
```powershell
C:/Users/Vihaan/AppData/Local/Programs/Python/Python314/python.exe utils/merge_all_leads.py
```

### 3. Update Excel Workbook
```powershell
C:/Users/Vihaan/AppData/Local/Programs/Python/Python314/python.exe utils/publish_influencer_leads.py
```

---

## Troubleshooting

### Still Getting Rate Limit Errors?
- Wait longer (try 2 hours)
- Use different IP (mobile hotspot, VPN)
- Use authenticated session (login with Instagram account)

### Login Failed?
- Check username/password
- Instagram may require 2FA verification
- Try logging in manually first on browser
- Use session file (instaloader creates automatically after first login)

### Discovered Brands Have Low Followers?
Adjust threshold in script:
```python
min_followers_threshold=500  # Change to 1000, 5000, etc.
```

---

## Privacy Note

✅ **Your credentials have been removed from the code.**

The script now uses environment variables for authentication (optional).
No credentials are stored in any files.

---

## Next Steps When Rate Limit Resets

Run the crawler with environment variables or just wait and run without auth:

```powershell
# Simple run (no auth)
cd "c:\Users\Vihaan\Desktop\references\n8n automation\lead-gen-system"
C:/Users/Vihaan/AppData/Local/Programs/Python/Python314/python.exe influencer_analysis/brand_network_crawler.py

# With auth (better limits)
$env:INSTAGRAM_USERNAME = "your_username"
$env:INSTAGRAM_PASSWORD = "your_password"
C:/Users/Vihaan/AppData/Local/Programs/Python/Python314/python.exe influencer_analysis/brand_network_crawler.py
```

Expected runtime: 5-15 minutes depending on network size.
