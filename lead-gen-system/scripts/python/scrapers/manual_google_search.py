"""
Manual Google Search scraper for business leads
Uses requests and BeautifulSoup to extract business info from Google Search results
"""
import requests
from bs4 import BeautifulSoup
import time
import json
from utils.logger import setup_logger
from utils.status_tracker import StatusTracker

logger = setup_logger('manual_scraper')
status = StatusTracker()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

import random
from urllib.parse import quote

SEARCH_QUERIES = [
    "up and coming restaurants Mumbai",
    "food companies Delhi",
    "fashion companies Bangalore"
]

RESULTS_PER_QUERY = 10  # Lower to avoid blocks


def scrape_google_search(query, num_results=RESULTS_PER_QUERY):
    """
    Scrape Google Search for business info
    Args:
        query: Search string
        num_results: Number of results to collect
    Returns:
        List of dicts: business_name, website, snippet
    """
    results = []
    start = 0
    while len(results) < num_results:
        url = f"https://www.google.com/search?q={quote(query)}&start={start}"
        logger.info(f"Scraping: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(resp.text, "html.parser")
            for g in soup.select('div.g'):
                name = g.select_one('h3')
                link = g.select_one('a')
                snippet = g.select_one('.VwiC3b')
                if name and link:
                    results.append({
                        'business_name': name.text.strip(),
                        'website': link['href'],
                        'snippet': snippet.text.strip() if snippet else ''
                    })
                if len(results) >= num_results:
                    break
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            break  # Stop on repeated failure
        start += 10
        delay = random.uniform(2, 5)
        logger.info(f"Sleeping for {delay:.1f} seconds to avoid blocks...")
        time.sleep(delay)
    logger.info(f"Collected {len(results)} results for '{query}'")
    status.increment('businesses_scraped', len(results))
    status.save()
    return results


def save_results(results, filename):
    with open(f'data/{filename}', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(results)} results to data/{filename}")


if __name__ == "__main__":
    all_results = []
    for query in SEARCH_QUERIES:
        results = scrape_google_search(query)
        save_results(results, f"{query.replace(' ', '_')}.json")
        all_results.extend(results)
    logger.info(f"Total businesses scraped: {len(all_results)}")
    status.update(businesses_scraped=len(all_results))
    status.save()
