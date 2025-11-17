"""
Enhanced Justdial Scraper for Japanese Restaurants Mumbai

Extracts comprehensive business data including:
- Restaurant name, cuisine, ratings
- Contact: phone, email, website
- Social media: Instagram, Facebook, Twitter
- Location details
- Lead scoring based on digital presence
"""

import time
import json
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd


@dataclass
class Restaurant:
    name: str
    cuisine: str
    rating: Optional[float]
    reviews: Optional[int]
    location: str
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    has_proper_website: bool
    instagram: Optional[str]
    facebook: Optional[str]
    twitter: Optional[str]
    score: int
    notes: str = ""


class JapaneseRestaurantScraper:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.restaurants = []
        
    def setup_driver(self):
        """Initialize Chrome WebDriver with anti-detection settings."""
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
        print("✅ Chrome WebDriver initialized")
    
    def wait_and_scroll(self, pause: float = 2.0):
        """Wait for page load and scroll to trigger lazy loading."""
        time.sleep(pause)
        # Scroll incrementally to load all listings
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        for i in range(0, total_height, 800):
            self.driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.5)
        time.sleep(2)
    
    def extract_restaurant_data(self, listing) -> Optional[Restaurant]:
        """Extract all restaurant data from a listing element."""
        try:
            # Name
            name = "Unknown"
            name_selectors = [
                'span.jcn',
                'a.resultbox_title_anchor',
                '.store-name',
                'h2.jcn'
            ]
            for sel in name_selectors:
                try:
                    elem = listing.find_element(By.CSS_SELECTOR, sel)
                    name = elem.text.strip()
                    if name:
                        break
                except:
                    pass
            
            if not name or name == "Unknown":
                return None
            
            # Cuisine (from category tags or description)
            cuisine = "Japanese"  # Default for this search
            try:
                cuisine_elem = listing.find_element(By.CSS_SELECTOR, '.cat-txt, .cuisine, .category-tag')
                cuisine = cuisine_elem.text.strip() or "Japanese"
            except:
                pass
            
            # Rating
            rating = None
            reviews = None
            rating_selectors = [
                'span.green-box',
                '.rating-value',
                'span.star_m'
            ]
            for sel in rating_selectors:
                try:
                    rating_elem = listing.find_element(By.CSS_SELECTOR, sel)
                    rating_text = rating_elem.text.strip()
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        rating = float(match.group(1))
                        break
                except:
                    pass
            
            # Reviews count
            try:
                reviews_elem = listing.find_element(By.CSS_SELECTOR, '.review-count, .votes, span[class*="review"]')
                reviews_text = reviews_elem.text.strip()
                match = re.search(r'(\d+)', reviews_text.replace(',', ''))
                if match:
                    reviews = int(match.group(1))
            except:
                pass
            
            # Location/Address
            location = ""
            addr_selectors = [
                'span.mrehover',
                '.resultbox_address',
                '.address',
                'p.address'
            ]
            for sel in addr_selectors:
                try:
                    addr_elem = listing.find_element(By.CSS_SELECTOR, sel)
                    location = addr_elem.text.strip()
                    if location:
                        break
                except:
                    pass
            
            # Phone
            phone = None
            phone_selectors = [
                'span.mobilesv',
                'a[href^="tel:"]',
                '.contact-info',
                'p.contact-info'
            ]
            for sel in phone_selectors:
                try:
                    phone_elem = listing.find_element(By.CSS_SELECTOR, sel)
                    phone_text = phone_elem.text or phone_elem.get_attribute('href') or ""
                    phone_numbers = re.findall(r'\d{10,12}', phone_text.replace(' ', '').replace('-', ''))
                    if phone_numbers:
                        phone = phone_numbers[0]
                        break
                except:
                    pass
            
            # Email
            email = None
            try:
                email_elem = listing.find_element(By.CSS_SELECTOR, 'a[href^="mailto:"]')
                email = email_elem.get_attribute('href').replace('mailto:', '').strip()
            except:
                # Also check in text
                try:
                    all_text = listing.text
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)
                    if email_match:
                        email = email_match.group(0)
                except:
                    pass
            
            # Website
            website = None
            has_proper_website = False
            try:
                links = listing.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href') or ""
                    # Filter out internal/social links
                    if href and href.startswith('http'):
                        if all(x not in href.lower() for x in ['justdial', 'facebook', 'instagram', 'twitter', 'linkedin', 'youtube', 'whatsapp']):
                            website = href
                            has_proper_website = True
                            break
            except:
                pass
            
            # Social Media
            instagram = None
            facebook = None
            twitter = None
            try:
                links = listing.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href') or ""
                    if 'instagram.com' in href.lower():
                        instagram = href
                    elif 'facebook.com' in href.lower():
                        facebook = href
                    elif 'twitter.com' in href.lower() or 'x.com' in href.lower():
                        twitter = href
            except:
                pass
            
            # Score calculation
            score = 0
            notes = []
            
            if not has_proper_website:
                score += 3
                notes.append("No proper website")
            
            if not phone:
                score += 2
                notes.append("No phone number")
            
            if not email:
                score += 1
                notes.append("No email")
            
            if rating and rating >= 4.0 and (not has_proper_website or not phone):
                score += 3
                notes.append(f"High rating ({rating}) but weak digital presence")
            
            if not instagram and not facebook:
                score += 1
                notes.append("No social media presence")
            
            return Restaurant(
                name=name,
                cuisine=cuisine,
                rating=rating,
                reviews=reviews,
                location=location,
                phone=phone,
                email=email,
                website=website,
                has_proper_website=has_proper_website,
                instagram=instagram,
                facebook=facebook,
                twitter=twitter,
                score=score,
                notes="; ".join(notes)
            )
            
        except Exception as e:
            print(f"⚠️  Extraction error: {str(e)[:100]}")
            return None
    
    def scrape_page(self, url: str) -> List[Restaurant]:
        """Scrape all restaurants from the given Justdial URL."""
        print(f"\n🔍 Scraping: {url}")
        
        self.driver.get(url)
        self.wait_and_scroll()
        
        # Find all listing containers
        listing_selectors = [
            'li.cntanr',
            'li[class*="result"]',
            'div.store-details',
            '.resultbox'
        ]
        
        listings = []
        for sel in listing_selectors:
            try:
                listings = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if listings:
                    print(f"✅ Found {len(listings)} listings using selector: {sel}")
                    break
            except:
                pass
        
        if not listings:
            print("❌ No listings found. Page may require manual inspection.")
            return []
        
        # Extract data from each listing
        print(f"\n📊 Extracting restaurant data...")
        for i, listing in enumerate(listings, 1):
            restaurant = self.extract_restaurant_data(listing)
            if restaurant:
                self.restaurants.append(restaurant)
                print(f"  {i}. {restaurant.name[:50]} (score: {restaurant.score})")
        
        return self.restaurants
    
    def save_results(self, query_name: str = "japanese_restaurants_mumbai") -> Dict[str, str]:
        """Save results to CSV and JSON."""
        if not self.restaurants:
            print("❌ No restaurants to save")
            return {}
        
        output_dir = Path("data")
        output_dir.mkdir(exist_ok=True)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"justdial_{query_name}_{ts}"
        
        csv_path = output_dir / f"{base}.csv"
        json_path = output_dir / f"{base}.json"
        
        # Sort by score (highest first)
        sorted_restaurants = sorted(self.restaurants, key=lambda r: (r.score, -(r.reviews or 0)), reverse=True)
        
        # CSV
        rows = [asdict(r) for r in sorted_restaurants]
        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        
        # JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Saved:")
        print(f"   CSV: {csv_path}")
        print(f"   JSON: {json_path}")
        
        return {"csv": str(csv_path), "json": str(json_path)}
    
    def print_summary(self):
        """Print summary statistics."""
        if not self.restaurants:
            return
        
        print(f"\n📈 Summary:")
        print(f"   Total restaurants: {len(self.restaurants)}")
        print(f"   High-priority leads (score >=6): {sum(1 for r in self.restaurants if r.score >= 6)}")
        print(f"   Missing website: {sum(1 for r in self.restaurants if not r.has_proper_website)}")
        print(f"   Missing phone: {sum(1 for r in self.restaurants if not r.phone)}")
        print(f"   Missing email: {sum(1 for r in self.restaurants if not r.email)}")
        print(f"   No social media: {sum(1 for r in self.restaurants if not r.instagram and not r.facebook)}")
        
        # Top 5 leads
        sorted_rest = sorted(self.restaurants, key=lambda r: (r.score, -(r.reviews or 0)), reverse=True)
        print(f"\n🎯 Top 5 lead opportunities:")
        for i, r in enumerate(sorted_rest[:5], 1):
            print(f"{i}. {r.name[:60]}")
            print(f"   Score: {r.score} | Rating: {r.rating or 'N/A'} | Reviews: {r.reviews or 0}")
            print(f"   Website: {'❌' if not r.has_proper_website else '✅'} | Phone: {'❌' if not r.phone else '✅'} | Email: {'❌' if not r.email else '✅'}")
            if r.notes:
                print(f"   Notes: {r.notes}")
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            print("\n✅ Browser closed")


def main():
    url = "https://www.justdial.com/Mumbai/Japanese-Restaurants/nct-10279229"
    
    scraper = JapaneseRestaurantScraper(headless=False)
    
    try:
        scraper.setup_driver()
        scraper.scrape_page(url)
        scraper.save_results("japanese_restaurants_mumbai")
        scraper.print_summary()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
