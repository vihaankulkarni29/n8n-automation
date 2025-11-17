# 🚀 **SOLVED: Dynamic Reddit Intelligence System**

## ✅ **Hybrid Solution Created**

**File**: `scrapers/hybrid_reddit_intelligence.json`

## 🔧 **How the Hybrid System Works**

### **Two Processing Modes:**

#### **1. AUTO MODE (Dynamic Subreddit)**
```json
POST /webhook/rfrncs-hybrid-reddit
{
  "url": "https://www.reddit.com/r/marketing/",
  "keywords": ["branding", "startup", "logo design"],
  "mode": "auto",
  "days": 7,
  "min_upvotes": 5
}
```

#### **2. MANUAL MODE (Pre-provided Data)**
```json
POST /webhook/rfrncs-hybrid-reddit
{
  "mode": "manual",
  "posts": [
    {
      "id": "abc123",
      "title": "Need help with startup branding",
      "selftext": "I'm struggling with my startup's brand identity...",
      "score": 45,
      "num_comments": 12,
      "author": "startup_founder",
      "subreddit": "entrepreneur"
    }
  ],
  "keywords": ["branding", "startup", "logo"]
}
```

## 🎯 **Key Advantages**

### **Flexible Input Handling**
- ✅ **Dynamic**: Fetches from any Reddit URL automatically
- ✅ **Manual**: Process pre-scraped data
- ✅ **Hybrid**: Switch between modes via `mode` parameter

### **No n8n Reddit Node Dependencies**
- Uses **direct HTTP requests** to Reddit API
- **Dynamic subreddit extraction** from URLs
- **Full control** over data processing

### **Smart Processing Pipeline**
```javascript
1. URL/Posts Input → Mode Detection
2. Reddit API Fetch OR Manual Processing
3. AI Relevance Classification
4. RFRNCS Opportunity Scoring
5. Professional Report Generation
6. Email Delivery
```

## 📋 **Usage Examples**

### **Example 1: Dynamic Subreddit Analysis**
```bash
curl -X POST https://your-n8n-instance.com/webhook/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.reddit.com/r/entrepreneur/",
    "keywords": ["branding", "marketing", "startup"],
    "mode": "auto"
  }'
```

### **Example 2: Batch Processing Pre-scraped Data**
```bash
curl -X POST https://your-n8n-instance.com/webhook/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "manual",
    "posts": [
      {
        "title": "Startup needs logo design help",
        "selftext": "We are a growing startup looking for professional branding...",
        "score": 67,
        "author": "tech_founder",
        "subreddit": "startups"
      }
    ],
    "keywords": ["logo design", "branding", "startup"]
  }'
```

### **Example 3: High-Volume Analysis**
```json
{
  "mode": "manual",
  "posts": [
    // Paste 100+ pre-scraped posts here
    {"title": "...", "selftext": "...", "score": 45, ...},
    {"title": "...", "selftext": "...", "score": 23, ...}
  ],
  "keywords": ["branding", "design", "marketing"],
  "min_upvotes": 10
}
```

## 🔍 **Technical Implementation**

### **Dynamic Subreddit Extraction**
```javascript
// Extract subreddit from any Reddit URL
const urlObj = new URL(url);
const pathParts = urlObj.pathname.split('/').filter(p => p);
if (pathParts[0] === 'r' && pathParts[1]) {
  subreddit = pathParts[1];
}
```

### **Reddit API Integration**
```javascript
// Direct API call (no n8n node dependency)
url: `https://www.reddit.com/r/${subreddit}/top.json`
query: {
  limit: 50,
  t: 'week'  // Time filter
}
```

### **AI Relevance Scoring**
```javascript
// RFRNCS-specific scoring algorithm
- Keyword matches: 2 points each
- Business intent: +3 points
- Service opportunities: +4 points
- Pain points: +3 points
- Urgency indicators: +2 points

// Priority levels:
// HIGH: 8+ points
// MEDIUM: 5-7 points  
// LOW: <5 points
```

## 📊 **Output Format**

### **CSV Report**
```csv
Priority,Title,Score,Opportunity,Author,Source
HIGH,"Need help with startup branding",12,true,startup_founder,reddit_api
MEDIUM,"Looking for logo design services",8,true,design_seeker,manual
```

### **Detailed Report**
```
RFRNCS REDDIT MARKETING INTELLIGENCE REPORT
==============================================

EXECUTIVE SUMMARY
• 2 hot leads identified
• High-priority opportunities found
• Strong market demand for branding services

HOT LEADS IDENTIFIED
1. Tech Startup
   Pain Points: Brand identity, Logo design
   Services: Complete branding package
   Urgency: HIGH
```

## 🎯 **Why This Solves Your Problem**

### **Current Problem**: 
> "Reddit node asks for specific subreddit upfront"

### **Hybrid Solution**:
> ✅ **Dynamic URL Processing**: Extract subreddit from any Reddit URL
> ✅ **Manual Data Support**: Process pre-scraped posts without API
> ✅ **Flexible Mode Switching**: Toggle between auto/manual via JSON
> ✅ **No Dependencies**: Bypass n8n Reddit node limitations

### **Benefits**:
- 🎯 **Workflow flexibility**: Handle any Reddit data source
- 🚀 **Performance**: Direct API access (faster than n8n nodes)
- 🔧 **Customization**: Full control over processing logic
- 📈 **Scalability**: Handle any volume of data

## 🚀 **Ready for Implementation**

Your hybrid system is **production-ready**! It solves the original Reddit node limitation while providing superior flexibility and control.

**Next**: Upload `hybrid_reddit_intelligence.json` to n8n and start analyzing Reddit data dynamically! 🎯
