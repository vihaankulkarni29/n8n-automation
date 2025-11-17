"""
Unified Local Business Scraper Runner

Runs Justdial and Zomato scrapers with configurable queries
and combines results for lead generation.
"""

import argparse
from pathlib import Path

# Import scrapers
from local_business_scraper import scrape_local_businesses
from zomato_scraper import scrape_zomato


def main():
    parser = argparse.ArgumentParser(description="Local business scraper for lead generation")
    parser.add_argument("--source", choices=["justdial", "zomato", "both"], default="both",
                        help="Data source to scrape")
    parser.add_argument("--query", default="cafes near Borivali",
                        help="Search query")
    parser.add_argument("--city", default="Mumbai",
                        help="City name")
    parser.add_argument("--max-pages", type=int, default=2,
                        help="Max pages for Justdial")
    parser.add_argument("--max-results", type=int, default=30,
                        help="Max results for Zomato")
    
    args = parser.parse_args()
    
    all_results = []
    
    print("=" * 70)
    print("🏪 LOCAL BUSINESS LEAD SCRAPER")
    print("=" * 70)
    
    # Run Justdial
    if args.source in ["justdial", "both"]:
        print("\n" + "─" * 70)
        print("📘 JUSTDIAL")
        print("─" * 70)
        try:
            businesses, files = scrape_local_businesses(
                query=args.query,
                city=args.city,
                source="justdial",
                max_pages=args.max_pages
            )
            all_results.extend(businesses)
            
            if businesses:
                print(f"\n🎯 Top 5 Justdial leads:")
                for i, b in enumerate(businesses[:5], 1):
                    print(f"{i}. {b.name[:60]}")
                    print(f"   Score: {b.score} | Website: {'❌' if not b.website_present else '✅'} | Phone: {'❌' if not b.phone_present else '✅'}")
        except Exception as e:
            print(f"❌ Justdial error: {str(e)[:200]}")
    
    # Run Zomato
    if args.source in ["zomato", "both"]:
        print("\n" + "─" * 70)
        print("🍽️  ZOMATO")
        print("─" * 70)
        try:
            restaurants, files = scrape_zomato(
                query=args.query,
                city=args.city,
                max_results=args.max_results
            )
            # Convert Restaurant to Business-like for consistency
            for r in restaurants:
                all_results.append(r)
            
            if restaurants:
                print(f"\n🎯 Top 5 Zomato leads:")
                for i, r in enumerate(restaurants[:5], 1):
                    print(f"{i}. {r.name[:60]}")
                    print(f"   Score: {r.score} | Website: {'❌' if not r.website_present else '✅'} | Phone: {'❌' if not r.phone_present else '✅'}")
                    if r.rating:
                        print(f"   Rating: {r.rating}/5")
        except Exception as e:
            print(f"❌ Zomato error: {str(e)[:200]}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 OVERALL SUMMARY")
    print("=" * 70)
    if all_results:
        high_score = [r for r in all_results if r.score >= 3]
        print(f"Total businesses scraped: {len(all_results)}")
        print(f"High-priority leads (score >=3): {len(high_score)}")
        print(f"Missing website: {sum(1 for r in all_results if not r.website_present)}")
        print(f"Missing phone: {sum(1 for r in all_results if not r.phone_present)}")
        
        # Top overall
        sorted_all = sorted(all_results, key=lambda r: (r.score, -(getattr(r, 'reviews', 0) or 0)), reverse=True)
        print(f"\n🏆 Top 3 overall leads:")
        for i, r in enumerate(sorted_all[:3], 1):
            print(f"{i}. {r.name[:60]} (score: {r.score})")
    else:
        print("No results collected. Try adjusting query or source.")
    
    print("\n" + "=" * 70)
    print("✅ Scraping complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
