# 🚀 **SPECIFIC POST REQUEST EXAMPLE**

## ✅ **EXACT COMMANDS FOR YOUR SETUP**

### **🔥 METHOD 1: Simple cURL Command**
```bash
curl -X POST http://localhost:5678/webhook-test/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.reddit.com/r/indianstartups/",
    "keywords": ["branding", "startup", "logo design", "marketing"],
    "mode": "auto"
  }'
```

### **🌐 METHOD 2: Postman**
1. **Create new request**
2. **Method**: `POST`
3. **URL**: `http://localhost:5678/webhook-test/rfrncs-hybrid-reddit`
4. **Headers**:
   ```
   Content-Type: application/json
   ```
5. **Body** (select "raw" and "JSON"):
```json
{
  "url": "https://www.reddit.com/r/indianstartups/",
  "keywords": ["branding", "startup", "logo design", "marketing"],
  "mode": "auto"
}
```

### **📱 METHOD 3: Browser JavaScript Console**
Open Chrome/Firefox Developer Tools (F12), go to Console, paste:

```javascript
fetch('http://localhost:5678/webhook-test/rfrncs-hybrid-reddit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: "https://www.reddit.com/r/indianstartups/",
    keywords: ["branding", "startup", "logo design", "marketing"],
    mode: "auto"
  })
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch((error) => console.error('Error:', error));
```

## ⚡ **QUICKEST COMMAND TO COPY-PASTE**

**Just run this in your terminal:**
```bash
curl -X POST http://localhost:5678/webhook-test/rfrncs-hybrid-reddit -H "Content-Type: application/json" -d "{\"url\": \"https://www.reddit.com/r/indianstartups/\", \"keywords\": [\"branding\", \"startup\", \"logo design\"], \"mode\": \"auto\"}"
```

## 📋 **PARAMETERS EXPLAINED**

```json
{
  "url": "https://www.reddit.com/r/indianstartups/",     ← The subreddit to analyze
  "keywords": ["branding", "startup", "logo design"],   ← What to look for
  "mode": "auto"                                        ← Dynamic processing
}
```

## 🎯 **WHAT WILL HAPPEN**

1. **Fetches** top posts from r/indianstartups
2. **Analyzes** content for branding/marketing opportunities  
3. **Scores** each post for RFRNCS relevance
4. **Generates** professional intelligence reports
5. **Emails** results to vihaankulkarni29@gmail.com

## 📊 **EXPECTED RESPONSE**

```json
{
  "subreddit": "indianstartups",
  "mode": "auto",
  "keywords": ["branding", "startup", "logo design", "marketing"],
  "total_posts_analyzed": 50,
  "relevant_posts_found": 8,
  "high_priority_posts": 2,
  "processed_at": "2025-11-17T02:59:49.193Z"
}
```

## 🔧 **TESTING OPTIONS**

### **Minimal Test**
```bash
curl -X POST http://localhost:5678/webhook-test/rfrncs-hybrid-reddit -H "Content-Type: application/json" -d '{"url": "https://www.reddit.com/r/indianstartups/", "mode": "auto"}'
```

### **Full Test with Custom Parameters**
```bash
curl -X POST http://localhost:5678/webhook-test/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.reddit.com/r/indianstartups/",
    "keywords": ["branding", "startup", "logo", "design", "marketing", "rebranding"],
    "mode": "auto",
    "days": 7,
    "min_upvotes": 5
  }'
```

## 🚨 **IF IT DOESN'T WORK**

### **Check List:**
1. ✅ Is n8n running on localhost:5678?
2. ✅ Is the workflow imported and activated?
3. ✅ Is the webhook path exactly: `/webhook-test/rfrncs-hybrid-reddit`?
4. ✅ Is your JSON payload properly formatted?

### **Troubleshooting Command:**
```bash
curl -v -X POST http://localhost:5678/webhook-test/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.reddit.com/r/indianstartups/", "mode": "auto"}'
```

**This will show detailed request/response information!**

## 🎉 **READY TO GO!**

**Copy the simple command above and run it in your terminal to start analyzing r/indianstartups for RFRNCS business opportunities!** 🚀
