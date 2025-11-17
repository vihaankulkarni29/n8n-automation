"""
Enhanced Justdial scraper with social media and marketing presence detection
Scrapes coffee shops and checks for website, Instagram, Facebook, etc.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import random
import re
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger('enhanced_scraper')

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    # Don't use headless for now to see what's happening
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_social_links(page_source):
    """Extract Instagram, Facebook, Twitter links from page source"""
    social_media = {
        'instagram': None,
        'facebook': None,
        'twitter': None,
        'linkedin': None
    }
    
    # Instagram pattern
    instagram_match = re.search(r'(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)', page_source)
    if instagram_match:
        social_media['instagram'] = f"https://instagram.com/{instagram_match.group(1)}"
    
    # Facebook pattern
    facebook_match = re.search(r'(?:https?://)?(?:www\.)?facebook\.com/([a-zA-Z0-9._]+)', page_source)
    if facebook_match:
        social_media['facebook'] = f"https://facebook.com/{facebook_match.group(1)}"
    
    # Twitter pattern
    twitter_match = re.search(r'(?:https?://)?(?:www\.)?(?:twitter|x)\.com/([a-zA-Z0-9._]+)', page_source)
    if twitter_match:
        social_media['twitter'] = f"https://twitter.com/{twitter_match.group(1)}"
    
    return social_media

def assess_online_presence(business_data):
    """
    Assess the online marketing presence of a business
    Returns: dict with presence score and details
    """
    score = 0
    has_presence = []
    
    # Website check (40 points)
    if business_data.get('website') and business_data['website'] not in ['', 'N/A', None]:
        score += 40
        has_presence.append('Website')
    
    # Instagram (30 points - important for restaurants/cafes)
    if business_data.get('instagram'):
        score += 30
        has_presence.append('Instagram')
    
    # Facebook (20 points)
    if business_data.get('facebook'):
        score += 20
        has_presence.append('Facebook')
    
    # Twitter (10 points)
    if business_data.get('twitter'):
        score += 10
        has_presence.append('Twitter')
    
    # Determine category
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
        priority = "URGENT"  # These need help the most!
    
    return {
        'online_score': score,
        'category': category,
        'priority': priority,
        'channels': ', '.join(has_presence) if has_presence else 'None',
        'has_website': 'Yes' if business_data.get('website') else 'No',
        'has_social': 'Yes' if any([business_data.get('instagram'), 
                                     business_data.get('facebook'), 
                                     business_data.get('twitter')]) else 'No'
    }

def scrape_justdial_coffee_shops(url="https://www.justdial.com/Mumbai/Coffee-Shops/nct-10104727", max_results=50):
    """
    Scrape Justdial coffee shops with enhanced data collection
    
    Returns:
        List of dicts with business data and online presence assessment
    """
    driver = setup_driver()
    results = []
    
    try:
        logger.info(f"Opening Justdial page: {url}")
        driver.get(url)
        time.sleep(8)  # Wait for page to fully load
        
        # Scroll to load more results
        for scroll in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        
        # Get page source for social media extraction
        page_source = driver.page_source
        
        # Find all business listings
        logger.info("Extracting business data...")
        
        # Try multiple selectors to find listings
        listings = []
        try:
            # Try first selector
            listings = driver.find_elements(By.CSS_SELECTOR, "li.cntanr")
            if not listings:
                # Try alternative
                listings = driver.find_elements(By.CSS_SELECTOR, "section.store-details")
            if not listings:
                # Try another alternative
                listings = driver.find_elements(By.XPATH, "//ul[@class='list']/li")
        except:
            pass
        
        logger.info(f"Found {len(listings)} potential listings")
        
        for idx, listing in enumerate(listings[:max_results]):
            try:
                business_data = {
                    'business_name': '',
                    'phone': '',
                    'address': '',
                    'website': '',
                    'rating': '',
                    'instagram': None,
                    'facebook': None,
                    'twitter': None,
                    'category': 'Coffee Shops',
                    'location': 'Mumbai',
                    'source': 'justdial',
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Extract business name
                try:
                    name_elem = listing.find_element(By.CSS_SELECTOR, "span.jcn, a.jcn, h2")
                    business_data['business_name'] = name_elem.text.strip()
                except:
                    try:
                        name_elem = listing.find_element(By.XPATH, ".//span[contains(@class, 'lng_cont_name')]")
                        business_data['business_name'] = name_elem.text.strip()
                    except:
                        pass
                
                # Extract phone
                try:
                    phone_elems = listing.find_elements(By.CSS_SELECTOR, "a[href^='tel:'], p.contact-info")
                    for elem in phone_elems:
                        phone_text = elem.get_attribute('href') or elem.text
                        phone_text = phone_text.replace('tel:', '').strip()
                        if phone_text and len(phone_text) >= 10:
                            business_data['phone'] = phone_text
                            break
                except:
                    pass
                
                # Extract address
                try:
                    addr_elem = listing.find_element(By.CSS_SELECTOR, "span.mrehover, p.address, span.cont_fl_addr")
                    business_data['address'] = addr_elem.text.strip()
                except:
                    pass
                
                # Extract rating
                try:
                    rating_elem = listing.find_element(By.CSS_SELECTOR, "span.green-box, span.rating")
                    business_data['rating'] = rating_elem.text.strip()
                except:
                    pass
                
                # Extract website
                try:
                    web_elem = listing.find_element(By.CSS_SELECTOR, "a.weburl, a[href*='website']")
                    business_data['website'] = web_elem.get_attribute('href')
                except:
                    pass
                
                # Extract social media from listing HTML
                listing_html = listing.get_attribute('outerHTML')
                social = extract_social_links(listing_html)
                business_data.update(social)
                
                # Skip if no business name found
                if not business_data['business_name']:
                    continue
                
                # Assess online presence
                presence = assess_online_presence(business_data)
                business_data.update(presence)
                
                results.append(business_data)
                logger.info(f"✓ {idx+1}. {business_data['business_name']} - {presence['category']} (Priority: {presence['priority']})")
                
            except Exception as e:
                logger.debug(f"Error parsing listing {idx+1}: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(results)} coffee shops")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
    
    finally:
        driver.quit()
    
    return results

def save_to_csv(data, filename='data/coffee_shops_mumbai.csv'):
    """Save business data to CSV file"""
    if not data:
        logger.warning("No data to save")
        return
    
    import os
    os.makedirs('data', exist_ok=True)
    
    # Define CSV columns
    fieldnames = [
        'business_name',
        'phone',
        'address',
        'rating',
        'website',
        'instagram',
        'facebook',
        'twitter',
        'has_website',
        'has_social',
        'online_score',
        'category',
        'priority',
        'channels',
        'location',
        'scraped_at'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extmode='ignore')
        writer.writeheader()
        
        for row in data:
            # Filter to only include defined fields
            filtered_row = {k: row.get(k, '') for k in fieldnames}
            writer.writerow(filtered_row)
    
    logger.info(f"✓ Saved {len(data)} records to {filename}")
    
    # Also create a priority-sorted version
    sorted_data = sorted(data, key=lambda x: x.get('online_score', 0))
    priority_filename = filename.replace('.csv', '_by_priority.csv')
    
    with open(priority_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extmode='ignore')
        writer.writeheader()
        for row in sorted_data:
            filtered_row = {k: row.get(k, '') for k in fieldnames}
            writer.writerow(filtered_row)
    
    logger.info(f"✓ Saved priority-sorted version to {priority_filename}")
    
    # Generate summary
    summary = generate_summary(data)
    summary_filename = filename.replace('.csv', '_summary.txt')
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write(summary)
    logger.info(f"✓ Saved summary to {summary_filename}")

def generate_summary(data):
    """Generate a summary report of the scraped data"""
    total = len(data)
    
    with_website = sum(1 for d in data if d.get('has_website') == 'Yes')
    with_social = sum(1 for d in data if d.get('has_social') == 'Yes')
    with_instagram = sum(1 for d in data if d.get('instagram'))
    with_facebook = sum(1 for d in data if d.get('facebook'))
    
    urgent = sum(1 for d in data if d.get('priority') == 'URGENT')
    low = sum(1 for d in data if d.get('priority') == 'LOW')
    medium = sum(1 for d in data if d.get('priority') == 'MEDIUM')
    high = sum(1 for d in data if d.get('priority') == 'HIGH')
    
    avg_score = sum(d.get('online_score', 0) for d in data) / total if total > 0 else 0
    
    summary = f"""
================================================================================
COFFEE SHOPS SCRAPING SUMMARY - Mumbai
================================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERALL STATISTICS:
-------------------
Total Businesses Scraped: {total}
Average Online Presence Score: {avg_score:.1f}/100

ONLINE PRESENCE BREAKDOWN:
--------------------------
Businesses with Website: {with_website} ({with_website/total*100:.1f}%)
Businesses with Social Media: {with_social} ({with_social/total*100:.1f}%)
  - Instagram: {with_instagram} ({with_instagram/total*100:.1f}%)
  - Facebook: {with_facebook} ({with_facebook/total*100:.1f}%)

LEAD PRIORITY CATEGORIES:
-------------------------
🔴 URGENT (No online presence): {urgent} businesses - BEST PROSPECTS!
🟡 LOW (Weak presence): {low} businesses
🟠 MEDIUM (Moderate presence): {medium} businesses
🟢 HIGH (Strong presence): {high} businesses

RECOMMENDATION:
---------------
Target URGENT and LOW priority businesses first - they need your services most!

TOP 10 BUSINESSES NEEDING HELP (URGENT):
-----------------------------------------
"""
    
    # Add top 10 urgent prospects
    urgent_prospects = [d for d in data if d.get('priority') == 'URGENT'][:10]
    for i, prospect in enumerate(urgent_prospects, 1):
        summary += f"{i}. {prospect.get('business_name', 'Unknown')}\n"
        summary += f"   Phone: {prospect.get('phone', 'N/A')}\n"
        summary += f"   Address: {prospect.get('address', 'N/A')}\n"
        summary += f"   Current Presence: {prospect.get('channels', 'None')}\n\n"
    
    summary += "================================================================================\n"
    
    return summary

if __name__ == "__main__":
    logger.info("Starting enhanced Justdial scraper for Coffee Shops...")
    
    # Scrape coffee shops
    coffee_shops = scrape_justdial_coffee_shops(
        url="https://www.justdial.com/Mumbai/Coffee-Shops/nct-10104727",
        max_results=50
    )
    
    if coffee_shops:
        # Save to CSV
        save_to_csv(coffee_shops)
        
        # Print summary
        summary = generate_summary(coffee_shops)
        print(summary)
    else:
        logger.error("No data scraped. Please check the website structure or run manually.")
