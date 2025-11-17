# RFRNCS Lead Generation System

A professional multi-source lead generation automation system for identifying businesses with weak branding signals. Built for RFRNCS (https://www.rfrncs.in/) to discover potential clients through intelligent scraping, AI analysis, and automated workflows.

## Overview

This system ingests URLs from multiple platforms (Y Combinator, Justdial, Reddit, Twitter/X, LinkedIn, Instagram, Zomato), extracts business data, scores branding weakness, analyzes leads using Gemini AI, and delivers actionable insights via email and JSON storage.

## Features

- **Multi-Source Ingestion**: Email-triggered URL processing from 8+ platforms
- **Intelligent Extraction**: Domain-specific parsers (YC __NEXT_DATA__, Justdial LD+JSON, social meta tags)
- **Branding Score**: Quantifies weakness signals (missing website, poor social presence, incomplete descriptions)
- **AI Analysis**: Gemini 1.5 Pro generates structured verdicts with confidence scores
- **Automated Delivery**: JSON persistence + CSV email reports
- **n8n Workflows**: Fully importable, production-ready automation pipelines

## Repository Structure

```
lead-gen-system/
├── config/                      # Configuration files
│   └── n8n/                     # n8n workflow configs & schemas
├── data/                        # Scraped data outputs (CSV/JSON)
├── docs/                        # All documentation
│   ├── n8n/                     # n8n automation docs
│   │   └── N8N_AUTOMATION_PROMPT.md   # Complete system spec
│   ├── project_requirements.md
│   ├── QUICK_SETUP.md
│   └── QUICK_COMMAND_REFERENCE.md
├── logs/                        # Execution logs
├── scripts/
│   ├── javascript/n8n/         # n8n Function node code
│   └── python/
│       ├── scrapers/           # Web scraping modules
│       ├── utils/              # Utility scripts
│       └── main.py             # Main orchestration
├── analysis/                    # Analysis modules
├── .env.example
├── README.md
└── requirements.txt
```

## Quick Start

### 1. Python Scrapers Setup

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env
notepad .env  # Add your API keys
```

### 2. Run Scrapers

```powershell
# Scrape Y Combinator startups
python scripts\python\scrapers\yc_scraper.py --region India --max 200

# Scrape Justdial businesses
python scripts\python\scrapers\justdial_enriched_scraper.py --url "https://www.justdial.com/Mumbai/Restaurants" --target 100
```

### 3. n8n Automation Setup

```bash
1. Import config/n8n/lead_ingest_option_aplus.json into n8n
2. Set GEMINI_API_KEY environment variable
3. Configure IMAP/SMTP credentials
4. Activate workflow
5. Send test email with URL to trigger processing
```

## Documentation

- **[N8N_AUTOMATION_PROMPT.md](docs/n8n/N8N_AUTOMATION_PROMPT.md)** - Complete n8n system specification
- **[QUICK_SETUP.md](docs/QUICK_SETUP.md)** - Step-by-step setup guide
- **[QUICK_COMMAND_REFERENCE.md](docs/QUICK_COMMAND_REFERENCE.md)** - Common CLI commands

## Scoring System

| Score | Signals | Priority |
|-------|---------|----------|
| 0-2 | Strong brand identity | Low |
| 3-5 | Moderate gaps | Medium |
| 6-9 | Weak branding | High |

**Scoring Logic**: No website (+3), Short description (+2), No socials (+2), High engagement + poor branding (+2)

## Output Files

### Python Scrapers
- `data/yc_startups_*.csv` - Y Combinator companies
- `data/justdial_*.csv` - Justdial businesses
- `data/leads_prioritized.csv` - High-score leads

### n8n Automation
- `data/lead_*.json` - Individual lead records with AI analysis
- Email: `lead_*.csv` - Simplified CSV attachment

## Environment Variables

```bash
# Python Scrapers
GOOGLE_MAPS_API_KEY=your_key
JUSTDIAL_API_KEY=your_key

# n8n Automation
GEMINI_API_KEY=your_google_ai_studio_key
```

## Performance

- **Python scrapers**: 50-200 leads/run (5-15 min)
- **n8n workflow**: 5-15 sec/URL (including AI analysis)
- **Rate limits**: Gemini 60 req/min (free tier)

## Roadmap

- [ ] Database storage (PostgreSQL/Supabase)
- [ ] WHOIS enrichment
- [ ] Social profile discovery
- [ ] CRM integration (HubSpot/Pipedrive)
- [ ] Screenshot capture & visual branding analysis

## License

Proprietary - RFRNCS (https://www.rfrncs.in/)

---

**Built for RFRNCS** - Automated lead generation for businesses that need branding support.
