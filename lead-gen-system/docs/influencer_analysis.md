# Instagram Influencer Brand Analyzer

Analyze Instagram influencer profiles to extract brand mentions from captions, hashtags, and tagged accounts for marketing strategy analysis.

## Features

✅ **Brand Mention Extraction**
- Case-insensitive brand matching with word boundaries
- Searches captions, hashtags, and tagged accounts
- 90+ pre-configured fashion brands (Nike, Adidas, Gucci, Zara, etc.)

✅ **Engagement Metrics**
- Likes and comments per post
- Total and average engagement per brand
- Engagement rate calculations

✅ **Flexible Export**
- CSV, JSON, and Excel formats
- Separate files for posts and brand summaries
- Brand mentions mapping dictionary

✅ **Reusable Functions**
- `get_captions()`: Extract captions from posts
- `extract_brands()`: Find brand mentions in text
- `get_dataframe()`: Convert results to pandas DataFrame
- `get_brand_summary()`: Aggregate brand statistics

## Installation

```bash
pip install instaloader pandas openpyxl
```

## Quick Start

### Basic Usage (No Login)

```python
from influencer_analysis import InstagramBrandAnalyzer

# Analyze public profile
analyzer = InstagramBrandAnalyzer(username='khalidwalb')
analyzer.load_profile()
analyzer.analyze_posts(max_posts=50)

# View results
analyzer.print_summary()

# Export to CSV
analyzer.export_results('khalidwalb_analysis', format='csv')
```

### With Custom Brands

```python
# Define custom brand list
fashion_brands = [
    'Nike', 'Adidas', 'Gucci', 'Zara', 'Louis Vuitton',
    'Supreme', 'Off-White', 'Yeezy', 'Jordan'
]

analyzer = InstagramBrandAnalyzer(
    username='khalidwalb',
    brands=fashion_brands
)

analyzer.load_profile()
analyzer.analyze_posts(max_posts=100)
analyzer.export_results('khalidwalb_custom', format='excel')
```

### Quick Analysis Function

```python
from influencer_analysis.instagram_analyzer import analyze_influencer

# One-liner analysis
analyzer = analyze_influencer(
    username='khalidwalb',
    max_posts=50,
    output_format='csv'
)
```

## Authentication (For Private Profiles)

```python
analyzer = InstagramBrandAnalyzer(username='private_account')

# Option 1: Login with credentials
analyzer.login('your_username', 'your_password')

# Option 2: Load saved session
analyzer.load_session('session_file')

# Then proceed with analysis
analyzer.load_profile()
analyzer.analyze_posts()
```

## Output Files

### Posts Data (`username_posts.csv`)
Contains detailed information for each post:

| Column | Description |
|--------|-------------|
| shortcode | Post ID |
| url | Direct link to post |
| date | Post timestamp |
| caption | Post caption (truncated to 200 chars) |
| hashtags | Comma-separated hashtags |
| tagged_users | Comma-separated tagged accounts |
| brands_mentioned | Brands found in this post |
| brands_count | Number of brands mentioned |
| likes | Like count |
| comments | Comment count |
| engagement | Total engagement (likes + comments) |
| engagement_rate | Engagement rate % |

### Brand Summary (`username_brands.csv`)
Aggregated brand statistics:

| Column | Description |
|--------|-------------|
| brand | Brand name |
| mentions | Number of posts mentioning brand |
| post_shortcodes | Comma-separated post IDs |
| total_likes | Sum of likes for brand posts |
| total_comments | Sum of comments for brand posts |
| total_engagement | Total engagement for brand |
| avg_engagement_per_post | Average engagement per mention |

### Brand Mentions Map (`username_brand_mentions.json`)
Dictionary format for programmatic access:

```json
{
  "Nike": ["CXXxxx", "CYYyyy"],
  "Adidas": ["CZZzzz"],
  "Gucci": ["CAAbbb", "CBBccc", "CCCddd"]
}
```

## API Reference

### Class: `InstagramBrandAnalyzer`

#### `__init__(username, brands=None, session_file=None)`
Initialize analyzer with username and optional custom brand list.

#### `load_profile()`
Load the Instagram profile metadata.

#### `analyze_posts(max_posts=50, include_engagement=True)`
Analyze posts to extract brand mentions and metrics.

#### `get_captions(max_posts=50) -> List[Tuple[str, str]]`
Extract captions from posts. Returns list of (shortcode, caption) tuples.

#### `extract_brands(text) -> Set[str]`
Extract brand mentions from text using case-insensitive matching.

#### `get_dataframe() -> pd.DataFrame`
Convert analysis results to pandas DataFrame.

#### `get_brand_summary() -> pd.DataFrame`
Get aggregated brand statistics DataFrame.

#### `export_results(output_file, format='csv', include_brand_summary=True)`
Export results to file. Formats: 'csv', 'json', 'excel'.

#### `print_summary()`
Print formatted summary to console.

## Pre-configured Brands (90+)

The analyzer includes 90+ fashion and lifestyle brands:

**Luxury**: Gucci, Louis Vuitton, Chanel, Dior, Prada, Versace, Balenciaga, Hermès, Fendi, Givenchy, Valentino, YSL, Bottega Veneta, Celine, Burberry, Armani, Dolce & Gabbana

**Streetwear**: Supreme, Off-White, Yeezy, Fear of God, Stone Island

**Sportswear**: Nike, Adidas, Puma, Reebok, Under Armour, Vans, Converse, Jordan, New Balance, Asics, Lululemon, Gymshark, Fabletics

**Fast Fashion**: Zara, H&M, Forever 21, Uniqlo, Gap, Asos, Boohoo, Fashion Nova, Shein

**Casual**: Levi's, Calvin Klein, Tommy Hilfiger, Ralph Lauren, Polo, Lacoste, Boss, Diesel

**Outdoor**: The North Face, Patagonia, Columbia, Arc'teryx, Canada Goose, Timberland

**And many more...**

## Example: Complete Analysis Workflow

```python
from influencer_analysis import InstagramBrandAnalyzer
import pandas as pd

# 1. Initialize analyzer
analyzer = InstagramBrandAnalyzer(username='khalidwalb')

# 2. Load profile
analyzer.load_profile()

# 3. Analyze posts
analyzer.analyze_posts(max_posts=50, include_engagement=True)

# 4. Get DataFrames
posts_df = analyzer.get_dataframe()
brands_df = analyzer.get_brand_summary()

# 5. Custom analysis
print(f"Total posts: {len(posts_df)}")
print(f"Brands found: {len(brands_df)}")
print(f"\nTop 5 brands:")
print(brands_df.head(5)[['brand', 'mentions', 'total_engagement']])

# 6. Filter posts with high engagement
high_engagement = posts_df[posts_df['engagement'] > posts_df['engagement'].median()]
print(f"\nHigh engagement posts: {len(high_engagement)}")

# 7. Export results
analyzer.export_results('khalidwalb_full_analysis', format='excel')
analyzer.print_summary()
```

## Example: Custom Brand Categories

```python
# Create brand categories
tech_brands = ['Apple', 'Samsung', 'Google', 'Microsoft', 'Tesla']
food_brands = ['Starbucks', 'McDonald\'s', 'KFC', 'Subway', 'Dominos']
all_brands = tech_brands + food_brands

# Analyze with custom brands
analyzer = InstagramBrandAnalyzer(
    username='tech_influencer',
    brands=all_brands
)

analyzer.load_profile()
analyzer.analyze_posts(max_posts=100)

# Separate analysis by category
df = analyzer.get_dataframe()
tech_posts = df[df['brands_mentioned'].str.contains('|'.join(tech_brands), na=False)]
food_posts = df[df['brands_mentioned'].str.contains('|'.join(food_brands), na=False)]

print(f"Tech brand mentions: {len(tech_posts)}")
print(f"Food brand mentions: {len(food_posts)}")
```

## Error Handling

The analyzer includes robust error handling:

- **Missing captions**: Returns empty string, continues analysis
- **Missing engagement data**: Returns 0, continues analysis
- **Tagged users errors**: Catches exceptions, returns empty list
- **Profile loading errors**: Raises exception with helpful message
- **Authentication errors**: Clear error messages for login failures

## Rate Limiting & Best Practices

1. **Start with small batches**: Test with 10-20 posts first
2. **Use saved sessions**: Avoid repeated logins
3. **Add delays**: Instagram may rate-limit aggressive scraping
4. **Public profiles**: Work best without authentication
5. **Private profiles**: Require login with follower access

## Troubleshooting

### "Profile not loaded" error
```python
# Always call load_profile() before analyze_posts()
analyzer.load_profile()
analyzer.analyze_posts()
```

### "Login required" for public profile
```python
# Instagram may require login for some profiles
# Use a temporary account
analyzer.login('temp_username', 'temp_password')
```

### No brands found
```python
# Check if brands are spelled correctly
# Try with lowercase search
brands = analyzer.extract_brands("nike shoes are great")
print(brands)  # Should find 'Nike'
```

## Command-Line Usage

```bash
# Run from command line
cd lead-gen-system
python -m influencer_analysis.instagram_analyzer
```

This will analyze `khalidwalb` profile and export results to `data/` folder.

## Integration with Lead Generation System

The analyzer can be integrated into the existing lead generation pipeline:

```python
# Add to main pipeline
from influencer_analysis import InstagramBrandAnalyzer

# Analyze influencer for brand partnerships
analyzer = InstagramBrandAnalyzer(username='fashion_influencer')
analyzer.load_profile()
analyzer.analyze_posts()

# Get brands they mention most
brand_df = analyzer.get_brand_summary()
top_brands = brand_df.head(5)['brand'].tolist()

# Use for targeted outreach
print(f"This influencer frequently mentions: {', '.join(top_brands)}")
```

## Performance

- **50 posts**: ~30-60 seconds
- **100 posts**: ~1-2 minutes
- **500 posts**: ~5-10 minutes

Performance depends on network speed and Instagram's response time.

## Future Enhancements

- [ ] Story analysis
- [ ] Reel/video caption extraction
- [ ] Sentiment analysis on brand mentions
- [ ] Competitor comparison
- [ ] Time-series trend analysis
- [ ] Geographic location tracking
- [ ] Collaboration detection (sponsored posts)

## License

Part of the Lead Generation System. See main project LICENSE.

## Support

For issues or questions, refer to the main project documentation or create an issue in the repository.
