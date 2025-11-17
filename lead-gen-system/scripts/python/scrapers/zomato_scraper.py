"""
Zomato Restaurant/Business Scraper

Extracts restaurant listings from Zomato to identify businesses
with weak digital presence for lead generation.
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
class Restaurant:
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
    cuisine: Optional[str] = None
    price_range: Optional[str] = None
    zomato_url: Optional[str] = None


def fetch_zomato_search(query: str, city: str = "Mumbai", max_results: int = 50, delay: float = 2.0) -> List[Dict[str, Any]]:
    """Fetch restaurant listings from Zomato.
    
    Note: Zomato heavily uses JavaScript/React and may block scraping.
    This implementation is for educational purposes and may not work in production.
    
    Alternative: Use Zomato API if available.
    """
    results = []
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    # Zomato search URL pattern (may vary)
    # Example: https://www.zomato.com/mumbai/cafes
    city_slug = city.lower().replace(" ", "-")
    query_slug = query.lower().replace(" ", "-")
    search_url = f"https://www.zomato.com/{city_slug}/{query_slug}"
    
    print(f"🔍 Fetching Zomato: '{query}' in {city}")
    print(f"   URL: {search_url}")
    print(f"   ⚠️  Note: Zomato uses heavy JS; may return limited results")
    
    try:
        resp = requests.get(search_url, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            print(f"❌ HTTP {resp.status_code}")
            return results
        
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Zomato structure: restaurant cards (selectors are heuristic)
        # Modern Zomato is React-based; static HTML may be limited
        cards = soup.find_all("div", class_=re.compile(r"search-result|restaurant-card"))
        
        if not cards:
            # Try alternative selectors
            cards = soup.find_all("article") or soup.find_all("a", href=re.compile(r"/restaurant/"))
        
        if not cards:
            print(f"⚠️  No restaurant cards found (likely JS-rendered)")
            # Fallback: try to extract any restaurant links
            links = soup.find_all("a", href=re.compile(r"zomato\.com/.*/restaurant/"))
            if links:
                print(f"   Found {len(links)} restaurant links (limited data)")
                for link in links[:max_results]:
                    results.append({
                        "url": link.get("href"),
                        "html": str(link.parent) if link.parent else str(link),
                    })
            return results
        
        print(f"   Found {len(cards)} restaurant cards")
        
        for card in cards[:max_results]:
            results.append({"html": str(card)})
        
    except requests.RequestException as e:
        print(f"❌ Request error: {str(e)[:150]}")
    
    print(f"✅ Collected {len(results)} raw entries")
    return results


def extract_zomato_metadata(entry: Dict[str, Any]) -> Restaurant:
    """Extract restaurant data from Zomato HTML block."""
    soup = BeautifulSoup(entry["html"], "html.parser")
    
    # Name
    name = "Unknown"
    name_tag = soup.find("h4") or soup.find("a", class_=re.compile(r"result-title"))
    if not name_tag:
        name_tag = soup.find(string=re.compile(r".{3,}"))  # any text > 3 chars
    if name_tag:
        name = name_tag.get_text(strip=True) if hasattr(name_tag, "get_text") else str(name_tag)
    
    # Address/location
    address = ""
    addr_tag = soup.find("div", class_=re.compile(r"address|location"))
    if not addr_tag:
        addr_tag = soup.find("p", class_=re.compile(r"subtext"))
    if addr_tag:
        address = addr_tag.get_text(strip=True)
    
    # Zomato URL
    zomato_url = entry.get("url")
    if not zomato_url:
        link = soup.find("a", href=True)
        if link:
            zomato_url = link["href"]
            if not zomato_url.startswith("http"):
                zomato_url = f"https://www.zomato.com{zomato_url}"
    
    # Phone (usually not on listing page; would need detail page scrape)
    phone = None
    phone_present = False
    phone_tag = soup.find("a", href=re.compile(r"tel:"))
    if phone_tag:
        phone_text = phone_tag["href"]
        phone = re.sub(r"[^\d+]", "", phone_text)
        phone_present = len(phone) >= 10
    
    # Website (usually not on listing page)
    website = None
    website_present = False
    website_tag = soup.find("a", href=re.compile(r"^http"))
    if website_tag:
        href = website_tag["href"]
        if "zomato" not in href:
            website = href
            website_present = True
    
    # Rating
    rating = None
    rating_tag = soup.find("div", class_=re.compile(r"rating"))
    if not rating_tag:
        rating_tag = soup.find(string=re.compile(r"\d+\.\d+"))
    if rating_tag:
        rating_text = rating_tag.get_text() if hasattr(rating_tag, "get_text") else str(rating_tag)
        match = re.search(r"(\d+\.?\d*)", rating_text)
        if match:
            rating = float(match.group(1))
    
    # Reviews
    reviews = None
    reviews_tag = soup.find(string=re.compile(r"\d+\s*(review|rating)", re.I))
    if reviews_tag:
        match = re.search(r"(\d+)", str(reviews_tag).replace(",", ""))
        if match:
            reviews = int(match.group(1))
    
    # Cuisine
    cuisine = None
    cuisine_tag = soup.find("span", class_=re.compile(r"cuisine"))
    if cuisine_tag:
        cuisine = cuisine_tag.get_text(strip=True)
    
    # Price range
    price_range = None
    price_tag = soup.find(string=re.compile(r"₹|Rs"))
    if price_tag:
        price_range = str(price_tag).strip()
    
    return Restaurant(
        name=name,
        address=address,
        website_present=website_present,
        phone_present=phone_present,
        rating=rating,
        reviews=reviews,
        score=0,  # calculated later
        phone=phone,
        website=website,
        cuisine=cuisine,
        price_range=price_range,
        zomato_url=zomato_url,
    )


def score_restaurant(restaurant: Restaurant) -> int:
    """Score restaurant by digital presence gaps."""
    score = 0
    if not restaurant.website_present:
        score += 3
    if not restaurant.phone_present:
        score += 2
    return score


def save_zomato_results(restaurants: List[Restaurant], query: str, city: str) -> Dict[str, str]:
    """Save ranked restaurant results to CSV/JSON."""
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = re.sub(r"[^\w\s-]", "", query).replace(" ", "_")
    base = f"zomato_{safe_query}_{city}_{ts}"
    
    csv_path = output_dir / f"{base}.csv"
    json_path = output_dir / f"{base}.json"
    
    rows = [asdict(r) for r in restaurants]
    
    # CSV
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    # JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    
    return {"csv": str(csv_path), "json": str(json_path)}


def scrape_zomato(query: str, city: str = "Mumbai", max_results: int = 50) -> tuple[List[Restaurant], Dict[str, str]]:
    """Main Zomato scraper: fetch, extract, score, rank, save.
    
    Args:
        query: Search query (e.g., "cafes" or "italian restaurants")
        city: City name
        max_results: Max restaurants to collect
    
    Returns:
        (ranked_restaurants, file_paths)
    """
    print(f"\n🚀 Starting Zomato scraper")
    print(f"   Query: '{query}' in {city}")
    
    # Fetch
    raw_results = fetch_zomato_search(query, city, max_results)
    
    if not raw_results:
        print("❌ No results fetched")
        return [], {}
    
    # Extract
    print(f"\n📊 Extracting metadata...")
    restaurants = []
    for entry in raw_results:
        try:
            rest = extract_zomato_metadata(entry)
            rest.city = city
            rest.score = score_restaurant(rest)
            restaurants.append(rest)
        except Exception as e:
            print(f"⚠️  Extraction error: {str(e)[:100]}")
    
    # Rank
    ranked = sorted(restaurants, key=lambda r: (r.score, -(r.reviews or 0)), reverse=True)
    
    print(f"✅ Extracted {len(ranked)} restaurants")
    
    # Save
    files = save_zomato_results(ranked, query, city)
    
    print(f"\n💾 Saved:")
    print(f"   CSV: {files['csv']}")
    print(f"   JSON: {files['json']}")
    
    # Summary
    high_priority = [r for r in ranked if r.score >= 3]
    print(f"\n📈 Summary:")
    print(f"   High-priority (score >=3): {len(high_priority)}")
    print(f"   Missing website: {sum(1 for r in ranked if not r.website_present)}")
    print(f"   Missing phone: {sum(1 for r in ranked if not r.phone_present)}")
    
    return ranked, files


if __name__ == "__main__":
    # Test run
    query = "cafes"
    city = "Mumbai"
    
    restaurants, files = scrape_zomato(query, city, max_results=30)
    
    if restaurants:
        print("\n🎯 Top 10 lead opportunities:")
        for i, r in enumerate(restaurants[:10], 1):
            print(f"{i:2d}. {r.name[:50]} (score: {r.score})")
            print(f"    Website: {'❌' if not r.website_present else '✅'}  Phone: {'❌' if not r.phone_present else '✅'}")
            if r.rating:
                print(f"    Rating: {r.rating}/5 ({r.reviews or 0} reviews)")
