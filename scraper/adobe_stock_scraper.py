"""
Adobe Stock Scraper - Selenium-based scraper for extracting product data
Supports pagination, all fields extraction, and CSV export
"""

import os
import re
import csv
import json
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs

import platform
import shutil
import subprocess

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from tqdm import tqdm
import pandas as pd

from config import (
    HEADLESS, DELAY_MIN, DELAY_MAX, MAX_RETRIES, PAGE_LOAD_TIMEOUT,
    MAX_RESULTS, BASE_URL, SEARCH_URL, ASSET_URL, OUTPUT_DIR, 
    CSV_FILENAME, RESULTS_PER_PAGE
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_user_agent():
    """Get a realistic user agent string"""
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    return random.choice(user_agents)


def find_chromedriver():
    """Find chromedriver path, handling Apple Silicon Macs properly.
    
    Uses webdriver-manager to automatically download the correct version
    that matches the installed Chrome browser.
    """
    
    # First, try webdriver-manager to get the matching version
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        
        logger.info("Getting matching ChromeDriver via webdriver-manager...")
        driver_path = ChromeDriverManager().install()
        logger.info(f"webdriver-manager returned: {driver_path}")
        
        dir_path = os.path.dirname(driver_path)
        
        for root, dirs, files in os.walk(dir_path):
            for fname in files:
                if fname == "chromedriver" or fname == "chromedriver.exe":
                    actual_path = os.path.join(root, fname)
                    if os.path.isfile(actual_path):
                        if not os.access(actual_path, os.X_OK):
                            os.chmod(actual_path, 0o755)
                            logger.info(f"Made chromedriver executable: {actual_path}")
                        logger.info(f"Found chromedriver executable: {actual_path}")
                        return actual_path
        
        if os.path.isfile(driver_path) and "chromedriver" in driver_path.lower():
            basename = os.path.basename(driver_path)
            if basename in ["chromedriver", "chromedriver.exe"]:
                if not os.access(driver_path, os.X_OK):
                    os.chmod(driver_path, 0o755)
                logger.info(f"Using chromedriver: {driver_path}")
                return driver_path
                    
    except Exception as e:
        logger.warning(f"webdriver-manager failed: {e}, trying system paths...")
    
    # Fallback to system-installed chromedriver
    system_paths = [
        "/opt/homebrew/bin/chromedriver",  # macOS Apple Silicon (Homebrew)
        "/usr/local/bin/chromedriver",      # macOS Intel (Homebrew)
        "/usr/bin/chromedriver",            # Linux system
        "/snap/bin/chromedriver",           # Linux snap
    ]
    
    for path in system_paths:
        if os.path.exists(path) and os.path.isfile(path):
            logger.info(f"Found system chromedriver at: {path}")
            if not os.access(path, os.X_OK):
                try:
                    os.chmod(path, 0o755)
                    logger.info(f"Made chromedriver executable: {path}")
                except:
                    pass
            return path
    
    # Try chromedriver in PATH
    chromedriver_in_path = shutil.which("chromedriver")
    if chromedriver_in_path:
        logger.info(f"Found chromedriver in PATH: {chromedriver_in_path}")
        return chromedriver_in_path
    
    raise RuntimeError(
        "ChromeDriver not found. Please install it:\n"
        "  macOS: brew install --cask chromedriver\n"
        "  Then run: xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver\n"
        "  Linux: sudo apt install chromium-chromedriver\n"
        "  Windows: Download from https://chromedriver.chromium.org/"
    )


class AdobeStockScraper:
    """
    Comprehensive Adobe Stock scraper using Selenium.
    Extracts all available product data and exports to CSV.
    """
    
    def __init__(self, headless: bool = None):
        self.headless = headless if headless is not None else HEADLESS
        self.driver = None
        self.wait = None
        self.results: List[Dict[str, Any]] = []
        self.similar_results: List[Dict[str, Any]] = []
        
    def _setup_driver(self):
        """Initialize Chrome WebDriver with memory-optimized settings"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        user_agent = get_user_agent()
        options.add_argument(f"--user-agent={user_agent}")
        options.add_argument("--window-size=1280,720")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--mute-audio")
        options.add_argument("--no-first-run")
        options.add_argument("--safebrowsing-disable-auto-update")
        options.add_argument("--js-flags=--max-old-space-size=512")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.stylesheets": 1,
            "profile.managed_default_content_settings.plugins": 2,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        options.add_argument("--lang=en-US")
        options.add_argument("--accept-language=en-US,en;q=0.9")
        
        chromedriver_path = find_chromedriver()
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=options)
        
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """
        })
        
        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        self.wait = WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT)
        
        logger.info("WebDriver initialized successfully")
    
    def _random_delay(self, min_delay: float = None, max_delay: float = None):
        """Add random delay to mimic human behavior"""
        min_d = min_delay or DELAY_MIN
        max_d = max_delay or DELAY_MAX
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)
    
    def _scroll_page(self, scroll_pause: float = 0.5, max_scrolls: int = 10):
        """Scroll page to load lazy-loaded content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for i in range(max_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(scroll_pause / 2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def _extract_asset_id_from_url(self, url: str) -> Optional[str]:
        """Extract asset ID from Adobe Stock URL"""
        if not url:
            return None
        
        patterns = [
            r'/images/(\d+)',
            r'/video/(\d+)',
            r'/templates/(\d+)',
            r'/3d-assets/(\d+)',
            r'/audio/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        match = re.search(r'/(\d+)(?:\?|$|-)', url)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_contributor_id(self, url: str) -> Optional[str]:
        """Extract contributor ID from URL"""
        if not url:
            return None
        match = re.search(r'/contributor/(\d+)', url)
        return match.group(1) if match else None
    
    def _determine_asset_type(self, element, url: str) -> str:
        """Determine asset type from element and URL"""
        url_lower = url.lower() if url else ""
        
        if '/video/' in url_lower:
            return 'video'
        elif '/templates/' in url_lower:
            return 'template'
        elif '/3d-assets/' in url_lower:
            return '3d'
        elif '/audio/' in url_lower:
            return 'audio'
        
        try:
            badges = element.find_elements(By.CSS_SELECTOR, "[class*='badge'], [class*='type'], [data-testid*='type']")
            for badge in badges:
                text = badge.text.lower()
                if 'vector' in text:
                    return 'vector'
                elif 'illustration' in text:
                    return 'illustration'
                elif 'video' in text:
                    return 'video'
                elif 'template' in text:
                    return 'template'
        except:
            pass
        
        try:
            video_indicators = element.find_elements(By.CSS_SELECTOR, "video, [class*='video'], [data-testid*='video']")
            if video_indicators:
                return 'video'
        except:
            pass
        
        return 'photo'
    
    def _extract_dimensions(self, text: str) -> Dict[str, Optional[int]]:
        """Extract width and height from dimension text"""
        result = {"width": None, "height": None}
        if not text:
            return result
        
        match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', text)
        if match:
            result["width"] = int(match.group(1))
            result["height"] = int(match.group(2))
        
        return result
    
    def _is_premium(self, element) -> bool:
        """Check if asset is premium"""
        try:
            premium_indicators = element.find_elements(By.CSS_SELECTOR, 
                "[class*='premium'], [data-testid*='premium'], [class*='Premium']")
            return len(premium_indicators) > 0
        except:
            return False
    
    def _parse_search_result_item(self, item, position: int) -> Optional[Dict[str, Any]]:
        """Parse a single search result item and extract all available data from list page"""
        try:
            asset_url = None
            asset_id = None
            
            link_selectors = [
                "a[href*='/images/']",
                "a[href*='/video/']",
                "a[href*='/templates/']",
                "a[href*='stock.adobe.com']",
                "a[data-testid='asset-link']",
                "a"
            ]
            
            for selector in link_selectors:
                try:
                    links = item.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        href = link.get_attribute("href")
                        if href and ('images' in href or 'video' in href or 'templates' in href):
                            asset_url = href
                            asset_id = self._extract_asset_id_from_url(href)
                            if asset_id:
                                break
                    if asset_id:
                        break
                except:
                    continue
            
            if not asset_id:
                return None
            
            title = ""
            thumbnail_url = ""
            img_selectors = ["img", "picture img", "picture source", "[data-testid='thumbnail'] img", "img[alt]"]
            for selector in img_selectors:
                try:
                    imgs = item.find_elements(By.CSS_SELECTOR, selector)
                    for img in imgs:
                        if not title:
                            alt = img.get_attribute("alt") or ""
                            if alt and len(alt) > 3:
                                title = alt.strip()
                        if not thumbnail_url:
                            src = img.get_attribute("src") or ""
                            if not src or "data:image" in src:
                                src = img.get_attribute("data-src") or ""
                            if not src:
                                srcset = img.get_attribute("srcset") or img.get_attribute("data-srcset") or ""
                                if srcset:
                                    parts = srcset.split(",")
                                    for part in parts:
                                        url_part = part.strip().split(" ")[0]
                                        if url_part and "http" in url_part:
                                            src = url_part
                                            break
                            if src and ("ftcdn" in src or "adobe" in src) and "data:image" not in src:
                                thumbnail_url = src
                        if title and thumbnail_url:
                            break
                    if title and thumbnail_url:
                        break
                except Exception:
                    continue
            
            contributor_id = None
            contributor_name = ""
            contributor_url = ""
            try:
                contrib_selectors = [
                    "a[href*='/contributor/']",
                    "[class*='contributor'] a",
                    "[class*='author'] a",
                    "[class*='Artist'] a",
                    "[data-testid*='contributor']",
                ]
                for sel in contrib_selectors:
                    try:
                        links = item.find_elements(By.CSS_SELECTOR, sel)
                        for link in links:
                            href = link.get_attribute("href") or ""
                            if "/contributor/" in href:
                                contributor_url = href
                                contributor_id = self._extract_contributor_id(href)
                                contributor_name = (link.text or "").strip()
                                if not contributor_name:
                                    contributor_name = link.get_attribute("title") or ""
                                break
                        if contributor_id:
                            break
                    except:
                        continue
            except:
                pass
            
            asset_type = self._determine_asset_type(item, asset_url)
            is_premium = self._is_premium(item)
            license_type = "Premium" if is_premium else "Standard"
            
            is_editorial = False
            is_ai_generated = False
            try:
                item_html = item.get_attribute("outerHTML") or ""
                item_text = item.text or ""
                if "editorial" in item_html.lower() or "editorial" in item_text.lower():
                    is_editorial = True
                if "ai generated" in item_html.lower() or "ai-generated" in item_html.lower() or "generative" in item_text.lower():
                    is_ai_generated = True
            except:
                pass
            
            dimensions = {"width": None, "height": None}
            try:
                dim_selectors = ["[class*='dimension']", "[class*='size']", "[class*='resolution']", "span"]
                for sel in dim_selectors:
                    elems = item.find_elements(By.CSS_SELECTOR, sel)
                    for elem in elems:
                        dims = self._extract_dimensions(elem.text)
                        if dims["width"]:
                            dimensions = dims
                            break
                    if dimensions["width"]:
                        break
            except:
                pass
            
            orientation = None
            aspect_ratio = None
            if dimensions["width"] and dimensions["height"]:
                w, h = dimensions["width"], dimensions["height"]
                if w > h:
                    orientation = "horizontal"
                elif h > w:
                    orientation = "vertical"
                else:
                    orientation = "square"
                aspect_ratio = round(w / h, 2) if h else None
            
            similar_count = None
            try:
                similar_elements = item.find_elements(By.CSS_SELECTOR, "[class*='similar'], [data-testid*='similar']")
                for elem in similar_elements:
                    match = re.search(r'(\d+)', elem.text)
                    if match:
                        similar_count = int(match.group(1))
                        break
            except:
                pass
            
            return {
                "position": position,
                "asset_id": asset_id,
                "asset_url": asset_url,
                "title": title,
                "thumbnail_url": thumbnail_url,
                "contributor_id": contributor_id,
                "contributor_name": contributor_name,
                "contributor_url": contributor_url,
                "asset_type": asset_type,
                "is_premium": is_premium,
                "is_editorial": is_editorial,
                "is_ai_generated": is_ai_generated,
                "license_type": license_type,
                "width": dimensions["width"],
                "height": dimensions["height"],
                "orientation": orientation,
                "aspect_ratio": aspect_ratio,
                "similar_count": similar_count,
                "source": "search",
                "scraped_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.warning(f"Error parsing item at position {position}: {e}")
            return None
    
    def _get_total_results_count(self) -> int:
        """Get total number of results for current search"""
        try:
            count_selectors = [
                "[data-testid='results-count']",
                "[class*='results-count']",
                "[class*='ResultsCount']",
                "span[class*='count']",
            ]
            
            for selector in count_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text
                        numbers = re.findall(r'[\d,]+', text.replace(',', ''))
                        if numbers:
                            return int(numbers[0].replace(',', ''))
                except:
                    continue
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            match = re.search(r'([\d,]+)\s*(?:results?|images?|assets?)', page_text, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(',', ''))
            
        except Exception as e:
            logger.warning(f"Could not get total results count: {e}")
        
        return 0
    
    def _navigate_to_page(self, page_num: int, search_query: str, filters: Dict = None) -> bool:
        """Navigate to a specific page of results"""
        try:
            params = {
                "k": search_query,
                "search_page": page_num,
                "search_type": "usertyped",
            }
            
            if filters:
                if filters.get("content_type"):
                    for ct in filters["content_type"]:
                        params[f"filters[content_type:{ct}]"] = "1"
                
                if filters.get("orientation"):
                    params["filters[orientation]"] = filters["orientation"]
                
                if filters.get("color"):
                    params["filters[color]"] = filters["color"]
            
            url = f"{SEARCH_URL}?{urlencode(params)}"
            logger.info(f"Navigating to page {page_num}: {url}")
            
            self.driver.get(url)
            self._random_delay()
            
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            
            self._scroll_page(scroll_pause=0.3, max_scrolls=5)
            
            return True
            
        except TimeoutException:
            logger.warning(f"Timeout navigating to page {page_num}")
            return False
        except Exception as e:
            logger.error(f"Error navigating to page {page_num}: {e}")
            return False
    
    def _get_result_items(self) -> List:
        """Get all result items from current page"""
        item_selectors = [
            "[data-testid='search-result-item']",
            "[class*='SearchResultItem']",
            "[class*='search-result-item']",
            "[class*='asset-card']",
            "[class*='AssetCard']",
            "article[class*='result']",
            "[data-testid='asset-card']",
        ]
        
        for selector in item_selectors:
            try:
                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    logger.info(f"Found {len(items)} items with selector: {selector}")
                    return items
            except:
                continue
        
        try:
            items = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/images/']")
            if items:
                parent_items = []
                for item in items:
                    try:
                        parent = item.find_element(By.XPATH, "./..")
                        grandparent = parent.find_element(By.XPATH, "./..")
                        if grandparent not in parent_items:
                            parent_items.append(grandparent)
                    except:
                        pass
                if parent_items:
                    logger.info(f"Found {len(parent_items)} items via link parents")
                    return parent_items
        except:
            pass
        
        logger.warning("No result items found on page")
        return []
    
    def search(
        self,
        query: str,
        max_results: int = None,
        filters: Dict = None,
        scrape_details: bool = False,
        scrape_similar: bool = False,
        max_similar_per_asset: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search Adobe Stock and extract all results.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to scrape (default: from config)
            filters: Optional filters dict
            scrape_details: If True, scrape each asset's detail page (keywords, dimensions, etc.)
            scrape_similar: If True (and scrape_details True), also scrape similar assets' details
            max_similar_per_asset: Max similar assets to scrape per main asset
        
        Returns:
            List of asset dicts. Similar assets are in self.similar_results.
        """
        max_results = max_results or MAX_RESULTS
        self.results = []
        
        if not self.driver:
            self._setup_driver()
        
        try:
            logger.info(f"Starting search for: '{query}' (max {max_results} results)")
            
            if not self._navigate_to_page(1, query, filters):
                logger.error("Failed to load initial search page")
                return []
            
            total_available = self._get_total_results_count()
            logger.info(f"Total results available: {total_available}")
            
            target_results = min(max_results, total_available) if total_available > 0 else max_results
            total_pages = (target_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
            
            logger.info(f"Will scrape up to {target_results} results across ~{total_pages} pages")
            
            with tqdm(total=target_results, desc="Scraping results", unit="items") as pbar:
                page_num = 1
                consecutive_empty_pages = 0
                
                while len(self.results) < target_results:
                    if page_num > 1:
                        if not self._navigate_to_page(page_num, query, filters):
                            consecutive_empty_pages += 1
                            if consecutive_empty_pages >= 3:
                                logger.warning("Too many consecutive empty pages, stopping")
                                break
                            page_num += 1
                            continue
                    
                    items = self._get_result_items()
                    
                    if not items:
                        consecutive_empty_pages += 1
                        if consecutive_empty_pages >= 3:
                            logger.warning("No items found for 3 consecutive pages, stopping")
                            break
                        page_num += 1
                        continue
                    
                    consecutive_empty_pages = 0
                    page_results = 0
                    
                    for item in items:
                        if len(self.results) >= target_results:
                            break
                        
                        position = len(self.results) + 1
                        
                        for attempt in range(MAX_RETRIES):
                            try:
                                data = self._parse_search_result_item(item, position)
                                if data:
                                    if not any(r["asset_id"] == data["asset_id"] for r in self.results):
                                        data["search_query"] = query
                                        data["search_page"] = page_num
                                        self.results.append(data)
                                        page_results += 1
                                        pbar.update(1)
                                break
                            except StaleElementReferenceException:
                                if attempt < MAX_RETRIES - 1:
                                    self._random_delay(0.5, 1.0)
                                    items = self._get_result_items()
                                    if position - 1 < len(items):
                                        item = items[position - 1]
                    
                    logger.info(f"Page {page_num}: scraped {page_results} items (total: {len(self.results)})")
                    
                    page_num += 1
                    self._random_delay()
            
            if scrape_details and self.results:
                logger.info("Scraping asset details (keywords, dimensions, preview, similar)...")
                self._scrape_asset_details(
                    scrape_similar=scrape_similar,
                    max_similar_per_asset=max_similar_per_asset,
                )
            
            logger.info(f"Search complete. Total results: {len(self.results)}; similar: {len(self.similar_results)}")
            return self.results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
    
    def _scrape_asset_details(self, scrape_similar: bool = False, max_similar_per_asset: int = 5):
        """Scrape individual asset pages: ALL available fields including keywords, dimensions, pricing, colors, releases, etc."""
        with tqdm(total=len(self.results), desc="Fetching details", unit="assets") as pbar:
            for result in self.results:
                try:
                    asset_id = result.get("asset_id")
                    if not asset_id:
                        pbar.update(1)
                        continue
                    
                    # Use the full URL from search results if available (includes slug and locale)
                    detail_url = result.get("asset_url") or f"{ASSET_URL}/{asset_id}"
                    self.driver.get(detail_url)
                    self._random_delay(1.5, 2.5)
                    
                    # Scroll to trigger lazy loading of keywords section
                    try:
                        self.driver.execute_script("window.scrollTo(0, 500);")
                        time.sleep(0.5)
                        self.driver.execute_script("window.scrollTo(0, 1000);")
                        time.sleep(0.5)
                    except:
                        pass
                    
                    page_html = ""
                    page_text = ""
                    try:
                        page_html = self.driver.page_source or ""
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text or ""
                    except:
                        pass
                    
                    keywords = []
                    keyword_selectors = [
                        "a[href*='k=']",
                        "a[href*='/search?k=']",
                        "[data-testid='keyword']",
                        "[data-testid*='keyword']",
                        "[class*='keyword'] a",
                        "[class*='Keyword'] a",
                        "[class*='tag-'] a",
                        "[class*='Tag'] a",
                        "section[class*='keyword'] a",
                        "div[class*='keyword'] a",
                    ]
                    # Skip UI text, navigation, and footer content
                    skip_texts = [
                        "ver más", "see more", "view more", "show more", "load more", "similar", "más", "more",
                        "mostrar todo", "show all", "ver todo", "cambiar", "change", "términos", "terms",
                        "licencia", "license", "privacidad", "privacy", "cookies", "adobe", "copyright",
                        "mapa del sitio", "sitemap", "empresa", "company", "formación", "training",
                        "asistencia", "support", "vender", "sell", "adchoices", "enable", "don't",
                        "all rights", "condiciones", "preferencias", "settings", "make it"
                    ]
                    for selector in keyword_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                text = (elem.text or "").strip()
                                if text and 1 < len(text) < 50 and text.lower() not in [k.lower() for k in keywords]:
                                    if not any(skip in text.lower() for skip in skip_texts):
                                        # Skip if it looks like a copyright notice or contains special chars
                                        if not re.search(r'[©®™]|\d{4}\s+Adobe|\(\d+\)', text):
                                            keywords.append(text)
                        except Exception:
                            continue
                    
                    # Primary method: extract keywords from page text after "KEYWORDS" or "PALABRAS CLAVE" section
                    # This is more reliable as keywords are displayed as plain text on the page
                    if len(keywords) < 5:
                        try:
                            # Find the keywords section and extract all words until next section
                            kw_section_match = re.search(
                                r'(?:SIMILAR KEYWORDS|PALABRAS CLAVE SIMILARES|KEYWORDS)\s*\n((?:[^\n]+\n?)+?)(?:SIMILAR|MÁS DE|MORE FROM|VIDEOS|VÍDEOS|\n\n|$)',
                                page_text, re.I
                            )
                            if kw_section_match:
                                kw_text = kw_section_match.group(1)
                                for line in kw_text.split('\n'):
                                    kw = line.strip()
                                    # Skip empty lines, numbers, UI text, and footer content
                                    if kw and 1 < len(kw) < 50 and not kw.isdigit():
                                        if kw.lower() not in [k.lower() for k in keywords]:
                                            if not any(skip in kw.lower() for skip in skip_texts):
                                                if not re.search(r'[©®™]|\d{4}\s+Adobe|\(\d+\)', kw):
                                                    keywords.append(kw)
                        except:
                            pass
                    
                    result["keywords_list"] = keywords[:100]
                    result["keywords"] = "|".join(keywords[:50])
                    result["keyword_count"] = len(keywords)
                    
                    if not result.get("title") or len(result.get("title", "")) < 5:
                        try:
                            title_selectors = ["h1", "meta[property='og:title']", "meta[name='title']", "[class*='title'] h1"]
                            for sel in title_selectors:
                                elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                                for elem in elems:
                                    if elem.tag_name.lower() == "meta":
                                        t = elem.get_attribute("content") or ""
                                    else:
                                        t = (elem.text or "").strip()
                                    if t and len(t) > 5:
                                        result["title"] = t[:500]
                                        break
                                if result.get("title"):
                                    break
                        except:
                            pass
                    
                    try:
                        desc_selectors = [
                            "meta[name='description']",
                            "meta[property='og:description']",
                            "[class*='description']",
                            "[data-testid='description']",
                        ]
                        for selector in desc_selectors:
                            try:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                for elem in elements:
                                    if elem.tag_name.lower() == "meta":
                                        desc = elem.get_attribute("content") or ""
                                    else:
                                        desc = (elem.text or "").strip()
                                    if desc and len(desc) > 10:
                                        result["description"] = desc[:2000]
                                        break
                                if result.get("description"):
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass
                    
                    try:
                        category_selectors = [
                            "a[href*='/category/']",
                            "[data-testid='category']",
                            "[class*='category'] a",
                            "[class*='Category'] a",
                            "nav a[href*='category']",
                        ]
                        categories = []
                        for selector in category_selectors:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                cat_text = (elem.text or "").strip()
                                if cat_text and 2 < len(cat_text) < 100 and cat_text not in categories:
                                    categories.append(cat_text)
                        if categories:
                            result["category"] = categories[0]
                            result["categories"] = categories[:5]
                    except Exception:
                        pass
                    
                    try:
                        dim_selectors = [
                            "[class*='dimension']",
                            "[class*='Dimension']",
                            "[class*='size']",
                            "[class*='Size']",
                            "[class*='resolution']",
                            "[data-testid='dimensions']",
                            "[data-testid='size']",
                        ]
                        for selector in dim_selectors:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                text = elem.text or ""
                                dims = self._extract_dimensions(text)
                                if dims["width"]:
                                    result["width"] = dims["width"]
                                    result["height"] = dims["height"]
                                    w, h = dims["width"], dims["height"]
                                    result["orientation"] = "horizontal" if w > h else "vertical" if h > w else "square"
                                    result["aspect_ratio"] = round(w / h, 2) if h else None
                                    result["megapixels"] = round((w * h) / 1000000, 2)
                                    break
                            if result.get("width"):
                                break
                        if not result.get("width"):
                            dim_match = re.search(r'(\d{3,5})\s*[x×X]\s*(\d{3,5})', page_text)
                            if dim_match:
                                w, h = int(dim_match.group(1)), int(dim_match.group(2))
                                result["width"] = w
                                result["height"] = h
                                result["orientation"] = "horizontal" if w > h else "vertical" if h > w else "square"
                                result["aspect_ratio"] = round(w / h, 2) if h else None
                                result["megapixels"] = round((w * h) / 1000000, 2)
                    except Exception:
                        pass
                    
                    try:
                        img_selectors = [
                            "img[src*='ftcdn']",
                            "img[src*='adobe']",
                            "picture img",
                            "[class*='preview'] img",
                            "[class*='Preview'] img",
                            "[data-testid='asset-image'] img",
                        ]
                        for sel in img_selectors:
                            imgs = self.driver.find_elements(By.CSS_SELECTOR, sel)
                            for img in imgs:
                                src = img.get_attribute("src") or img.get_attribute("data-src") or ""
                                if src and ("ftcdn" in src or "adobe" in src) and "data:image" not in src:
                                    if "thumb" not in src.lower() and "_s." not in src.lower():
                                        result["preview_url"] = src
                                        break
                                    elif not result.get("thumbnail_url"):
                                        result["thumbnail_url"] = src
                            if result.get("preview_url"):
                                break
                    except Exception:
                        pass
                    
                    try:
                        format_selectors = [
                            "[class*='file-type']",
                            "[class*='FileType']",
                            "[class*='format']",
                            "[class*='Format']",
                            "[data-testid='file-type']",
                        ]
                        for selector in format_selectors:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                fmt = (elem.text or "").strip().upper()
                                if fmt and len(fmt) < 30:
                                    if any(x in fmt for x in ("JPEG", "JPG", "PNG", "EPS", "AI", "SVG", "VIDEO", "MP4", "MOV", "VECTOR", "PSD", "TIFF")):
                                        result["file_format"] = fmt
                                        break
                            if result.get("file_format"):
                                break
                        if not result.get("file_format"):
                            fmt_match = re.search(r'\b(JPEG|JPG|PNG|EPS|AI|SVG|MP4|MOV|PSD|TIFF|VECTOR)\b', page_text, re.I)
                            if fmt_match:
                                result["file_format"] = fmt_match.group(1).upper()
                    except Exception:
                        pass
                    
                    try:
                        price_selectors = [
                            "[class*='price']",
                            "[class*='Price']",
                            "[class*='credit']",
                            "[class*='Credit']",
                            "[data-testid='price']",
                        ]
                        for selector in price_selectors:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                price_text = (elem.text or "").strip()
                                if price_text:
                                    price_match = re.search(r'[\$€£]?\s*(\d+(?:[.,]\d{2})?)', price_text)
                                    if price_match:
                                        result["price"] = price_match.group(0).strip()
                                    credit_match = re.search(r'(\d+)\s*credit', price_text, re.I)
                                    if credit_match:
                                        result["credits"] = int(credit_match.group(1))
                                    break
                            if result.get("price") or result.get("credits"):
                                break
                    except Exception:
                        pass
                    
                    try:
                        if "editorial" in page_html.lower() or "editorial" in page_text.lower():
                            result["is_editorial"] = True
                        if "ai generated" in page_html.lower() or "ai-generated" in page_html.lower() or "generative ai" in page_text.lower():
                            result["is_ai_generated"] = True
                        if "model release" in page_text.lower():
                            result["has_model_release"] = "model release" in page_text.lower() and "no model release" not in page_text.lower()
                        if "property release" in page_text.lower():
                            result["has_property_release"] = "property release" in page_text.lower() and "no property release" not in page_text.lower()
                    except Exception:
                        pass
                    
                    try:
                        color_selectors = [
                            "[class*='color']",
                            "[class*='Color']",
                            "[data-testid*='color']",
                            "[style*='background-color']",
                        ]
                        colors = []
                        for selector in color_selectors:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                bg = elem.value_of_css_property("background-color") or ""
                                if bg and bg != "rgba(0, 0, 0, 0)" and bg != "transparent":
                                    colors.append(bg)
                                color_text = (elem.text or "").strip()
                                if color_text and len(color_text) < 30:
                                    colors.append(color_text)
                            if len(colors) >= 5:
                                break
                        if colors:
                            result["color_palette"] = colors[:10]
                    except Exception:
                        pass
                    
                    try:
                        date_match = re.search(r'(?:uploaded|added|created)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})', page_text, re.I)
                        if date_match:
                            result["upload_date"] = date_match.group(1)
                    except Exception:
                        pass
                    
                    try:
                        if not result.get("contributor_id") or not result.get("contributor_name"):
                            contrib_selectors = [
                                "a[href*='/contributor/']",
                                "[class*='contributor'] a",
                                "[class*='Contributor'] a",
                                "[class*='author'] a",
                                "[class*='Author'] a",
                                "[class*='artist'] a",
                                "[class*='Artist'] a",
                            ]
                            for sel in contrib_selectors:
                                links = self.driver.find_elements(By.CSS_SELECTOR, sel)
                                for link in links:
                                    href = link.get_attribute("href") or ""
                                    if "/contributor/" in href:
                                        result["contributor_url"] = href
                                        result["contributor_id"] = self._extract_contributor_id(href)
                                        name = (link.text or "").strip()
                                        if not name:
                                            name = link.get_attribute("title") or ""
                                        # Try parent element text if link text is empty
                                        if not name:
                                            try:
                                                parent = link.find_element(By.XPATH, "..")
                                                name = (parent.text or "").strip()
                                            except:
                                                pass
                                        result["contributor_name"] = name
                                        break
                                if result.get("contributor_id"):
                                    break
                            
                            # Fallback: extract contributor from page text (e.g., "by panitan" or "de panitan")
                            if not result.get("contributor_name"):
                                contrib_match = re.search(r'(?:by|de|from|por)\s+([A-Za-z0-9_-]+)', page_text, re.I)
                                if contrib_match:
                                    result["contributor_name"] = contrib_match.group(1)
                    except Exception:
                        pass
                    
                    try:
                        video_duration = None
                        if result.get("asset_type") == "video":
                            dur_match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', page_text)
                            if dur_match:
                                mins = int(dur_match.group(1))
                                secs = int(dur_match.group(2))
                                video_duration = mins * 60 + secs
                                result["video_duration_seconds"] = video_duration
                            fps_match = re.search(r'(\d+(?:\.\d+)?)\s*fps', page_text, re.I)
                            if fps_match:
                                result["video_fps"] = float(fps_match.group(1))
                    except Exception:
                        pass
                    
                    try:
                        dpi_match = re.search(r'(\d+)\s*(?:dpi|ppi)', page_text, re.I)
                        if dpi_match:
                            result["dpi"] = int(dpi_match.group(1))
                        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|KB|GB)', page_text, re.I)
                        if size_match:
                            result["file_size"] = f"{size_match.group(1)} {size_match.group(2).upper()}"
                    except Exception:
                        pass
                    
                    similar_ids = []
                    try:
                        similar_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/images/'], a[href*='/video/']")
                        seen = {str(asset_id)}
                        for link in similar_links:
                            href = link.get_attribute("href")
                            if not href:
                                continue
                            sid = self._extract_asset_id_from_url(href)
                            if sid and sid not in seen:
                                seen.add(sid)
                                similar_ids.append(sid)
                                if len(similar_ids) >= 20:
                                    break
                    except Exception:
                        pass
                    result["similar_asset_ids"] = similar_ids
                    
                    if scrape_similar and similar_ids:
                        for rank, sim_id in enumerate(similar_ids[:max_similar_per_asset], 1):
                            if any(s.get("asset_id") == sim_id and s.get("similar_to_asset_id") == asset_id for s in self.similar_results):
                                continue
                            sim_data = self._scrape_single_asset_detail(sim_id, similar_to_asset_id=asset_id, rank=rank)
                            if sim_data:
                                self.similar_results.append(sim_data)
                    
                except Exception as e:
                    logger.warning(f"Error scraping details for asset {result.get('asset_id')}: {e}")
                pbar.update(1)
    
    def _scrape_single_asset_detail(self, asset_id: str, similar_to_asset_id: str = None, rank: int = 0) -> Optional[Dict[str, Any]]:
        """Scrape one asset detail page (for similar assets). Returns dict with asset data and similar_to_asset_id."""
        try:
            detail_url = f"{ASSET_URL}/{asset_id}"
            self.driver.get(detail_url)
            self._random_delay(0.8, 1.5)
            
            title = ""
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, "h1, [class*='title'] img[alt], meta[property='og:title']")
                for el in els:
                    if el.tag_name.lower() == "meta":
                        title = (el.get_attribute("content") or "").strip()
                    elif el.tag_name.lower() == "img":
                        title = (el.get_attribute("alt") or "").strip()
                    else:
                        title = (el.text or "").strip()
                    if title:
                        break
            except Exception:
                pass
            
            thumbnail_url = ""
            preview_url = ""
            for img in self.driver.find_elements(By.CSS_SELECTOR, "img[src*='adobe'], img[data-src*='adobe']"):
                src = img.get_attribute("src") or img.get_attribute("data-src") or ""
                if "adobe" in src:
                    if not thumbnail_url or "thumb" in src.lower():
                        thumbnail_url = src
                    if "thumb" not in src.lower() and "small" not in src.lower():
                        preview_url = src
                if thumbnail_url and preview_url:
                    break
            
            contributor_id = None
            contributor_name = ""
            try:
                for link in self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/contributor/']"):
                    href = link.get_attribute("href")
                    if href:
                        contributor_id = self._extract_contributor_id(href)
                        contributor_name = (link.text or "").strip()
                        if contributor_id:
                            break
            except Exception:
                pass
            
            keywords = []
            for selector in ["a[href*='k=']", "[class*='keyword']", "[class*='tag']"]:
                try:
                    for elem in self.driver.find_elements(By.CSS_SELECTOR, selector):
                        text = (elem.text or "").strip()
                        if text and 1 < len(text) < 80 and text not in keywords:
                            keywords.append(text)
                except Exception:
                    continue
            
            category = ""
            try:
                for el in self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/category/']"):
                    category = (el.text or "").strip()
                    if category:
                        break
            except Exception:
                pass
            
            return {
                "asset_id": asset_id,
                "similar_to_asset_id": similar_to_asset_id,
                "rank": rank,
                "title": title or f"Asset {asset_id}",
                "thumbnail_url": thumbnail_url,
                "preview_url": preview_url,
                "asset_url": detail_url,
                "contributor_id": contributor_id,
                "contributor_name": contributor_name,
                "keywords_list": keywords[:50],
                "keywords": "|".join(keywords[:30]),
                "category": category,
                "source": "similar",
                "scraped_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Error scraping similar asset {asset_id}: {e}")
            return None
    
    def export_to_csv(self, filename: str = None, output_dir: str = None) -> str:
        """Export results to CSV file"""
        if not self.results:
            logger.warning("No results to export")
            return ""
        
        output_dir = output_dir or OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_slug = re.sub(r'[^\w\s-]', '', self.results[0].get("search_query", "search"))[:30]
            query_slug = re.sub(r'[-\s]+', '_', query_slug).strip('_')
            filename = f"adobe_stock_{query_slug}_{timestamp}.csv"
        
        filepath = os.path.join(output_dir, filename)
        
        df = pd.DataFrame(self.results)
        
        columns_order = [
            "position", "asset_id", "title", "description", "asset_type",
            "contributor_id", "contributor_name", "contributor_url",
            "is_premium", "is_editorial", "is_ai_generated", "license_type",
            "width", "height", "orientation", "aspect_ratio", "megapixels",
            "keywords", "keywords_list", "keyword_count", "category", "categories",
            "similar_count", "similar_asset_ids",
            "file_format", "file_size", "dpi",
            "price", "credits",
            "has_model_release", "has_property_release",
            "color_palette", "upload_date",
            "video_duration_seconds", "video_fps",
            "asset_url", "thumbnail_url", "preview_url",
            "search_query", "search_page", "source", "scraped_at"
        ]
        
        existing_columns = [col for col in columns_order if col in df.columns]
        extra_columns = [col for col in df.columns if col not in columns_order]
        df = df[existing_columns + extra_columns]
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"Exported {len(self.results)} results to: {filepath}")
        
        return filepath
    
    def export_to_json(self, filename: str = None, output_dir: str = None) -> str:
        """Export results to JSON file"""
        if not self.results:
            logger.warning("No results to export")
            return ""
        
        output_dir = output_dir or OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_slug = re.sub(r'[^\w\s-]', '', self.results[0].get("search_query", "search"))[:30]
            query_slug = re.sub(r'[-\s]+', '_', query_slug).strip('_')
            filename = f"adobe_stock_{query_slug}_{timestamp}.json"
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            payload = {
                "query": self.results[0].get("search_query", "") if self.results else "",
                "total_results": len(self.results),
                "similar_count": len(self.similar_results),
                "scraped_at": datetime.utcnow().isoformat(),
                "results": self.results,
                "similar_results": self.similar_results,
            }
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(self.results)} results to: {filepath}")
        return filepath
    
    def close(self):
        """Clean up WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except:
                pass
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """Main entry point for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Adobe Stock Scraper")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--max-results", type=int, default=500, help="Maximum results to scrape")
    parser.add_argument("-d", "--details", action="store_true", help="Also scrape asset detail pages (keywords, dimensions, preview URL, etc.)")
    parser.add_argument("-s", "--similar", action="store_true", help="Also scrape similar assets (requires --details)")
    parser.add_argument("--max-similar", type=int, default=5, help="Max similar assets to scrape per result (default: 5)")
    parser.add_argument("-o", "--output", help="Output filename (default: auto-generated)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--json", action="store_true", help="Export as JSON instead of CSV")
    parser.add_argument("--content-type", nargs="+", choices=["photo", "illustration", "vector", "video"], 
                        help="Filter by content type")
    parser.add_argument("--orientation", choices=["horizontal", "vertical", "square"],
                        help="Filter by orientation")
    
    args = parser.parse_args()
    
    filters = {}
    if args.content_type:
        filters["content_type"] = args.content_type
    if args.orientation:
        filters["orientation"] = args.orientation
    
    with AdobeStockScraper(headless=args.headless) as scraper:
        results = scraper.search(
            query=args.query,
            max_results=args.max_results,
            filters=filters if filters else None,
            scrape_details=args.details,
            scrape_similar=args.similar and args.details,
            max_similar_per_asset=args.max_similar,
        )
        
        if results:
            if args.json:
                filepath = scraper.export_to_json(args.output)
            else:
                filepath = scraper.export_to_csv(args.output)
            
            print(f"\nScraping complete!")
            print(f"Total results: {len(results)}")
            print(f"Output file: {filepath}")
        else:
            print("No results found")


if __name__ == "__main__":
    main()
