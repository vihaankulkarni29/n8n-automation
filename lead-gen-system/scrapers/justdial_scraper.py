"""
Robust JustDial scraper for collecting coffee shop data
"""
import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger

logger = setup_logger(__name__)

class JustDialScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.collected_businesses = []
        self.unique_phones = set()
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1366,768')
        chrome_options.add_argument('--enable-unsafe-swiftshader')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("Chrome WebDriver initialized")
        
    def wait_for_page_load(self, timeout=10):
        """Wait for page to fully load"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(2)  # Additional wait for dynamic content
            return True
        except TimeoutException:
            logger.warning("Page load timeout")
            return False
    
    def extract_business_info(self, listing_element):
        """Extract business information from a listing element"""
        business = {
            'business_name': '',
            'cuisine': '',
            'phone': '',
            'email': '',
            'address': '',
            'website': '',
            'has_proper_website': False,
            'instagram': '',
            'facebook': '',
            'twitter': '',
            'rating': '',
            'reviews': '',
            'score': 0,
            'notes': ''
        }
        
        try:
            # Try multiple selectors for business name
            name_selectors = [
                '.jcn a',
                '.resultbox_title_anchor',
                'span.jcn',
                'a.resultbox_title_anchor'
            ]
            for selector in name_selectors:
                try:
                    name_elem = listing_element.find_element(By.CSS_SELECTOR, selector)
                    business['business_name'] = name_elem.text.strip()
                    if business['business_name']:
                        break
                except:
                    continue
            
            # Try to find phone number
            phone_selectors = [
                '.newpr_list .contact-info',
                'p.contact-info',
                '.mobilesv a',
                'span.mobilesv'
            ]
            for selector in phone_selectors:
                try:
                    phone_elem = listing_element.find_element(By.CSS_SELECTOR, selector)
                    phone_text = phone_elem.text.strip()
                    # Extract numbers only
                    phone_numbers = re.findall(r'\d{10}', phone_text.replace(' ', '').replace('-', ''))
                    if phone_numbers:
                        business['phone'] = phone_numbers[0]
                        break
                except:
                    continue
            
            # Try to find address
            address_selectors = [
                '.resultbox_address',
                'span.mrehover',
                '.loc a'
            ]
            for selector in address_selectors:
                try:
                    addr_elem = listing_element.find_element(By.CSS_SELECTOR, selector)
                    business['address'] = addr_elem.text.strip()
                    if business['address']:
                        break
                except:
                    continue
            
            # Try to find cuisine/category
            cuisine_selectors = [
                '.cat-txt',
                '.cuisine',
                '.category-tag',
                'span[class*="cuisine"]'
            ]
            for selector in cuisine_selectors:
                try:
                    cuisine_elem = listing_element.find_element(By.CSS_SELECTOR, selector)
                    business['cuisine'] = cuisine_elem.text.strip()
                    if business['cuisine']:
                        break
                except:
                    continue
            
            # Try to find rating
            rating_selectors = [
                '.green-box',
                'span.star_m',
                '.rating-value'
            ]
            for selector in rating_selectors:
                try:
                    rating_elem = listing_element.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    # Extract numeric rating
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        business['rating'] = rating_match.group(1)
                        break
                except:
                    continue
            
            # Try to find reviews count
            reviews_selectors = [
                '.review-count',
                '.votes',
                'span[class*="review"]'
            ]
            for selector in reviews_selectors:
                try:
                    reviews_elem = listing_element.find_element(By.CSS_SELECTOR, selector)
                    reviews_text = reviews_elem.text.strip()
                    reviews_match = re.search(r'(\d+)', reviews_text.replace(',', ''))
                    if reviews_match:
                        business['reviews'] = reviews_match.group(1)
                        break
                except:
                    continue
            
            # Try to find email
            try:
                email_elem = listing_element.find_element(By.CSS_SELECTOR, 'a[href^="mailto:"]')
                business['email'] = email_elem.get_attribute('href').replace('mailto:', '').strip()
            except:
                # Also check in text
                try:
                    all_text = listing_element.text
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)
                    if email_match:
                        business['email'] = email_match.group(0)
                except:
                    pass
            
            # Try to find website and social media
            try:
                all_links = listing_element.find_elements(By.TAG_NAME, 'a')
                for link in all_links:
                    href = link.get_attribute('href') or ''
                    if not href or not href.startswith('http'):
                        continue
                    
                    # Social media
                    if 'instagram.com' in href.lower():
                        business['instagram'] = href
                    elif 'facebook.com' in href.lower():
                        business['facebook'] = href
                    elif 'twitter.com' in href.lower() or 'x.com' in href.lower():
                        business['twitter'] = href
                    # Proper website (not justdial, not social media, not whatsapp)
                    elif all(x not in href.lower() for x in ['justdial', 'facebook', 'instagram', 'twitter', 'linkedin', 'youtube', 'whatsapp', 'x.com']):
                        business['website'] = href
                        business['has_proper_website'] = True
            except:
                pass
            
            # Calculate lead score
            score = 0
            score_notes = []
            
            if not business['has_proper_website']:
                score += 3
                score_notes.append('No website')
            
            if not business['phone']:
                score += 2
                score_notes.append('No phone')
            
            if not business['email']:
                score += 1
                score_notes.append('No email')
            
            # High rating bonus
            if business['rating']:
                try:
                    rating_val = float(business['rating'])
                    if rating_val >= 4.0 and (not business['has_proper_website'] or not business['phone']):
                        score += 3
                        score_notes.append(f'High rating ({rating_val}) but weak presence')
                except:
                    pass
            
            if not business['instagram'] and not business['facebook']:
                score += 1
                score_notes.append('No social media')
            
            business['score'] = score
            if score_notes:
                business['notes'] = '; '.join(score_notes)
                
        except Exception as e:
            logger.error(f"Error extracting business info: {e}")
        
        return business
    
    def click_show_more(self):
        """Try to click 'Show More' button to load more listings"""
        try:
            show_more_selectors = [
                'a.show-more',
                'button.show-more',
                'a[title="Show More"]',
                '.loadmore'
            ]
            
            for selector in show_more_selectors:
                try:
                    show_more = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if show_more.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", show_more)
                        time.sleep(1)
                        show_more.click()
                        time.sleep(3)
                        logger.info("Clicked 'Show More' button")
                        return True
                except:
                    continue
            return False
        except Exception as e:
            logger.error(f"Error clicking show more: {e}")
            return False

    def handle_popups(self):
        """Close common popups/banners that block content"""
        try:
            selectors = [
                'button[aria-label="Close"]',
                'button[aria-label="close"]',
                '.close',
                '.jdmodal .close',
                '#best_deal_pop_close',
                'div[role="dialog"] button',
                'button.cookie_accept',
                'button:contains("Allow")',
                'button:contains("Not Now")'
            ]
            closed_any = False
            for sel in selectors:
                try:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in elems:
                        if el.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                            time.sleep(0.5)
                            el.click()
                            closed_any = True
                except:
                    continue
            if closed_any:
                logger.info("Closed one or more popups/banners")
            return closed_any
        except Exception as e:
            logger.error(f"Error handling popups: {e}")
            return False

    def wait_for_listings(self, timeout=15):
        """Wait until any listing selector is present"""
        try:
            listing_selectors = [
                'li.cntanr',
                '.resultbox',
                'div.resultbox',
                'div.store-details',
                'section#allResult .resultbox',
                'ul.rsl-list > li'
            ]
            end = time.time() + timeout
            while time.time() < end:
                for sel in listing_selectors:
                    els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if els:
                        return True
                time.sleep(0.5)
            return False
        except Exception as e:
            logger.error(f"Error waiting for listings: {e}")
            return False
    
    def scroll_page(self, times=5, wait=3):
        """Scroll page multiple times to load more content"""
        if self.driver is None:
            logger.error("WebDriver not initialized for scrolling.")
            return False
        try:
            for i in range(times):
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                logger.info(f"Scrolled to bottom {i+1}/{times}")
                time.sleep(wait)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("No further increase in page height after scrolling.")
                    break
            return True
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
            return False

    def try_pagination(self):
        """Try to click pagination links/buttons if present"""
        try:
            pag_selectors = [
                'a[aria-label="Next"]',
                'a.next',
                'button.next',
                '.pagination-next',
                'a[rel="next"]'
            ]
            for selector in pag_selectors:
                try:
                    pag_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if pag_elem.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", pag_elem)
                        time.sleep(1)
                        pag_elem.click()
                        logger.info("Clicked pagination next button/link.")
                        time.sleep(4)
                        return True
                except:
                    continue
            return False
        except Exception as e:
            logger.error(f"Error clicking pagination: {e}")
            return False
    
    def scrape_coffee_shops(self, url, target_count=100):
        """Scrape coffee shops from JustDial"""
        logger.info(f"Starting scrape for {target_count} coffee shops from: {url}")
        try:
            self.setup_driver()
            if not self.driver:
                logger.error("WebDriver failed to initialize")
                return []
            self.driver.get(url)
            self.wait_for_page_load(15)
            # Try to clear popups and wait for listings
            self.handle_popups()
            self.wait_for_listings(15)
            logger.info("Page loaded, starting to extract listings...")

            attempts = 0
            max_attempts = 20
            while len(self.collected_businesses) < target_count and attempts < max_attempts:
                attempts += 1
                logger.info(f"Attempt {attempts}/{max_attempts} - Collected: {len(self.collected_businesses)}/{target_count}")

                listing_selectors = [
                    'li.cntanr',
                    '.resultbox',
                    'li[class*="result"]',
                    'div.store-details'
                ]
                listings = []
                for selector in listing_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            listings = elements
                            logger.info(f"Found {len(listings)} listings with selector: {selector}")
                            break
                    except Exception as e:
                        logger.error(f"Error finding elements for {selector}: {e}")

                if not listings:
                    logger.warning("No listings found, trying to scroll...")
                    # Save debug HTML on first few attempts
                    if attempts <= 2:
                        try:
                            html_path = os.path.join('data', f'page_{attempts}_debug.html')
                            os.makedirs(os.path.dirname(html_path), exist_ok=True)
                            with open(html_path, 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            logger.info(f"Saved debug HTML to {html_path}")
                        except Exception as e:
                            logger.error(f"Failed saving debug HTML: {e}")
                    self.scroll_page(times=7, wait=4)
                    continue

                # Extract info from each listing on the page
                for listing in listings:
                    if len(self.collected_businesses) >= target_count:
                        break
                    try:
                        business = self.extract_business_info(listing)
                        if business['business_name']:
                            norm_name = business['business_name'].strip().lower()
                            if business['phone']:
                                if business['phone'] not in self.unique_phones:
                                    self.unique_phones.add(business['phone'])
                                    self.collected_businesses.append(business)
                            else:
                                if norm_name not in self.unique_phones:
                                    self.unique_phones.add(norm_name)
                                    self.collected_businesses.append(business)
                            logger.info(f"Collected: {business['business_name']} ({len(self.collected_businesses)}/{target_count})")
                    except Exception as e:
                        logger.error(f"Error processing listing: {e}")
                        continue

                # Load more if needed
                if len(self.collected_businesses) < target_count:
                    loaded = False
                    if self.click_show_more():
                        loaded = True
                    elif self.try_pagination():
                        loaded = True
                    else:
                        loaded = self.scroll_page(times=5, wait=4)
                    if not loaded:
                        logger.warning("Cannot load more results")
                        time.sleep(5)

            logger.info(f"Scraping complete! Collected {len(self.collected_businesses)} unique coffee shops")
        except Exception as e:
            logger.error(f"Scraping error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
        return self.collected_businesses

    def save_to_csv(self, filename):
        """Save collected data to CSV"""
        if not self.collected_businesses:
            logger.warning("No businesses to save")
            return
        sorted_businesses = sorted(
            self.collected_businesses,
            key=lambda x: (x.get('score', 0), -int(x.get('reviews', 0) or 0)),
            reverse=True,
        )
        filepath = os.path.join('data', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        fieldnames = [
            'business_name', 'cuisine', 'phone', 'email', 'address', 'website',
            'has_proper_website', 'instagram', 'facebook', 'twitter', 'rating',
            'reviews', 'score', 'notes'
        ]
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sorted_businesses)
        logger.info(f"Saved {len(self.collected_businesses)} businesses to {filepath}")
        print(f"\n✅ Saved {len(self.collected_businesses)} businesses to {filepath}")
        high_priority = sum(1 for b in sorted_businesses if b.get('score', 0) >= 6)
        print(f"\n📈 Lead Quality:")
        print(f"   High-priority (score >=6): {high_priority}")
        print(f"   Missing website: {sum(1 for b in sorted_businesses if not b.get('has_proper_website'))}")
        print(f"   Missing phone: {sum(1 for b in sorted_businesses if not b.get('phone'))}")
        print(f"   Missing email: {sum(1 for b in sorted_businesses if not b.get('email'))}")

    def save_to_json(self, filename):
        """Save collected data to JSON"""
        if not self.collected_businesses:
            logger.warning("No businesses to save")
            return
        filepath = os.path.join('data', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.collected_businesses, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.collected_businesses)} businesses to {filepath}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="JustDial Business Scraper")
    parser.add_argument('--url', default="https://www.justdial.com/Mumbai/Coffee-Shops/nct-10104727", help="JustDial URL to scrape")
    parser.add_argument('--target', type=int, default=100, help="Target number of businesses")
    parser.add_argument('--headless', action='store_true', help="Run in headless mode")
    args = parser.parse_args()
    
    print("🚀 Starting JustDial Business Scraper...")
    print("=" * 60)
    print(f"URL: {args.url}")
    print(f"Target: {args.target} businesses")
    print("=" * 60)
    
    scraper = JustDialScraper(headless=args.headless)
    
    businesses = scraper.scrape_coffee_shops(args.url, target_count=args.target)
    
    if businesses:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Extract category from URL
        category = 'businesses'
        try:
            url_parts = args.url.split('/')
            if len(url_parts) >= 4:
                category = url_parts[3].replace('-', '_').lower()
        except:
            pass
        
        csv_name = f"justdial_{category}_{timestamp}.csv"
        json_name = f"justdial_{category}_{timestamp}.json"
        
        scraper.save_to_csv(csv_name)
        scraper.save_to_json(json_name)
        
        print("\n" + "=" * 60)
        print(f"✅ SUCCESS! Collected {len(businesses)} unique businesses")
        print(f"📁 CSV file: data/{csv_name}")
        print(f"📁 JSON file: data/{json_name}")
        print("\n🎯 Top 5 leads (by score):")
        sorted_b = sorted(businesses, key=lambda x: (x.get('score', 0), -int(x.get('reviews', 0) or 0)), reverse=True)
        for i, b in enumerate(sorted_b[:5], 1):
            print(f"   {i}. {b.get('business_name', 'Unknown')[:50]} (score: {b.get('score', 0)})")
        print("=" * 60)
    else:
        print("\n❌ No data collected. Check logs/main.log for details")


if __name__ == "__main__":
    main()
