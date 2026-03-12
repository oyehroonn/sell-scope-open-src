"""Configuration for Adobe Stock Scraper"""

import os
from dotenv import load_dotenv

load_dotenv()

# Scraping settings
HEADLESS = os.getenv("SCRAPER_HEADLESS", "false").lower() == "true"
DELAY_MIN = float(os.getenv("SCRAPER_DELAY_MIN", "1.5"))
DELAY_MAX = float(os.getenv("SCRAPER_DELAY_MAX", "3.5"))
MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
PAGE_LOAD_TIMEOUT = int(os.getenv("SCRAPER_PAGE_TIMEOUT", "30"))
MAX_RESULTS = int(os.getenv("SCRAPER_MAX_RESULTS", "1000"))

# Adobe Stock URLs
BASE_URL = "https://stock.adobe.com"
SEARCH_URL = f"{BASE_URL}/search"
ASSET_URL = f"{BASE_URL}/images"
CONTRIBUTOR_URL = f"{BASE_URL}/contributor"

# Output settings
OUTPUT_DIR = os.getenv("SCRAPER_OUTPUT_DIR", "output")
CSV_FILENAME = os.getenv("SCRAPER_CSV_FILENAME", "adobe_stock_results.csv")

# Results per page on Adobe Stock
RESULTS_PER_PAGE = 100
