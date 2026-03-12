# Adobe Stock Scraper

A comprehensive Selenium-based scraper for Adobe Stock that extracts all product data and exports to CSV/JSON.

## Features

- **Full data extraction**: Asset ID, title, contributor, type, dimensions, keywords, and more
- **Pagination support**: Scrape hundreds or thousands of results
- **Keyword scraping**: Optionally scrape individual asset pages for keywords
- **Anti-detection**: Rotating user agents, random delays, human-like behavior
- **Multiple export formats**: CSV and JSON
- **Batch scraping**: Process multiple queries at once
- **Filters**: Content type, orientation, and more

## Installation

```bash
cd scraper
pip install -r requirements.txt
```

## Usage

### Interactive Mode

```bash
python run_scraper.py
```

This will prompt you for:
- Search query
- Maximum results
- Whether to scrape keywords
- Headless mode
- Filters

### Command Line

```bash
# Basic search
python adobe_stock_scraper.py "minimalist home office" -n 500

# With full details (keywords, dimensions, preview URL, category, similar asset IDs)
python adobe_stock_scraper.py "remote work" -n 200 --details

# With similar assets scraped too (their keywords, creators)
python adobe_stock_scraper.py "fruit" -n 10 --details --similar --max-similar 5

# Headless mode
python adobe_stock_scraper.py "business team" -n 100 --headless

# Filter by content type
python adobe_stock_scraper.py "nature landscape" -n 300 --content-type photo vector

# Export as JSON
python adobe_stock_scraper.py "technology" -n 100 --json
```

### Batch Scraping

```bash
# From command line
python batch_scraper.py -q "home office" "remote work" "business meeting" -n 100

# From file
python batch_scraper.py -f queries.txt -n 200 --details
```

Create a `queries.txt` file with one query per line:
```
home office
remote work
business team
technology abstract
# Lines starting with # are ignored
nature landscape
```

## Full import to SellScope API

After scraping, import into the database (requires API running):

```bash
# Sync to API (full import: searches, assets, keywords, similar, contributors)
python api_integration.py "fruit" -n 10 --details --similar --no-sync  # scrape only
# Then import the generated JSON:
python import_json_to_api.py output/adobe_stock_fruit_*.json
```

Or scrape and sync in one go:

```bash
python api_integration.py "fruit" -n 10 --details --similar
```

The API endpoint `POST /scraper/full-import` accepts `{ "query", "results", "similar_results" }` and populates the nested schema (Search, Contributor, Asset, Keyword, AssetKeyword, SearchResult, SimilarAsset, Category, AssetCategory).

## Output Fields

| Field | Description |
|-------|-------------|
| position | Ranking position in search results |
| asset_id | Unique Adobe Stock asset ID |
| title | Asset title/description |
| asset_type | photo, vector, illustration, video, template, 3d, audio |
| contributor_id | Contributor's ID |
| contributor_name | Contributor's display name |
| is_premium | Whether it's a premium asset |
| license_type | Standard or Premium |
| width | Image width in pixels |
| height | Image height in pixels |
| orientation | horizontal, vertical, or square |
| keywords | Pipe-separated keywords (if --details used) |
| keyword_count | Number of keywords |
| category | Asset category |
| similar_count | Number of similar assets |
| asset_url | Full URL to asset page |
| thumbnail_url | URL to thumbnail image |
| search_query | The search query used |
| search_page | Page number where result was found |
| scraped_at | Timestamp of scraping |

## Configuration

Create a `.env` file in the scraper directory:

```env
SCRAPER_HEADLESS=false
SCRAPER_DELAY_MIN=1.5
SCRAPER_DELAY_MAX=3.5
SCRAPER_MAX_RETRIES=3
SCRAPER_PAGE_TIMEOUT=30
SCRAPER_MAX_RESULTS=1000
SCRAPER_OUTPUT_DIR=output
```

## Tips

1. **Start small**: Test with 50-100 results first to verify data quality
2. **Use headless for large jobs**: Faster and uses less memory
3. **Add delays for safety**: Default delays help avoid rate limiting
4. **Scrape keywords sparingly**: Detail page scraping is slow (1-2 seconds per asset)
5. **Monitor for changes**: Adobe Stock may update their HTML structure

## Example Output (CSV)

```csv
position,asset_id,title,asset_type,contributor_id,contributor_name,is_premium,license_type,width,height,orientation,keywords,keyword_count,asset_url,thumbnail_url,search_query,search_page,scraped_at
1,123456789,Modern home office with plants,photo,9876543,CreativeStudio,False,Standard,5000,3333,horizontal,home|office|modern|workspace|interior,5,https://stock.adobe.com/images/123456789,https://...,home office,1,2024-01-15T10:30:00
```

## Troubleshooting

### Chrome driver issues
The scraper uses `webdriver-manager` to automatically download the correct Chrome driver. Make sure Chrome is installed.

### Timeouts
Increase `SCRAPER_PAGE_TIMEOUT` in config if you have slow internet.

### No results found
- Check if the search query returns results on Adobe Stock website
- Adobe may have updated their HTML structure - check the selectors

### Rate limiting
If you get blocked:
- Increase delays in config
- Use a VPN or proxy
- Reduce concurrent requests
