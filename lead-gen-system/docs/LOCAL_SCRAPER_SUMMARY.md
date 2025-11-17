# Local Business Scraper - Implementation Summary

## Overview
Built lightweight local business scrapers for **Justdial** and **Zomato** to identify businesses with weak digital presence (no website/phone) for lead generation.

## Files Created

### 1. `scrapers/local_business_scraper.py`
- **Purpose**: Requests+BeautifulSoup scraper for Justdial
- **Functions**:
  - `fetch_justdial_search()`: Fetch business listings
  - `extract_business_metadata()`: Extract name, address, website, phone, rating
  - `score_business()`: Score by digital gaps (+3 no website, +2 no phone)
  - `save_business_results()`: Save to CSV/JSON
  - `scrape_local_businesses()`: Main pipeline
- **Status**: ⚠️ **Blocked** - Justdial uses JavaScript rendering (React/Next.js)
- **Alternative**: Use existing `scrapers/justdial_scraper.py` (Selenium-based)

### 2. `scrapers/zomato_scraper.py`
- **Purpose**: Requests+BeautifulSoup scraper for Zomato restaurants
- **Functions**:
  - `fetch_zomato_search()`: Fetch restaurant listings
  - `extract_zomato_metadata()`: Extract restaurant data
  - `score_restaurant()`: Score by digital gaps
  - `save_zomato_results()`: Save to CSV/JSON
  - `scrape_zomato()`: Main pipeline
- **Status**: ⚠️ **Likely Blocked** - Zomato also uses heavy JavaScript (React)
- **Note**: May return limited results from static HTML

### 3. `scrapers/run_local_scraper.py`
- **Purpose**: Unified runner for both scrapers
- **Features**:
  - CLI args: `--source`, `--query`, `--city`, `--max-pages`
  - Runs Justdial and/or Zomato
  - Combines results and shows top leads
- **Usage**:
  ```powershell
  python scrapers/run_local_scraper.py --source justdial --query "cafes" --city "Mumbai" --max-pages 2
  ```

## Scoring Logic
```
score = 0
if no website: score += 3  # Prime target for website/branding
if no phone: score += 2     # Needs basic contact setup
```

Higher score = weaker marketing presence = better lead opportunity

## Test Results

### Run 1: Justdial Cafes Mumbai (1 page)
```
Status: HTTP 200
Content: 575KB HTML
Listings found: 20 (via basic selector heuristic)
Extraction: ALL FAILED - names "Unknown"
```

**Root Cause**: Justdial uses client-side rendering (JSX/React). Static HTML from `requests` doesn't contain business data.

**Evidence**:
- Found 34 `<script>` tags
- Found 5 JSON-LD scripts (but only schema.org metadata, not business listings)
- Found 277 containers with class `jsx-*` (React component classes)
- No traditional HTML selectors (`li.cntanr`, `div.store-details`, etc.) found
- Page title exists but no h4/h3 business name tags

## Recommendations

### Option 1: Use Existing Selenium Scraper ✅ RECOMMENDED
- File: `scrapers/justdial_scraper.py` (already exists)
- Uses Selenium WebDriver to render JavaScript
- More reliable for Justdial

### Option 2: Try Alternative Sources
Instead of Justdial/Zomato (both JS-heavy), target:
- **Google My Business** (via Google Maps API) - structured data
- **Yellow Pages India** - may have less JS
- **IndiaMART** - B2B directory
- **TradeIndia** - B2B leads (already attempted, blocked)

### Option 3: API-Based Approach
- **Google Places API**: Structured business data with website/phone fields
- **Yelp API** (if available in India)
- **Foursquare API**: Location-based business data

### Option 4: Enhance Current Implementation
Add Selenium fallback to `local_business_scraper.py` when requests fails:
```python
if not raw_results:
    print("⚠️  Switching to Selenium...")
    from selenium import webdriver
    # ... Selenium logic
```

## Current Status
- ✅ Architecture designed (modular functions)
- ✅ Scoring logic implemented
- ✅ CSV/JSON save functionality
- ✅ Unified runner with CLI
- ⚠️ Extraction blocked by JS rendering
- ⏸️ Testing paused pending solution choice

## Next Steps
1. **Decide**: Use existing Selenium scraper OR pivot to API/alternative sources
2. **If Selenium**: Test `justdial_scraper.py` with scoring logic additions
3. **If API**: Implement Google Places API scraper (requires API key)
4. **If Alternative**: Test Yellow Pages India or similar directories

## Data Output Format
```csv
name, address, website_present, phone_present, rating, reviews, score, phone, website, city, category
```

High-priority leads: `score >= 3` (no website or missing phone)

---

**Conclusion**: The lightweight requests-based approach hit anti-scraping/JS-rendering blocks. The existing Selenium scraper or API-based approaches are better suited for production use.
