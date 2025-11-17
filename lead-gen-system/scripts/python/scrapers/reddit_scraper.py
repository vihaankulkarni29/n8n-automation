"""
Reddit JSON API Scraper for r/indianstartups

Fetches posts via Reddit's public JSON endpoints (no auth required),
computes engagement scores, and saves ranked results.
"""

import time
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple

import requests

REDDIT_BASE = "https://www.reddit.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class RedditPost:
    title: str
    reddit_url: str
    external_url: str
    external_domain: str
    author: str
    upvotes: int
    comments: int
    score: int
    created_utc: int
    created_iso: str
    flair: str
    selftext: str


def fetch_posts(subreddit: str, sort: str = "hot", limit: int = 100, delay: float = 1.0) -> List[Dict[str, Any]]:
    """Fetch posts from subreddit using Reddit JSON API.

    Args:
        subreddit: Subreddit name (without r/)
        sort: 'hot' | 'new' | 'top'
        limit: Max posts to fetch (Reddit caps at 100 per request)
        delay: Delay between retries/requests (seconds)

    Returns:
        List of raw post dicts (data children)
    """
    sort = sort.lower()
    assert sort in {"hot", "new", "top"}

    url = f"{REDDIT_BASE}/r/{subreddit}/{sort}.json"
    params = {"limit": min(limit, 100)}
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code != 200:
            # Basic retry once with small backoff for transient errors
            time.sleep(delay)
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code} for {url}")
        data = resp.json()
        children = data.get("data", {}).get("children", [])
        return [c.get("data", {}) for c in children if isinstance(c, dict)]
    except requests.RequestException as e:
        raise RuntimeError(f"Network error: {str(e)[:200]}")
    except json.JSONDecodeError:
        raise RuntimeError("Invalid JSON response from Reddit")


def extract_metadata(raw: Dict[str, Any]) -> RedditPost:
    """Extract required fields and compute engagement score for a single post."""
    title = raw.get("title", "").strip()
    permalink = raw.get("permalink", "") or ""
    reddit_url = f"{REDDIT_BASE}{permalink}" if permalink else raw.get("url", "")
    external_url = raw.get("url_overridden_by_dest") or raw.get("url", "")
    # derive domain for external links
    external_domain = ""
    try:
        from urllib.parse import urlparse
        if external_url:
            external_domain = urlparse(external_url).netloc
    except Exception:
        external_domain = ""
    author = raw.get("author", "")
    upvotes = int(raw.get("score", 0) or 0)
    comments = int(raw.get("num_comments", 0) or 0)
    created_utc = int(raw.get("created_utc", 0) or 0)
    created_iso = (
        datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        if created_utc
        else ""
    )
    flair = raw.get("link_flair_text") or ""
    selftext = (raw.get("selftext") or "").strip()

    engagement_score = upvotes + (2 * comments)

    return RedditPost(
        title=title,
        reddit_url=reddit_url,
        external_url=external_url,
        external_domain=external_domain,
        author=author,
        upvotes=upvotes,
        comments=comments,
        score=engagement_score,
        created_utc=created_utc,
        created_iso=created_iso,
        flair=flair,
        selftext=selftext,
    )


def rank_posts(posts: List[RedditPost]) -> List[RedditPost]:
    """Rank posts by engagement score (descending)."""
    return sorted(posts, key=lambda p: p.score, reverse=True)

BRANDING_KEYWORDS = [
    # branding/marketing needs
    "branding", "brand", "logo", "name", "naming", "identity", "story",
    "website", "landing page", "lp", "copy", "copywriting", "content",
    "marketing", "growth", "seo", "ads", "google ads", "meta ads",
    "facebook ads", "instagram ads", "performance marketing", "campaign",
    "design", "ui", "ux", "rebrand", "revamp", "feedback", "critique",
]

LAUNCH_KEYWORDS = [
    "launched", "launch", "built", "building", "mvp", "side project",
    "showcase", "demo", "beta", "early access", "need feedback",
]

BRANDING_FLAIRS = {
    "startup showcase", "startup help", "how to grow?", "feedback",
    "business ride along", "product", "marketing",
}

def classify_branding_need(p: RedditPost) -> Tuple[int, List[str]]:
    """Heuristically score how likely the post needs branding/marketing help.

    Returns (branding_need_score, reasons)
    """
    score = 0
    reasons: List[str] = []

    text = f"{p.title} \n {p.selftext}".lower()
    flair = (p.flair or "").lower()

    # Flair signals
    if flair in BRANDING_FLAIRS:
        score += 2
        reasons.append(f"Flair suggests need: {p.flair}")

    # Keyword signals
    if any(k in text for k in BRANDING_KEYWORDS):
        score += 2
        reasons.append("Mentions branding/marketing keywords")

    if any(k in text for k in LAUNCH_KEYWORDS):
        score += 1
        reasons.append("Launch/feedback intent")

    # External link signals
    domain = (p.external_domain or "").lower()
    if domain.endswith("myshopify.com"):
        score += 2
        reasons.append("Using myshopify.com (needs custom domain)")
    if domain and (domain.endswith("linktr.ee") or domain.endswith("bio.link")):
        score += 1
        reasons.append("Using link aggregator instead of site")

    # Engagement gate (interest exists)
    if p.score >= 30 or p.comments >= 10:
        score += 1
        reasons.append("Community engagement present")

    return score, reasons

def filter_branding_leads(posts: List[RedditPost], min_need: int = 3, min_score: int = 20) -> List[Dict[str, Any]]:
    """Filter posts to those likely needing branding/marketing help.

    min_need: minimum branding_need_score from classifier
    min_score: minimum engagement score to ensure relevance
    Returns list of dicts with extra fields: branding_need_score, reasons
    """
    results: List[Dict[str, Any]] = []
    for p in posts:
        need, reasons = classify_branding_need(p)
        if need >= min_need and p.score >= min_score:
            row = asdict(p)
            row["branding_need_score"] = need
            row["branding_reasons"] = reasons
            results.append(row)
    # sort by need then engagement
    results.sort(key=lambda r: (r["branding_need_score"], r["score"]), reverse=True)
    return results


def save_results(posts: List[RedditPost], output_dir: Path | None = None, base_name: str | None = None) -> Dict[str, str]:
    """Save results to CSV and JSON.

    Returns:
        Dict with file paths for 'csv' and 'json'
    """
    if output_dir is None:
        output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = base_name or "reddit_indianstartups"
    csv_path = output_dir / f"{base}_{ts}.csv"
    json_path = output_dir / f"{base}_{ts}.json"

    # Convert to dicts
    rows = [asdict(p) for p in posts]

    # Write CSV
    import pandas as pd

    df = pd.DataFrame(rows, columns=[
        "title",
        "reddit_url",
        "external_url",
        "external_domain",
        "author",
        "upvotes",
        "comments",
        "score",
        "flair",
        "selftext",
        "created_iso",
        "created_utc",
    ])
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    return {"csv": str(csv_path), "json": str(json_path)}


def fetch_rank_save(
    subreddit: str = "indianstartups", sort: str = "hot", limit: int = 100
) -> Tuple[List[RedditPost], Dict[str, str]]:
    """Convenience: fetch posts, rank, and save outputs."""
    raw_posts = fetch_posts(subreddit=subreddit, sort=sort, limit=limit)

    # Filter out stickied/mod posts
    filtered = [p for p in raw_posts if not p.get("stickied")]

    posts = [extract_metadata(p) for p in filtered]
    ranked = rank_posts(posts)
    files = save_results(ranked)
    return ranked, files

def fetch_branding_leads(
    subreddit: str = "indianstartups",
    sort: str = "hot",
    limit: int = 100,
    min_need: int = 3,
    min_score: int = 20,
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Fetch posts, classify branding need, filter, and save to files."""
    raw_posts = fetch_posts(subreddit=subreddit, sort=sort, limit=limit)
    filtered = [p for p in raw_posts if not p.get("stickied")]
    posts = [extract_metadata(p) for p in filtered]
    ranked = rank_posts(posts)
    branding_rows = filter_branding_leads(ranked, min_need=min_need, min_score=min_score)

    # Save branding-focused outputs
    from pandas import DataFrame
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"reddit_indianstartups_branding_{ts}"

    # CSV
    csv_path = output_dir / f"{base}.csv"
    DataFrame(branding_rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
    # JSON
    json_path = output_dir / f"{base}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(branding_rows, f, ensure_ascii=False, indent=2)

    return branding_rows, {"csv": str(csv_path), "json": str(json_path)}


if __name__ == "__main__":
    posts, files = fetch_rank_save()
    print(f"Saved {len(posts)} posts")
    print(files)
