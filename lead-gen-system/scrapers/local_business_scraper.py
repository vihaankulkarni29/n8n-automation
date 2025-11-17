"""
Local Business Scraper - Lightweight version using requests + BeautifulSoup

Extracts local business listings from Justdial to identify businesses
with weak digital presence (no website/phone) for lead generation.
"""

import time
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
import pandas as pd

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class Business:
    name: str
    address: str
    website_present: bool
    phone_present: bool
    rating: Optional[float]
    reviews: Optional[int]
    score: int
    phone: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


def fetch_justdial_search(query: str, city: str = "Mumbai", max_pages: int = 3, delay: float = 2.0) -> List[Dict[str, Any]]:
    """Fetch business listings from Justdial.
    
    Note: Justdial may require JavaScript or has anti-scraping.
    This is a basic implementation that may need adjustment.
    """
    results = []
    headers = {"User-Agent": USER_AGENT}
    
    # Justdial URL pattern varies; this is a heuristic
    base_url = f"https://www.justdial.com/{city}/{query.replace(' ', '-')}"
    
    print(f"🔍 Fetching Justdial: '{query}' in {city}")
    print(f"   URL: {base_url}")
    
    for page in range(1, max_pages + 1):
        try:
            url = f"{base_url}/page-{page}" if page > 1 else base_url
            resp = requests.get(url, headers=headers, timeout=15)
            
            if resp.status_code != 200:
                print(f"⚠️  HTTP {resp.status_code} on page {page}")
                break
            
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # Extract listings (selectors are heuristic and may need updates)
            listings = soup.find_all("li", class_=re.compile(r"cntanr|resultbox"))
            
            if not listings:
                # Try alternative
                listings = soup.find_all("div", class_=re.compile(r"store|listing"))
            
            if not listings:
                print(f"⚠️  No listings found on page {page} (may be blocked or selector outdated)")
                break
            
            print(f"   Found {len(listings)} listings on page {page}")
            results.extend([{"html": str(li), "page": page} for li in listings])
            
            time.sleep(delay)
            
        except requests.RequestException as e:
            print(f"❌ Request error: {str(e)[:150]}")
            break
    
    print(f"✅ Collected {len(results)} raw listings")
    return results


def extract_business_metadata(entry: Dict[str, Any]) -> Business:
    """Extract business data from HTML block."""
    soup = BeautifulSoup(entry["html"], "html.parser")
    
    # Name
    name = "Unknown"
    name_tag = soup.find("span", class_=re.compile(r"jcn|storename"))
    if not name_tag:
        name_tag = soup.find("h3") or soup.find("a", class_=re.compile(r"name"))
    if name_tag:
        name = name_tag.get_text(strip=True)
    
    # Address
    address = ""
    addr_tag = soup.find("span", class_=re.compile(r"mrehover|adr"))
    if not addr_tag:
        addr_tag = soup.find("p", class_=re.compile(r"address"))
    if addr_tag:
        address = addr_tag.get_text(strip=True)
    
    # Phone
    phone = None
    phone_present = False
    phone_tag = soup.find("span", class_=re.compile(r"mobilesv|phone"))
    if not phone_tag:
        phone_tag = soup.find("a", href=re.compile(r"tel:"))
    if phone_tag:
        phone_text = phone_tag.get("href", "") or phone_tag.get_text()
        phone = re.sub(r"[^\d+]", "", phone_text)
        if phone and len(phone) >= 10:
            phone_present = True
    
    # Website
    website = None
    website_present = False
    website_tag = soup.find("a", class_=re.compile(r"web"))
    if not website_tag:
        # Find any http link not from justdial
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and "justdial" not in href and "whatsapp" not in href:
                website = href
                website_present = True
                break
    else:
        website = website_tag.get("href")
        website_present = True
    
    # Rating
    rating = None
    rating_tag = soup.find("span", class_=re.compile(r"star|rating"))
    if rating_tag:
        rating_text = rating_tag.get_text()
        match = re.search(r"(\d+\.?\d*)", rating_text)
        if match:
            rating = float(match.group(1))
    
    # Reviews
    reviews = None
    reviews_tag = soup.find("span", class_=re.compile(r"review|votes"))
    if reviews_tag:
        reviews_text = reviews_tag.get_text()
        match = re.search(r"(\d+)", reviews_text.replace(",", ""))
        if match:
            reviews = int(match.group(1))
    
    return Business(
        name=name,
        address=address,
        website_present=website_present,
        phone_present=phone_present,
        rating=rating,
        reviews=reviews,
        score=0,  # calculated later
        phone=phone,
        website=website,
    )


def score_business(business: Business) -> int:
    """Score business by digital presence gaps.
    
    Higher score = weaker marketing presence = better lead
    """
    score = 0
    if not business.website_present:
        score += 3
    if not business.phone_present:
        score += 2
    return score


def save_business_results(businesses: List[Business], query: str, city: str, source: str = "justdial") -> Dict[str, str]:
    """Save ranked business results to CSV/JSON."""
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = re.sub(r"[^\w\s-]", "", query).replace(" ", "_")
    base = f"{source}_{safe_query}_{city}_{ts}"
    
    csv_path = output_dir / f"{base}.csv"
    json_path = output_dir / f"{base}.json"
    
    rows = [asdict(b) for b in businesses]
    
    # CSV
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    # JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    
    return {"csv": str(csv_path), "json": str(json_path)}


def scrape_local_businesses(query: str, city: str = "Mumbai", source: str = "justdial", max_pages: int = 3) -> tuple[List[Business], Dict[str, str]]:
    """Main scraper: fetch, extract, score, rank, save.
    
    Args:
        query: Search query (e.g., "cafes near Borivali")
        city: City name
        source: Data source ("justdial" or "zomato")
        max_pages: Max pages to scrape
    
    Returns:
        (ranked_businesses, file_paths)
    """
    print(f"\n🚀 Starting {source} scraper")
    print(f"   Query: '{query}' in {city}")
    
    # Fetch
    if source == "justdial":
        raw_results = fetch_justdial_search(query, city, max_pages)
    else:
        print(f"❌ Source '{source}' not implemented yet")
        return [], {}
    
    if not raw_results:
        print("❌ No results fetched")
        return [], {}
    
    # Extract
    print(f"\n📊 Extracting metadata...")
    businesses = []
    for entry in raw_results:
        try:
            biz = extract_business_metadata(entry)
            biz.city = city
            biz.category = query
            biz.score = score_business(biz)
            businesses.append(biz)
        except Exception as e:
            print(f"⚠️  Extraction error: {str(e)[:100]}")
    
    # Rank
    ranked = sorted(businesses, key=lambda b: (b.score, -(b.reviews or 0)), reverse=True)
    
    print(f"✅ Extracted {len(ranked)} businesses")
    
    # Save
    files = save_business_results(ranked, query, city, source)
    
    print(f"\n💾 Saved:")
    print(f"   CSV: {files['csv']}")
    print(f"   JSON: {files['json']}")
    
    # Summary
    high_priority = [b for b in ranked if b.score >= 3]
    print(f"\n📈 Summary:")
    print(f"   High-priority (score >=3): {len(high_priority)}")
    print(f"   Missing website: {sum(1 for b in ranked if not b.website_present)}")
    print(f"   Missing phone: {sum(1 for b in ranked if not b.phone_present)}")
    
    return ranked, files


if __name__ == "__main__":
    # Test run
    query = "cafes near Borivali"
    city = "Mumbai"
    
    businesses, files = scrape_local_businesses(query, city, source="justdial", max_pages=2)
    
    if businesses:
        print("\n🎯 Top 10 lead opportunities:")
        for i, b in enumerate(businesses[:10], 1):
            print(f"{i:2d}. {b.name[:50]} (score: {b.score})")
            print(f"    Website: {'❌' if not b.website_present else '✅'}  Phone: {'❌' if not b.phone_present else '✅'}")
