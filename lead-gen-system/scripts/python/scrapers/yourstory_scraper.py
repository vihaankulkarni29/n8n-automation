"""
YourStory Startup Scraper
Scrapes Indian startup data from YourStory including funding, team size, and contact info
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from typing import List, Dict
import time
import re
from pathlib import Path


class YourStoryScraper:
    """
    Scrape startup data from YourStory.
    """
    
    BASE_URL = "https://yourstory.com"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    def __init__(self, delay: float = 2.0):
        """
        Initialize scraper.
        
        Args:
            delay: Delay between requests in seconds
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def scrape_funding_articles(self, max_pages: int = 3) -> List[Dict]:
        """
        Scrape funding announcements from YourStory articles.
        
        Args:
            max_pages: Number of pages to scrape
            
        Returns:
            List of startup dicts from funding articles
        """
        print(f"\n{'='*80}")
        print(f"YOURSTORY FUNDING ANNOUNCEMENTS SCRAPER")
        print(f"{'='*80}")
        
        startups = []
        
        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/category/funding?page={page}"
            
            try:
                print(f"\n🔍 Page {page}: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    print(f"   ❌ Failed: Status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find article cards/links
                articles = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/'))
                
                print(f"   Found {len(articles)} articles")
                
                for article in articles[:20]:  # Limit per page
                    try:
                        title = article.get_text(strip=True)
                        article_url = article.get('href', '')
                        
                        if not article_url.startswith('http'):
                            article_url = self.BASE_URL + article_url
                        
                        # Extract startup name and funding from title
                        startup_data = self._parse_funding_title(title, article_url)
                        
                        if startup_data:
                            startups.append(startup_data)
                    
                    except Exception:
                        continue
                
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"   ⚠️  Error: {str(e)[:100]}")
                continue
        
        # Remove duplicates
        unique_startups = []
        seen_names = set()
        
        for startup in startups:
            name = startup.get('name', '').lower()
            if name and name not in seen_names:
                unique_startups.append(startup)
                seen_names.add(name)
        
        print(f"\n✅ Found {len(unique_startups)} unique startups from funding articles")
        return unique_startups
    
    def _parse_funding_title(self, title: str, url: str) -> Dict:
        """
        Parse startup name and funding from article title.
        
        Args:
            title: Article title
            url: Article URL
            
        Returns:
            Dict with startup data or None
        """
        # Common patterns in funding announcements
        # "X raises $Y", "X secures funding", "X bags investment"
        
        patterns = [
            r'([A-Z][a-zA-Z\s]+?)\s+(?:raises|secures|bags|gets)\s+\$?([\d.]+)\s*(M|Million|Cr|Crore)',
            r'([A-Z][a-zA-Z\s]+?)\s+(?:funding|investment)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.I)
            if match:
                name = match.group(1).strip()
                funding = match.group(2) if len(match.groups()) > 1 else None
                unit = match.group(3) if len(match.groups()) > 2 else None
                
                return {
                    'name': name,
                    'description': title[:500],
                    'funding': f"{funding} {unit}" if funding and unit else None,
                    'yourstory_url': url,
                    'location': 'India',
                }
        
        return None
    
    def _extract_startup_data(self, element) -> Dict:
        """
        Extract startup data from HTML element.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Dict with startup data
        """
        try:
            data = {
                'name': None,
                'description': None,
                'industry': None,
                'website': None,
                'funding': None,
                'founded_year': None,
                'team_size': None,
                'location': 'India',
                'yourstory_url': None,
            }
            
            # Extract name
            name_elem = (
                element.find('h2') or
                element.find('h3') or
                element.find(class_=re.compile(r'title|name|company', re.I))
            )
            if name_elem:
                data['name'] = name_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = element.find('p', class_=re.compile(r'desc|summary', re.I))
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)[:500]
            
            # Extract URL
            link = element.find('a', href=True)
            if link and '/companies/' in link['href']:
                if link['href'].startswith('http'):
                    data['yourstory_url'] = link['href']
                else:
                    data['yourstory_url'] = self.BASE_URL + link['href']
            
            # Extract funding info
            funding_text = str(element)
            funding_match = re.search(r'\$?([\d.]+)\s*(M|Million|Cr|Crore|K|Lakh)', funding_text, re.I)
            if funding_match:
                data['funding'] = funding_match.group(0)
            
            return data
            
        except Exception as e:
            return {}
    
    def get_startup_details(self, company_url: str) -> Dict:
        """
        Get detailed information for a specific startup.
        
        Args:
            company_url: YourStory company profile URL
            
        Returns:
            Dict with detailed startup info
        """
        try:
            response = self.session.get(company_url, timeout=15)
            
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {}
            
            # Extract company details from profile page
            # This structure varies greatly on YourStory
            
            # Try to find website
            website_link = soup.find('a', href=re.compile(r'^https?://(www\.)?[a-zA-Z0-9]'))
            if website_link:
                details['website'] = website_link.get('href')
            
            # Try to find social links
            social_links = soup.find_all('a', href=re.compile(r'linkedin|twitter|facebook|instagram'))
            for link in social_links:
                url = link.get('href', '')
                if 'linkedin' in url:
                    details['linkedin'] = url
                elif 'twitter' in url:
                    details['twitter'] = url
            
            return details
            
        except Exception as e:
            return {}
    
    def scrape_to_dataframe(self, max_pages: int = 3) -> pd.DataFrame:
        """
        Scrape startups and return as DataFrame.
        
        Args:
            max_pages: Number of article pages to scrape
            
        Returns:
            pandas DataFrame
        """
        startups = self.scrape_funding_articles(max_pages=max_pages)
        
        if not startups:
            return pd.DataFrame()
        
        df = pd.DataFrame(startups)
        
        # Add metadata
        df['source'] = 'yourstory'
        df['collected_at'] = datetime.now().isoformat(timespec='seconds')
        
        return df
    
    def save_results(self, df: pd.DataFrame, output_dir: str = 'data') -> str:
        """
        Save results to CSV.
        
        Args:
            df: DataFrame with startup data
            output_dir: Output directory
            
        Returns:
            Output file path
        """
        if df.empty:
            print("⚠️  No data to save")
            return ""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_path / f'yourstory_startups_{timestamp}.csv'
        
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Saved to: {output_file}")
        return str(output_file)


def main():
    """
    Main function to scrape YourStory funding announcements.
    """
    scraper = YourStoryScraper(delay=2.0)
    
    # Scrape funding articles
    df = scraper.scrape_to_dataframe(max_pages=5)
    
    if not df.empty:
        scraper.save_results(df)
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total startups: {len(df)}")
        print(f"With funding info: {df['funding'].notna().sum() if 'funding' in df.columns else 0}")
        print(f"\nTop startups by recent funding:")
        if 'name' in df.columns:
            for idx, row in df.head(10).iterrows():
                funding_info = f" - {row.get('funding', 'N/A')}" if row.get('funding') else ""
                print(f"  {row['name']}{funding_info}")
    else:
        print("\n⚠️  No startups found in funding articles.")
        print("Try again later or check if YourStory structure changed.")


if __name__ == '__main__':
    main()
