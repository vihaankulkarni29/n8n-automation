# 🚀 **Simple RFRNCS Lead Analyzer - Quick Start Guide**

## 📋 **Overview**
A streamlined n8n workflow for analyzing leads from CSV files. Uses AI agents to understand what companies do and assess their fit for RFRNCS branding services.

## 🎯 **Workflow Architecture**
```
Manual Trigger → CSV Reader → Loop Over Leads → Company Analysis AI → RFRNCS Fit AI → CSV Report → Email
```

## 📊 **CSV Input Format**
Your CSV should have these columns (flexible naming):
- `name` or `company` - Company name
- `website` - Company website URL
- `description` or `about` - Company description

**Sample CSV:**
```csv
name,website,description
"Tai Pei Restaurant","https://taipei.com","Authentic Asian cuisine restaurant"
"Tech Startup Inc","https://techstartup.com","SaaS platform for small businesses"
```

**Important**: Save your CSV file and upload it when prompted by the workflow.

## 🛠️ **Setup Steps**

### **1. Import Workflow**
1. Open n8n dashboard
2. Go to **Workflows** → **Import from File**
3. Upload `simple_lead_analyzer.json`
4. **Activate** the workflow

### **2. Configure AI Agents**
The workflow has two AI agent nodes with placeholder prompts. Customize them:

#### **Company Analysis Agent** (First AI)
- **Purpose**: Analyzes what the company does, sells, target market, etc.
- **Current Prompt**: Basic analysis - you can enhance it
- **Output**: JSON with company details

#### **RFRNCS Fit Analysis Agent** (Second AI)
- **Purpose**: Evaluates if company needs RFRNCS services
- **Current Prompt**: Basic fit assessment - customize for your needs
- **Output**: JSON with fit score, recommended services, budget potential

### **3. Configure Email**
- **From/To**: Both set to `vihaankulkarni29@gmail.com`
- **Subject**: Auto-generated with lead count
- **Attachment**: CSV report with all analysis

## 🎮 **How to Use**

### **Step 1: Prepare CSV**
Create a CSV file with your leads data.

### **Step 2: Trigger Workflow**
1. Go to your workflow in n8n
2. Click **"Test workflow"** button
3. The workflow will prompt for CSV file upload
4. Upload your CSV file
5. Click **Execute**

### **Step 3: Monitor Progress**
- Watch the workflow execute through each lead
- AI agents will analyze each company
- Final CSV is generated and emailed

## 📊 **Output CSV Format**
The final CSV will contain these columns:

**Company Analysis:**
- `company_name` - Company name
- `website` - Website URL
- `company_overview` - What they do
- `products_services` - What they sell
- `target_market` - Who they serve
- `business_model` - How they make money
- `industry` - Industry sector
- `key_features` - Main offerings
- `competitive_advantage` - What makes them unique

**RFRNCS Fit Analysis:**
- `fit_score` - 1-10 rating (10 = perfect fit)
- `needs_branding_services` - true/false
- `recommended_services` - RFRNCS services needed
- `budget_potential` - Estimated budget range
- `urgency_level` - high/medium/low
- `conversion_probability` - Likelihood of conversion
- `reasoning` - Detailed explanation
- `next_steps` - Recommended approach

## 🎯 **Customization Options**

### **AI Agent Prompts**
Edit the prompts in the AI agent nodes to:
- Focus on specific industries
- Include additional analysis criteria
- Customize scoring methodology
- Add company-specific questions

### **CSV Output**
Modify the "Format Final Results" code node to:
- Add/remove columns
- Change data formatting
- Include additional calculations

### **Email Template**
Customize the email node to:
- Change subject line
- Modify message content
- Add multiple recipients

## 📈 **Performance Notes**

### **Processing Time**
- **1-2 leads**: ~30 seconds
- **10 leads**: ~2-3 minutes
- **50 leads**: ~10-15 minutes

### **Cost Considerations**
- Each AI agent call costs API credits
- Gemini API pricing applies
- Optimize prompts to reduce token usage

## 🔧 **Troubleshooting**

### **Common Issues**
1. **CSV Upload Fails**: Ensure CSV has headers and proper formatting
2. **AI Agent Errors**: Check API keys and prompt formatting
3. **Email Not Sent**: Verify email credentials in n8n

### **Debug Mode**
- Run workflow with small CSV (2-3 leads) first
- Check execution logs for errors
- Verify AI agent outputs in intermediate steps

## 📚 **Advanced Usage**

### **Batch Processing**
- Process large CSVs in chunks
- Schedule automated runs
- Integrate with CRM systems

### **Custom Scoring**
- Modify fit_score calculations
- Add weighted criteria
- Include historical conversion data

### **Integration Options**
- Connect to Google Sheets
- Push to CRM APIs
- Trigger follow-up workflows

## 🎉 **Ready to Analyze!**

**Your simple lead analyzer is ready! Just upload a CSV and let the AI agents do the work of understanding companies and identifying RFRNCS opportunities.**

**Start with a small test CSV to verify everything works, then scale up to larger lead lists!** 🚀