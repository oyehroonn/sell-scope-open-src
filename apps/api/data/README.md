# CSV data directory (source of truth when USE_CSV_STORE=True)

The API uses these CSV files instead of Postgres when `USE_CSV_STORE=True`.  
Files are created with headers only if missing; the store loads them at startup and writes back on every mutation.

## Files and columns

| File | Purpose | Key columns |
|------|--------|-------------|
| **searches.csv** | Search runs | `term`, `total_results_available`, `scraped_at`, `created_at` |
| **assets.csv** | All assets (search + similar) | `adobe_id` (unique), `title`, `description`, `contributor_id`, `thumbnail_url`, `preview_url`, `keywords` (JSON array), `category`, `width`, `height`, `source`, `scraped_at`, ... |
| **contributors.csv** | Creators | `adobe_id` (unique), `name`, `profile_url`, `scraped_at` |
| **keywords.csv** | Normalized keywords | `term` (unique), `normalized_term`, `type` (search/asset/hashtag) |
| **search_results.csv** | Asset ↔ search | `search_term`, `asset_adobe_id`, `position`, `page`, `scraped_at` |
| **similar_assets.csv** | Similar relationship | `main_asset_adobe_id`, `similar_asset_adobe_id`, `rank`, `scraped_at` |
| **asset_keywords.csv** | Asset ↔ keyword | `asset_adobe_id`, `keyword_term`, `source` (e.g. meta) |
| **categories.csv** | Categories | `name` |
| **asset_categories.csv** | Asset ↔ category | `asset_adobe_id`, `category_name` |

- **Natural keys**: No integer IDs; `adobe_id`, `term`, `search_term` identify rows.
- **JSON columns**: `assets.keywords`, `assets.color_palette`, `assets.style_tags`, `keywords.related_keywords` are stored as JSON strings.
- **Booleans**: Stored as `true` / `false`. **Dates**: ISO format.

## Scraper alignment

The scraper exports JSON with:

- `query`, `results` (list of items with `asset_id`, `title`, `contributor_id`, `keywords_list`, `category`, etc.)
- `similar_results` (list with `asset_id`, `similar_to_asset_id`, `rank`, …)

`POST /scraper/full-import` accepts that JSON and, in CSV mode, updates these files via the in-memory store.

## Pandas store (USE_PANDAS_STORE=True)

When `USE_PANDAS_STORE=True`, the main database is a **nested pandas store**: one pickle file `data/pandas/store.pkl` containing a dict of DataFrames (assets, searches, contributors, keywords, search_results, similar_assets, asset_keywords, categories, asset_categories). Each asset row includes a **`scraped_data`** column with the **full scraped payload** (all fields from the scraper). Read/write operations update the in-memory DataFrames and persist to disk. Use `GET /assets/{adobe_id}/scraped` to retrieve the full nested scraped data for an asset.

## Location

Default path is `data/` under the API app (e.g. `apps/api/data`). Override with env `DATA_DIR` (absolute or relative to the app directory). Pandas store file: `data/pandas/store.pkl`.
