# Google Maps API Setup Guide

## Step-by-Step Instructions

### Step 1: Go to Google Cloud Console
1. Open your browser and go to: **https://console.cloud.google.com/**
2. Sign in with your Google account

### Step 2: Create a New Project (or Select Existing)
1. Click on the project dropdown at the top (next to "Google Cloud")
2. Click **"NEW PROJECT"**
3. Enter project name: `lead-gen-system` (or any name you prefer)
4. Click **"CREATE"**
5. Wait for project creation (takes 10-20 seconds)
6. Select your new project from the dropdown

### Step 3: Enable Places API
1. In the left sidebar, click **"APIs & Services"** → **"Library"**
   - Or go directly to: https://console.cloud.google.com/apis/library
2. In the search box, type: **"Places API"**
3. Click on **"Places API"** from the results
4. Click the blue **"ENABLE"** button
5. Wait for it to enable (takes a few seconds)

### Step 4: Create API Key
1. In the left sidebar, click **"APIs & Services"** → **"Credentials"**
   - Or go to: https://console.cloud.google.com/apis/credentials
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"API key"**
4. Your API key will be created and shown in a popup
5. **COPY THIS KEY IMMEDIATELY** - it looks like: `AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 5: Restrict API Key (Important for Security)
1. In the API key popup, click **"RESTRICT KEY"** (or click the key name)
2. Under "API restrictions":
   - Select **"Restrict key"**
   - Click **"Select APIs"** dropdown
   - Search and check: **"Places API"**
   - Click **"OK"**
3. Click **"SAVE"** at the bottom

### Step 6: Enable Billing (Required for Places API)
⚠️ **Important**: Places API requires a billing account, BUT you get $200 free credit per month

1. Go to **"Billing"** in the left sidebar
2. Click **"LINK A BILLING ACCOUNT"**
3. Click **"CREATE BILLING ACCOUNT"**
4. Fill in your details (credit card required but won't be charged within free tier)
5. Accept terms and click **"START MY FREE TRIAL"**

**Free Tier Limits:**
- $200 free credit per month
- Places API: First ~40,000 searches free (within $200 credit)
- You'll get ~28,000 place details requests free per month

### Step 7: Add API Key to Project
1. Open your project folder in VS Code
2. Navigate to: `lead-gen-system` folder
3. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item ".env.example" ".env"
   ```
4. Open `.env` file
5. Replace `your_google_maps_api_key_here` with your actual API key:
   ```
   GOOGLE_MAPS_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. Save the file

### Step 8: Test Your API Key
Run this test command in PowerShell:

```powershell
# Test if API key works (replace YOUR_API_KEY with your actual key)
$apiKey = "YOUR_API_KEY"
$testUrl = "https://maps.googleapis.com/maps/api/place/textsearch/json?query=restaurants+in+Mumbai&key=$apiKey"
Invoke-RestMethod -Uri $testUrl
```

If it works, you'll see JSON data with restaurant listings!

---

## Quick Reference

**What you need:**
- ✅ Google account
- ✅ Credit card (for billing setup, won't be charged in free tier)
- ✅ 10-15 minutes

**API Key format:**
```
AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Cost estimate for our project:**
- Target: 2,000 businesses by Tuesday
- Estimated cost: ~$0-10 (well within $200 free credit)

---

## Troubleshooting

### "API key not valid" error
- Wait 2-3 minutes after creating the key (propagation delay)
- Ensure Places API is enabled
- Check if billing is activated

### "This API project is not authorized to use this API"
- Make sure you enabled "Places API" specifically
- Check API restrictions allow Places API

### "You have exceeded your rate limit"
- Using free tier rate limit (100 requests per 100 seconds)
- Add delays between requests (we already handle this in code)

---

## Alternative: Use Outscraper (Backup Option)

If Google Maps API is too complex, try Outscraper:

1. Go to: https://outscraper.com/
2. Sign up (free tier: 1,000 credits/month)
3. Get API key from dashboard
4. Much simpler setup, no billing required for free tier
