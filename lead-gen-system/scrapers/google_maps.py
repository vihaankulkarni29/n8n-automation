"""
Outscraper API-based Google Maps business scraper
Collects business listings using Outscraper's free API
"""
import requests
import time
from utils.logger import setup_logger
from utils.status_tracker import StatusTracker
from utils.config import config

logger = setup_logger('scraper')
status = StatusTracker()

OUTSCRAPER_API_KEY = 'N2ViZWJkY2ZhNWIwNDAyMTg4ZDRjOTM4ZjU2NTZlZGV8MjFjMDVlYjAwZQ'
OUTSCRAPER_ENDPOINT = 'https://api.outscraper.com/maps/search'


def search_outscraper(query, location, limit=100):
    """
    Search businesses using Outscraper API
    Args:
        query: Business type or keyword
        location: City or region
        limit: Max results
    Returns:
        List of business dicts
    """
    params = {
        'query': f'{query} in {location}',
        'limit': limit,
        'async': False
    }
    headers = {
        'X-API-KEY': OUTSCRAPER_API_KEY
    }
    logger.info(f"Searching Outscraper: {params['query']}")
    try:
        response = requests.get(OUTSCRAPER_ENDPOINT, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Extract businesses
        results = data.get('data', [])
        logger.info(f"Found {len(results)} businesses for {params['query']}")
        status.increment('businesses_scraped', len(results))
        status.save()
        return results
    except Exception as e:
        logger.error(f"Outscraper API error: {e}")
        status.increment('errors')
        status.save()
        return []


def save_results(results, filename):
    """Save results to JSON file"""
    import json
    import os
    os.makedirs('data', exist_ok=True)
    with open(f'data/{filename}', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(results)} results to data/{filename}")


if __name__ == "__main__":
    # Example usage
    queries = [
        ("web design agency", "Mumbai"),
        ("digital marketing services", "Delhi"),
        ("software development company", "Bangalore"),
    ]
    all_results = []
    for query, location in queries:
        results = search_outscraper(query, location, limit=100)
        save_results(results, f"{query.replace(' ', '_')}_{location}.json")
        all_results.extend(results)
        time.sleep(2)  # Rate limit
    logger.info(f"Total businesses scraped: {len(all_results)}")
    status.update(businesses_scraped=len(all_results))
    status.save()
