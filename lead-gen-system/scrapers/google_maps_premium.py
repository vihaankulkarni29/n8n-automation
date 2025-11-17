"""
Google Maps Scraper using Outscraper API
Premium data source - verified businesses with high email/website coverage
"""
import os
import json
import csv
from datetime import datetime
from outscraper import ApiClient
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GoogleMapsScraper:
    """Scrape businesses from Google Maps using Outscraper API"""
    
    def __init__(self, api_key=None):
        # Get API key from environment or parameter
        self.api_key = api_key or os.getenv('OUTSCRAPER_API_KEY')
        if not self.api_key:
            raise ValueError("OUTSCRAPER_API_KEY not found. Get one from outscraper.com")
        
        self.client = ApiClient(api_key=self.api_key)
        self.businesses = []
        
    def scrape_category(self, query, limit=100):
        """
        Scrape businesses from Google Maps
        
        Args:
            query: Search query (e.g., "Digital marketing agency in Mumbai")
            limit: Number of results to fetch
        """
        logger.info(f"Scraping Google Maps for: {query}")
        print(f"\n🔍 Searching Google Maps: {query}")
        print(f"Target: {limit} businesses")
        print("="*70)
        
        try:
            # Outscraper API call
            results = self.client.google_maps_search(
                query=query,
                limit=limit,
                language='en',
                region='IN'
            )
            
            for place_data in results:
                for place in place_data:
                    business = self.parse_place_data(place)
                    if business:
                        self.businesses.append(business)
                        logger.info(f"✓ {business['business_name']}")
                        
                        # Print summary
                        print(f"\n📍 {business['business_name']}")
                        print(f"   📞 {business['phone'] or 'No phone'}")
                        print(f"   🌐 {business['website'] or 'No website'}")
                        print(f"   ⭐ {business['rating']} ({business['reviews']} reviews)")
            
            logger.info(f"Scraped {len(self.businesses)} businesses")
            print(f"\n✅ Total collected: {len(self.businesses)} businesses")
            
        except Exception as e:
            logger.error(f"Error scraping Google Maps: {e}")
            print(f"\n❌ Error: {e}")
            print("\nNote: You need an Outscraper API key. Get one at:")
            print("https://outscraper.com/pricing/")
            print("Cost: ~$1 per 1000 results (worth it for quality data!)")
    
    def parse_place_data(self, place):
        """Parse Google Maps place data into business dict"""
        try:
            # Extract address components
            address = place.get('full_address') or place.get('address', '')
            
            # Get website and clean it
            website = place.get('site') or place.get('website')
            
            # Get phone number
            phone = place.get('phone')
            if phone:
                # Clean phone number
                phone = phone.replace('+91', '').replace('-', '').replace(' ', '').strip()
            
            # Get rating and reviews
            rating = place.get('rating')
            reviews = place.get('reviews') or place.get('reviews_count') or 0
            
            # Get business hours
            hours = place.get('working_hours')
            if isinstance(hours, dict):
                hours = str(hours)
            
            business = {
                'business_name': place.get('name'),
                'address': address,
                'phone': phone,
                'email': None,  # Will try to find
                'website': website,
                'rating': rating,
                'reviews': reviews,
                'category': place.get('type') or place.get('category'),
                'google_maps_url': place.get('google_url') or place.get('url'),
                'latitude': place.get('latitude'),
                'longitude': place.get('longitude'),
                'place_id': place.get('place_id'),
                'business_status': place.get('business_status'),
                'price_level': place.get('price_level'),
                'working_hours': hours,
                'popular_times': str(place.get('popular_times')) if place.get('popular_times') else None,
                'verified': place.get('verified', False),
            }
            
            # Try to extract email from website or description
            description = place.get('description', '')
            if description:
                import re
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', description)
                if email_match:
                    business['email'] = email_match.group(0)
            
            return business
            
        except Exception as e:
            logger.error(f"Error parsing place data: {e}")
            return None
    
    def save_to_csv(self, filename='google_maps_businesses.csv'):
        """Save businesses to CSV"""
        if not self.businesses:
            logger.warning("No businesses to save")
            return None
        
        filepath = os.path.join('data', filename)
        
        fieldnames = [
            'business_name', 'address', 'phone', 'email', 'website',
            'rating', 'reviews', 'category', 'google_maps_url',
            'latitude', 'longitude', 'place_id', 'business_status',
            'price_level', 'working_hours', 'verified'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.businesses)
        
        logger.info(f"Saved {len(self.businesses)} businesses to {filepath}")
        print(f"\n💾 Saved to: {filepath}")
        return filepath
    
    def save_to_json(self, filename='google_maps_businesses.json'):
        """Save businesses to JSON"""
        if not self.businesses:
            return None
        
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.businesses, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.businesses)} businesses to {filepath}")
        print(f"💾 Saved to: {filepath}")
        return filepath
    
    def get_statistics(self):
        """Get statistics about scraped data"""
        if not self.businesses:
            return {}
        
        total = len(self.businesses)
        with_phone = sum(1 for b in self.businesses if b.get('phone'))
        with_email = sum(1 for b in self.businesses if b.get('email'))
        with_website = sum(1 for b in self.businesses if b.get('website'))
        verified = sum(1 for b in self.businesses if b.get('verified'))
        avg_rating = sum(b.get('rating', 0) or 0 for b in self.businesses) / total
        
        stats = {
            'total_businesses': total,
            'with_phone': with_phone,
            'with_email': with_email,
            'with_website': with_website,
            'verified': verified,
            'average_rating': round(avg_rating, 2),
            'phone_coverage': f"{with_phone/total*100:.1f}%",
            'email_coverage': f"{with_email/total*100:.1f}%",
            'website_coverage': f"{with_website/total*100:.1f}%",
        }
        
        return stats


def main():
    """Main execution"""
    print("🚀 Google Maps Premium Scraper")
    print("="*70)
    print("\n⚠️  SETUP REQUIRED:")
    print("1. Get API key from: https://outscraper.com")
    print("2. Add to .env file: OUTSCRAPER_API_KEY=your_key_here")
    print("3. Cost: ~$1 per 1000 results (5000 free credits on signup!)")
    print("\n" + "="*70 + "\n")
    
    # Check for API key
    api_key = os.getenv('OUTSCRAPER_API_KEY')
    if not api_key:
        print("❌ OUTSCRAPER_API_KEY not found in .env file")
        print("\nTo get started:")
        print("1. Sign up at https://outscraper.com")
        print("2. Get your API key from dashboard")
        print("3. Add to .env: OUTSCRAPER_API_KEY=your_key_here")
        return
    
    try:
        scraper = GoogleMapsScraper(api_key=api_key)
        
        # Define search queries
        queries = [
            "Digital marketing agency in Mumbai",
            "Web design company in Bangalore",
            "Fashion boutique in Delhi",
        ]
        
        # Scrape each query
        for query in queries:
            scraper.scrape_category(query, limit=50)
        
        # Save results
        if scraper.businesses:
            scraper.save_to_csv('google_maps_premium.csv')
            scraper.save_to_json('google_maps_premium.json')
            
            # Print statistics
            stats = scraper.get_statistics()
            print("\n" + "="*70)
            print("📊 DATA QUALITY STATISTICS")
            print("="*70)
            print(f"Total Businesses: {stats['total_businesses']}")
            print(f"Phone Coverage: {stats['phone_coverage']}")
            print(f"Email Coverage: {stats['email_coverage']}")
            print(f"Website Coverage: {stats['website_coverage']}")
            print(f"Verified Businesses: {stats['verified']}")
            print(f"Average Rating: {stats['average_rating']}")
            print("="*70)
            
    except ValueError as e:
        print(f"\n❌ {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
