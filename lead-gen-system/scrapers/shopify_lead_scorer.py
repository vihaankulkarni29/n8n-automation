"""
Shopify Lead Scoring Scraper
Discovers Shopify stores via Google search and scores them as potential leads
based on website quality, branding, and marketing presence.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import time
from pathlib import Path
import re
from urllib.parse import urlparse, urljoin
import json


class ShopifyLeadScorer:
    """
    Discover and score Shopify stores as potential leads based on:
    - Domain quality (myshopify.com vs custom)
    - Content quality (About page, storytelling)
    - Theme sophistication
    - Social media presence
    """
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    # Industry keywords
    INDUSTRY_KEYWORDS = {
        'fashion': [
            'fashion', 'clothing', 'apparel', 'dress', 'shirt', 'pants', 'shoes', 
            'accessories', 'jewelry', 'watches', 'bags', 'style', 'wear', 'outfit',
            'boutique', 'designer', 'collection', 'wardrobe', 'footwear', 'handbags'
        ],
        'technology': [
            'tech', 'gadget', 'electronics', 'computer', 'phone', 'software', 
            'hardware', 'device', 'digital', 'smart', 'wireless', 'bluetooth',
            'laptop', 'tablet', 'accessory', 'charger', 'cable', 'audio', 'gaming'
        ],
        'b2b_design': [
            'design', 'branding', 'marketing', 'agency', 'business', 'corporate',
            'professional', 'services', 'consulting', 'solutions', 'enterprise',
            'wholesale', 'bulk', 'b2b', 'trade', 'supplier', 'manufacturer'
        ]
    }
    
    # Default Shopify themes (subset)
    DEFAULT_THEMES = [
        'debut', 'brooklyn', 'minimal', 'supply', 'narrative', 'simple',
        'venture', 'boundless', 'express', 'prestige', 'dawn', 'craft'
    ]
    
    def __init__(self, delay: float = 2.0):
        """Initialize scraper."""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def discover_stores(self, queries: List[str], max_per_query: int = 10) -> List[str]:
        """
        Discover Shopify stores via Google search.
        
        Args:
            queries: List of search queries (e.g., 'site:myshopify.com fashion')
            max_per_query: Maximum stores per query
            
        Returns:
            List of unique store URLs
        """
        print(f"\n{'='*80}")
        print(f"SHOPIFY STORE DISCOVERY")
        print(f"{'='*80}")
        
        all_stores = set()
        
        for query in queries:
            print(f"\n🔍 Searching: {query}")
            
            try:
                # Use DuckDuckGo HTML search (more lenient than Google)
                search_url = f"https://html.duckduckgo.com/html/"
                params = {'q': query}
                
                response = self.session.get(search_url, params=params, timeout=15)
                
                if response.status_code != 200:
                    print(f"   ❌ Search failed: Status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract URLs from search results
                links = soup.find_all('a', class_='result__url')
                
                count = 0
                for link in links:
                    if count >= max_per_query:
                        break
                    
                    href = link.get('href', '')
                    
                    # Clean and validate URL
                    if 'myshopify.com' in href or self._is_shopify_store(href):
                        clean_url = self._clean_url(href)
                        if clean_url:
                            all_stores.add(clean_url)
                            count += 1
                
                print(f"   ✅ Found {count} stores")
                
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
        
        stores_list = list(all_stores)
        print(f"\n✅ Total unique stores discovered: {len(stores_list)}")
        
        return stores_list
    
    def _clean_url(self, url: str) -> Optional[str]:
        """Clean and normalize URL."""
        try:
            if not url.startswith('http'):
                url = 'https://' + url
            
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            return base_url
        except:
            return None
    
    def _is_shopify_store(self, url: str) -> bool:
        """Quick check if URL is a Shopify store."""
        try:
            response = self.session.get(url, timeout=5)
            content = response.text.lower()
            
            return (
                'shopify' in content or
                'cdn.shopify.com' in content or
                'myshopify.com' in content
            )
        except:
            return False
    
    def extract_metadata(self, store_url: str) -> Dict:
        """
        Extract metadata from a Shopify store.
        
        Args:
            store_url: Store URL
            
        Returns:
            Dict with metadata
        """
        print(f"\n📊 Analyzing: {store_url}")
        
        metadata = {
            'url': store_url,
            'domain': urlparse(store_url).netloc,
            'is_myshopify_domain': 'myshopify.com' in store_url,
            'has_custom_domain': 'myshopify.com' not in store_url,
            'has_about_page': False,
            'about_page_word_count': 0,
            'has_story_page': False,
            'story_page_word_count': 0,
            'theme_name': 'unknown',
            'is_default_theme': False,
            'social_links': [],
            'has_instagram': False,
            'has_facebook': False,
            'has_linkedin': False,
            'has_twitter': False,
            'meta_description': '',
            'page_title': '',
            'error': None
        }
        
        try:
            # Fetch homepage
            response = self.session.get(store_url, timeout=15)
            
            if response.status_code != 200:
                metadata['error'] = f"HTTP {response.status_code}"
                return metadata
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract page title
            title_tag = soup.find('title')
            if title_tag:
                metadata['page_title'] = title_tag.get_text(strip=True)
            
            # Extract meta description
            meta_desc = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
            if meta_desc:
                metadata['meta_description'] = meta_desc.get('content', '')[:300]
            
            # Detect theme
            theme_name = self._detect_theme(soup, response.text)
            metadata['theme_name'] = theme_name
            metadata['is_default_theme'] = any(default in theme_name.lower() for default in self.DEFAULT_THEMES)
            
            # Find social links
            social_links = self._extract_social_links(soup)
            metadata['social_links'] = social_links
            metadata['has_instagram'] = any('instagram.com' in link for link in social_links)
            metadata['has_facebook'] = any('facebook.com' in link for link in social_links)
            metadata['has_linkedin'] = any('linkedin.com' in link for link in social_links)
            metadata['has_twitter'] = any('twitter.com' in link or 'x.com' in link for link in social_links)
            
            # Check for About page
            about_data = self._check_about_page(store_url, soup)
            metadata.update(about_data)
            
            print(f"   ✅ Analyzed successfully")
            
        except Exception as e:
            metadata['error'] = str(e)[:100]
            print(f"   ❌ Error: {metadata['error']}")
        
        return metadata
    
    def _detect_theme(self, soup: BeautifulSoup, html: str) -> str:
        """Detect Shopify theme name."""
        # Look for theme name in HTML comments or meta tags
        theme_pattern = re.search(r'theme[_-]name["\']?\s*[:=]\s*["\']([^"\']+)', html, re.I)
        if theme_pattern:
            return theme_pattern.group(1)
        
        # Look for Shopify.theme references
        shopify_theme = re.search(r'Shopify\.theme\s*=\s*{\s*name:\s*["\']([^"\']+)', html, re.I)
        if shopify_theme:
            return shopify_theme.group(1)
        
        # Check for common theme indicators in class names
        body_tag = soup.find('body')
        if body_tag:
            classes = ' '.join(body_tag.get('class', []))
            for theme in self.DEFAULT_THEMES:
                if theme in classes.lower():
                    return theme
        
        return 'unknown'
    
    def _extract_social_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract social media links."""
        social_links = []
        social_domains = ['instagram.com', 'facebook.com', 'twitter.com', 'x.com', 'linkedin.com', 'youtube.com', 'tiktok.com']
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(domain in href for domain in social_domains):
                social_links.append(href)
        
        return list(set(social_links))
    
    def _check_about_page(self, base_url: str, homepage_soup: BeautifulSoup) -> Dict:
        """Check for About/Story pages and analyze content."""
        result = {
            'has_about_page': False,
            'about_page_word_count': 0,
            'has_story_page': False,
            'story_page_word_count': 0,
        }
        
        # Common About page URLs
        about_urls = [
            urljoin(base_url, '/pages/about'),
            urljoin(base_url, '/pages/about-us'),
            urljoin(base_url, '/pages/our-story'),
            urljoin(base_url, '/about'),
            urljoin(base_url, '/about-us'),
        ]
        
        # Also look for About links on homepage
        for link in homepage_soup.find_all('a', href=True):
            href = link['href'].lower()
            if 'about' in href or 'story' in href:
                full_url = urljoin(base_url, link['href'])
                if full_url not in about_urls:
                    about_urls.append(full_url)
        
        # Check each potential About page
        for url in about_urls[:5]:  # Limit to 5 checks
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Remove script and style tags
                    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    
                    text = soup.get_text(separator=' ', strip=True)
                    word_count = len(text.split())
                    
                    if word_count > 50:  # Minimum words to count as real content
                        if 'story' in url.lower():
                            result['has_story_page'] = True
                            result['story_page_word_count'] = word_count
                        else:
                            result['has_about_page'] = True
                            result['about_page_word_count'] = word_count
                        
                        break  # Found a valid About page
                
                time.sleep(0.5)
                
            except:
                continue
        
        return result
    
    def classify_industry(self, metadata: Dict) -> Tuple[str, float]:
        """
        Classify store industry based on content.
        
        Args:
            metadata: Store metadata dict
            
        Returns:
            Tuple of (industry, confidence_score)
        """
        text = f"{metadata.get('page_title', '')} {metadata.get('meta_description', '')}".lower()
        
        scores = {}
        
        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[industry] = score
        
        if not any(scores.values()):
            return ('unknown', 0.0)
        
        best_industry = max(scores, key=scores.get)
        total_keywords = len(self.INDUSTRY_KEYWORDS[best_industry])
        confidence = scores[best_industry] / total_keywords
        
        return (best_industry, confidence)
    
    def score_leads(self, metadata: Dict) -> Dict:
        """
        Score a store as a potential lead based on weaknesses.
        
        Scoring:
        - myshopify.com domain = +3 (needs custom domain)
        - No About page = +3 (needs content)
        - Short About page (<150 words) = +2 (needs better storytelling)
        - Default theme = +2 (needs custom design)
        - No social links = +3 (needs marketing)
        - Few social links (1-2) = +2 (weak social presence)
        
        Args:
            metadata: Store metadata dict
            
        Returns:
            Dict with lead score and weaknesses
        """
        score = 0
        weaknesses = []
        
        # Domain quality
        if metadata['is_myshopify_domain']:
            score += 3
            weaknesses.append('Using myshopify.com domain (needs custom domain)')
        
        # Content quality
        if not metadata['has_about_page'] and not metadata['has_story_page']:
            score += 3
            weaknesses.append('No About/Story page (needs brand storytelling)')
        elif metadata['about_page_word_count'] < 150 and metadata['story_page_word_count'] < 150:
            score += 2
            weaknesses.append('Weak About page (<150 words)')
        
        # Design quality
        if metadata['is_default_theme']:
            score += 2
            weaknesses.append(f"Using default Shopify theme ({metadata['theme_name']})")
        
        # Marketing presence
        social_count = len(metadata['social_links'])
        if social_count == 0:
            score += 3
            weaknesses.append('No social media links (needs marketing setup)')
        elif social_count <= 2:
            score += 2
            weaknesses.append('Weak social media presence (1-2 platforms)')
        
        # Classify lead quality
        if score >= 8:
            lead_quality = 'hot'
        elif score >= 5:
            lead_quality = 'warm'
        elif score >= 3:
            lead_quality = 'cold'
        else:
            lead_quality = 'poor'
        
        return {
            'lead_score': score,
            'lead_quality': lead_quality,
            'weaknesses': weaknesses,
            'weakness_count': len(weaknesses)
        }
    
    def run_pipeline(self, queries: List[str], max_stores: int = 20) -> pd.DataFrame:
        """
        Run the complete lead scoring pipeline.
        
        Args:
            queries: Search queries
            max_stores: Maximum stores to analyze
            
        Returns:
            DataFrame with scored leads
        """
        print(f"\n{'='*80}")
        print(f"SHOPIFY LEAD SCORING PIPELINE")
        print(f"{'='*80}")
        
        # Step 1: Discover stores
        store_urls = self.discover_stores(queries, max_per_query=max_stores // len(queries))
        
        if not store_urls:
            print("\n⚠️  No stores discovered")
            return pd.DataFrame()
        
        # Limit to max_stores
        store_urls = store_urls[:max_stores]
        
        # Step 2: Extract metadata and score
        results = []
        
        for i, url in enumerate(store_urls, 1):
            print(f"\n[{i}/{len(store_urls)}] Processing: {url}")
            
            # Extract metadata
            metadata = self.extract_metadata(url)
            
            # Classify industry
            industry, confidence = self.classify_industry(metadata)
            metadata['industry'] = industry
            metadata['industry_confidence'] = confidence
            
            # Score as lead
            lead_data = self.score_leads(metadata)
            metadata.update(lead_data)
            
            results.append(metadata)
            
            time.sleep(self.delay)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Sort by lead score (highest first)
        df = df.sort_values('lead_score', ascending=False)
        
        return df
    
    def save_results(self, df: pd.DataFrame, output_format: str = 'both') -> Dict[str, str]:
        """
        Save results to CSV and/or JSON.
        
        Args:
            df: Results DataFrame
            output_format: 'csv', 'json', or 'both'
            
        Returns:
            Dict with output file paths
        """
        if df.empty:
            print("\n⚠️  No data to save")
            return {}
        
        output_dir = Path('data')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        files = {}
        
        # Save CSV
        if output_format in ['csv', 'both']:
            csv_file = output_dir / f'shopify_leads_scored_{timestamp}.csv'
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            files['csv'] = str(csv_file)
            print(f"\n✅ Saved CSV: {csv_file}")
        
        # Save JSON (more detailed)
        if output_format in ['json', 'both']:
            json_file = output_dir / f'shopify_leads_scored_{timestamp}.json'
            df.to_json(json_file, orient='records', indent=2)
            files['json'] = str(json_file)
            print(f"✅ Saved JSON: {json_file}")
        
        # Print summary
        self._print_summary(df)
        
        return files
    
    def _print_summary(self, df: pd.DataFrame):
        """Print analysis summary."""
        print(f"\n{'='*80}")
        print(f"LEAD SCORING SUMMARY")
        print(f"{'='*80}")
        
        print(f"\nTotal stores analyzed: {len(df)}")
        
        # Lead quality breakdown
        if 'lead_quality' in df.columns:
            print(f"\n🎯 LEAD QUALITY:")
            quality_counts = df['lead_quality'].value_counts()
            for quality, count in quality_counts.items():
                print(f"   {quality.upper()}: {count} stores")
        
        # Industry breakdown
        if 'industry' in df.columns:
            print(f"\n🏭 INDUSTRIES:")
            industry_counts = df['industry'].value_counts().head(5)
            for industry, count in industry_counts.items():
                print(f"   {industry}: {count} stores")
        
        # Top weaknesses
        if 'weaknesses' in df.columns:
            all_weaknesses = []
            for weaknesses_list in df['weaknesses']:
                all_weaknesses.extend(weaknesses_list)
            
            from collections import Counter
            weakness_counts = Counter(all_weaknesses).most_common(5)
            
            print(f"\n⚠️  TOP WEAKNESSES:")
            for weakness, count in weakness_counts:
                print(f"   {count} stores: {weakness}")
        
        # Top leads
        print(f"\n🔥 TOP 10 LEADS (by score):")
        top_leads = df.nlargest(10, 'lead_score')
        for idx, row in top_leads.iterrows():
            print(f"\n   {row['domain']} (Score: {row['lead_score']})")
            print(f"      Industry: {row.get('industry', 'unknown')}")
            print(f"      Quality: {row['lead_quality'].upper()}")
            if row.get('weaknesses'):
                print(f"      Issues: {', '.join(row['weaknesses'][:2])}")


def main():
    """Main function to run lead scoring."""
    scraper = ShopifyLeadScorer(delay=2.0)
    
    # Search queries targeting different industries
    queries = [
        'site:myshopify.com fashion india',
        'site:myshopify.com clothing brand',
        'site:myshopify.com technology gadgets',
        'site:myshopify.com jewelry accessories',
    ]
    
    # Run pipeline
    df = scraper.run_pipeline(queries, max_stores=20)
    
    if not df.empty:
        scraper.save_results(df, output_format='both')
    else:
        print("\n⚠️  No stores found to analyze")
        print("Note: Google/DuckDuckGo may block automated searches.")
        print("Consider using the Shopify Store Directory API or manual seed URLs.")


if __name__ == '__main__':
    main()
