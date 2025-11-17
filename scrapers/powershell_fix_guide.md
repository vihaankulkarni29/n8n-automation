# 🔧 **POWERSHELL VERSION - Fix the curl Command**

## ✅ **CORRECT POWERSHELL COMMANDS**

### **🚀 METHOD 1: PowerShell Native (Recommended)**
```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook-test/rfrncs-hybrid-reddit" -Method POST -ContentType "application/json" -Body '{"url": "https://www.reddit.com/r/indianstartups/", "keywords": ["branding", "startup", "logo design", "marketing"], "mode": "auto"}'
```

### **⚡ METHOD 2: One-Liner (Copy-Paste Ready)**
```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook-test/rfrncs-hybrid-reddit" -Method POST -ContentType "application/json" -Body '{"url": "https://www.reddit.com/r/indianstartups/", "keywords": ["branding", "startup", "logo design"], "mode": "auto"}'
```

### **📝 METHOD 3: Multi-Line (Easier to Read)**
```powershell
$body = @'
{
  "url": "https://www.reddit.com/r/indianstartups/",
  "keywords": ["branding", "startup", "logo design", "marketing"],
  "mode": "auto"
}
'@

Invoke-RestMethod -Uri "http://localhost:5678/webhook-test/rfrncs-hybrid-reddit" -Method POST -ContentType "application/json" -Body $body
```

### **🌐 METHOD 4: Using curl.exe (If Available)**
```powershell
curl.exe -X POST http://localhost:5678/webhook-test/rfrncs-hybrid-reddit -H "Content-Type: application/json" -d '{"url": "https://www.reddit.com/r/indianstartups/", "keywords": ["branding", "startup", "logo design"], "mode": "auto"}'
```

## 🎯 **WHY THE ORIGINAL COMMAND FAILED**

### **The Issue:**
- **Windows PowerShell** has `curl` as an alias for `Invoke-WebRequest`
- **Invoke-WebRequest** has different syntax than Unix curl
- **Unix curl syntax** (`curl -X POST`) doesn't work in PowerShell

### **The Solution:**
Use `Invoke-RestMethod` or `curl.exe` for proper HTTP requests in PowerShell.

## 📋 **COMPARISON: OLD vs NEW**

### **❌ OLD (Unix curl - won't work in PowerShell):**
```powershell
curl -X POST http://localhost:5678/webhook-test/rfrncs-hybrid-reddit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.reddit.com/r/indianstartups/", "mode": "auto"}'
```

### **✅ NEW (PowerShell native):**
```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook-test/rfrncs-hybrid-reddit" -Method POST -ContentType "application/json" -Body '{"url": "https://www.reddit.com/r/indianstartups/", "keywords": ["branding", "startup", "logo design"], "mode": "auto"}'
```

## 🛠️ **POWERShell PARAMETER EXPLANATION**

```powershell
Invoke-RestMethod
  -Uri "http://localhost:5678/webhook-test/rfrncs-hybrid-reddit"  # URL
  -Method POST                                                   # HTTP Method
  -ContentType "application/json"                               # Header
  -Body '{"url": "...", "mode": "auto"}'                        # JSON Data
```

## 🔍 **TESTING THE CONNECTION**

### **Quick Test (Check if n8n is running):**
```powershell
Invoke-RestMethod -Uri "http://localhost:5678/" -Method GET
```

### **Test Webhook (Simple version):**
```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook-test/rfrncs-hybrid-reddit" -Method POST -ContentType "application/json" -Body '{"url": "https://www.reddit.com/r/indianstartups/", "mode": "auto"}'
```

## 📱 **ALTERNATIVE: POSTMAN (Easiest)**

If PowerShell is giving you trouble, use **Postman**:

1. Download Postman from postman.com
2. Create new request:
   - **Method**: `POST`
   - **URL**: `http://localhost:5678/webhook-test/rfrncs-hybrid-reddit`
   - **Headers**: Add `Content-Type: application/json`
   - **Body**: 
   ```json
   {
     "url": "https://www.reddit.com/r/indianstartups/",
     "keywords": ["branding", "startup", "logo design", "marketing"],
     "mode": "auto"
   }
   ```

## 🎯 **READY TO RUN!**

**Copy Method 1 or 2 and paste into PowerShell - this will trigger your Reddit intelligence analysis!** 🚀

The system will:
1. **Analyze** r/indianstartups posts
2. **Find** branding/marketing opportunities
3. **Score** posts for RFRNCS relevance
4. **Email** intelligence reports to you
