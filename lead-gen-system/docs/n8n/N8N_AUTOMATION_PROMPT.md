# RFRNCS Universal Lead Generation Bot - Complete System Specification

## System Overview

Build a **universal, multi-platform lead generation bot** in n8n that:
1. Monitors email inbox for URLs from **14+ platforms** (Instagram, Twitter, LinkedIn, Facebook, TikTok, YouTube, Reddit, Y Combinator, Justdial, Zomato, Product Hunt, Crunchbase, Medium, Substack, and any generic website)
2. **Automatically detects platform** and applies platform-specific extraction logic
3. Extracts **multiple entities per page** (accounts, mentions, companies, products)
4. Normalizes all data into a **universal schema** (brand, service, instagram_id, email, phone, website, description)
5. Analyzes each lead using **Gemini AI** with marketing gap analysis
6. Generates **priority scores** (0-10) and **verdict** (High/Low priority)
7. Sorts results by priority and emails **formatted CSV report** with summary stats

**Target Use Case**: Identify businesses/creators with weak digital presence as potential clients for RFRNCS branding services (https://www.rfrncs.in/).

**Key Innovation**: Single workflow handles ALL platforms automatically - no manual source selection needed.

---

## Architecture

- **IMAP Email Polling**: Checks inbox every minute
- **Supported Platforms** (14+):
  - **Social**: Instagram, Twitter/X, LinkedIn, Facebook, TikTok, YouTube, Reddit
  - **Business**: Y Combinator, Justdial, Zomato, Product Hunt, Crunchbase
  - **Content**: Medium, Substack
  - **Generic**: Any website with structured data or meta tags

### Universal Processing Pipeline

```
Email Trigger (every 1 min, mark as read)
  ↓
Extract URL (regex from subject/body/html)
  ↓
Detect Platform (hostname-based classification)
  ↓
Fetch Page (HTTP request with 30s timeout, follow redirects)
  ↓
Extract Entities (platform-specific logic, multi-item output)
  ↓
Normalize to Universal Schema (brand, service, instagram_id, email, phone, website, description)
  ↓
Build AI Prompt (marketing gap analysis)
  ↓
Gemini Analysis (Flash model, priority scoring)
  ↓
Parse & Finalize (merge AI verdict + brand data)
  ↓
Sort by Priority Score (descending, 10 → 0)
  ↓
Convert to CSV (timestamped filename)
  ↓
Email CSV Report (formatted with stats and top leads preview)
```

**Key Feature**: Single linear pipeline - no branching, no conditionals. Platform detection drives extraction logic internally.

---

## Data Flow Specifications

### 1. Extract Query From Email
**Input**: Email with subject/body/html  
**Output**: `{ query: "URL or #hashtag" }`  
**Logic**:
- Match first `#[A-Za-z0-9_]+` pattern → return hashtag
- Else match first `https?://...` → return URL
- Scan subject, text body, then HTML body in order

### 2. Detect Source
**Input**: `{ query: "..." }`  
**Output**: `{ source_type: "yc"|"justdial"|"reddit"|"twitter"|"linkedin"|"instagram"|"zomato"|"instagram_hashtag"|"linkedin_hashtag"|"generic", value: "..." }`  
**Logic**:
- If starts with `#` → `instagram_hashtag` (default)
- Parse URL hostname and match:
  - `ycombinator.com/companies` → `yc`
  - `justdial.com` → `justdial`
  - `reddit.com` → `reddit`
  - `twitter.com` | `x.com` → `twitter`
  - `linkedin.com` → `linkedin`
  - `instagram.com` → `instagram`
  - `zomato.com` → `zomato`
  - else → `generic`

### 3. Branch: Hashtag vs URL

**IF Hashtag?** (Condition node)
- TRUE path → Build Hashtag Item (minimal stub object)
- FALSE path → HTTP Fetch → Quick Parse HTML → Extract Entities

### 4. Build Hashtag Item
**Output**:
```json
{
  "sourceType": "instagram_hashtag",
  "source_url": "#tag",
  "account_name": "",
  "bio": "",
  "profile_website": "",
  "profile_url": "",
  "followers": 0,
  "industry": "Unspecified"
}
```

### 5. HTTP Fetch
**Input**: `{ value: "https://..." }`  
**Config**: 
- URL: `={{$json.value || $json.url || $json.source_url}}`
- Response Format: `string`
- Timeout: 30s (default)

### 6. Quick Parse HTML
**Input**: `{ body: "HTML string" }`  
**Output**:
```json
{
  "sourceType": "detected_type",
  "source_url": "canonical or input URL",
  "name": "og:site_name or <title>",
  "description": "meta description or og:description",
  "website": "canonical URL",
  "metrics": {},
  "assets": {},
  "raw_html": "full HTML for next stage"
}
```
**Logic**:
- Extract `og:site_name` or `<title>` → name
- Extract `meta[name=description]` or `og:description` → description
- Extract `<link rel=canonical>` → canonical URL
- Detect source type from canonical hostname
- Preserve full HTML in `raw_html` for entity extraction

### 7. Extract Entities (Pre-Normalization Parser)
**Purpose**: Parse structured data from HTML to extract **multiple entities** per page  
**Input**: Item with `raw_html`, `source_url`, `sourceType`  
**Output**: Array of entity items (1 to N per input)

**Extraction Strategy by Source**:

#### YC (ycombinator.com/companies)
- **Method**: Parse `<script id="__NEXT_DATA__">` JSON
- **Deep Traversal**: Recursively search for objects with:
  - `typeof o.name === 'string'`
  - Has `o.website || o.www || o.url || o.slug`
- **Mapped Fields**:
  ```javascript
  {
    sourceType: 'yc',
    source_url: 'https://www.ycombinator.com/companies/' + slug,
    name: o.name,
    website: o.website || o.www || o.url,
    description: o.description || o.one_liner || o.shortDescription,
    industry: industries[0] || 'Unspecified',
    metrics: {},
    assets: {}
  }
  ```

#### Justdial (justdial.com)
- **Method**: Parse `<script type="application/ld+json">` blocks
- **Filter**: `@type` includes `LocalBusiness` or `Organization`
- **Mapped Fields**:
  ```javascript
  {
    sourceType: 'justdial',
    source_url: baseUrl,
    name: o.name,
    website: o.url,
    listing_description: o.description || address,
    phone: o.telephone,
    contact_info: { phone: o.telephone },
    metrics: { 
      rating: aggregateRating.ratingValue,
      reviews: aggregateRating.reviewCount 
    },
    assets: {},
    industry: 'Restaurants'
  }
  ```

#### Reddit (reddit.com)
- **Method**: Regex extraction from HTML
- **Extract**:
  - `og:title` → thread excerpt
  - `"author":"..."` from embedded JSON → author
  - `href="/user/..."` → author (fallback)
  - `"score":(\d+)` → upvotes
  - Extract all `href="https://..."` links excluding reddit.com → external website
- **Mapped Fields**:
  ```javascript
  {
    sourceType: 'reddit',
    source_url: baseUrl,
    author: author,
    thread_excerpt: ogTitle,
    website: firstNonRedditLink,
    profile_url: 'https://www.reddit.com/user/' + author,
    metrics: { upvotes: score },
    assets: {}
  }
  ```

#### Twitter/X (twitter.com, x.com)
- **Method**: Meta tag extraction
- **Extract**:
  - `og:title` → caption
  - `meta[name=author]` → author
  - External links (excluding twitter.com, x.com) → website
- **Mapped Fields**:
  ```javascript
  {
    sourceType: 'twitter',
    source_url: baseUrl,
    author: metaAuthor,
    caption: ogTitle,
    website: firstNonTwitterLink,
    profile_url: baseUrl,
    metrics: {},
    assets: {}
  }
  ```

#### LinkedIn (linkedin.com)
- **Method**: Meta tag extraction
- **Extract**:
  - `og:title` → caption
  - `og:description` → description
  - External links (excluding linkedin.com) → website
- **Mapped Fields**:
  ```javascript
  {
    sourceType: 'linkedin',
    source_url: baseUrl,
    author: '',
    caption: ogTitle,
    description: ogDesc,
    website: firstNonLinkedInLink,
    profile_url: baseUrl,
    metrics: {},
    assets: {}
  }
  ```

**Deduplication**: Apply `uniqBy` on `(name|author) + website + source_url` to remove duplicates within each page.

**Fallback**: If no entities extracted, return single item with source type, source_url, name, description, website from Quick Parse.

### 8. Merge Branches
**Type**: Merge node (passThrough mode)  
**Combines**: Hashtag items + Extracted entities → unified stream

### 9. Normalize to Common Schema
**Purpose**: Transform source-specific fields into unified schema  
**Output Schema**:
```json
{
  "source": "yc|justdial|reddit|twitter|linkedin|instagram_hashtag|linkedin_hashtag|zomato|generic",
  "source_url": "original URL",
  "name": "business/account name",
  "industry_category": "industry/vertical",
  "description": "bio/summary/listing description",
  "website": "official website URL",
  "website_present": true|false,
  "socials": {
    "profile": "social profile URL",
    "facebook": "...",
    "instagram": "...",
    "linkedin": "..."
  },
  "contact_info": {
    "email": "...",
    "phone": "..."
  },
  "metrics": {
    "followers": 0,
    "reviews": 0,
    "rating": 0.0,
    "upvotes": 0,
    "price_level": null
  },
  "assets": {
    "logo": "...",
    "cover_image": "...",
    "branding_quality": "poor|fair|good|unknown"
  }
}
```

**Normalization Rules by Source**:
- **YC**: name, industry → industry_category, description, website
- **Justdial/Zomato**: name, listing_description → description, website, contact_info {phone, email}, metrics {reviews, rating, price_level}
- **Instagram/LinkedIn Hashtag**: account_name → name, bio → description, profile_website → website, profile_url → socials.profile, followers → metrics.followers
- **Reddit/Twitter/LinkedIn**: author → name, thread_excerpt/caption → description, website, profile_url → socials.profile, metrics {followers, upvotes}
- **Generic**: name, description, website as-is

### 10. Compute Branding Score
**Purpose**: Quantify branding weakness (higher score = weaker brand = better lead)  
**Scoring Logic**:
```javascript
score = 0
if (!website_present) score += 3           // No website = strong signal
if (description.length > 0 && < 150) score += 2  // Short/incomplete description
if (!hasSocials) score += 2                // No social profiles linked
if ((followers >= 5000 || reviews >= 200) && brandingQuality === 'poor'|'unknown') {
  score += 2                                // High engagement but poor branding
}
return score  // Range: 0-9
```

**Output**: Append `score` field to each item

### 11. Build AI Prompt
**Purpose**: Prepare structured prompt for Gemini analysis  
**Prompt Template**:
```
You are a brand strategy analyst at rfrncs (https://www.rfrncs.in/). 
Analyze ONLY the provided data and return JSON with keys:
- verdict: "Needs RFRNCS branding support" | "Strong brand identity, low priority."
- reasoning: array of short bullets explaining the verdict
- confidence: 0-1 (float)

Data:
{
  "name": "...",
  "industry_category": "...",
  "description": "...",
  "website_present": true|false,
  "socials": {...},
  "metrics": {...},
  "assets": {...},
  "score": 5
}

Return JSON only.
```

**Output**: Append `__ai_prompt` field to each item

### 12. Gemini Analysis
**Config**:
- **Method**: POST
- **URL**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={{$env.GEMINI_API_KEY}}`
- **Body**:
  ```json
  {
    "contents": [
      {
        "parts": [
          { "text": "{{$json.__ai_prompt}}" }
        ]
      }
    ]
  }
  ```

**Response Shape**:
```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          { "text": "{\"verdict\":\"...\",\"reasoning\":[...],\"confidence\":0.85}" }
        ]
      }
    }
  ]
}
```

### 13. Parse Gemini Response
**Logic**:
- Extract `candidates[0].content.parts[0].text`
- Parse as JSON → `analysis` object
- **Fallback**: If parse fails, use default:
  ```json
  {
    "verdict": "Strong brand identity, low priority.",
    "reasoning": ["insufficient evidence"],
    "confidence": 0.2
  }
  ```

**Output**: Append `analysis` field to each item

### 14. Finalize
**Purpose**: Add audit trail and deduplication key  
**Logic**:
```javascript
timestamp = new Date().toISOString()
hash_key = djb2(name.toLowerCase() + '|' + website.toLowerCase() + '|' + source.toLowerCase())
// djb2 = simple hash function returning hex string
```

**Output**: Append `timestamp` and `hash_key` fields

### 15. Parallel Output

#### Path A: JSON → Binary → Write JSON File
- **Convert**: JSON → Binary (all fields)
- **Write**: `lead-gen-system/integration/n8n/out/lead_{{$json.hash_key}}.json`
- **Purpose**: Persistent storage, deduplication, audit trail

#### Path B: JSON → CSV → Email
- **Convert**: JSON → CSV file (spreadsheet format)
- **Filename**: `lead_{{$json.hash_key}}.csv`
- **Email Config**:
  - To: `vihaankulkarni29@gmail.com` (or configured address)
  - Subject: `RFRNCS Lead CSV`
  - Body: `Attached: latest lead CSV.`
  - Attachment: CSV file

---

## Configuration Requirements

### Environment Variables
```bash
GEMINI_API_KEY=your_google_ai_studio_api_key
```

### IMAP Email Trigger
- **Host**: `imap.gmail.com` (or provider)
- **Port**: 993 (SSL)
- **User**: Your email
- **Password**: App-specific password
- **Options**: 
  - Download Attachments: `false`
  - Allow Unauthorized Certs: `false`

### Email Send Node
- **SMTP Host**: `smtp.gmail.com`
- **Port**: 587 (TLS) or 465 (SSL)
- **From Email**: Sender address
- **Credentials**: Same as IMAP or separate

---

## Usage Workflow

### Step 1: Import Workflow
1. Copy `lead_ingest_option_aplus.json` into n8n
2. Import via: Settings → Import from File

### Step 2: Configure Credentials
1. Set `GEMINI_API_KEY` in n8n environment settings
2. Create IMAP credential in n8n
3. Create SMTP credential in n8n
4. Assign credentials to IMAP Email and Email Send nodes

### Step 3: Activate Workflow
1. Set workflow to "Active"
2. n8n begins monitoring IMAP inbox

### Step 4: Send Test Emails

**Example 1: YC Startup**
```
To: yourself@gmail.com
Subject: New lead source
Body: https://www.ycombinator.com/companies
```

**Example 2: Justdial Restaurant**
```
Subject: Check this out
Body: https://www.justdial.com/Mumbai/Korean-Restaurants/nct-10366486
```

**Example 3: Reddit Thread**
```
Body: https://www.reddit.com/r/startups/comments/abc123/...
```

**Example 4: Twitter Profile**
```
Body: https://twitter.com/someaccount
```

**Example 5: LinkedIn Post**
```
Body: https://www.linkedin.com/posts/...
```

**Example 6: Instagram Hashtag**
```
Body: #smallbusinessowner
```

### Step 5: Verify Output
1. **JSON Files**: Check `lead-gen-system/integration/n8n/out/lead_*.json`
2. **Email**: Receive CSV attachment in inbox
3. **n8n Logs**: Review execution logs for errors

---

## Expected Output Structure

### JSON File Example
```json
{
  "source": "yc",
  "source_url": "https://www.ycombinator.com/companies/example",
  "name": "Example Startup",
  "industry_category": "B2B Software",
  "description": "AI-powered analytics for SMBs",
  "website": "https://example.com",
  "website_present": true,
  "socials": {},
  "contact_info": {},
  "metrics": {},
  "assets": {},
  "score": 4,
  "analysis": {
    "verdict": "Needs RFRNCS branding support",
    "reasoning": [
      "Website exists but no social media presence",
      "Short description suggests incomplete brand story",
      "Score of 4 indicates moderate branding gaps"
    ],
    "confidence": 0.78
  },
  "timestamp": "2025-11-16T10:30:45.123Z",
  "hash_key": "a3f9c2b1"
}
```

### CSV Columns
- source
- source_url
- name
- industry_category
- description
- website
- website_present
- score
- analysis.verdict
- analysis.confidence
- timestamp

---

## Scoring Interpretation

| Score | Interpretation | Priority |
|-------|---------------|----------|
| 0-2 | Strong brand identity | Low |
| 3-5 | Moderate branding gaps | Medium |
| 6-9 | Weak/incomplete branding | High |

**High-priority leads** (score ≥ 6):
- No website
- No social presence
- Very short/missing descriptions
- High engagement but poor brand assets

---

## Extension Points

### Future Enhancements

1. **WHOIS Enrichment**
   - Check domain registration age
   - Extract registrant contact info

2. **Wappalyzer API**
   - Detect tech stack (WordPress, Shopify, custom)
   - Identify CMS/platform weaknesses

3. **Social Discovery**
   - Search for Twitter/Facebook/Instagram profiles by business name
   - Calculate social presence score

4. **t.co Link Expansion**
   - For Twitter/X, expand shortened URLs to real destinations

5. **Database Storage**
   - Replace file storage with PostgreSQL/Supabase
   - Implement true deduplication on hash_key
   - Track lead history and status changes

6. **Slack/Discord Notifications**
   - Real-time alerts for high-score leads
   - Daily digest of new leads

7. **Batch Processing**
   - Support bulk CSV upload of URLs
   - Process multiple URLs in single execution

8. **Screenshot Capture**
   - Use Puppeteer/Playwright to capture website screenshots
   - Analyze visual branding quality

9. **Competitor Analysis**
   - For YC startups, fetch competitors from same batch
   - Compare branding scores within cohort

10. **CRM Integration**
    - Push qualified leads to HubSpot/Pipedrive/Airtable
    - Auto-create deals for high-confidence verdicts

---

## Troubleshooting

### Common Issues

**Issue**: Import fails with "Invalid JSON"  
**Solution**: Ensure no comments in Function node code, proper escape sequences

**Issue**: Gemini returns 401 Unauthorized  
**Solution**: Check GEMINI_API_KEY is set correctly in n8n environment

**Issue**: IMAP Email not triggering  
**Solution**: 
- Verify IMAP is enabled on email provider
- Check credentials and app-specific password
- Confirm workflow is "Active"

**Issue**: Extract Entities returns empty array  
**Solution**: 
- Check if website uses JavaScript rendering (may need browser automation)
- Verify source type detection is correct
- Check `raw_html` field has content

**Issue**: CSV email not received  
**Solution**: 
- Check SMTP credentials
- Verify "To Email" address
- Check spam/junk folder
- Review n8n execution logs for email send errors

**Issue**: Duplicate leads in output  
**Solution**: 
- Deduplication happens within single execution via hash_key
- Cross-execution dedup requires database storage (future enhancement)

---

## Performance Considerations

- **Execution Time**: ~5-15 seconds per URL (depending on HTML size and Gemini latency)
- **Rate Limits**: 
  - Gemini API: 60 requests/minute (free tier)
  - IMAP: Typically no strict limits for personal accounts
- **Concurrency**: n8n processes one email at a time by default
- **Storage**: JSON files grow linearly; rotate/archive old files periodically

---

## Security Notes

- **API Keys**: Store in n8n environment variables, never hardcode
- **Email Credentials**: Use app-specific passwords, not main account passwords
- **Output Files**: Contain sensitive lead data; restrict filesystem access
- **CSV Emails**: Contain lead data; ensure secure email transport (TLS)

---

## Success Metrics

### KPIs to Track
1. **Leads Ingested**: Total count of URLs/hashtags processed
2. **Entities Extracted**: Average entities per URL (should be >1 for YC/Justdial)
3. **High-Score Leads**: Count of leads with score ≥ 6
4. **AI Confidence**: Average confidence of "Needs RFRNCS" verdicts
5. **Conversion Rate**: % of emailed leads that become clients (external tracking)

### Sample Dashboard (External Tool)
- Daily lead volume chart
- Source breakdown (YC vs Justdial vs Reddit, etc.)
- Score distribution histogram
- Top 10 highest-score leads table

---

## Deployment Checklist

- [ ] n8n instance running (cloud or self-hosted)
- [ ] Workflow imported and validated
- [ ] GEMINI_API_KEY configured
- [ ] IMAP credentials set and tested
- [ ] SMTP credentials set and tested
- [ ] Output directory exists: `lead-gen-system/integration/n8n/out/`
- [ ] Workflow activated
- [ ] Test email sent and processed successfully
- [ ] JSON file created in output directory
- [ ] CSV email received
- [ ] Score and analysis fields populated correctly

---

## Summary

This n8n automation turns **email-triggered URLs** from diverse platforms into **actionable, scored, AI-analyzed lead records** ready for outreach. It's designed for **RFRNCS** to discover businesses with weak branding signals, providing a continuous pipeline of high-potential clients.

**Core Value Proposition**: 
- **Zero manual scraping** – Just forward a link
- **Multi-source unification** – One schema for all platforms
- **AI-powered prioritization** – Gemini decides which leads need help most
- **Instant delivery** – CSV in inbox within seconds

**Philosophy**: 
*"Every URL is a potential client. Let automation find the ones who need you most."*
