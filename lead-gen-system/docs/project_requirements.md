# GitHub Copilot Prompts for Lead Gen System

## Phase 1: Python Scrapers

### Prompt 1.1 - Google Maps Scraper
```
Create a Python script using requests and BeautifulSoup to scrape business listings from Google Maps API.
Requirements:
- Function search_google_maps(query, location, api_key) that returns list of businesses
- Extract: business_name, website, phone, address, industry
- Handle pagination for 100+ results
- Rate limiting: 1 request per 2 seconds
- Error handling for missing data
- Save results to JSON file
- Use Google Places API for structured data
```

### Prompt 1.2 - Justdial Scraper
```
Build a web scraper for Justdial.com to extract business listings.
Requirements:
- Use Selenium with headless Chrome for dynamic content
- Target categories: manufacturing, retail, services
- Extract: company name, website URL, phone, location, rating
- Implement retry logic for failed requests
- Save to CSV with proper encoding
- Add random delays between requests (2-5 seconds)
```

### Prompt 1.3 - IndiaMART Scraper
```
Create an IndiaMART business directory scraper using Scrapy framework.
Requirements:
- Spider class that crawls multiple industry categories
- Parse company profile pages for website URLs
- Extract contact details when available
- Respect robots.txt
- Implement concurrent requests (max 5)
- Export to JSON Lines format
```

## Phase 2: Website Analysis

### Prompt 2.1 - Website Checker
```
Build a Python module to analyze website quality with these functions:

1. check_website_exists(url) - validates URL and checks if site loads
2. check_mobile_responsive(url) - uses Selenium to test viewport sizes
3. get_page_speed_score(url, api_key) - calls Google PageSpeed Insights API
4. check_ssl_certificate(url) - verifies HTTPS and cert validity
5. get_last_modified(url) - extracts last-modified date from headers
6. calculate_overall_score(metrics_dict) - returns 0-100 score

Requirements:
- Timeout handling (10 seconds max)
- Return structured dict for each check
- Log errors to file
- Batch processing support for multiple URLs
```

### Prompt 2.2 - Screenshot Capture
```
Create a Python script to capture website screenshots and detect outdated design patterns.
Requirements:
- Use Playwright for reliable screenshots
- Capture full-page and mobile viewport
- Save images with timestamp and company name
- Implement basic image analysis: check for common 2000s-era patterns (flash, frames, table layouts)
- Return design_score: modern (10), average (5), outdated (1)
```

## Phase 3: Data Enrichment

### Prompt 3.1 - Contact Finder
```
Build a contact enrichment module that finds email addresses and decision-makers.
Requirements:
- Function find_email(company_name, domain) using Hunter.io API
- Function find_linkedin_profiles(company_name) using RapidAPI
- Verify email deliverability
- Extract job titles: Founder, CEO, CMO, Marketing Head
- Return dict with contact_name, email, title, linkedin_url
- Handle API rate limits with exponential backoff
```

## Phase 4: N8N Integration

### Prompt 4.1 - N8N Webhook Receiver
```
Create a Python Flask app that acts as webhook endpoint for n8n.
Requirements:
- POST endpoint /process-leads that receives company data JSON
- Triggers website analysis pipeline
- Returns structured results: {company, score, contacts, status}
- Implements queue system for batch processing
- Logs all requests to file
```

### Prompt 4.2 - Google Sheets Writer
```
Build a Python module to write lead data to Google Sheets using gspread library.
Requirements:
- Function authenticate_sheets(credentials_json) for OAuth
- Function append_lead(sheet_id, lead_data) to add rows
- Function update_lead_score(sheet_id, row_id, score) for updates
- Batch writing support for efficiency
- Handle duplicate detection by company name
- Format cells: scores as numbers, URLs as hyperlinks
```

## Phase 5: Orchestration Script

### Prompt 5.1 - Main Pipeline
```
Create the main orchestration script that ties all components together.
Requirements:
- Command-line interface with arguments: --source, --batch-size, --output
- Run scraper based on source (gmaps/justdial/indiamart)
- Process websites in batches of 50
- Enrich contacts for leads with score > 60
- Write to Google Sheets with proper error handling
- Generate summary report: total processed, qualified leads, errors
- Schedule daily runs using APScheduler
- Config file for API keys and settings (YAML)
```

## Phase 6: Utilities

### Prompt 6.1 - Configuration Manager
```
Create a config management utility for the lead gen system.
Requirements:
- Load settings from config.yaml: API keys, thresholds, file paths
- Validate all required keys are present
- Environment variable override support
- Function get_config(key, default=None)
- Separate configs for dev/prod environments
```

### Prompt 6.2 - Logger Setup
```
Build a centralized logging system for all modules.
Requirements:
- Configure Python logging with rotation (10MB files)
- Separate logs: scraping.log, analysis.log, enrichment.log, errors.log
- Format: timestamp, level, module, message
- Console output for important events
- Function setup_logger(name) returns configured logger
```

---

## Development Order
1. Start with Website Checker (2.1) - easiest to test
2. Build Google Maps Scraper (1.1) - reliable data source
3. Create Google Sheets Writer (4.2) - test data flow
4. Implement Contact Finder (3.1) - adds value to leads
5. Build Main Pipeline (5.1) - connect everything
6. Add other scrapers (1.2, 1.3) - scale data collection
7. Implement N8N webhook (4.1) - enable automation

## Testing Tips
- Test each module independently with sample data
- Use small batches (5-10 companies) during development
- Keep API keys in .env file, never commit to git
- Set up error notifications early

---

# IMPLEMENTATION PLAN

## ⚡ URGENT: 12-HOUR SPRINT PLAN
**Deadline**: Complete setup and start data collection within 12 hours
**Run Duration**: Until Tuesday (data submission deadline)
**Strategy**: MVP approach - build minimum viable components, skip nice-to-haves

---

## 🎯 CRITICAL PATH - NEXT 12 HOURS

### Hour 1-2: Rapid Setup & Core Infrastructure
**Goal**: Get Python environment ready with essential tools only

- [ ] Create minimal project structure (skip tests, screenshots, webhook for now)
- [ ] Install ONLY critical dependencies
- [ ] Set up basic logging (single file, simple format)
- [ ] Create basic config management (simple dict, no YAML complexity)
- [ ] **OUTPUT**: Working Python environment

### Hour 3-4: Google Maps Scraper (PRIORITY 1)
**Goal**: Get business data flowing ASAP

- [ ] Use Google Places API (fastest, most reliable)
- [ ] Implement basic `search_google_maps()` - no fancy features
- [ ] Extract: name, website, phone, address only
- [ ] Save to JSON immediately (no database)
- [ ] Test with 1 query, aim for 20+ results
- [ ] **OUTPUT**: JSON file with business data

### Hour 5-6: Website Checker (SIMPLIFIED)
**Goal**: Quick quality scoring to filter leads

- [ ] Implement ONLY essential checks:
  - `check_website_exists()` - HTTP 200 check
  - `check_ssl_certificate()` - HTTPS validation
  - Simple scoring: SSL=50 points, loads=50 points
- [ ] Skip: mobile responsive, PageSpeed API, screenshots
- [ ] Process in batches of 10
- [ ] **OUTPUT**: Scored leads in JSON

### Hour 7-8: Google Sheets Integration
**Goal**: Get data into deliverable format

- [ ] Google Sheets API setup (use service account for speed)
- [ ] Implement `append_lead()` only
- [ ] Simple columns: Company, Website, Phone, Score, Status
- [ ] No duplicate detection (accept duplicates for speed)
- [ ] Test with 10 leads
- [ ] **OUTPUT**: Leads visible in Google Sheet

### Hour 9-10: Simple Pipeline
**Goal**: Connect everything into automated flow

- [ ] Create `main.py` with basic flow:
  1. Scrape Google Maps
  2. Check websites
  3. Filter score > 40
  4. Write to Sheets
- [ ] Add basic error handling (try/except, continue on error)
- [ ] Log everything to single file
- [ ] **OUTPUT**: End-to-end pipeline running

### Hour 11-12: Deploy & Run
**Goal**: Start collecting real data

- [ ] Configure for continuous running
- [ ] Set up multiple search queries (10-20 industries/locations)
- [ ] Add simple scheduling (run every 30 minutes)
- [ ] Monitor first 2-3 runs
- [ ] Fix critical bugs only
- [ ] **OUTPUT**: System running autonomously

---

## 📋 ABSOLUTE MINIMUM VIABLE SYSTEM

### What We're Building (MVP):
```
1. Google Maps Scraper → 2. Basic Website Check → 3. Google Sheets Output
```

### What We're SKIPPING (for now):
- ❌ Justdial & IndiaMART scrapers (Google Maps enough)
- ❌ Contact enrichment (Hunter.io takes time)
- ❌ Screenshots (not critical for scoring)
- ❌ N8N webhook (direct Python execution)
- ❌ Mobile responsive testing
- ❌ PageSpeed API
- ❌ Complex configuration management
- ❌ Unit tests
- ❌ Retry logic (fail fast, move on)

### What We CAN Add Later (if time permits):
- ⏳ Contact finder (if finish early)
- ⏳ Better scoring algorithm
- ⏳ Duplicate detection

---

## 🚀 QUICK START COMMANDS

### Immediate Setup (Copy-paste these):
```powershell
# Navigate to project
cd "c:\Users\Vihaan\Desktop\references\n8n automation"

# Create structure
mkdir scrapers, analysis, integration, utils, data, logs

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install essentials ONLY
pip install requests google-api-python-client google-auth-httplib2 google-auth-oauthlib gspread python-dotenv

# Create .env file
@"
GOOGLE_MAPS_API_KEY=your_key_here
GOOGLE_SHEET_ID=your_sheet_id_here
"@ | Out-File -FilePath .env -Encoding utf8
```

---

## 📊 DATA COLLECTION TARGETS (Until Tuesday)

### Minimum Acceptable:
- **500 businesses scraped**
- **300 websites analyzed**
- **150 qualified leads** (score > 40)

### Optimal Goal:
- **2,000 businesses scraped**
- **1,500 websites analyzed**
- **500 qualified leads**

### Search Queries to Run (Priority Order):
1. "web design agency in Mumbai"
2. "digital marketing services Delhi"
3. "software development company Bangalore"
4. "small business consultants Pune"
5. "manufacturing companies Chennai"
6. "retail stores Hyderabad"
7. "restaurants Mumbai"
8. "hotels Goa"
9. "real estate agents Delhi"
10. "construction companies Bangalore"

---

## ⏰ HOURLY CHECKPOINTS

| Hour | Checkpoint | Go/No-Go Decision |
|------|------------|-------------------|
| 2 | Python environment working | If NO: Use system Python, skip venv |
| 4 | Google Maps returning data | If NO: Switch to web scraping Google search |
| 6 | Website checker scoring sites | If NO: Use simple domain validation only |
| 8 | Data flowing to Google Sheets | If NO: Export to CSV instead |
| 10 | Pipeline runs without crashing | If NO: Add more try/except blocks |
| 12 | System collecting data autonomously | If NO: Run manually every hour |

---

## 🆘 BACKUP PLAN (If Things Fail)

### If Google Places API doesn't work:
- Use Outscraper API (has free tier)
- Scrape Google Search results directly
- Use Yelp API instead

### If Google Sheets API is too complex:
- Export to CSV every run
- Manually import to Sheets once a day
- Use simpler Sheets library (pygsheets)

### If Website checker is too slow:
- Skip website analysis entirely
- Just validate domain exists (DNS lookup)
- Accept all businesses with websites

### If Nothing Works by Hour 8:
- **NUCLEAR OPTION**: Use existing lead gen tools
  - Apollo.io (free trial, 50 leads)
  - Lusha (free tier)
  - Manually scrape top 200 businesses

---

## 📈 MONITORING (ESSENTIAL)

### Create simple dashboard file `status.txt`:
```
Last Run: [timestamp]
Businesses Scraped: [count]
Websites Checked: [count]
Leads in Sheet: [count]
Errors: [count]
Next Run: [timestamp]
```

### Check every 2 hours:
- Look at `status.txt`
- Check Google Sheet row count
- Scan logs for errors
- Verify script still running

---

## 🔧 SIMPLIFIED TECH STACK

**Must Have:**
- Python 3.10+
- requests (HTTP calls)
- gspread (Google Sheets)
- Google Places API

**Nice to Have (add if time):**
- Selenium (for stubborn sites)
- APScheduler (for scheduling)

---

## Project Overview
**Goal**: Build an automated lead generation system that scrapes business data, analyzes website quality, enriches contact information, and outputs qualified leads to Google Sheets via N8N automation.

**Timeline**: 4-6 weeks (assuming 15-20 hours/week)

**Tech Stack**:
- Python 3.10+
- Selenium, Scrapy, BeautifulSoup, Playwright
- Flask (webhook server)
- Google Sheets API, Hunter.io, RapidAPI
- APScheduler (job scheduling)
- N8N (workflow automation)

---

## Phase-by-Phase Implementation

### **Week 1: Foundation & Core Infrastructure**

#### Day 1-2: Project Setup
- [ ] Create project structure:
  ```
  lead-gen-system/
  ├── scrapers/
  │   ├── __init__.py
  │   ├── google_maps.py
  │   ├── justdial.py
  │   └── indiamart.py
  ├── analysis/
  │   ├── __init__.py
  │   ├── website_checker.py
  │   └── screenshot_capture.py
  ├── enrichment/
  │   ├── __init__.py
  │   └── contact_finder.py
  ├── integration/
  │   ├── __init__.py
  │   ├── webhook_server.py
  │   └── sheets_writer.py
  ├── utils/
  │   ├── __init__.py
  │   ├── config.py
  │   └── logger.py
  ├── data/
  │   ├── raw/
  │   ├── processed/
  │   └── screenshots/
  ├── logs/
  ├── tests/
  ├── main.py
  ├── config.yaml
  ├── .env.example
  ├── requirements.txt
  └── README.md
  ```
- [ ] Set up virtual environment: `python -m venv venv`
- [ ] Create `requirements.txt` with initial dependencies
- [ ] Initialize Git repository, add `.gitignore`

#### Day 3-4: Utilities (Phase 6)
**Start here because all other modules depend on these**

- [ ] **Logger Setup (6.2)**
  - Implement `utils/logger.py`
  - Configure rotating file handlers
  - Test with sample logs
  - Expected output: 4 log files created with proper formatting

- [ ] **Configuration Manager (6.1)**
  - Implement `utils/config.py`
  - Create `config.yaml` template
  - Add environment variable support
  - Test loading and validation
  - Expected output: Config loaded successfully, env vars override YAML

#### Day 5-7: Website Checker (2.1)
**Easiest to test, immediate value**

- [ ] Install dependencies: `requests`, `selenium`, `certifi`
- [ ] Implement `analysis/website_checker.py`:
  - `check_website_exists()` - HTTP status validation
  - `check_ssl_certificate()` - SSL verification
  - `get_last_modified()` - Header parsing
  - `check_mobile_responsive()` - Selenium viewport testing
  - `get_page_speed_score()` - PageSpeed API integration
  - `calculate_overall_score()` - Weighted scoring algorithm
- [ ] Create unit tests with mock websites
- [ ] Test with 10 real websites, validate scores
- [ ] **Milestone**: Website analysis working end-to-end

---

### **Week 2: Data Collection & Output**

#### Day 8-10: Google Maps Scraper (1.1)
**Most reliable data source**

- [ ] Set up Google Places API credentials
- [ ] Implement `scrapers/google_maps.py`:
  - API authentication
  - `search_google_maps()` function
  - Pagination logic for 100+ results
  - Rate limiting (1 req/2 sec)
  - JSON export functionality
- [ ] Test with queries: "restaurants in Mumbai", "manufacturers in Delhi"
- [ ] Validate data quality (missing fields < 10%)
- [ ] **Milestone**: 100+ businesses scraped successfully

#### Day 11-14: Google Sheets Integration (4.2)
**Critical for data output**

- [ ] Set up Google Cloud project, enable Sheets API
- [ ] Download OAuth credentials JSON
- [ ] Install `gspread`, `google-auth` libraries
- [ ] Implement `integration/sheets_writer.py`:
  - `authenticate_sheets()` - OAuth flow
  - `append_lead()` - Single row insertion
  - `update_lead_score()` - Cell updates
  - Batch writing for performance
  - Duplicate detection by company name
  - Cell formatting (hyperlinks, numbers)
- [ ] Create test spreadsheet
- [ ] Test with 50 sample leads
- [ ] **Milestone**: Leads flowing to Google Sheets with proper formatting

---

### **Week 3: Enrichment & Additional Scrapers**

#### Day 15-17: Contact Finder (3.1)
**Adds high value to qualified leads**

- [ ] Sign up for Hunter.io API (free tier: 50 searches/month)
- [ ] Get RapidAPI key for LinkedIn search
- [ ] Implement `enrichment/contact_finder.py`:
  - `find_email()` - Hunter.io integration
  - `find_linkedin_profiles()` - RapidAPI search
  - Email verification logic
  - Exponential backoff for rate limits
  - Job title extraction (CEO, Founder, CMO, etc.)
- [ ] Test with 20 companies
- [ ] Validate email accuracy (manual check 5 samples)
- [ ] **Milestone**: Contact enrichment working for high-scoring leads

#### Day 18-19: Justdial Scraper (1.2)
**Supplements Google Maps data**

- [ ] Install Selenium, ChromeDriver
- [ ] Implement `scrapers/justdial.py`:
  - Headless Chrome setup
  - Category-based search
  - Dynamic content handling
  - Retry logic (3 attempts)
  - Random delays (2-5 sec)
  - CSV export
- [ ] Test with 3 categories
- [ ] Compare output with manual browsing
- [ ] **Milestone**: Alternative scraper operational

#### Day 20-21: IndiaMART Scraper (1.3)
**Third data source for comprehensive coverage**

- [ ] Install Scrapy framework
- [ ] Implement `scrapers/indiamart.py`:
  - Spider class for industry categories
  - Profile page parsing
  - robots.txt compliance
  - Concurrent requests (max 5)
  - JSON Lines export
- [ ] Test with 2 industries
- [ ] Validate against ToS
- [ ] **Milestone**: 3 scraping sources active

---

### **Week 4: Orchestration & Automation**

#### Day 22-25: Main Pipeline (5.1)
**Brings everything together**

- [ ] Install `argparse`, `APScheduler`
- [ ] Implement `main.py`:
  - CLI argument parsing (--source, --batch-size, --output)
  - Scraper routing logic
  - Batch processing (50 companies/batch)
  - Website analysis pipeline
  - Contact enrichment for score > 60
  - Google Sheets output
  - Summary report generation
  - Error aggregation and logging
- [ ] Test full pipeline with 10 companies
- [ ] Validate data flow: Scraper → Analysis → Enrichment → Sheets
- [ ] **Milestone**: End-to-end automation working

#### Day 26-27: Screenshot Capture (2.2)
**Visual quality assessment**

- [ ] Install Playwright: `playwright install`
- [ ] Implement `analysis/screenshot_capture.py`:
  - Full-page screenshot capture
  - Mobile viewport testing
  - Image storage with metadata
  - Basic pattern detection (frames, tables)
  - Design score calculation
- [ ] Test with 15 websites
- [ ] Store screenshots in `data/screenshots/`
- [ ] **Milestone**: Visual analysis complement

#### Day 28: Scheduling Setup
- [ ] Configure APScheduler for daily runs
- [ ] Set up cron expression: `0 9 * * *` (9 AM daily)
- [ ] Test with mock schedule (every 5 min)
- [ ] Add email/Slack notifications on completion
- [ ] **Milestone**: System runs autonomously

---

### **Week 5-6: N8N Integration & Polish**

#### Day 29-31: N8N Webhook Server (4.1)
**Enables external triggers**

- [ ] Install Flask, Flask-CORS
- [ ] Implement `integration/webhook_server.py`:
  - Flask app setup
  - POST `/process-leads` endpoint
  - JSON schema validation
  - Queue system (using Python Queue)
  - Background job processing
  - Status endpoint `/status/{job_id}`
  - Request logging
- [ ] Deploy locally, test with Postman
- [ ] Create N8N workflow:
  - Trigger: HTTP Request or Schedule
  - Action: Call webhook
  - Output: Parse results, send to Slack/email
- [ ] **Milestone**: N8N automation functional

#### Day 32-35: Testing & Refinement
- [ ] **Integration Testing**:
  - Run pipeline with 100 companies across all sources
  - Monitor error rates, success rates
  - Verify Google Sheets accuracy
  - Check contact enrichment quality
  - Validate screenshot storage

- [ ] **Performance Optimization**:
  - Profile slow functions
  - Optimize API calls (batch where possible)
  - Implement caching for repeated lookups
  - Reduce memory usage for large batches

- [ ] **Error Handling**:
  - Test network failures
  - Handle API rate limits gracefully
  - Validate malformed data inputs
  - Add retry logic everywhere

#### Day 36-40: Documentation & Deployment
- [ ] **Documentation**:
  - Complete README.md with setup instructions
  - Document API key acquisition process
  - Add troubleshooting guide
  - Create `.env.example` with all required keys
  - Write inline code documentation

- [ ] **Deployment Prep**:
  - Test on clean machine (VM or Docker)
  - Create Docker container (optional)
  - Set up production config.yaml
  - Configure production logging
  - Set up monitoring (healthchecks.io or UptimeRobot)

- [ ] **Final Testing**:
  - Production run with 500 companies
  - Validate all data outputs
  - Check scheduled runs
  - Test N8N webhook reliability

---

## Success Metrics

### Week 1
- ✅ Project structure created
- ✅ Logger and config working
- ✅ Website checker analyzes 10+ sites accurately

### Week 2
- ✅ 100+ businesses scraped from Google Maps
- ✅ Data flowing to Google Sheets with formatting

### Week 3
- ✅ Contact enrichment finds emails for 60%+ of leads
- ✅ All 3 scrapers operational

### Week 4
- ✅ Full pipeline processes 50 companies end-to-end
- ✅ Screenshots captured and analyzed
- ✅ Automated scheduling works

### Week 5-6
- ✅ N8N webhook integration complete
- ✅ System runs autonomously for 7 days
- ✅ Documentation complete, ready for handoff

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limits exceeded | High | Implement aggressive caching, use multiple API keys, add exponential backoff |
| Scrapers break due to site changes | High | Add health checks, implement fallback logic, monitor error logs daily |
| Google Sheets API quota exceeded | Medium | Batch writes, cache locally, use multiple service accounts |
| Poor email accuracy from Hunter.io | Medium | Use multiple enrichment services (Clearbit, Apollo), verify deliverability |
| Website analysis too slow | Medium | Implement async processing, reduce timeout, skip non-critical checks |
| N8N webhook unreliable | Low | Add retry logic, implement job queue, send failure notifications |

---

## Daily Development Workflow

1. **Start of day**: Pull latest code, review logs from scheduled runs
2. **Development**: Work on current phase component, write tests
3. **Testing**: Validate with sample data (5-10 items)
4. **Integration**: Test with previous components
5. **Commit**: Push working code with descriptive commit message
6. **End of day**: Update checklist, plan tomorrow's tasks

---

## Key Decision Points

### Week 1 Decision
- **Question**: Which website metrics matter most for scoring?
- **Answer**: Speed (30%), Mobile (25%), SSL (20%), Freshness (15%), Uptime (10%)

### Week 2 Decision
- **Question**: How to handle duplicate companies across scrapers?
- **Answer**: Use domain as unique key, merge data from multiple sources

### Week 3 Decision
- **Question**: What's the threshold for "qualified lead"?
- **Answer**: Score > 60 AND website exists AND has contact info

### Week 4 Decision
- **Question**: How to prioritize batch processing?
- **Answer**: Process highest potential leads first (based on industry, location)

---

## Post-Launch Optimization (Week 7+)

- [ ] A/B test different scoring algorithms
- [ ] Add machine learning for lead quality prediction
- [ ] Implement dashboard for real-time monitoring
- [ ] Add CRM integration (HubSpot, Salesforce)
- [ ] Scale to 1000+ leads/day
- [ ] Add email outreach automation
- [ ] Implement lead scoring based on engagement