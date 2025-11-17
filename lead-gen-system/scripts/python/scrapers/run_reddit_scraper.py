"""
Runner for Reddit JSON API scraper (r/indianstartups)
"""

import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scrapers.reddit_scraper import fetch_rank_save


def main():
    print("\n" + "="*80)
    print("REDDIT r/indianstartups - HOT POSTS")
    print("="*80)

    try:
        posts, files = fetch_rank_save(subreddit="indianstartups", sort="hot", limit=100)
        print(f"\n✅ Saved {len(posts)} ranked posts")
        print(f"CSV:  {files.get('csv')}")
        print(f"JSON: {files.get('json')}")

        # Show top 10 summary
        print("\nTOP 10 BY ENGAGEMENT:")
        for i, p in enumerate(posts[:10], start=1):
            print(f"{i:2d}. [{p.score}] {p.title}")
            print(f"    ↑{p.upvotes}  💬{p.comments}  Flair: {p.flair or '-'}")
            print(f"    {p.reddit_url}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Tip: If Reddit rate-limits, wait a minute and retry.")


if __name__ == "__main__":
    main()
