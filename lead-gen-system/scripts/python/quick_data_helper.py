"""
QUICK DATA COLLECTION HELPER
Simple CSV template creator and analyzer for manual data entry
"""
import csv
from datetime import datetime

def assess_online_presence(business):
    """Assess online marketing presence and assign priority"""
    score = 0
    has_presence = []
    
    # Check each channel
    if business.get('website', '').strip():
        score += 40
        has_presence.append('Website')
    
    if business.get('instagram', '').strip():
        score += 30
        has_presence.append('Instagram')
    
    if business.get('facebook', '').strip():
        score += 20
        has_presence.append('Facebook')
    
    if business.get('twitter', '').strip():
        score += 10
        has_presence.append('Twitter')
    
    # Assign category and priority
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
        priority = "URGENT"  # Best prospects for your services!
    
    return {
        'online_score': score,
        'category': category,
        'priority': priority,
        'channels': ', '.join(has_presence) if has_presence else 'None',
        'has_website': 'Yes' if business.get('website', '').strip() else 'No',
        'has_social': 'Yes' if any([business.get('instagram', '').strip(), 
                                     business.get('facebook', '').strip()]) else 'No'
    }

def create_template():
    """Create template CSV for manual data entry"""
    template_file = 'data/TEMPLATE_CoffeeShops_Mumbai.csv'
    
    headers = ['business_name', 'phone', 'address', 'website', 'instagram', 'facebook', 'rating', 'notes']
    
    # Example rows to show format
    examples = [
        {
            'business_name': 'Starbucks Bandra',
            'phone': '02226430500',
            'address': 'Hill Road, Bandra West, Mumbai',
            'website': 'https://www.starbucks.in',
            'instagram': 'https://instagram.com/starbucksindia',
            'facebook': 'https://facebook.com/StarbucksIndia',
            'rating': '4.2',
            'notes': 'Example - Delete this row and add real data'
        },
        {
            'business_name': 'Local Cafe (No Website)',
            'phone': '9876543210',
            'address': 'Andheri East, Mumbai',
            'website': '',
            'instagram': '',
            'facebook': '',
            'rating': '3.8',
            'notes': 'URGENT prospect - no online presence'
        }
    ]
    
    with open(template_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(examples)
    
    print("="*70)
    print("✓ TEMPLATE CREATED:", template_file)
    print("="*70)
    print("\n📋 INSTRUCTIONS:")
    print("-" *70)
    print("1. Open this file in Excel or Google Sheets")
    print("2. Delete the example rows")
    print("3. Go to: https://www.justdial.com/Mumbai/Coffee-Shops/nct-10104727")
    print("4. Copy business details and paste into the template:")
    print("   - Business Name")
    print("   - Phone Number")
    print("   - Address")
    print("   - Website (if shown)")
    print("   - Instagram link (check their Justdial page)")
    print("   - Facebook link (check their Justdial page)")
    print("   - Rating")
    print("\n5. Save the file when done")
    print("6. Run the analyzer to get priority scores:")
    print("   python analyze_data.py")
    print("\n" + "="*70)
    print("🎯 TARGET: Collect 50-100 coffee shops")
    print("⏱️  TIME: Should take 1-2 hours")
    print("="*70)

def analyze_data(input_file='data/TEMPLATE_CoffeeShops_Mumbai.csv'):
    """Analyze manually entered data"""
    try:
        businesses = []
        
        # Read data
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip example rows
                if 'Example' in row.get('notes', '') or 'Delete' in row.get('notes', ''):
                    continue
                
                # Assess online presence
                assessment = assess_online_presence(row)
                row.update(assessment)
                row['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                businesses.append(row)
        
        if not businesses:
            print("\n⚠️  No data found (or only example rows)")
            print("Please add real business data to the template file")
            return
        
        # Save analyzed data
        output_file = input_file.replace('TEMPLATE_', 'ANALYZED_')
        
        fieldnames = list(businesses[0].keys())
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sorted(businesses, key=lambda x: x['online_score']))
        
        # Print summary
        print("\n" + "="*70)
        print("✓ ANALYSIS COMPLETE")
        print("="*70)
        print(f"\nTotal Businesses Analyzed: {len(businesses)}")
        print(f"Output File: {output_file}")
        
        # Priority breakdown
        urgent = [b for b in businesses if b['priority'] == 'URGENT']
        low = [b for b in businesses if b['priority'] == 'LOW']
        medium = [b for b in businesses if b['priority'] == 'MEDIUM']
        high = [b for b in businesses if b['priority'] == 'HIGH']
        
        print("\n📊 PRIORITY BREAKDOWN:")
        print("-" * 70)
        print(f"🔴 URGENT (No online presence):  {len(urgent)} businesses")
        print(f"🟡 LOW (Weak presence):          {len(low)} businesses")
        print(f"🟠 MEDIUM (Moderate presence):   {len(medium)} businesses")
        print(f"🟢 HIGH (Strong presence):       {len(high)} businesses")
        
        print("\n💡 RECOMMENDATION:")
        print("-" * 70)
        print(f"Focus on {len(urgent)} URGENT prospects - they need your services most!")
        
        if urgent:
            print("\n🎯 TOP 5 URGENT PROSPECTS:")
            print("-" * 70)
            for i, b in enumerate(urgent[:5], 1):
                print(f"{i}. {b['business_name']}")
                print(f"   Phone: {b.get('phone', 'N/A')}")
                print(f"   Current: {b['channels']}\n")
        
        print("="*70)
        
    except FileNotFoundError:
        print(f"\n❌ File not found: {input_file}")
        print("Run this script first to create the template")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'analyze':
        # Analyze existing data
        input_file = sys.argv[2] if len(sys.argv) > 2 else 'data/TEMPLATE_CoffeeShops_Mumbai.csv'
        analyze_data(input_file)
    else:
        # Create template
        create_template()
        print("\n💡 TIP: After filling the template, run:")
        print("   python quick_data_helper.py analyze")
