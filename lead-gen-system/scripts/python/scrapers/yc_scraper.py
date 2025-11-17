import os
import re
import csv
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# Selenium for JS-rendered content
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


class YCStartupScraper:
    """
    Scrapes Y Combinator Startup Directory to identify startups with weak brand identity.
    Scores companies based on missing website, short descriptions, and lack of media.
    """
    
    BASE_URL = "https://www.ycombinator.com/companies"
    
    def __init__(self, rate_delay: float = 0.2, use_selenium: bool = True, exclude_existing: bool = False, regions: Optional[str] = None):
        self.rate_delay = rate_delay
        self.use_selenium = use_selenium
        self.exclude_existing = exclude_existing
        self.regions = regions
        self.driver: Optional[webdriver.Chrome] = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.results: List[Dict] = []
        self.existing_names: set[str] = set()
        # Active URL (region-specific if provided)
        if self.regions:
            self.active_url = f"{self.BASE_URL}?regions={quote_plus(self.regions)}"
        else:
            self.active_url = self.BASE_URL

    def load_existing_names(self, directory: str = 'data') -> None:
        """Load existing company names from prior yc_startups CSV files."""
        try:
            import glob
            pattern = os.path.join(directory, 'yc_startups_*.csv')
            for path in glob.glob(pattern):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            if i == 0:
                                continue
                            parts = line.split(',')
                            if parts:
                                name = parts[0].strip().strip('"')
                                if name:
                                    self.existing_names.add(name.lower())
                except Exception:
                    continue
            if self.existing_names:
                logger.info(f"Loaded {len(self.existing_names)} existing names to exclude")
        except Exception as e:
            logger.warning(f"Failed loading existing names: {e}")
    
    def fetch_companies(self, batch_filter: Optional[List[str]] = None, max_pages: int = 10) -> List[Dict]:
        """
        Fetch company listings from YC directory.
        
        Args:
            batch_filter: List of batch names to filter (e.g., ["W25", "F24", "S24"])
            max_pages: Maximum number of pages to crawl
            
        Returns:
            List of company metadata dictionaries
        """
        companies = []
        page = 1
        
        # YC directory uses filters via query params or client-side JS
        # We'll try to get the full list and filter client-side
        # The page may be JS-rendered; if so, we'll get what we can from initial HTML
        
        try:
            logger.info(f"Fetching YC companies from {self.active_url}")
            
            if self.use_selenium:
                # Use Selenium for JS-rendered content
                soup = self._fetch_with_selenium()
            else:
                response = self.session.get(self.BASE_URL, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # YC directory structure varies; common patterns:
            # - Company cards in divs/sections
            # - May use React/Next.js with data in script tags
            
            # Try to find company data in JSON-LD or embedded script
            companies_data = self._extract_from_scripts(soup)
            if companies_data:
                logger.info(f"Found {len(companies_data)} companies from embedded data")
                companies.extend(companies_data)
            else:
                # Anchor-first strategy: company profile links /companies/<slug>
                anchor_blocks = soup.find_all('a', href=lambda h: isinstance(h, str) and h.startswith('/companies/') and h.count('/') == 2)
                company_blocks = list(anchor_blocks)
                if len(company_blocks) < 50:
                    # Fallback: generic block finder merges in additional elements
                    fallback = self._find_company_blocks(soup)
                    seen_ids = set(id(b) for b in company_blocks)
                    for fb in fallback:
                        if id(fb) not in seen_ids:
                            company_blocks.append(fb)
                logger.info(f"Found {len(company_blocks)} company blocks in HTML (anchor-first)")
                
                # Debug: save first block HTML for inspection
                if company_blocks:
                    try:
                        debug_path = os.path.join('data', 'yc_sample_block.html')
                        with open(debug_path, 'w', encoding='utf-8') as f:
                            f.write(str(company_blocks[0].prettify()))
                        logger.info(f"Saved sample block to {debug_path}")
                    except Exception:
                        pass
            
                for block in company_blocks:
                    metadata = self.extract_metadata(block)
                    if metadata and metadata.get('name'):
                        companies.append(metadata)
            
            # Filter by batch if specified
            if batch_filter:
                companies = [c for c in companies if self._batch_matches(c.get('batch', ''), batch_filter)]
                logger.info(f"Filtered to {len(companies)} companies matching batches: {batch_filter}")
            
            return companies
            
        except Exception as e:
            logger.error(f"Error fetching companies: {e}")
            return companies
    
    def _extract_from_scripts(self, soup: BeautifulSoup) -> List[Dict]:
        """Try to extract company data from embedded JSON/scripts"""
        companies = []
        
        # Look for Next.js data or JSON-LD
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                if not script.string:
                    continue
                data = json.loads(script.string)
                # Navigate the data structure to find companies
                # This is site-specific and may need adjustment
                if isinstance(data, dict):
                    # Common patterns: data.props.pageProps.companies, data.companies, etc.
                    for key in ['companies', 'startups', 'data']:
                        if key in data:
                            items = data[key]
                            if isinstance(items, list):
                                companies.extend(self._parse_company_list(items))
            except Exception:
                continue
        
        # Also check for __NEXT_DATA__ or similar
        next_data_scripts = soup.find_all('script', id='__NEXT_DATA__')
        for script in next_data_scripts:
            try:
                if not script.string:
                    continue
                data = json.loads(script.string)
                # Traverse props
                props = data.get('props', {}).get('pageProps', {})
                for key in ['companies', 'startups', 'directory', 'data']:
                    if key in props:
                        items = props[key]
                        if isinstance(items, list):
                            companies.extend(self._parse_company_list(items))
            except Exception:
                continue
        
        # Deep fallback: search any list of dicts containing 'name' and optional 'batch'/'industry'
        if not companies:
            def deep_collect(obj):
                if isinstance(obj, dict):
                    for v in obj.values():
                        deep_collect(v)
                elif isinstance(obj, list):
                    # Heuristic: list of dicts with 'name' field
                    if obj and all(isinstance(x, dict) for x in obj):
                        sample = obj[0]
                        if any(k in sample for k in ['name','company_name']) and len(obj) > 3:
                            for item in obj:
                                name = item.get('name') or item.get('company_name')
                                if not name:
                                    continue
                                companies.append({
                                    'name': name,
                                    'batch': item.get('batch') or item.get('yc_batch',''),
                                    'industry': item.get('industry') or item.get('vertical',''),
                                    'location': item.get('location') or item.get('hq_location',''),
                                    'website': item.get('website') or item.get('url',''),
                                    'description': item.get('description') or item.get('one_liner',''),
                                    'logo': item.get('logo') or item.get('logo_url',''),
                                    'video': item.get('video') or item.get('demo_video',''),
                                })
                    else:
                        for v in obj:
                            deep_collect(v)
            # Try with __NEXT_DATA__ if present
            nd = soup.find('script', id='__NEXT_DATA__')
            if nd and nd.string:
                try:
                    jd = json.loads(nd.string)
                    deep_collect(jd)
                except Exception:
                    pass
        return companies
    
    def _parse_company_list(self, items: List) -> List[Dict]:
        """Parse a list of company objects from JSON"""
        companies = []
        for item in items:
            if not isinstance(item, dict):
                continue
            
            # Map common field names
            company = {
                'name': item.get('name') or item.get('company_name') or '',
                'batch': item.get('batch') or item.get('yc_batch') or '',
                'industry': item.get('industry') or item.get('vertical') or item.get('tags', [''])[0] if isinstance(item.get('tags'), list) else '',
                'location': item.get('location') or item.get('hq_location') or '',
                'website': item.get('website') or item.get('url') or '',
                'description': item.get('description') or item.get('one_liner') or '',
                'logo': item.get('logo') or item.get('logo_url') or '',
                'video': item.get('video') or item.get('demo_video') or ''
            }
            
            if company['name']:
                companies.append(company)
        
        return companies
    
    def _setup_driver(self):
        """Setup Selenium Chrome driver"""
        chrome_options = Options()
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
    
    def _fetch_with_selenium(self) -> BeautifulSoup:
        """Fetch page using Selenium for JS-rendered content"""
        if not self.driver:
            self._setup_driver()
        
        assert self.driver is not None
        self.driver.get(self.active_url)
        
        # Wait for content to load
        try:
            WebDriverWait(self.driver, 8).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(1)  # Allow JS to populate content
        except TimeoutException:
            logger.warning("Page load timeout")
        
        # Adaptive scroll targeting >=400 distinct /companies/<slug> anchors
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        prev_count = 0
        stable_iters = 0
        for i in range(40):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.6)
            html_mid = self.driver.page_source
            tmp = BeautifulSoup(html_mid, 'html.parser')
            anchors = tmp.find_all('a', href=lambda h: isinstance(h, str) and h.startswith('/companies/') and h.count('/') == 2)
            count = len(anchors)
            if count > prev_count:
                prev_count = count
                stable_iters = 0
            else:
                stable_iters += 1
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if count >= 400 or stable_iters >= 5 or new_height == last_height:
                break
            last_height = new_height
        
        html = self.driver.page_source
        return BeautifulSoup(html, 'html.parser')
    
    def _close_driver(self):
        """Close Selenium driver"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        finally:
            self.driver = None

    def _extract_detail_page(self, url: str) -> Dict:
        """Extract detail page fields (HTTP + HTML/JSON parsing; avoids Selenium flakiness)."""
        data = {
            'team_size': '',
            'founders': '',
            'github': '',
            'website': '',
            'location': ''
        }
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Prefer Next.js __NEXT_DATA__ if available
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data and next_data.string:
                try:
                    jd = json.loads(next_data.string)
                    props = jd.get('props', {}).get('pageProps', {})

                    def walk(obj):
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                kl = k.lower()
                                if isinstance(v, (dict, list)):
                                    walk(v)
                                else:
                                    if isinstance(v, str):
                                        vl = v.lower()
                                        if not data['website'] and v.startswith('http') and 'ycombinator.com' not in vl and 'github.com' not in vl:
                                            data['website'] = v
                                        if not data['github'] and 'github.com' in vl:
                                            data['github'] = v
                                    if 'team' in kl and isinstance(v, (int, str)) and not data['team_size']:
                                        try:
                                            data['team_size'] = str(int(v))
                                        except Exception:
                                            pass
                                    if ('location' in kl or 'hq' in kl) and isinstance(v, str) and not data['location']:
                                        data['location'] = v
                        elif isinstance(obj, list):
                            for it in obj:
                                walk(it)

                    walk(props)

                    # Collect founder names from arrays of dicts containing name + founder-ish keys
                    founders = []
                    def collect_founders(obj):
                        if isinstance(obj, dict):
                            ks = {k.lower() for k in obj.keys()}
                            if 'name' in ks and any(f in ks for f in ['founder', 'founders', 'role']):
                                nm = obj.get('name')
                                if isinstance(nm, str):
                                    founders.append(nm)
                            for v in obj.values():
                                collect_founders(v)
                        elif isinstance(obj, list):
                            for it in obj:
                                collect_founders(it)
                    collect_founders(props)
                    if founders and not data['founders']:
                        data['founders'] = ', '.join(sorted(set(founders)))
                except Exception:
                    pass

            # Fallbacks via visible HTML
            body_text = soup.get_text('\n', strip=True)
            if not data['team_size']:
                m_ts = re.search(r'Team\s*Size\s*(\d+)', body_text, re.I)
                if m_ts:
                    data['team_size'] = m_ts.group(1)
            if not data['founders']:
                founders = []
                for a in soup.find_all('a', href=True):
                    href = str(a.get('href') or '')
                    if '/profiles/' in href:
                        txt = a.get_text(strip=True)
                        if txt and len(txt.split()) <= 4:
                            founders.append(txt)
                if founders:
                    data['founders'] = ', '.join(sorted(set(founders)))
            if not data['website'] or not data['github']:
                # Collect candidate links
                candidates = []
                banned_hosts = {
                    'ycombinator.com', 'news.ycombinator.com', 'bookface.ycombinator.com',
                    'startupschool.org', 'www.startupschool.org',
                    'twitter.com', 'x.com', 'www.twitter.com', 'www.x.com',
                    'linkedin.com', 'www.linkedin.com',
                    'facebook.com', 'www.facebook.com',
                    'medium.com', 'www.medium.com',
                    'youtube.com', 'www.youtube.com', 'youtu.be',
                    'github.com', 'www.github.com'
                }
                from urllib.parse import urlparse
                for a in soup.find_all('a', href=True):
                    href = str(a.get('href') or '')
                    if href.startswith('http'):
                        host = urlparse(href).netloc.lower()
                        if host in banned_hosts:
                            if not data['github'] and 'github.com' in host:
                                data['github'] = href
                            continue
                        candidates.append((host, href))
                # Pick best candidate: prefer domain containing slug tokens
                slug = ''
                try:
                    slug = url.rstrip('/').split('/')[-1].lower()
                except Exception:
                    pass
                tokens = [t for t in re.split(r'[-_\.]', slug) if t]
                best = None
                best_score = -1
                for host, href in candidates:
                    score = 0
                    if slug and slug in host:
                        score += 3
                    for t in tokens:
                        if t and t in host:
                            score += 1
                    # Prefer shorter hosts (company.com vs sub.sub.company.com)
                    score -= host.count('.')
                    if score > best_score:
                        best_score = score
                        best = href
                if not data['website'] and best:
                    data['website'] = best
            if not data['location']:
                m_loc = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2}(?:,\s*(?:USA|United States))?)', body_text)
                if m_loc:
                    data['location'] = m_loc.group(1)
        except Exception as e:
            logger.warning(f"Detail extraction failed for {url}: {e}")
        return data
    
    def _find_company_blocks(self, soup: BeautifulSoup) -> List:
        """Find company card/block elements in HTML"""
        # Common selectors for YC directory
        selectors = [
            'div[class*="company"]',
            'div[class*="startup"]',
            'a[class*="company"]',
            'section[class*="company"]',
            'article'
        ]
        
        for selector in selectors:
            blocks = soup.select(selector)
            if len(blocks) > 5:  # Likely found the right container
                return blocks
        
        # Fallback: any divs with multiple links and text
        return soup.find_all('div', class_=True, limit=200)
    
    def extract_metadata(self, block) -> Dict:
        """
        Extract company metadata from a company block/card.
        
        Args:
            block: BeautifulSoup element representing a company
            
        Returns:
            Dictionary with company metadata
        """
        metadata = {
            'name': '',
            'batch': '',
            'industry': '',
            'location': '',
            'website': '',
            'description': '',
            'logo': '',
            'video': '',
            'detail_url': ''
        }
        
        try:
            # Unified text for regex searches
            text = block.get_text(' ', strip=True)
            # Prefer explicit name/location spans
            name_span = block.find('span', class_=lambda c: c and c.startswith('_coName_'))
            if name_span and name_span.get_text(strip=True):
                metadata['name'] = name_span.get_text(strip=True)
            loc_span = block.find('span', class_=lambda c: c and c.startswith('_coLocation_'))
            if loc_span and loc_span.get_text(strip=True):
                metadata['location'] = loc_span.get_text(strip=True)
            # Root anchor fallback for detail URL
            if block.name == 'a':
                root_href = block.get('href') or ''
                if root_href.startswith('/companies/'):
                    metadata['detail_url'] = f"https://www.ycombinator.com{root_href}"
            
            # Name - usually in h2, h3, or strong tag, or link text
            if not metadata['name']:
                for tag in ['h3', 'h2', 'h4', 'strong', 'a']:
                    el = block.find(tag)
                    if el and el.get_text(strip=True):
                        text_content = el.get_text(strip=True)
                        if len(text_content) > 2 and len(text_content) < 100 and not text_content.lower().startswith('http'):
                            metadata['name'] = text_content
                            break
            
            # Batch - check data attributes first (YC often uses these)
            if not metadata['batch']:
                pill_spans = block.find_all('span', class_=lambda c: c and c.startswith('pill'))
                for ps in pill_spans:
                    pill_text = ps.get_text(strip=True)
                    if re.search(r'(Summer|Winter|Fall|Spring)\s+20\d{2}', pill_text):
                        metadata['batch'] = pill_text
                        break
                if not metadata['batch']:
                    m = re.search(r'\b([SWF]\d{2})\b', text)
                    if m:
                        metadata['batch'] = m.group(1).upper()
            
            # Industry/tags - often in span, small, or badge elements
            industries = []
            for ps in block.find_all('span', class_=lambda c: c and c.startswith('pill')):
                pill_text = ps.get_text(strip=True)
                if pill_text and pill_text != metadata.get('batch') and not re.search(r'(Summer|Winter|Fall|Spring)\s+20\d{2}', pill_text):
                    industries.append(pill_text)
            if industries:
                metadata['industry'] = ', '.join(industries)
            
            # Location - patterns like "San Francisco, CA", "New York", "Remote"
            location_match = re.search(r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,?\s*[A-Z]{2}|Remote|[A-Z][a-z]+,?\s*[A-Z][a-z]+)\b', text)
            if location_match:
                metadata['location'] = location_match.group(1)
            
            # Website - look for links
            links = block.find_all('a', href=True)
            for link in links:
                href = link['href']
                if href.startswith('http') and 'ycombinator.com' not in href:
                    metadata['website'] = href
                    break
                # capture detail link to company page
                if href.startswith('/companies/'):
                    metadata['detail_url'] = f"https://www.ycombinator.com{href}"
            
            # Description - usually in p tags or longer text blocks
            desc_container = block.find('div', class_=lambda c: c and 'text-sm' in c)
            if desc_container:
                desc_span = desc_container.find('span')
                if desc_span:
                    desc = desc_span.get_text(strip=True)
                    if desc:
                        metadata['description'] = desc
            
            # Logo/images
            img = block.find('img', src=True)
            if img:
                metadata['logo'] = img['src']
            
            # Video - look for video tags or common video service patterns
            for tag in block.find_all(['video', 'iframe']):
                if tag.get('src'):
                    metadata['video'] = tag['src']
                    break
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata
    
    def score_company(self, metadata: Dict) -> int:
        """
        Score company for lead potential based on weak brand signals.
        
        Scoring rules:
        - No website: +3
        - Short/generic description (<150 chars): +2
        - No logo: +2
        - No video/demo: +2
        - No GitHub link: +1
        - Team size < 5 (if available): +1
        - No founders parsed: +1
        
        Higher score = weaker brand identity = better lead
        
        Args:
            metadata: Company metadata dictionary
            
        Returns:
            Lead score (0-9)
        """
        score = 0
        
        # No website
        if not metadata.get('website'):
            score += 3
        
        # Short/weak description
        desc = metadata.get('description', '')
        if len(desc) < 150:
            score += 2
        
        # No logo
        if not metadata.get('logo'):
            score += 2
        
        # No video/demo
        if not metadata.get('video'):
            score += 2
        # GitHub
        if not metadata.get('github'):
            score += 1
        # Team size
        try:
            ts = int(metadata.get('team_size') or 0)
            if ts and ts < 5:
                score += 1
        except Exception:
            pass
        # Founders
        if not metadata.get('founders'):
            score += 1
        
        return score
    
    def _batch_matches(self, batch: str, filters: List[str]) -> bool:
        """Check if batch string matches any filter"""
        if not batch:
            return False
        
        batch_upper = batch.upper().strip()
        for filt in filters:
            filt_upper = filt.upper().strip()
            # Match exact or abbreviated forms
            # e.g., "W25" matches "Winter 2025", "W25", etc.
            if filt_upper in batch_upper or batch_upper in filt_upper:
                return True
            
            # Try to match year+season
            year_match = re.search(r'(\d{2,4})', batch_upper)
            season_match = re.search(r'(W|WINTER|F|FALL|S|SUMMER)', batch_upper)
            filt_year = re.search(r'(\d{2,4})', filt_upper)
            filt_season = re.search(r'(W|WINTER|F|FALL|S|SUMMER)', filt_upper)
            
            if year_match and season_match and filt_year and filt_season:
                if year_match.group(1)[-2:] == filt_year.group(1)[-2:]:  # Compare last 2 digits of year
                    if season_match.group(1)[0] == filt_season.group(1)[0]:  # Compare first letter of season
                        return True
        
        return False
    
    def save_results(self, base_name: str = 'yc_startups') -> Dict[str, str]:
        """
        Save results to CSV and JSON files.
        
        Args:
            base_name: Base filename for output files
            
        Returns:
            Dictionary with paths to saved files
        """
        if not self.results:
            logger.warning("No results to save")
            return {}
        
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = os.path.join('data', f'{base_name}_{ts}.csv')
        json_path = os.path.join('data', f'{base_name}_{ts}.json')
        os.makedirs('data', exist_ok=True)
        
        fields = ['name', 'batch', 'industry', 'location', 'website_present',
              'website', 'detail_url', 'description', 'description_length', 'logo', 'video',
              'team_size', 'founders', 'github', 'score']
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for row in self.results:
                w.writerow({k: row.get(k, '') for k in fields})
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.results)} results to {csv_path} and {json_path}")
        return {'csv': csv_path, 'json': json_path}
    
    def run(self, batch_filter: Optional[List[str]] = None, max_results: int = 100) -> List[Dict]:
        """
        Main pipeline: fetch, score, rank, and store companies.
        
        Args:
            batch_filter: List of batch names to filter (e.g., ["W25", "F24"])
            max_results: Maximum number of results to return
            
        Returns:
            List of scored and ranked companies
        """
        logger.info("Starting YC Startup scraper")
        
        # Load existing if excluding
        if self.exclude_existing and not self.existing_names:
            self.load_existing_names()

        # Fetch listing-level companies
        companies = self.fetch_companies(batch_filter=batch_filter)

        # Exclude existing names early
        if self.exclude_existing and self.existing_names:
            before = len(companies)
            companies = [c for c in companies if c.get('name','').lower() not in self.existing_names]
            logger.info(f"Excluded {before - len(companies)} previously saved companies; {len(companies)} remain")

        # Filter out navigation/header blocks lacking detail_url or with root directory link
        filtered = []
        for c in companies:
            detail = c.get('detail_url','')
            if not detail or detail.rstrip('/') == 'https://www.ycombinator.com/companies':
                continue
            # Require some descriptive signal
            if not c.get('description') or len(c.get('description','').strip()) < 10:
                # Allow short description only if batch is present (real company)
                if not c.get('batch'):
                    continue
            filtered.append(c)
        if len(filtered) != len(companies):
            logger.info(f"Filtered out {len(companies)-len(filtered)} navigation/invalid blocks")
        companies = filtered
        
        if not companies:
            logger.warning("No companies found")
            return []
        
        # Enrich each company with detail page data in parallel
        from concurrent.futures import ThreadPoolExecutor, as_completed
        urls_to_fetch = [(i, str(c.get('detail_url'))) for i, c in enumerate(companies) if c.get('detail_url')]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_idx = {executor.submit(self._extract_detail_page, url): idx for idx, url in urls_to_fetch}
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    detail = future.result()
                    for k, v in detail.items():
                        if v and not companies[idx].get(k):
                            companies[idx][k] = v
                except Exception as e:
                    logger.warning(f"Detail enrichment failed for company {idx}: {e}")

        # Score each company
        scored_companies = []
        for company in companies:
            score = self.score_company(company)
            company['score'] = score
            company['website_present'] = bool(company.get('website'))
            company['description_length'] = len(company.get('description', ''))
            scored_companies.append(company)
        
        # Sort by score (highest first = weakest brand)
        scored_companies.sort(key=lambda x: x['score'], reverse=True)
        
        # Limit results
        self.results = scored_companies[:max_results]
        
        logger.info(f"Processed {len(self.results)} companies")
        logger.info(f"Top score: {self.results[0]['score'] if self.results else 0}")
        logger.info(f"Avg score: {sum(c['score'] for c in self.results) / len(self.results) if self.results else 0:.2f}")
        
        return self.results
    
    def __del__(self):
        """Cleanup driver on deletion"""
        self._close_driver()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='YC Startup Directory Scraper')
    parser.add_argument('--batch', nargs='+', help='Batch filters (e.g., W25 F24 S24)')
    parser.add_argument('--max', type=int, default=100, help='Maximum results')
    parser.add_argument('--exclude-existing', action='store_true', help='Exclude companies already saved in prior yc_startups CSVs')
    parser.add_argument('--regions', type=str, help='Region filter (e.g., "South Asia")')
    args = parser.parse_args()
    
    scraper = YCStartupScraper(exclude_existing=args.exclude_existing, regions=args.regions)
    print("🚀 Starting YC Startup Scraper")
    print("=" * 60)
    if args.batch:
        print(f"Batch filter: {', '.join(args.batch)}")
    print(f"Max results: {args.max}")
    print("=" * 60)
    
    results = scraper.run(batch_filter=args.batch, max_results=args.max)
    
    if results:
        paths = scraper.save_results()
        print("\n✅ Success")
        print(f"CSV: {paths['csv']}")
        print(f"JSON: {paths['json']}")
        print(f"\nTop 10 leads (highest score = weakest brand):")
        print("-" * 60)
        for i, company in enumerate(results[:10], 1):
            print(f"{i}. {company['name']} ({company['batch']}) - Score: {company['score']}")
            print(f"   Location: {company.get('location', 'N/A')}")
            print(f"   Website: {'Yes' if company['website_present'] else 'No'}")
            print(f"   Description: {len(company.get('description', ''))} chars")
            print()
    else:
        print("\n❌ No results")


if __name__ == '__main__':
    main()
