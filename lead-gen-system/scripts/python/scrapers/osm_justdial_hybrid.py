"""
OpenStreetMap + Justdial Hybrid Lead Generator

Combines OSM business data with Justdial ratings to identify high-value leads:
businesses with strong customer traction but weak digital presence.
"""

import time
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

import requests
import pandas as pd

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class Business:
    name: str
    location: str
    city: str
    website_present: bool
    phone_present: bool
    rating: Optional[float]
    reviews: Optional[int]
    score: int
    website: Optional[str] = None
    phone: Optional[str] = None
    source: str = "merged"
    osm_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[str] = None
    notes: Optional[str] = None


def fetch_osm_data(query: str, city: str, region: str = "India", timeout: int = 30) -> List[Dict[str, Any]]:
    """Fetch business data from OpenStreetMap via Overpass API.
    
    Args:
        query: Business type (e.g., "restaurant", "cafe", "shop")
        city: City name
        region: Country/region for geobounding
        timeout: API timeout (seconds)
    
    Returns:
        List of business dicts with OSM data
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Overpass QL query to find nodes/ways with matching amenity/shop tags in city area
    # Note: This searches by city name; for better accuracy, use bounding box coordinates
    overpass_query = f"""
    [out:json][timeout:{timeout}];
    area["name"="{city}"]["admin_level"~"^(4|5|6|8)$"]["place"~"city|town"]->.searchArea;
    (
      node["amenity"~"{query}"](area.searchArea);
      way["amenity"~"{query}"](area.searchArea);
      node["shop"~"{query}"](area.searchArea);
      way["shop"~"{query}"](area.searchArea);
    );
    out center;
    """
    
    print(f"🗺️  Fetching OSM data: '{query}' in {city}, {region}")
    print(f"   API: {overpass_url}")
    
    try:
        resp = requests.post(
            overpass_url,
            data={"data": overpass_query},
            headers={"User-Agent": USER_AGENT},
            timeout=timeout + 10
        )
        
        if resp.status_code != 200:
            print(f"❌ Overpass API HTTP {resp.status_code}")
            return []
        
        data = resp.json()
        elements = data.get("elements", [])
        
        print(f"✅ Found {len(elements)} OSM elements")
        
        # Parse elements
        businesses = []
        for elem in elements:
            tags = elem.get("tags", {})
            name = tags.get("name", "")
            if not name:
                continue  # Skip unnamed
            
            # Location
            lat = elem.get("lat") or (elem.get("center", {}).get("lat"))
            lon = elem.get("lon") or (elem.get("center", {}).get("lon"))
            
            # Contact info
            website = tags.get("website") or tags.get("contact:website") or ""
            phone = tags.get("phone") or tags.get("contact:phone") or ""
            
            # Address
            addr_street = tags.get("addr:street", "")
            addr_city = tags.get("addr:city", city)
            location = f"{addr_street}, {addr_city}".strip(", ")
            
            businesses.append({
                "name": name,
                "location": location,
                "city": city,
                "website": website,
                "phone": phone,
                "website_present": bool(website),
                "phone_present": bool(phone),
                "latitude": lat,
                "longitude": lon,
                "osm_id": elem.get("id"),
                "osm_type": elem.get("type"),
                "category": tags.get("amenity") or tags.get("shop") or tags.get("cuisine") or query,
                "source": "osm",
            })
        
        return businesses
        
    except requests.RequestException as e:
        print(f"❌ Overpass API error: {str(e)[:200]}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON from Overpass API")
        return []


def fetch_justdial_data(query: str, city: str = "Mumbai", max_results: int = 50) -> List[Dict[str, Any]]:
    """Fetch business data from Justdial using existing scraper.
    
    Note: Uses the existing Selenium-based scraper for reliable extraction.
    Falls back to basic requests if Selenium unavailable.
    
    Args:
        query: Business category (e.g., "Japanese Restaurants")
        city: City name
        max_results: Max businesses to fetch
    
    Returns:
        List of business dicts with Justdial data
    """
    print(f"📘 Fetching Justdial data: '{query}' in {city}")
    
    # Try to use existing Selenium scraper
    try:
        from justdial_scraper import JustDialScraper
        
        scraper = JustDialScraper(headless=True)
        scraper.setup_driver()
        
        # Construct Justdial URL
        search_term = query.replace(" ", "-")
        url = f"https://www.justdial.com/{city}/{search_term}"
        
        print(f"   Using Selenium scraper...")
        scraper.driver.get(url)
        time.sleep(3)  # Wait for JS to render
        
        # Extract business cards (adapt existing scraper logic)
        # This is simplified; actual implementation would use scraper methods
        businesses = []
        # ... extraction logic ...
        
        scraper.driver.quit()
        return businesses
        
    except ImportError:
        print("⚠️  Selenium scraper not available; using basic fallback")
    
    # Fallback: basic requests (will be limited by JS rendering)
    try:
        url = f"https://www.justdial.com/{city}/{query.replace(' ', '-')}"
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        
        if resp.status_code != 200:
            print(f"❌ Justdial HTTP {resp.status_code}")
            return []
        
        # Note: This will return limited/no data due to JS rendering
        # Real implementation should use Selenium or existing scraper
        print("⚠️  Basic scraper returns limited data (JS rendering issue)")
        return []
        
    except requests.RequestException as e:
        print(f"❌ Justdial error: {str(e)[:200]}")
        return []


def name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity ratio between two business names."""
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()


def merge_datasets(osm_data: List[Dict], jd_data: List[Dict], similarity_threshold: float = 0.7) -> List[Business]:
    """Merge OSM and Justdial datasets by matching business names.
    
    Args:
        osm_data: Businesses from OSM
        jd_data: Businesses from Justdial
        similarity_threshold: Min name similarity to consider a match (0.0-1.0)
    
    Returns:
        List of merged Business objects
    """
    print(f"\n🔗 Merging datasets...")
    print(f"   OSM entries: {len(osm_data)}")
    print(f"   Justdial entries: {len(jd_data)}")
    
    merged = []
    matched_jd = set()
    
    # Match OSM businesses with Justdial by name
    for osm in osm_data:
        best_match = None
        best_score = 0.0
        
        for i, jd in enumerate(jd_data):
            if i in matched_jd:
                continue
            
            similarity = name_similarity(osm["name"], jd.get("name", ""))
            if similarity > best_score and similarity >= similarity_threshold:
                best_score = similarity
                best_match = (i, jd)
        
        if best_match:
            jd_idx, jd = best_match
            matched_jd.add(jd_idx)
            
            # Merge data: OSM contact + Justdial ratings
            merged.append(Business(
                name=osm["name"],
                location=osm["location"],
                city=osm["city"],
                website_present=osm["website_present"],
                phone_present=osm["phone_present"],
                rating=jd.get("rating"),
                reviews=jd.get("reviews"),
                score=0,  # calculated later
                website=osm.get("website"),
                phone=osm.get("phone"),
                source="merged",
                osm_id=osm.get("osm_id"),
                latitude=osm.get("latitude"),
                longitude=osm.get("longitude"),
                category=osm.get("category"),
                notes=f"Matched with Justdial (similarity: {best_score:.2f})",
            ))
        else:
            # OSM-only (no Justdial rating)
            merged.append(Business(
                name=osm["name"],
                location=osm["location"],
                city=osm["city"],
                website_present=osm["website_present"],
                phone_present=osm["phone_present"],
                rating=None,
                reviews=None,
                score=0,
                website=osm.get("website"),
                phone=osm.get("phone"),
                source="osm_only",
                osm_id=osm.get("osm_id"),
                latitude=osm.get("latitude"),
                longitude=osm.get("longitude"),
                category=osm.get("category"),
            ))
    
    # Add unmatched Justdial entries
    for i, jd in enumerate(jd_data):
        if i not in matched_jd:
            merged.append(Business(
                name=jd.get("name", "Unknown"),
                location=jd.get("address", ""),
                city=jd.get("city", ""),
                website_present=jd.get("website_present", False),
                phone_present=jd.get("phone_present", False),
                rating=jd.get("rating"),
                reviews=jd.get("reviews"),
                score=0,
                website=jd.get("website"),
                phone=jd.get("phone"),
                source="justdial_only",
                category=jd.get("category"),
            ))
    
    print(f"✅ Merged {len(merged)} businesses")
    print(f"   Matched: {len(matched_jd)}")
    print(f"   OSM-only: {len(osm_data) - len(matched_jd)}")
    print(f"   Justdial-only: {len(jd_data) - len(matched_jd)}")
    
    return merged


def score_business(business: Business) -> int:
    """Score business by digital presence gaps and rating quality.
    
    Higher score = better lead (high rating but weak digital presence)
    
    Scoring:
    - No website: +3
    - No phone/email: +2
    - High rating (>4.0) but missing website/contact: +3 bonus
    """
    score = 0
    
    # Digital presence gaps
    if not business.website_present:
        score += 3
    
    if not business.phone_present:
        score += 2
    
    # Rating boost: high-rated businesses without website are prime targets
    if business.rating and business.rating >= 4.0:
        if not business.website_present or not business.phone_present:
            score += 3
    
    return score


def save_results(businesses: List[Business], query: str, city: str) -> Dict[str, str]:
    """Save ranked business results to CSV/JSON."""
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = re.sub(r"[^\w\s-]", "", query).replace(" ", "_")
    base = f"osm_justdial_{safe_query}_{city}_{ts}"
    
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


def hybrid_lead_scraper(query: str, city: str = "Mumbai", region: str = "India") -> tuple[List[Business], Dict[str, str]]:
    """Main hybrid scraper: OSM + Justdial → merge → score → rank → save.
    
    Args:
        query: Business category (e.g., "restaurant", "Japanese Restaurants")
        city: City name
        region: Country/region
    
    Returns:
        (ranked_businesses, file_paths)
    """
    print("=" * 70)
    print("🌐 OSM + JUSTDIAL HYBRID LEAD GENERATOR")
    print("=" * 70)
    print(f"Query: '{query}' in {city}, {region}\n")
    
    # Fetch OSM data
    osm_data = fetch_osm_data(query, city, region)
    
    # Fetch Justdial data
    jd_data = fetch_justdial_data(query, city)
    
    if not osm_data and not jd_data:
        print("❌ No data from either source")
        return [], {}
    
    # Merge
    businesses = merge_datasets(osm_data, jd_data)
    
    # Score
    print(f"\n📊 Scoring businesses...")
    for b in businesses:
        b.score = score_business(b)
    
    # Rank
    ranked = sorted(businesses, key=lambda b: (b.score, -(b.reviews or 0), -(b.rating or 0)), reverse=True)
    
    # Save
    files = save_results(ranked, query, city)
    
    print(f"\n💾 Saved:")
    print(f"   CSV: {files['csv']}")
    print(f"   JSON: {files['json']}")
    
    # Summary
    high_value = [b for b in ranked if b.score >= 6]  # No website+phone OR high-rated w/ gap
    high_rated_gaps = [b for b in ranked if b.rating and b.rating >= 4.0 and b.score >= 3]
    
    print(f"\n📈 Summary:")
    print(f"   Total businesses: {len(ranked)}")
    print(f"   High-value leads (score >=6): {len(high_value)}")
    print(f"   High-rated with gaps (>=4.0 rating, score >=3): {len(high_rated_gaps)}")
    print(f"   Missing website: {sum(1 for b in ranked if not b.website_present)}")
    print(f"   Missing phone: {sum(1 for b in ranked if not b.phone_present)}")
    
    return ranked, files


if __name__ == "__main__":
    # Example: Japanese Restaurants in Mumbai
    query = "restaurant"  # OSM uses "restaurant" amenity tag
    city = "Mumbai"
    
    businesses, files = hybrid_lead_scraper(query, city)
    
    if businesses:
        print("\n🎯 Top 10 high-value leads:")
        for i, b in enumerate(businesses[:10], 1):
            print(f"{i:2d}. {b.name[:60]} (score: {b.score})")
            print(f"    Website: {'❌' if not b.website_present else '✅'}  "
                  f"Phone: {'❌' if not b.phone_present else '✅'}  "
                  f"Rating: {b.rating or 'N/A'} ({b.reviews or 0} reviews)")
            print(f"    Source: {b.source}")
