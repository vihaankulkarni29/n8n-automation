import os
import re
import csv
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Minimal logger fallback if utils.logger is unavailable
try:
    from utils.logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)


class JustDialEnrichedScraper:
    def __init__(self, headless: bool = True, rate_delay: float = 1.0):
        self.headless = headless
        self.rate_delay = rate_delay
        self.driver: Optional[webdriver.Chrome] = None
        self.results: List[Dict] = []

    # 1) fetch_page(url)
    def fetch_page(self, url: str, wait_selector: Optional[str] = None, timeout: int = 15) -> bool:
        try:
            if self.driver is None:
                self._setup_driver()
            assert self.driver is not None
            self.driver.get(url)
            self._wait_for_ready(timeout)
            # Attempt to dismiss common popups after navigation
            self._handle_popups()
            if wait_selector:
                d = self.driver
                assert d is not None
                WebDriverWait(d, timeout).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, wait_selector))
                )
            time.sleep(1.0)
            return True
        except Exception as e:
            logger.error(f"fetch_page error: {e}")
            return False

    def _setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        self.driver = webdriver.Chrome(options=chrome_options)
        try:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception:
            pass

    def _handle_popups(self):
        try:
            d = self.driver
            assert d is not None
            # Try generic close buttons
            close_selectors = [
                '[aria-label="close"]', '[aria-label="Close"]', '.close', '.modal-close', '.jd_modal .close',
                '.mse-pop .close', '.popup-close', 'button[title="Close"]'
            ]
            for sel in close_selectors:
                try:
                    els = d.find_elements(By.CSS_SELECTOR, sel)
                    for el in els:
                        if el.is_displayed():
                            d.execute_script("arguments[0].click();", el)
                            time.sleep(0.2)
                except Exception:
                    continue
            # Try common negative/deny buttons by text via XPath
            text_variants = [
                'Not Now', 'No Thanks', 'Deny', 'Deny Location', 'Later', 'Skip', 'Close'
            ]
            for txt in text_variants:
                try:
                    btns = d.find_elements(By.XPATH, f"//button[contains(., '{txt}')]|//a[contains(., '{txt}')]")
                    for b in btns:
                        if b.is_displayed():
                            d.execute_script("arguments[0].click();", b)
                            time.sleep(0.2)
                except Exception:
                    continue
        except Exception:
            pass

    def _wait_for_ready(self, timeout: int = 15):
        try:
            d = self.driver
            assert d is not None
            WebDriverWait(d, timeout).until(
                lambda drv: drv.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(1.0)
        except TimeoutException:
            logger.warning("Page readyState timeout")

    def _close(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        finally:
            self.driver = None

    # 2) extract_metadata(entry_block)
    def extract_metadata_from_list(self, entry) -> Dict:
        data = {
            'name': '', 'address': '', 'phone': '', 'email': '', 'website_present': False,
            'website': '', 'cuisines': '', 'rating': '', 'reviews': '', 'pricing': ''
        }
        try:
            # Name
            for sel in ['.jcn a', '.resultbox_title_anchor', 'a.resultbox_title_anchor', 'h2 a']:
                try:
                    el = entry.find_element(By.CSS_SELECTOR, sel)
                    txt = el.text.strip()
                    if txt:
                        data['name'] = txt
                        break
                except Exception:
                    continue
            # Address
            for sel in ['.resultbox_address', 'span.mrehover', '.loc a', 'p.address', '.adr']:
                try:
                    el = entry.find_element(By.CSS_SELECTOR, sel)
                    txt = el.text.strip()
                    if txt:
                        data['address'] = txt
                        break
                except Exception:
                    continue
            # Rating
            for sel in ['.green-box', '.rating-value', 'span.star_m']:
                try:
                    el = entry.find_element(By.CSS_SELECTOR, sel)
                    m = re.search(r'(\d+\.?\d*)', el.text.strip())
                    if m:
                        data['rating'] = m.group(1)
                        break
                except Exception:
                    continue
            # Reviews
            for sel in ['.review-count', '.votes', 'span[class*="review"]']:
                try:
                    el = entry.find_element(By.CSS_SELECTOR, sel)
                    m = re.search(r'(\d[\d,]*)', el.text.strip())
                    if m:
                        data['reviews'] = m.group(1).replace(',', '')
                        break
                except Exception:
                    continue
            # Cuisines (chips/tags)
            for sel in ['.cat-txt', '.cuisine', '.category-tag', 'span[class*="cuisine"]']:
                try:
                    el = entry.find_element(By.CSS_SELECTOR, sel)
                    txt = el.text.strip()
                    if txt:
                        data['cuisines'] = txt
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"extract_metadata_from_list error: {e}")
        return data

    # 3) decode_phone(entry_block)
    def decode_phone(self, scope_el) -> str:
        # Try tel: links first
        try:
            for a in scope_el.find_elements(By.CSS_SELECTOR, 'a[href^="tel:"]'):
                href = a.get_attribute('href') or ''
                digits = re.sub(r'[^+\d]', '', href)
                if digits:
                    return digits
        except Exception:
            pass
        # Fallback: raw text digits visible
        try:
            txt = scope_el.text
            m = re.findall(r'\+?\d[\d\s\-]{7,}\d', txt)
            if m:
                return re.sub(r'[^+\d]', '', m[0])
        except Exception:
            pass
        # Obfuscation via spans/images is site-specific; leaving generic fallback
        return ''

    def extract_detail_page(self) -> Dict:
        # Assumes driver is on the detail page
        data = {
            'phone': '', 'email': '', 'website_present': False, 'website': '',
            'cuisines': '', 'rating': '', 'reviews': '', 'pricing': '',
            'instagram': '', 'facebook': '', 'twitter': '', 'linkedin': '', 'youtube': ''
        }
        try:
            d = self.driver
            assert d is not None
            # Add retry/safety check for driver connection
            try:
                _ = d.current_url  # Test if driver is still connected
            except Exception:
                logger.warning("Driver connection lost on detail page")
                return data
            # Phone
            try:
                data['phone'] = self.decode_phone(d.find_element(By.TAG_NAME, 'body'))
            except Exception:
                pass
            # Email
            try:
                a = d.find_element(By.CSS_SELECTOR, 'a[href^="mailto:"]')
                data['email'] = (a.get_attribute('href') or '').replace('mailto:', '').strip()
            except Exception:
                # Regex fallback in page source
                try:
                    m = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', d.page_source)
                    if m:
                        data['email'] = m.group(0)
                except Exception:
                    pass
            # Website
            try:
                links = d.find_elements(By.TAG_NAME, 'a')
                for a in links:
                    href = (a.get_attribute('href') or '').strip()
                    if href and href.startswith('http'):
                        low = href.lower()
                        # Capture socials while scanning
                        if any(x in low for x in ['instagram.com', 'instagr.am']):
                            data['instagram'] = href
                        elif 'facebook.com' in low:
                            data['facebook'] = href
                        elif 'linkedin.com' in low:
                            data['linkedin'] = href
                        elif 'youtube.com' in low or 'youtu.be' in low:
                            data['youtube'] = href
                        elif 'twitter.com' in low or low.startswith('https://x.com'):
                            data['twitter'] = href
                        # Heuristic for first non-directory website link
                        if all(x not in low for x in ['justdial', 'facebook', 'instagram', 'twitter', 'linkedin', 'youtube', 'whatsapp', 'x.com']):
                            data['website'] = href
                            data['website_present'] = True
                            break
            except Exception:
                pass
            # Cuisines (detail chips/labels)
            for sel in ['.cuisine', '.category', '.category-tag', '.chip', 'ul.cuisine-list li']:
                try:
                    el = d.find_element(By.CSS_SELECTOR, sel)
                    t = el.text.strip()
                    if t:
                        data['cuisines'] = t
                        break
                except Exception:
                    continue
            # Rating/Reviews
            try:
                el = d.find_element(By.CSS_SELECTOR, '.rating-value, .green-box, span[itemprop="ratingValue"]')
                m = re.search(r'(\d+\.?\d*)', el.text.strip())
                if m:
                    data['rating'] = m.group(1)
            except Exception:
                pass
            try:
                el = d.find_element(By.CSS_SELECTOR, '.review-count, .votes, span[itemprop="ratingCount"]')
                m = re.search(r'(\d[\d,]*)', el.text.strip())
                if m:
                    data['reviews'] = m.group(1).replace(',', '')
            except Exception:
                pass
            # Pricing (Average cost for two)
            try:
                # Search common phrasings
                txt = d.find_element(By.TAG_NAME, 'body').text
                m = re.search(r'(Average\s*Cost\s*for\s*two|Cost\s*for\s*Two|Average\s*price)[^\n]*', txt, re.I)
                if m:
                    data['pricing'] = m.group(0).strip()
                else:
                    # Try to capture a currency range like ₹1,000 - ₹2,000
                    m2 = re.search(r'[₹Rs\.\$]\s?\d[\d,]*(\s?-\s?[₹Rs\.\$]?\s?\d[\d,]*)?', txt)
                    if m2:
                        data['pricing'] = m2.group(0).strip()
                # Sanitize improbable short fragments
                if data['pricing'] and len(data['pricing']) < 6:
                    if not re.search(r'(cost|two|₹|rs|\$|price)', data['pricing'], re.I):
                        data['pricing'] = ''
            except Exception:
                pass

            # JSON-LD structured data parsing for robust fields
            try:
                scripts = d.find_elements(By.XPATH, "//script[@type='application/ld+json']")
                for s in scripts:
                    try:
                        raw = s.get_attribute('innerText') or ''
                        if not raw.strip():
                            continue
                        # Some pages contain multiple JSON objects/arrays
                        parsed = json.loads(raw)
                        items = parsed if isinstance(parsed, list) else [parsed]
                        for obj in items:
                            if not isinstance(obj, dict):
                                continue
                            typ = (obj.get('@type') or obj.get('@TYPE') or '')
                            if isinstance(typ, list):
                                typ = ' '.join([str(t) for t in typ])
                            if any(k in str(typ).lower() for k in ['restaurant', 'localbusiness', 'foodestablishment']):
                                # Website/url
                                if not data['website']:
                                    url_v = (obj.get('url') or obj.get('URL') or '').strip()
                                    if url_v and url_v.startswith('http') and 'justdial' not in url_v.lower():
                                        data['website'] = url_v
                                        data['website_present'] = True
                                # Phone/email
                                if not data['phone']:
                                    tel = (obj.get('telephone') or obj.get('phone') or '')
                                    if tel:
                                        data['phone'] = re.sub(r'[^+\d]', '', str(tel))
                                if not data['email']:
                                    em = obj.get('email') or ''
                                    if isinstance(em, str) and '@' in em:
                                        data['email'] = em
                                # Cuisines
                                if not data['cuisines']:
                                    sc = obj.get('servesCuisine')
                                    if isinstance(sc, list):
                                        data['cuisines'] = ', '.join([str(x) for x in sc if x])
                                    elif isinstance(sc, str):
                                        data['cuisines'] = sc
                                # Aggregate rating
                                agg = obj.get('aggregateRating') or {}
                                if isinstance(agg, dict):
                                    if not data['rating']:
                                        rv = agg.get('ratingValue') or agg.get('rating')
                                        if rv:
                                            data['rating'] = str(rv)
                                    if not data['reviews']:
                                        rc = agg.get('reviewCount') or agg.get('ratingCount')
                                        if rc:
                                            try:
                                                data['reviews'] = str(int(str(rc).replace(',', '')))
                                            except Exception:
                                                data['reviews'] = str(rc)
                                # Price range
                                if not data['pricing']:
                                    pr = obj.get('priceRange')
                                    if isinstance(pr, str) and pr.strip():
                                        data['pricing'] = pr.strip()
                                # Socials via sameAs
                                same_as = obj.get('sameAs') or []
                                if isinstance(same_as, list):
                                    for link in same_as:
                                        if not isinstance(link, str):
                                            continue
                                        low = link.lower()
                                        if 'instagram.com' in low and not data['instagram']:
                                            data['instagram'] = link
                                        elif 'facebook.com' in low and not data['facebook']:
                                            data['facebook'] = link
                                        elif 'linkedin.com' in low and not data['linkedin']:
                                            data['linkedin'] = link
                                        elif ('youtube.com' in low or 'youtu.be' in low) and not data['youtube']:
                                            data['youtube'] = link
                                        elif ('twitter.com' in low or low.startswith('https://x.com')) and not data['twitter']:
                                            data['twitter'] = link
                    except Exception:
                        continue
            except Exception:
                pass
        except Exception as e:
            logger.error(f"extract_detail_page error: {e}")
        return data

    def get_listing_elements(self):
        d = self.driver
        assert d is not None
        sels = ['li.cntanr', '.resultbox', 'div.resultbox', 'div.store-details', 'ul.rsl-list > li']
        for s in sels:
            els = d.find_elements(By.CSS_SELECTOR, s)
            if els:
                return els
        return []

    def get_entry_link(self, entry) -> Optional[str]:
        for sel in ['.jcn a', '.resultbox_title_anchor', 'a.resultbox_title_anchor', 'h2 a']:
            try:
                a = entry.find_element(By.CSS_SELECTOR, sel)
                href = a.get_attribute('href')
                if href and href.startswith('http'):
                    return href
            except Exception:
                continue
        return None

    def load_more(self) -> bool:
        # Try Show More, then pagination, else scroll
        # Return True if it likely loaded new content
        # Show More
        try:
            d = self.driver
            assert d is not None
            for sel in ['a.show-more', 'button.show-more', 'a[title="Show More"]', '.loadmore']:
                try:
                    btn = d.find_element(By.CSS_SELECTOR, sel)
                    if btn.is_displayed():
                        d.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(0.8)
                        btn.click()
                        time.sleep(2)
                        self._handle_popups()
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        # Next pagination
        try:
            d = self.driver
            assert d is not None
            for sel in ['a[aria-label="Next"]', 'a.next', 'button.next', '.pagination-next', 'a[rel="next"]']:
                try:
                    nxt = d.find_element(By.CSS_SELECTOR, sel)
                    if nxt.is_displayed():
                        d.execute_script("arguments[0].scrollIntoView(true);", nxt)
                        time.sleep(0.8)
                        nxt.click()
                        time.sleep(2)
                        self._handle_popups()
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        # Scroll fallback
        try:
            d = self.driver
            assert d is not None
            last_h = d.execute_script("return document.body.scrollHeight")
            d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_h = d.execute_script("return document.body.scrollHeight")
            return new_h > last_h
        except Exception:
            return False

    # 4) save_results(data)
    def save_results(self, base_name: str = 'justdial_mumbai') -> Dict[str, str]:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = os.path.join('data', f'{base_name}_{ts}.csv')
        json_path = os.path.join('data', f'{base_name}_{ts}.json')
        os.makedirs('data', exist_ok=True)
        fields = ['name', 'address', 'phone', 'email', 'website_present', 'website', 'cuisines', 'rating', 'reviews', 'pricing',
                  'instagram', 'facebook', 'twitter', 'linkedin', 'youtube']
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for row in self.results:
                w.writerow({k: row.get(k, '') for k in fields})
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.results)} results to {csv_path} and {json_path}")
        return {'csv': csv_path, 'json': json_path}

    # Pipeline
    def run(self, url: str, target: int = 60):
        try:
            if not self.fetch_page(url, wait_selector='.resultbox, li.cntanr'):
                return []
            seen_names = set()
            attempts = 0
            max_attempts = 20
            while len(self.results) < target and attempts < max_attempts:
                attempts += 1
                entries = self.get_listing_elements()
                logger.info(f"Page scan: found {len(entries)} listing elements")

                # Snapshot batch with pre-extracted list metadata and links to avoid stale elements
                batch = []
                for entry in entries:
                    try:
                        list_meta = self.extract_metadata_from_list(entry)
                        detail_url = self.get_entry_link(entry)
                        batch.append({'list_meta': list_meta, 'detail_url': detail_url})
                    except Exception:
                        continue

                start_seen = len(seen_names)
                for item in batch:
                    if len(self.results) >= target:
                        break
                    list_meta = item.get('list_meta') or {}
                    if not list_meta.get('name'):
                        continue
                    norm = list_meta['name'].strip().lower()
                    if norm in seen_names:
                        continue
                    # Try to open detail page in same tab (safer for headless)
                    detail_url = item.get('detail_url')
                    detail_meta = {}
                    if detail_url:
                        if self.fetch_page(detail_url):
                            detail_meta = self.extract_detail_page()
                            # go back
                            try:
                                d = self.driver
                                assert d is not None
                                d.back()
                                self._wait_for_ready(10)
                                self._handle_popups()
                                time.sleep(self.rate_delay)
                            except Exception:
                                # If back fails, reload list page
                                self.fetch_page(url, wait_selector='.resultbox, li.cntanr')
                    # Merge list + detail (detail overrides empties)
                    merged = dict(list_meta)
                    for k, v in detail_meta.items():
                        if v and (not merged.get(k)):
                            merged[k] = v
                    # website_present should reflect website field
                    merged['website_present'] = bool(merged.get('website'))
                    self.results.append(merged)
                    seen_names.add(norm)
                    logger.info(f"Added: {merged.get('name', '')}")
                    time.sleep(self.rate_delay)
                if len(self.results) >= target:
                    break
                # If no new unique names were added in this iteration, try load_more once; if still no progress, stop
                if len(seen_names) == start_seen:
                    if not self.load_more():
                        logger.info("No more content loaded via pagination/scroll.")
                        break
                    # After trying to load more, if still no new elements next loop, attempts will increment and we will exit eventually
                else:
                    # Some progress made; attempt to load more for next batch
                    self.load_more()
                time.sleep(self.rate_delay)
            return self.results
        finally:
            self._close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Justdial Enriched Scraper')
    parser.add_argument('--url', required=True, help='Justdial listing URL')
    parser.add_argument('--target', type=int, default=60, help='Target number of results')
    parser.add_argument('--headless', action='store_true', help='Run headless')
    args = parser.parse_args()

    scraper = JustDialEnrichedScraper(headless=args.headless)
    print("🚀 Starting Justdial Enriched Scraper")
    print("=" * 60)
    print(f"URL: {args.url}")
    print(f"Target: {args.target}")
    print("=" * 60)

    results = scraper.run(args.url, target=args.target)
    if results:
        paths = scraper.save_results('justdial_mumbai')
        print("\n✅ Success")
        print(f"CSV: {paths['csv']}")
        print(f"JSON: {paths['json']}")
    else:
        print("\n❌ No results")


if __name__ == '__main__':
    main()
