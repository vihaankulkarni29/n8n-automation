"""
Detailed JustDial scraper for extracting comprehensive business information
Extracts: Address, Phone, Email, Website, Reviews, Rating, Cost, Cuisines, Veg/Non-Veg, Timings
"""
import time
import csv
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DetailedJustDialScraper:
    """Scraper for extracting detailed business information from JustDial"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.businesses = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver with anti-detection measures"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.maximize_window()
        logger.info("Chrome WebDriver initialized")
        
    def wait_for_page_load(self, timeout=15):
        """Wait for page to fully load"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(3)  # Additional wait for dynamic content
            return True
        except TimeoutException:
            logger.warning("Page load timeout")
            return False
    
    def get_soup(self):
        """Get BeautifulSoup object from current page"""
        return BeautifulSoup(self.driver.page_source, 'lxml')
    
    def get_business_name(self, listing_soup):
        """Extract business name"""
        try:
            selectors = [
                ('span', {'class': 'jcn'}),
                ('a', {'class': 'resultbox_title_anchor'}),
                ('h2', {}),
            ]
            for tag, attrs in selectors:
                element = listing_soup.find(tag, attrs)
                if element:
                    return element.get_text(strip=True)
            return None
        except Exception as e:
            logger.error(f"Error extracting business name: {e}")
            return None
    
    def get_address(self, listing_soup):
        """Extract complete address"""
        try:
            selectors = [
                ('span', {'class': 'mrehover'}),
                ('p', {'class': 'address'}),
                ('span', {'class': 'cont_fl_addr'}),
            ]
            for tag, attrs in selectors:
                element = listing_soup.find(tag, attrs)
                if element:
                    address = element.get_text(strip=True)
                    # Clean up address
                    address = re.sub(r'\s+', ' ', address)
                    return address
            return None
        except Exception as e:
            logger.error(f"Error extracting address: {e}")
            return None
    
    def get_phone(self, listing_soup):
        """Extract phone number"""
        try:
            # Try multiple selectors
            selectors = [
                ('p', {'class': 'contact-info'}),
                ('span', {'class': 'mobilesv'}),
                ('a', {'class': 'telicon'}),
            ]
            
            for tag, attrs in selectors:
                element = listing_soup.find(tag, attrs)
                if element:
                    text = element.get_text(strip=True)
                    # Extract 10-digit number
                    phone = re.sub(r'\D', '', text)
                    matches = re.findall(r'\d{10}', phone)
                    if matches:
                        return matches[0]
            
            # Try finding in onclick attributes
            phone_links = listing_soup.find_all('a', href=re.compile(r'tel:'))
            for link in phone_links:
                href = link.get('href', '')
                phone = re.sub(r'\D', '', href)
                matches = re.findall(r'\d{10}', phone)
                if matches:
                    return matches[0]
            
            return None
        except Exception as e:
            logger.error(f"Error extracting phone: {e}")
            return None
    
    def get_email(self, listing_soup):
        """Extract email ID"""
        try:
            # Look for email patterns
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            
            # Check all links
            links = listing_soup.find_all('a', href=re.compile(r'mailto:'))
            for link in links:
                href = link.get('href', '')
                email = re.search(email_pattern, href)
                if email:
                    return email.group(0)
            
            # Check all text
            text = listing_soup.get_text()
            email = re.search(email_pattern, text)
            if email:
                return email.group(0)
            
            # Check if email is hidden behind form
            email_forms = listing_soup.find_all(['button', 'a'], string=re.compile(r'email|Email|E-mail', re.I))
            if email_forms:
                return "hidden behind form"
            
            return None
        except Exception as e:
            logger.error(f"Error extracting email: {e}")
            return None
    
    def get_website(self, listing_soup):
        """Extract website URL"""
        try:
            # Look for website links
            links = listing_soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                # Filter out JustDial, social media, and mailto links
                if (href.startswith('http') and 
                    'justdial.com' not in href and
                    'facebook.com' not in href and
                    'instagram.com' not in href and
                    'twitter.com' not in href and
                    'linkedin.com' not in href):
                    return href
            
            # Check for website icon/button
            website_buttons = listing_soup.find_all(['a', 'button'], string=re.compile(r'website|Website|Visit', re.I))
            for button in website_buttons:
                href = button.get('href')
                if href and href.startswith('http'):
                    return href
            
            return None
        except Exception as e:
            logger.error(f"Error extracting website: {e}")
            return None
    
    def get_rating_and_reviews(self, listing_soup):
        """Extract rating and review count"""
        try:
            rating = None
            reviews = None
            
            # Look for rating
            rating_selectors = [
                ('span', {'class': 'green-box'}),
                ('span', {'class': 'star_m'}),
                ('div', {'class': 'rating'}),
            ]
            
            for tag, attrs in rating_selectors:
                element = listing_soup.find(tag, attrs)
                if element:
                    text = element.get_text(strip=True)
                    # Extract numeric rating
                    match = re.search(r'(\d+\.?\d*)', text)
                    if match:
                        rating = float(match.group(1))
                        break
            
            # Look for review count
            review_patterns = [
                r'(\d+)\s*reviews?',
                r'(\d+)\s*ratings?',
                r'Votes\s*:\s*(\d+)',
            ]
            
            text = listing_soup.get_text()
            for pattern in review_patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    reviews = int(match.group(1))
                    break
            
            return rating, reviews
        except Exception as e:
            logger.error(f"Error extracting rating/reviews: {e}")
            return None, None
    
    def get_cost_for_two(self, listing_soup):
        """Extract average cost for two"""
        try:
            # Look for cost patterns
            patterns = [
                r'₹\s*(\d+)\s*for\s*two',
                r'Cost\s*for\s*two\s*:\s*₹?\s*(\d+)',
                r'Average\s*cost\s*:\s*₹?\s*(\d+)',
            ]
            
            text = listing_soup.get_text()
            for pattern in patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    return int(match.group(1))
            
            return None
        except Exception as e:
            logger.error(f"Error extracting cost: {e}")
            return None
    
    def get_cuisines(self, listing_soup):
        """Extract types of cuisines"""
        try:
            cuisines = []
            
            # Look for cuisine tags/labels
            cuisine_selectors = [
                ('span', {'class': 'cuisine'}),
                ('div', {'class': 'cuisines'}),
                ('p', {'class': 'cuisines'}),
            ]
            
            for tag, attrs in cuisine_selectors:
                elements = listing_soup.find_all(tag, attrs)
                for element in elements:
                    cuisine_text = element.get_text(strip=True)
                    if cuisine_text:
                        cuisines.append(cuisine_text)
            
            # Look in text for common cuisine keywords
            if not cuisines:
                text = listing_soup.get_text()
                cuisine_keywords = [
                    'North Indian', 'South Indian', 'Chinese', 'Italian', 
                    'Continental', 'Mexican', 'Thai', 'Japanese', 'Mediterranean',
                    'Fast Food', 'Street Food', 'Bakery', 'Cafe', 'Desserts',
                    'Beverages', 'Seafood', 'Mughlai', 'Punjabi', 'Bengali'
                ]
                
                for keyword in cuisine_keywords:
                    if keyword in text:
                        cuisines.append(keyword)
            
            return ', '.join(cuisines) if cuisines else None
        except Exception as e:
            logger.error(f"Error extracting cuisines: {e}")
            return None
    
    def get_veg_status(self, listing_soup):
        """Extract Veg/Non-Veg/Pure Veg status"""
        try:
            text = listing_soup.get_text().lower()
            
            if 'pure veg' in text or 'pure vegetarian' in text:
                return 'Pure Veg'
            elif 'non-veg' in text or 'non veg' in text or 'nonveg' in text:
                return 'Non-Veg'
            elif 'veg' in text or 'vegetarian' in text:
                return 'Veg'
            
            # Check for veg/non-veg icons
            veg_icons = listing_soup.find_all(['img', 'span'], alt=re.compile(r'veg|vegetarian', re.I))
            if veg_icons:
                return 'Veg/Non-Veg'
            
            return None
        except Exception as e:
            logger.error(f"Error extracting veg status: {e}")
            return None
    
    def get_timings(self, listing_soup):
        """Extract opening and closing times"""
        try:
            timings = {}
            
            # Look for timing patterns
            patterns = [
                r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s*(?:to|-)\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
                r'Open\s*:\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
                r'Close\s*:\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
            ]
            
            text = listing_soup.get_text()
            
            # Try to find opening and closing time
            for pattern in patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    if len(match.groups()) == 2:
                        timings['opening'] = match.group(1)
                        timings['closing'] = match.group(2)
                        return timings
            
            # Look for timing elements
            timing_selectors = [
                ('span', {'class': 'timings'}),
                ('div', {'class': 'timings'}),
                ('p', {'class': 'timings'}),
            ]
            
            for tag, attrs in timing_selectors:
                element = listing_soup.find(tag, attrs)
                if element:
                    timing_text = element.get_text(strip=True)
                    return {'timings': timing_text}
            
            return None
        except Exception as e:
            logger.error(f"Error extracting timings: {e}")
            return None
    
    def extract_business_details(self, listing_soup):
        """Extract all details from a business listing"""
        business = {
            'business_name': self.get_business_name(listing_soup),
            'address': self.get_address(listing_soup),
            'phone': self.get_phone(listing_soup),
            'email': self.get_email(listing_soup),
            'website': self.get_website(listing_soup),
            'rating': None,
            'reviews': None,
            'cost_for_two': self.get_cost_for_two(listing_soup),
            'cuisines': self.get_cuisines(listing_soup),
            'veg_status': self.get_veg_status(listing_soup),
            'timings': self.get_timings(listing_soup),
        }
        
        # Get rating and reviews
        rating, reviews = self.get_rating_and_reviews(listing_soup)
        business['rating'] = rating
        business['reviews'] = reviews
        
        return business
    
    def extract_json_ld_data(self, soup):
        """Extract business data from JSON-LD structured data"""
        businesses = []
        try:
            # Find all script tags with type="application/ld+json"
            scripts = soup.find_all('script', type='application/ld+json')
            
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Check if it's a list of items
                    if isinstance(data, dict) and 'itemListElement' in data:
                        for item in data['itemListElement']:
                            try:
                                business_data = item.get('item', {})
                                
                                # Extract address
                                address_data = business_data.get('address', {})
                                full_address = ', '.join(filter(None, [
                                    address_data.get('streetAddress', ''),
                                    address_data.get('addresslocality', ''),
                                    address_data.get('addressRegion', ''),
                                    address_data.get('postalCode', '')
                                ]))
                                
                                # Extract cuisines
                                cuisines_list = business_data.get('servesCuisine', [])
                                cuisines = ', '.join(cuisines_list) if isinstance(cuisines_list, list) else cuisines_list
                                
                                # Extract rating
                                rating_data = business_data.get('aggregateRating', {})
                                rating = rating_data.get('ratingvalue')
                                reviews = rating_data.get('ratingcount')
                                
                                # Extract phone - clean up format
                                phone = business_data.get('telephone', '')
                                if phone:
                                    # Remove country code and formatting
                                    phone = re.sub(r'[^\d]', '', phone)
                                    if len(phone) > 10:
                                        phone = phone[-10:]  # Take last 10 digits
                                
                                business = {
                                    'business_name': business_data.get('name', ''),
                                    'address': full_address if full_address else None,
                                    'phone': phone if phone else None,
                                    'email': None,  # Not in JSON-LD
                                    'website': None,  # Will try to find separately
                                    'rating': float(rating) if rating else None,
                                    'reviews': int(reviews) if reviews else None,
                                    'cost_for_two': None,  # Will extract from priceRange
                                    'cuisines': cuisines if cuisines else None,
                                    'veg_status': None,  # Not in JSON-LD
                                    'timings': None,  # Not in JSON-LD
                                }
                                
                                # Try to estimate cost from priceRange (₹ symbols)
                                price_range = business_data.get('priceRange', '')
                                if price_range:
                                    rupee_count = price_range.count('₹')
                                    if rupee_count > 0:
                                        # Estimate: ₹ = 200, ₹₹ = 500, ₹₹₹ = 1000, ₹₹₹₹ = 2000
                                        cost_estimate = {1: 200, 2: 500, 3: 1000, 4: 2000}.get(rupee_count)
                                        business['cost_for_two'] = cost_estimate
                                
                                if business['business_name']:
                                    businesses.append(business)
                                    
                            except Exception as e:
                                logger.error(f"Error parsing business item: {e}")
                                continue
                    
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error parsing JSON-LD: {e}")
                    continue
            
            return businesses
            
        except Exception as e:
            logger.error(f"Error extracting JSON-LD data: {e}")
            return []
    
    def scrape_page(self, url, page_num=1):
        """Scrape all businesses from a single page"""
        try:
            if page_num > 1:
                url = f"{url}/page-{page_num}"
            
            logger.info(f"Scraping page {page_num}: {url}")
            self.driver.get(url)
            self.wait_for_page_load()
            
            # Get page source and parse
            soup = self.get_soup()
            
            # Save HTML for debugging
            with open(f'data/detailed_page_{page_num}.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            # Extract businesses from JSON-LD structured data
            page_businesses = self.extract_json_ld_data(soup)
            
            logger.info(f"Found {len(page_businesses)} businesses with detailed data on page {page_num}")
            
            # Print extracted data
            for idx, business in enumerate(page_businesses, 1):
                logger.info(f"  [{idx}] {business['business_name']}")
                
                print(f"\n{'='*70}")
                print(f"Business #{idx}: {business['business_name']}")
                print(f"{'='*70}")
                for key, value in business.items():
                    if value:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
                print(f"{'='*70}")
            
            return page_businesses
            
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {e}")
            return []
    
    def scrape(self, url, max_pages=10):
        """Scrape multiple pages"""
        logger.info(f"Starting detailed scrape from: {url}")
        print(f"\n🔍 Starting Detailed JustDial Scraper")
        print(f"{'='*70}\n")
        
        try:
            self.setup_driver()
            
            for page in range(1, max_pages + 1):
                businesses = self.scrape_page(url, page)
                
                if not businesses:
                    logger.warning(f"No businesses on page {page}, stopping")
                    break
                
                self.businesses.extend(businesses)
                logger.info(f"Total collected: {len(self.businesses)}")
                
                time.sleep(3)  # Be respectful
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.businesses
    
    def save_to_csv(self, filename='detailed_businesses.csv'):
        """Save collected data to CSV"""
        if not self.businesses:
            logger.warning("No businesses to save")
            return None
        
        filepath = os.path.join('data', filename)
        
        # Flatten timings dict to string
        for business in self.businesses:
            if isinstance(business.get('timings'), dict):
                business['timings'] = ', '.join([f"{k}: {v}" for k, v in business['timings'].items()])
        
        fieldnames = [
            'business_name', 'address', 'phone', 'email', 'website',
            'rating', 'reviews', 'cost_for_two', 'cuisines', 
            'veg_status', 'timings'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.businesses)
        
        logger.info(f"Saved {len(self.businesses)} businesses to {filepath}")
        print(f"\n✅ Saved to CSV: {filepath}")
        return filepath
    
    def save_to_json(self, filename='detailed_businesses.json'):
        """Save collected data to JSON"""
        if not self.businesses:
            logger.warning("No businesses to save")
            return None
        
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.businesses, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.businesses)} businesses to {filepath}")
        print(f"✅ Saved to JSON: {filepath}")
        return filepath


def main():
    """Main execution"""
    print("🚀 Detailed JustDial Business Scraper")
    print("="*70)
    
    # Configuration
    url = "https://www.justdial.com/Mumbai/Coffee-Shops/nct-10104727"
    max_pages = 5  # Scrape 5 pages for testing
    
    scraper = DetailedJustDialScraper(headless=False)
    businesses = scraper.scrape(url, max_pages=max_pages)
    
    if businesses:
        print(f"\n{'='*70}")
        print(f"📊 SCRAPING COMPLETE!")
        print(f"{'='*70}")
        print(f"Total Businesses Collected: {len(businesses)}")
        
        # Save to both formats
        csv_file = scraper.save_to_csv('detailed_coffee_shops.csv')
        json_file = scraper.save_to_json('detailed_coffee_shops.json')
        
        # Print summary statistics
        print(f"\n📈 Summary Statistics:")
        print(f"{'='*70}")
        
        with_phone = sum(1 for b in businesses if b.get('phone'))
        with_email = sum(1 for b in businesses if b.get('email') and b['email'] != 'hidden behind form')
        with_website = sum(1 for b in businesses if b.get('website'))
        with_rating = sum(1 for b in businesses if b.get('rating'))
        with_cost = sum(1 for b in businesses if b.get('cost_for_two'))
        with_timings = sum(1 for b in businesses if b.get('timings'))
        
        print(f"  Businesses with Phone: {with_phone} ({with_phone/len(businesses)*100:.1f}%)")
        print(f"  Businesses with Email: {with_email} ({with_email/len(businesses)*100:.1f}%)")
        print(f"  Businesses with Website: {with_website} ({with_website/len(businesses)*100:.1f}%)")
        print(f"  Businesses with Rating: {with_rating} ({with_rating/len(businesses)*100:.1f}%)")
        print(f"  Businesses with Cost Info: {with_cost} ({with_cost/len(businesses)*100:.1f}%)")
        print(f"  Businesses with Timings: {with_timings} ({with_timings/len(businesses)*100:.1f}%)")
        
        print(f"\n✨ All data saved successfully!")
        
    else:
        print("\n❌ No data collected. Check logs for details.")


if __name__ == "__main__":
    main()
