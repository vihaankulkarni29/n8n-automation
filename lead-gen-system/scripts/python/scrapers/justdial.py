"""
Justdial scraper using Selenium for dynamic content
Scrapes business listings from Justdial.com
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import random
from utils.logger import setup_logger
from utils.status_tracker import StatusTracker

logger = setup_logger('justdial_scraper')
status = StatusTracker()

# Search queries for target industries
SEARCH_QUERIES = [
    ("Restaurants", "Mumbai"),
    ("Food Companies", "Delhi"),
    ("Fashion Companies", "Bangalore")
]

def setup_driver():
    """Setup Chrome driver with headless mode"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_justdial(query, location, max_results=50):
    """
    Scrape Justdial for business listings
    
    Args:
        query: Business category (e.g., "Restaurants")
        location: City name (e.g., "Mumbai")
        max_results: Maximum number of results to collect
        
    Returns:
        List of business dicts with name, phone, website, address
    """
    driver = setup_driver()
    results = []
    
    try:
        # Construct Justdial search URL
        search_url = f"https://www.justdial.com/{location}/{query.replace(' ', '-')}"
        logger.info(f"Scraping Justdial: {search_url}")
        
        driver.get(search_url)
        time.sleep(5)  # Wait for page to load
        
        # Scroll to load more results
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 5
        
        while len(results) < max_results and scroll_attempts < max_scrolls:
            # Find all business listings
            try:
                listings = driver.find_elements(By.CSS_SELECTOR, "li[class*='cntanr']")
                
                for listing in listings:
                    if len(results) >= max_results:
                        break
                    
                    try:
                        # Extract business name
                        name_elem = listing.find_element(By.CSS_SELECTOR, "span[class*='lng_cont_name']")
                        business_name = name_elem.text.strip() if name_elem else ""
                        
                        # Extract phone
                        phone = ""
                        try:
                            phone_elem = listing.find_element(By.CSS_SELECTOR, "p[class*='contact-info'] a")
                            phone = phone_elem.get_attribute("href").replace("tel:", "") if phone_elem else ""
                        except:
                            pass
                        
                        # Extract address
                        address = ""
                        try:
                            addr_elem = listing.find_element(By.CSS_SELECTOR, "span[class*='mrehover']")
                            address = addr_elem.text.strip() if addr_elem else ""
                        except:
                            pass
                        
                        # Extract website (if available)
                        website = ""
                        try:
                            web_elem = listing.find_element(By.CSS_SELECTOR, "a[class*='website']")
                            website = web_elem.get_attribute("href") if web_elem else ""
                        except:
                            pass
                        
                        # Only add if we have at least a name
                        if business_name:
                            results.append({
                                'business_name': business_name,
                                'phone': phone,
                                'address': address,
                                'website': website,
                                'source': 'justdial',
                                'category': query,
                                'location': location
                            })
                            logger.info(f"Found: {business_name}")
                    
                    except Exception as e:
                        logger.debug(f"Error parsing listing: {e}")
                        continue
                
            except NoSuchElementException:
                logger.warning("No listings found on page")
                break
            
            # Scroll down to load more results
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
        
        logger.info(f"Scraped {len(results)} businesses from Justdial for '{query}' in {location}")
        status.increment('businesses_scraped', len(results))
        status.save()
        
    except Exception as e:
        logger.error(f"Justdial scraping error: {e}")
        status.increment('errors')
        status.save()
    
    finally:
        driver.quit()
    
    return results

def save_results(results, filename):
    """Save results to JSON file"""
    import os
    os.makedirs('data', exist_ok=True)
    filepath = f'data/{filename}'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(results)} results to {filepath}")

if __name__ == "__main__":
    all_results = []
    
    for query, location in SEARCH_QUERIES:
        logger.info(f"Starting scrape for '{query}' in {location}")
        results = scrape_justdial(query, location, max_results=50)
        
        if results:
            filename = f"{query.replace(' ', '_')}_{location}.json"
            save_results(results, filename)
            all_results.extend(results)
        
        # Delay between queries to avoid being blocked
        time.sleep(random.uniform(5, 10))
    
    logger.info(f"Total businesses scraped: {len(all_results)}")
    status.update(businesses_scraped=len(all_results))
    status.save()
