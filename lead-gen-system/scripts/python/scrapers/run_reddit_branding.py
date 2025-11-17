import argparse
from pprint import pprint

from reddit_scraper import fetch_branding_leads


def main():
    parser = argparse.ArgumentParser(description="Fetch branding/marketing leads from r/indianstartups")
    parser.add_argument("--subreddit", default="indianstartups", help="Subreddit to fetch from")
    parser.add_argument("--sort", default="hot", choices=["hot", "new", "top"], help="Sort order")
    parser.add_argument("--limit", type=int, default=100, help="Max posts to fetch (<=100)")
    parser.add_argument("--min-need", type=int, default=3, help="Min branding need score")
    parser.add_argument("--min-score", type=int, default=20, help="Min engagement score")

    args = parser.parse_args()

    rows, files = fetch_branding_leads(
        subreddit=args.subreddit,
        sort=args.sort,
        limit=args.limit,
        min_need=args.min_need,
        min_score=args.min_score,
    )

    print(f"\n✅ Saved {len(rows)} branding-focused posts")
    print(f"CSV: {files['csv']}\nJSON: {files['json']}")

    preview = rows[:10]
    if preview:
        print("\nTop results:")
        for i, r in enumerate(preview, 1):
            title = (r.get("title") or "").strip()
            flair = r.get("flair") or ""
            score = r.get("score")
            need = r.get("branding_need_score")
            reasons = ", ".join(r.get("branding_reasons") or [])
            print(f"{i:2d}. [{flair}] score={score} need={need} - {title}")
            if reasons:
                print(f"    reasons: {reasons}")
    else:
        print("No posts matched filters. Try lowering --min-need or --min-score.")


if __name__ == "__main__":
    main()
