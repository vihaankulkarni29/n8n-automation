# 🚀 **RFRNCS Webhook Lead Analyzer - Complete Guide**

## 📋 **Overview**
A webhook-powered n8n workflow that receives CSV data via HTTP POST, analyzes leads using AI agents, and emails comprehensive reports. Perfect for integrating with external systems that send lead data automatically.

## 🎯 **Workflow Architecture**
```
Webhook → Extract CSV → Parse Data → Loop Over Leads → Company Analysis AI → RFRNCS Fit AI → CSV Report → Email
```

## 🌐 **Webhook Endpoint**
- **Method**: `POST`
- **Path**: `rfrncs-webhook-leads`
- **Full URL**: `https://your-n8n-instance.com/webhook/rfrncs-webhook-leads`

## 📊 **Supported Input Formats**

### **Format 1: Direct CSV Text**
```json
POST /webhook/rfrncs-webhook-leads
Content-Type: application/json

{
  "csv": "name,website,description\n\"Tai Pei Restaurant\",\"https://taipei.com\",\"Authentic Asian cuisine\"\n\"Tech Startup Inc\",\"https://techstartup.com\",\"SaaS platform\""
}
```

### **Format 2: Alternative Field Name**
```json
{
  "csv_content": "name,website,description\n\"Company\",\"https://site.com\",\"Description\""
}
```

### **Format 3: JSON Array**
```json
[
  {
    "name": "Tai Pei Restaurant",
    "website": "https://taipei.com",
    "description": "Authentic Asian cuisine"
  },
  {
    "name": "Tech Startup Inc",
    "website": "https://techstartup.com",
    "description": "SaaS platform"
  }
]
```

### **Format 4: File Upload**
Send as `multipart/form-data` with CSV file attached as `data`.

## 🎮 **How to Use**

### **Step 1: Import & Activate**
1. Import `webhook_lead_analyzer.json` into n8n
2. Activate the workflow
3. Note the webhook URL from the Webhook Trigger node

### **Step 2: Send Data**
Use any HTTP client (curl, Postman, your application) to send CSV data:

#### **cURL Example:**
```bash
curl -X POST https://your-n8n-instance.com/webhook/rfrncs-webhook-leads \
  -H "Content-Type: application/json" \
  -d '{
    "csv": "name,website,description\n\"Tai Pei\",\"https://taipei.com\",\"Restaurant\"\n\"Tech Inc\",\"https://tech.com\",\"SaaS\""
  }'
```

#### **Postman Example:**
- Method: `POST`
- URL: `https://your-n8n-instance.com/webhook/rfrncs-webhook-leads`
- Headers: `Content-Type: application/json`
- Body:
```json
{
  "csv": "name,website,description\n\"Company\",\"https://site.com\",\"Description\""
}
```

### **Step 3: Receive Results**
- Workflow processes leads automatically
- CSV report generated with full analysis
- Email sent to `vihaankulkarni29@gmail.com` with attachment

## 📊 **CSV Input Requirements**
- **Headers Required**: `name`, `website`, `description` (flexible naming)
- **Format**: Standard CSV with quoted fields
- **Encoding**: UTF-8
- **Delimiter**: Comma (,)

**Sample CSV:**
```csv
name,website,description
"Tai Pei Authentic Asian Cuisine","https://taipei.com","Japanese restaurant in Mumbai"
"Clear","https://clear.in","Fintech company for tax filing"
"Sanitation and Health Rights in India","https://shri.org","Healthcare NGO"
```

## 📈 **Processing Flow**

### **1. Data Reception**
- Webhook receives HTTP POST request
- Extracts CSV data from multiple supported formats
- Validates data structure

### **2. CSV Parsing**
- Converts CSV text to structured JSON
- Handles quoted fields and special characters
- Creates individual lead objects

### **3. AI Analysis Pipeline**
- **Loop**: Processes each lead individually
- **Company Analysis AI**: Analyzes business model, products, market
- **RFRNCS Fit AI**: Evaluates branding/marketing service needs

### **4. Report Generation**
- Combines all analysis results
- Creates comprehensive CSV report
- Generates email with attachment

## 🎯 **AI Analysis Details**

### **Company Analysis Agent**
Analyzes each company and provides:
- **Company Overview**: What they do
- **Products/Services**: What they sell
- **Target Market**: Who they serve
- **Business Model**: How they make money
- **Industry**: Sector classification
- **Key Features**: Main offerings
- **Competitive Advantage**: What makes them unique

### **RFRNCS Fit Analysis Agent**
Evaluates RFRNCS service opportunities:
- **Fit Score**: 1-10 rating
- **Needs Branding Services**: true/false
- **Recommended Services**: Specific RFRNCS offerings
- **Budget Potential**: Estimated price range
- **Urgency Level**: high/medium/low
- **Conversion Probability**: Success likelihood
- **Reasoning**: Detailed explanation
- **Next Steps**: Recommended approach

## 📊 **Output CSV Format**
The final report includes all analysis fields:

```
Company Name,Website,Company Overview,Products Services,Target Market,Business Model,Industry,Key Features,Competitive Advantage,Fit Score,Needs Branding Services,Recommended Services,Budget Potential,Urgency Level,Conversion Probability,Reasoning,Next Steps
```

## 🔧 **Customization Options**

### **AI Agent Prompts**
Edit the prompts in AI agent nodes to:
- Focus on specific industries
- Include additional analysis criteria
- Customize scoring methodology
- Add company-specific questions

### **Webhook Path**
Change the webhook path in the Webhook Trigger node:
- Current: `rfrncs-webhook-leads`
- Custom: `your-custom-path`

### **Email Configuration**
Modify email settings in the Email node:
- Change sender/receiver addresses
- Customize subject and message
- Add CC/BCC recipients

## 📈 **Integration Examples**

### **From External Application:**
```javascript
// Node.js example
const axios = require('axios');

const csvData = `name,website,description
"Company A","https://companya.com","Description A"
"Company B","https://companyb.com","Description B"`;

await axios.post('https://your-n8n-instance.com/webhook/rfrncs-webhook-leads', {
  csv: csvData
});
```

### **From Zapier/Make:**
- **Trigger**: New CSV file in Google Drive
- **Action**: HTTP POST to webhook URL
- **Data**: CSV content in request body

### **From CRM System:**
- **Trigger**: New leads added
- **Export**: Leads as CSV
- **Send**: POST request to webhook

## 🔐 **Security & Error Handling**

### **Input Validation**
- Checks for valid CSV structure
- Handles missing fields gracefully
- Provides clear error messages

### **Error Responses**
- Invalid CSV: `"No CSV data found"`
- Empty data: `"Invalid CSV: Need headers and data"`
- Processing errors: Detailed error messages

### **Rate Limiting**
- Processes leads sequentially to avoid API limits
- Built-in delays between AI calls

## 📊 **Performance Metrics**

### **Processing Times**
- **1-5 leads**: 1-2 minutes
- **10-20 leads**: 3-5 minutes
- **50+ leads**: 10-15 minutes

### **Cost Considerations**
- Each AI agent call consumes API credits
- Gemini API pricing applies
- Optimize prompts to reduce token usage

## 🎯 **Use Cases**

### **Lead Generation Integration**
- Connect with lead gen tools (ZoomInfo, Hunter.io)
- Automatic analysis of new prospects
- CRM enrichment with AI insights

### **Sales Team Automation**
- Daily lead analysis reports
- Prioritized prospect lists
- Automated follow-up recommendations

### **Marketing Agency Operations**
- Bulk lead qualification
- Competitive analysis
- Opportunity identification

## 🚀 **Advanced Features**

### **Batch Processing**
- Handles large CSV files
- Processes leads in optimized batches
- Maintains analysis quality

### **Custom Scoring**
- Modify fit score calculations
- Add weighted criteria
- Include historical conversion data

### **Multi-format Support**
- CSV text, JSON arrays, file uploads
- Flexible input handling
- Automatic format detection

## 📞 **Monitoring & Debugging**

### **Webhook Logs**
- Check n8n execution logs
- Monitor webhook response times
- Track processing status

### **Error Troubleshooting**
- Verify webhook URL is correct
- Check CSV format and encoding
- Validate AI API credentials

## 🎉 **Ready for Integration!**

**Your webhook-powered lead analyzer is ready to receive CSV data from any source and deliver comprehensive AI-powered analysis reports!**

**Simply POST your CSV data to the webhook URL and get professional lead analysis delivered to your email automatically.** 🚀