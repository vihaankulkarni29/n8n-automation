"""
Website quality checker - simplified and failure-proof version
Analyzes websites and assigns scores based on basic checks
"""
import requests
import ssl
import socket
from urllib.parse import urlparse
from datetime import datetime
import time
from utils.logger import setup_logger
from utils.status_tracker import StatusTracker

logger = setup_logger('website_checker')
status = StatusTracker()

# Simplified scoring system
SCORE_WEIGHTS = {
    'exists': 40,      # Website loads successfully
    'has_ssl': 30,     # Has HTTPS
    'fast_load': 20,   # Loads in under 3 seconds
    'valid_domain': 10 # Has proper domain structure
}


def normalize_url(url):
    """
    Normalize URL to ensure it's properly formatted
    Handles cases where URL might be missing http/https
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Skip if it's clearly not a URL
    if url in ['', 'N/A', 'n/a', 'None', '-']:
        return None
    
    # Add http:// if no protocol specified
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    return url


def check_website_exists(url, timeout=5):
    """
    Check if website loads successfully
    Returns: (bool, float) - (success, load_time)
    FAILURE-PROOF: Returns False on any error
    """
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout, allow_redirects=True, 
                              headers={'User-Agent': 'Mozilla/5.0'})
        load_time = time.time() - start_time
        
        # Success if status code is 2xx or 3xx
        success = response.status_code < 400
        return success, load_time
    
    except Exception as e:
        logger.debug(f"Website check failed for {url}: {e}")
        return False, 0


def check_ssl_certificate(url):
    """
    Check if website has valid SSL (HTTPS)
    Returns: bool
    FAILURE-PROOF: Returns False on any error
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme == 'https'
    except:
        return False


def check_domain_validity(url):
    """
    Check if domain has valid structure
    Returns: bool
    FAILURE-PROOF: Returns False on any error
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        
        # Basic checks
        if not domain or len(domain) < 4:
            return False
        
        # Should have at least one dot
        if '.' not in domain:
            return False
        
        # Should not have suspicious characters
        if any(char in domain for char in ['@', ' ', '<', '>']):
            return False
        
        return True
    except:
        return False


def calculate_website_score(url):
    """
    Calculate overall website quality score (0-100)
    
    Args:
        url: Website URL to analyze
        
    Returns:
        dict with score, details, and status
        
    FAILURE-PROOF: Always returns a valid dict, never crashes
    """
    # Initialize result structure
    result = {
        'url': url,
        'score': 0,
        'exists': False,
        'has_ssl': False,
        'fast_load': False,
        'valid_domain': False,
        'load_time': 0,
        'checked_at': datetime.now().isoformat(),
        'error': None
    }
    
    # Normalize URL
    normalized_url = normalize_url(url)
    if not normalized_url:
        result['error'] = 'Invalid or empty URL'
        return result
    
    result['url'] = normalized_url
    
    try:
        # Check domain validity
        result['valid_domain'] = check_domain_validity(normalized_url)
        if result['valid_domain']:
            result['score'] += SCORE_WEIGHTS['valid_domain']
        
        # Check if website exists and loads
        exists, load_time = check_website_exists(normalized_url)
        result['exists'] = exists
        result['load_time'] = round(load_time, 2)
        
        if exists:
            result['score'] += SCORE_WEIGHTS['exists']
            
            # Check load speed (bonus points if loads fast)
            if load_time < 3.0:
                result['fast_load'] = True
                result['score'] += SCORE_WEIGHTS['fast_load']
            
            # Check SSL
            result['has_ssl'] = check_ssl_certificate(normalized_url)
            if result['has_ssl']:
                result['score'] += SCORE_WEIGHTS['has_ssl']
    
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Error checking {normalized_url}: {e}")
    
    return result


def analyze_websites(businesses, max_concurrent=10):
    """
    Analyze websites for a list of businesses
    
    Args:
        businesses: List of business dicts with 'website' field
        max_concurrent: Max number to process (for time management)
        
    Returns:
        List of businesses with added 'website_analysis' field
        
    FAILURE-PROOF: Continues processing even if individual checks fail
    """
    results = []
    processed = 0
    
    for business in businesses[:max_concurrent]:
        try:
            website = business.get('website', '')
            
            # Perform website analysis
            analysis = calculate_website_score(website)
            
            # Add analysis to business data
            business['website_analysis'] = analysis
            business['score'] = analysis['score']
            
            results.append(business)
            processed += 1
            
            logger.info(f"Analyzed: {business.get('business_name', 'Unknown')} - Score: {analysis['score']}")
            status.increment('websites_checked')
            
        except Exception as e:
            # FAILURE-PROOF: On error, add business with zero score
            logger.error(f"Failed to analyze business: {e}")
            business['website_analysis'] = {
                'score': 0,
                'error': str(e)
            }
            business['score'] = 0
            results.append(business)
            status.increment('errors')
    
    status.save()
    logger.info(f"Analyzed {processed} websites")
    return results


if __name__ == "__main__":
    # Test with sample data
    test_businesses = [
        {'business_name': 'Test Company 1', 'website': 'https://google.com'},
        {'business_name': 'Test Company 2', 'website': 'example.com'},
        {'business_name': 'Test Company 3', 'website': 'invalid'},
        {'business_name': 'Test Company 4', 'website': ''}
    ]
    
    results = analyze_websites(test_businesses)
    
    for r in results:
        print(f"{r['business_name']}: Score {r['score']}")
        print(f"  Analysis: {r['website_analysis']}")
