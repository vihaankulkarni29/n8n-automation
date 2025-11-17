"""
Manual data entry helper with automated online presence analysis
Helps you quickly add businesses and automatically checks their online presence
"""
import csv
import requests
import re
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger('data_helper')

def check_website_exists(url):
    """Quick check if website is accessible"""
    if not url or url in ['', 'N/A', 'None']:
        return False
    
    try:
        if not url.startswith('http'):
            url = 'http://' + url
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def search_instagram(business_name):
    """Try to find Instagram handle (simplified)"""
    # Placeholder - would need Instagram API or scraping
    # For now, return None - user can fill manually
    return None

def assess_online_presence(business):
    """Assess online marketing presence"""
    score = 0
    has_presence = []
    
    if business.get('website') and business['website'] != '':
        score += 40
        has_presence.append('Website')
    
    if business.get('instagram') and business['instagram'] != '':
        score += 30
        has_presence.append('Instagram')
    
    if business.get('facebook') and business['facebook'] != '':
        score += 20
        has_presence.append('Facebook')
    
    if business.get('twitter') and business['twitter'] != '':
        score += 10
        has_presence.append('Twitter')
    
    # Determine priority
    if score >= 70:
        category = "Strong Online Presence"
        priority = "HIGH"
    elif score >= 40:
        category = "Moderate Online Presence"
        priority = "MEDIUM"
    elif score >= 20:
        category = "Weak Online Presence"
        priority = "LOW"
    else:
        category = "No Online Presence"
        priority = "URGENT"
    
    return {
        'online_score': score,
        'category': category,
        'priority': priority,
        'channels': ', '.join(has_presence) if has_presence else 'None',
        'has_website': 'Yes' if business.get('website') else 'No',
        'has_social': 'Yes' if any([business.get('instagram'), business.get('facebook')]) else 'No'
    }

def process_manual_entries(input_csv, output_csv):
    """
    Process manually entered data and add online presence assessment
    
    Input CSV should have columns: business_name, phone, address, website, instagram, facebook
    """
    businesses = []
    
    # Read input
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assess online presence
            presence = assess_online_presence(row)
            row.update(presence)
            row['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            businesses.append(row)
            
            logger.info(f"Processed: {row['business_name']} - {presence['priority']}")
    
    # Write output with analysis
    fieldnames = [
        'business_name', 'phone', 'address', 'website', 'instagram', 'facebook',
        'twitter', 'has_website', 'has_social', 'online_score', 'category', 'priority',
        'channels', 'scraped_at'
    ]
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(businesses)
    
    logger.info(f"✓ Processed {len(businesses)} businesses")
    logger.info(f"✓ Saved to {output_csv}")
    
    # Generate summary
    urgent = sum(1 for b in businesses if b['priority'] == 'URGENT')
    logger.info(f"✓ Found {urgent} URGENT prospects (no online presence)")
    
    return businesses

# Create template CSV
def create_template():
    """Create a template CSV for manual data entry"""
    template_file = 'data/TEMPLATE_manual_entry.csv'
    
    headers = ['business_name', 'phone', 'address', 'website', 'instagram', 'facebook', 'twitter', 'rating']
    
    sample_data = [
        {
            'business_name': 'Example Coffee Shop',
            'phone': '9876543210',
            'address': 'Bandra, Mumbai',
            'website': 'https://example.com',
            'instagram': 'https://instagram.com/example',
            'facebook': '',
            'twitter': '',
            'rating': '4.2'
        }
    ]
    
    with open(template_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sample_data)
    
    print(f"✓ Created template: {template_file}")
    print("\nInstructions:")
    print("1. Open the template in Excel/Google Sheets")
    print("2. Delete the example row")
    print("3. Add your businesses (copy-paste from Justdial)")
    print("4. Save the file")
    print("5. Run: python -m scrapers.enhanced_justdial")
    print("\nThe system will automatically:")
    print("- Assess online presence")
    print("- Calculate priority scores")
    print("- Identify URGENT prospects")

if __name__ == "__main__":
    create_template()
