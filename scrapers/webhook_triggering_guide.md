# 🚀 **HOW TO TRIGGER YOUR REDDIT INTELLIGENCE WEBHOOK**

## 📋 **STEP-BY-STEP TRIGGERING GUIDE**

### **Step 1: Import Workflow to n8n**
1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Upload `scrapers/hybrid_reddit_intelligence.json`
4. **Activate** the workflow

### **Step 2: Find Your Webhook URL**
1. Click on the **"Webhook Trigger"** node
2. Copy the **Webhook URL** (will look like): 
   ```
   https://your-n8n-instance.com/webhook/rfrncs-hybrid-reddit
   ```

### **Step 3: Send HTTP Requests to Trigger**

## 🔥 **METHOD 1: Using curl (Command Line)**

### **Auto Mode - Dynamic Subreddit**
```bash
curl -X POST https://your-n8n-instance.com/webhook/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.reddit.com/r/entrepreneur/",
    "keywords": ["branding", "startup", "logo design", "rebranding"],
    "mode": "auto",
    "days": 7,
    "min_upvotes": 5
  }'
```

### **Manual Mode - Pre-scraped Data**
```bash
curl -X POST https://your-n8n-instance.com/webhook/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "manual",
    "posts": [
      {
        "title": "Need help with startup branding",
        "selftext": "I am a founder struggling with brand identity. Looking for professional help.",
        "score": 67,
        "num_comments": 15,
        "author": "startup_founder123",
        "subreddit": "entrepreneur",
        "url": "https://reddit.com/r/entrepreneur/comments/example",
        "permalink": "/r/entrepreneur/comments/example"
      }
    ],
    "keywords": ["branding", "startup", "logo design"]
  }'
```

## 🌐 **METHOD 2: Using Postman or REST Client**

### **1. Create New Request**
- **Method**: `POST`
- **URL**: Your webhook URL
- **Headers**: 
  ```
  Content-Type: application/json
  ```

### **2. Body (Raw JSON)**

#### **Auto Mode Example:**
```json
{
  "url": "https://www.reddit.com/r/marketing/",
  "keywords": ["branding", "startup", "logo design", "rebranding"],
  "mode": "auto",
  "days": 7,
  "min_upvotes": 5
}
```

#### **Manual Mode Example:**
```json
{
  "mode": "manual",
  "posts": [
    {
      "title": "Logo design for tech startup needed urgently",
      "selftext": "We are a growing B2B SaaS startup and need a complete brand identity overhaul. Current logo looks unprofessional.",
      "score": 89,
      "num_comments": 23,
      "author": "tech_lead",
      "subreddit": "startups",
      "url": "https://reddit.com/r/startups/comments/example",
      "permalink": "/r/startups/comments/example"
    }
  ],
  "keywords": ["branding", "logo design", "startup", "SaaS"],
  "min_upvotes": 10
}
```

## 📱 **METHOD 3: Using Browser (Simple Test)**

### **Quick Browser Test**
1. Open **Chrome/Firefox Developer Tools** (F12)
2. Go to **Console** tab
3. Paste this code:

```javascript
fetch('https://your-n8n-instance.com/webhook/rfrncs-hybrid-reddit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: "https://www.reddit.com/r/entrepreneur/",
    keywords: ["branding", "startup", "logo"],
    mode: "auto"
  })
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch((error) => console.error('Error:', error));
```

4. Press **Enter** to trigger

## ⚡ **METHOD 4: Automated Scheduling**

### **n8n Cron Trigger (Optional)**
Add a Cron node to run automatically:

```javascript
// Schedule: Every Monday at 9 AM
0 9 * * 1

// This will trigger the workflow automatically
```

## 📊 **EXPECTED RESPONSE**

### **Success Response**
```json
{
  "subreddit": "entrepreneur",
  "mode": "auto",
  "keywords": ["branding", "startup", "logo"],
  "total_posts_analyzed": 45,
  "relevant_posts_found": 12,
  "high_priority_posts": 3,
  "processed_at": "2025-11-17T02:57:17.677Z"
}
```

### **Email Delivery**
- 📧 **CSV Report**: Sent to `vihaankulkarni29@gmail.com`
- 📄 **Detailed Report**: Complete analysis
- 📊 **Intelligence Summary**: Executive overview

## 🎯 **QUICK TEST EXAMPLES**

### **Test 1: Simple Reddit Analysis**
```bash
curl -X POST https://your-n8n-instance.com/webhook/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.reddit.com/r/marketing/", "mode": "auto"}'
```

### **Test 2: Multiple Keywords**
```bash
curl -X POST https://your-n8n-instance.com/webhook/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.reddit.com/r/startups/",
    "keywords": ["branding", "logo", "design", "rebranding", "identity"],
    "mode": "auto",
    "min_upvotes": 3
  }'
```

### **Test 3: Batch Data Processing**
```bash
curl -X POST https://your-n8n-instance.com/webhook/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "manual",
    "posts": [
      {
        "title": "Need logo redesign ASAP",
        "selftext": "Our current branding is outdated and unprofessional",
        "score": 34,
        "author": "business_owner"
      }
    ],
    "keywords": ["logo", "branding", "design"]
  }'
```

## 🔧 **TROUBLESHOOTING**

### **Common Issues:**
1. **Webhook URL**: Make sure workflow is activated
2. **JSON Format**: Use valid JSON syntax
3. **HTTPS**: Use secure HTTPS URL
4. **Gemini API**: Ensure API key is configured

### **Testing Checklist:**
- ✅ Workflow imported and activated
- ✅ Webhook URL copied correctly
- ✅ JSON payload formatted properly
- ✅ Headers set to `Content-Type: application/json`
- ✅ Gemini API key configured in n8n

## 🎉 **READY TO TRIGGER!**

Choose any method above and start generating RFRNCS marketing intelligence from Reddit! The system will automatically:

1. **Process** your input (URL or posts)
2. **Analyze** content with AI
3. **Score** for RFRNCS opportunities
4. **Generate** professional reports
5. **Email** results to you

**🚀 Go trigger your first Reddit intelligence analysis!**