"""
Deep Analyzer - Orchestrates comprehensive keyword analysis with multi-page scraping
Combines search results, asset details, contributor profiles, and similar assets
"""

import os
import re
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import (
    HEADLESS, DELAY_MIN, DELAY_MAX, PAGE_LOAD_TIMEOUT,
    BASE_URL, SEARCH_URL, ASSET_URL, CONTRIBUTOR_URL, OUTPUT_DIR
)
from adobe_stock_scraper import find_chromedriver, get_user_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnalysisDepth:
    """Analysis depth configuration"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    DEEP = "deep"
    
    @staticmethod
    def get_config(depth: str) -> Dict[str, Any]:
        configs = {
            "simple": {
                "max_assets": 20,
                "scrape_details": False,
                "scrape_contributors": False,
                "scrape_similar": False,
                "max_contributors": 0,
                "max_similar_per_asset": 0,
                "parallel_scraping": False,
                "max_workers": 1,
            },
            "medium": {
                "max_assets": 30,
                "scrape_details": True,
                "scrape_contributors": True,
                "scrape_similar": True,
                "max_contributors": 8,
                "max_similar_per_asset": 2,
                "parallel_scraping": True,
                "max_workers": 3,
            },
            "deep": {
                "max_assets": 60,
                "scrape_details": True,
                "scrape_contributors": True,
                "scrape_similar": True,
                "max_contributors": 15,
                "max_similar_per_asset": 3,
                "parallel_scraping": True,
                "max_workers": 4,
            },
        }
        return configs.get(depth, configs["medium"])


class DeepAnalyzer:
    """Orchestrates deep keyword analysis with comprehensive data collection"""
    
    def __init__(self, headless: bool = True, progress_callback: Callable = None):
        self.headless = headless
        self.driver = None
        self.progress_callback = progress_callback
        self._setup_driver()
    
    def _setup_driver(self):
        """Initialize Selenium WebDriver"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-agent={get_user_agent()}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        chromedriver_path = find_chromedriver()
        service = Service(chromedriver_path)
        
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        logger.info("WebDriver initialized for deep analysis")
    
    def _random_delay(self, min_delay: float = None, max_delay: float = None):
        """Add random delay to avoid detection"""
        min_d = min_delay or DELAY_MIN
        max_d = max_delay or DELAY_MAX
        time.sleep(random.uniform(min_d, max_d))
    
    def _report_progress(self, step: str, progress: int, message: str):
        """Report progress to callback if available"""
        if self.progress_callback:
            self.progress_callback({
                "step": step,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            })
        logger.info(f"[{progress}%] {step}: {message}")
    
    def analyze_keyword_deep(
        self,
        keyword: str,
        depth: str = "medium",
        custom_config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Perform deep analysis on a keyword.
        
        Args:
            keyword: The keyword to analyze
            depth: Analysis depth (simple, medium, deep)
            custom_config: Optional custom configuration overrides
        
        Returns:
            Comprehensive analysis results
        """
        config = AnalysisDepth.get_config(depth)
        if custom_config:
            config.update(custom_config)
        
        analysis = {
            "keyword": keyword,
            "depth": depth,
            "config": config,
            "search_results": {},
            "assets": [],
            "asset_details": [],
            "contributors": [],
            "contributor_profiles": [],
            "similar_assets": [],
            "market_analysis": {},
            "scoring": {},
            "visualizations": {},
            "scraped_at": datetime.utcnow().isoformat(),
            "errors": [],
        }
        
        try:
            # Step 1: Search Results (10%)
            self._report_progress("search", 10, f"Searching for '{keyword}'...")
            search_data = self._scrape_search_results(keyword, config["max_assets"])
            analysis["search_results"] = search_data
            analysis["assets"] = search_data.get("assets", [])
            
            # Step 2: Asset Details (30%)
            if config["scrape_details"] and analysis["assets"]:
                use_parallel = config.get("parallel_scraping", False)
                max_workers = config.get("max_workers", 3)
                assets_to_scrape = analysis["assets"][:config["max_assets"]]
                
                if use_parallel:
                    self._report_progress("assets", 30, f"Parallel scraping {len(assets_to_scrape)} assets with {max_workers} workers...")
                else:
                    self._report_progress("assets", 30, f"Analyzing {len(assets_to_scrape)} assets...")
                
                asset_details = self._scrape_asset_details(
                    assets_to_scrape, 
                    use_parallel=use_parallel, 
                    max_workers=max_workers
                )
                analysis["asset_details"] = asset_details
            
            # Step 3: Contributor Profiles (60%)
            if config["scrape_contributors"]:
                # Extract contributor IDs from asset_details (where we actually get them from detail pages)
                # Fall back to assets if asset_details is empty
                source_assets = analysis.get("asset_details") or analysis.get("assets", [])
                contributor_ids = self._extract_unique_contributors(source_assets)
                logger.info(f"Extracted {len(contributor_ids)} unique contributor IDs from {len(source_assets)} assets")
                
                self._report_progress("contributors", 60, f"Profiling {min(len(contributor_ids), config['max_contributors'])} contributors...")
                profiles = self._scrape_contributor_profiles(
                    contributor_ids[:config["max_contributors"]]
                )
                analysis["contributor_profiles"] = profiles
            
            # Step 4: Similar Assets (80%)
            if config["scrape_similar"] and analysis["asset_details"]:
                self._report_progress("similar", 80, "Analyzing similar assets...")
                similar = self._scrape_similar_assets(
                    analysis["asset_details"],
                    config["max_similar_per_asset"]
                )
                analysis["similar_assets"] = similar
            
            # Step 5: Calculate Scores and Analysis (90%)
            self._report_progress("scoring", 90, "Calculating scores...")
            analysis["market_analysis"] = self._analyze_market(analysis)
            analysis["scoring"] = self._calculate_enhanced_scores(analysis)
            
            # Step 6: Generate Visualization Data (100%)
            self._report_progress("visualizations", 100, "Generating visualization data...")
            analysis["visualizations"] = self._generate_visualization_data(analysis)
            
        except Exception as e:
            logger.error(f"Error in deep analysis: {e}")
            analysis["errors"].append(str(e))
        
        return analysis
    
    def _scrape_search_results(self, keyword: str, max_results: int) -> Dict[str, Any]:
        """Scrape search results for keyword"""
        results = {
            "keyword": keyword,
            "nb_results": 0,
            "assets": [],
            "related_searches": [],
            "categories": [],
            "filters_available": {},
        }
        
        try:
            # Search with relevance sort
            params = {"k": keyword, "search_type": "usertyped"}
            url = f"{SEARCH_URL}?{urlencode(params)}"
            
            self.driver.get(url)
            self._random_delay(2, 4)
            
            # Wait for results
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        "[data-testid='search-result-item'], [class*='AssetCard'], a[href*='/images/']"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for results for '{keyword}'")
            
            # Scroll to load more
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 1000)")
                time.sleep(0.5)
            
            # Extract total results
            results["nb_results"] = self._extract_total_results()
            
            # Extract assets
            results["assets"] = self._extract_search_assets(max_results)
            
            # Extract related searches
            results["related_searches"] = self._extract_related_searches()
            
            # Extract categories from filters
            results["categories"] = self._extract_filter_categories()
            
            # Extract available filters
            results["filters_available"] = self._extract_available_filters()
            
            # Also get results sorted by downloads
            params["order"] = "nb_downloads"
            url = f"{SEARCH_URL}?{urlencode(params)}"
            self.driver.get(url)
            self._random_delay(1, 2)
            
            # Get additional result count (might be more accurate)
            downloads_count = self._extract_total_results()
            results["nb_results"] = max(results["nb_results"], downloads_count)
            
        except Exception as e:
            logger.error(f"Error scraping search results: {e}")
        
        return results
    
    def _extract_total_results(self) -> int:
        """Extract total number of results"""
        try:
            # Try specific elements
            selectors = [
                "[data-testid='search-results-count']",
                "[class*='ResultsCount']",
                "[class*='results-count']",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    match = re.search(r'([\d,]+)', el.text)
                    if match:
                        return int(match.group(1).replace(",", ""))
            
            # Try page text
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            patterns = [
                r'([\d,]+)\s*(?:results?|assets?|images?)',
                r'(?:of|showing)\s*([\d,]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    count = int(match.group(1).replace(",", ""))
                    if count > 0:
                        return count
            
            # Try JSON in page source
            page_source = self.driver.page_source
            json_patterns = [
                r'"nb_results":\s*(\d+)',
                r'"totalResults":\s*(\d+)',
                r'"total_count":\s*(\d+)',
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, page_source)
                if match:
                    return int(match.group(1))
                    
        except Exception as e:
            logger.warning(f"Could not extract total results: {e}")
        
        return 0
    
    def _extract_search_assets(self, max_results: int) -> List[Dict[str, Any]]:
        """Extract assets from search results"""
        assets = []
        
        try:
            selectors = [
                "[data-testid='search-result-item']",
                "[class*='AssetCard']",
                "div[class*='search-result']",
            ]
            
            items = []
            for selector in selectors:
                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    break
            
            if not items:
                items = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/images/']")
            
            for i, item in enumerate(items[:max_results]):
                try:
                    asset = {
                        "position": i + 1,
                        "asset_id": None,
                        "asset_url": None,
                        "title": None,
                        "thumbnail_url": None,
                        "contributor_id": None,
                        "contributor_name": None,
                        "asset_type": "photo",
                        "is_premium": False,
                        "is_editorial": False,
                        "is_ai_generated": False,
                    }
                    
                    # Get asset ID and URL
                    links = item.find_elements(By.CSS_SELECTOR, "a[href*='/images/'], a[href*='/video/']")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        match = re.search(r'/(images|video)/[^/]*/(\d+)', href)
                        if match:
                            asset["asset_type"] = "video" if match.group(1) == "video" else "photo"
                            asset["asset_id"] = match.group(2)
                            asset["asset_url"] = href
                            break
                    
                    if not asset["asset_id"]:
                        continue
                    
                    # Get title and thumbnail
                    imgs = item.find_elements(By.CSS_SELECTOR, "img")
                    for img in imgs:
                        alt = img.get_attribute("alt") or ""
                        if alt and len(alt) > 2:
                            asset["title"] = alt
                        src = img.get_attribute("src") or ""
                        if "ftcdn" in src:
                            asset["thumbnail_url"] = src
                        if asset["title"]:
                            break
                    
                    # Get contributor
                    contrib_links = item.find_elements(By.CSS_SELECTOR, "a[href*='/contributor/']")
                    for link in contrib_links:
                        href = link.get_attribute("href") or ""
                        match = re.search(r'/contributor/(\d+)', href)
                        if match:
                            asset["contributor_id"] = match.group(1)
                            asset["contributor_name"] = link.text.strip() or None
                            break
                    
                    # Check flags
                    item_html = item.get_attribute("innerHTML") or ""
                    item_html_lower = item_html.lower()
                    asset["is_premium"] = "premium" in item_html_lower
                    asset["is_editorial"] = "editorial" in item_html_lower
                    asset["is_ai_generated"] = "ai generated" in item_html_lower or "generative" in item_html_lower
                    
                    assets.append(asset)
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not extract search assets: {e}")
        
        return assets
    
    def _extract_related_searches(self) -> List[str]:
        """Extract related search suggestions"""
        related = []
        
        try:
            selectors = [
                "[class*='RelatedSearch'] a",
                "[class*='related-search'] a",
                "a[href*='/search?k=']",
            ]
            
            seen = set()
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements[:20]:
                    try:
                        text = el.text.strip()
                        if text and len(text) > 1 and len(text) < 50 and text.lower() not in seen:
                            seen.add(text.lower())
                            related.append(text)
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"Could not extract related searches: {e}")
        
        return related[:15]
    
    def _extract_filter_categories(self) -> List[Dict[str, Any]]:
        """Extract categories from filters"""
        categories = []
        
        try:
            selectors = [
                "[class*='CategoryFilter'] a",
                "a[href*='filters[category]']",
                "[class*='category'] a",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements[:20]:
                    try:
                        text = el.text.strip()
                        if text:
                            count_match = re.search(r'\((\d+)\)', text)
                            name = re.sub(r'\s*\(\d+\)\s*', '', text).strip()
                            if name:
                                categories.append({
                                    "name": name,
                                    "count": int(count_match.group(1)) if count_match else None,
                                })
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"Could not extract categories: {e}")
        
        return categories[:15]
    
    def _extract_available_filters(self) -> Dict[str, List[str]]:
        """Extract available filter options"""
        filters = {
            "content_types": [],
            "orientations": [],
            "colors": [],
            "people": [],
        }
        
        try:
            # Look for filter sections
            page_source = self.driver.page_source
            
            # Content types
            content_patterns = ["photo", "vector", "illustration", "video", "template", "3d", "audio"]
            for ct in content_patterns:
                if re.search(rf'\b{ct}s?\b', page_source, re.IGNORECASE):
                    filters["content_types"].append(ct)
            
            # Orientations
            orient_patterns = ["horizontal", "vertical", "square", "panoramic"]
            for o in orient_patterns:
                if re.search(rf'\b{o}\b', page_source, re.IGNORECASE):
                    filters["orientations"].append(o)
                    
        except Exception as e:
            logger.warning(f"Could not extract filters: {e}")
        
        return filters
    
    def _scrape_asset_details(self, assets: List[Dict], use_parallel: bool = False, max_workers: int = 3) -> List[Dict[str, Any]]:
        """Scrape detailed information for each asset - supports parallel scraping"""
        
        if use_parallel and len(assets) > 5:
            return self._scrape_asset_details_parallel(assets, max_workers)
        
        # Sequential scraping (original method)
        details = []
        total = len(assets)
        
        for i, asset in enumerate(assets):
            if not asset.get("asset_url"):
                continue
            
            try:
                logger.info(f"Scraping asset {i+1}/{total}: {asset.get('asset_id')}")
                detail = self._scrape_single_asset_detail(asset)
                details.append(detail)
                
                if i < len(assets) - 1:
                    self._random_delay(0.5, 1.5)  # Reduced delay
                    
            except Exception as e:
                logger.warning(f"Error scraping asset {asset.get('asset_id')}: {e}")
                details.append({**asset, "error": str(e)})
        
        return details
    
    def _scrape_asset_details_parallel(self, assets: List[Dict], max_workers: int = 3) -> List[Dict[str, Any]]:
        """Scrape asset details using multiple browser instances in parallel"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        total = len(assets)
        logger.info(f"Starting parallel scraping of {total} assets with {max_workers} workers")
        
        # Split assets into chunks for each worker
        def chunk_list(lst, n):
            chunk_size = max(1, len(lst) // n)
            chunks = []
            for i in range(0, len(lst), chunk_size):
                chunks.append(lst[i:i + chunk_size])
            return chunks[:n]  # Ensure we don't exceed n chunks
        
        chunks = chunk_list(assets, max_workers)
        all_details = []
        
        def scrape_chunk(chunk_assets, worker_id):
            """Scrape a chunk of assets with a dedicated browser"""
            chunk_details = []
            driver = None
            
            try:
                # Create a new browser instance for this worker
                options = Options()
                if self.headless:
                    options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                options.add_argument(f"--user-agent={get_user_agent()}")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                
                chromedriver_path = find_chromedriver()
                if chromedriver_path:
                    service = Service(chromedriver_path)
                    driver = webdriver.Chrome(service=service, options=options)
                else:
                    driver = webdriver.Chrome(options=options)
                
                driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
                
                for i, asset in enumerate(chunk_assets):
                    if not asset.get("asset_url"):
                        continue
                    
                    try:
                        detail = self._scrape_single_asset_with_driver(driver, asset)
                        chunk_details.append(detail)
                        logger.info(f"Worker {worker_id}: Scraped {i+1}/{len(chunk_assets)} - {asset.get('asset_id')}")
                        
                        if i < len(chunk_assets) - 1:
                            time.sleep(random.uniform(0.5, 1.5))
                            
                    except Exception as e:
                        logger.warning(f"Worker {worker_id}: Error scraping {asset.get('asset_id')}: {e}")
                        chunk_details.append({**asset, "error": str(e)})
                        
            except Exception as e:
                logger.error(f"Worker {worker_id} failed to initialize: {e}")
                # Return assets as-is with error
                for asset in chunk_assets:
                    chunk_details.append({**asset, "error": f"Worker failed: {e}"})
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
            
            return chunk_details
        
        # Execute parallel scraping
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(scrape_chunk, chunk, i): i 
                for i, chunk in enumerate(chunks)
            }
            
            for future in as_completed(futures):
                worker_id = futures[future]
                try:
                    chunk_results = future.result()
                    all_details.extend(chunk_results)
                    logger.info(f"Worker {worker_id} completed with {len(chunk_results)} results")
                except Exception as e:
                    logger.error(f"Worker {worker_id} raised exception: {e}")
        
        logger.info(f"Parallel scraping complete: {len(all_details)} assets scraped")
        return all_details
    
    def _scrape_single_asset_with_driver(self, driver, asset: Dict) -> Dict[str, Any]:
        """Scrape a single asset using a provided driver instance (for parallel scraping)"""
        detail = {**asset}
        
        try:
            driver.get(asset["asset_url"])
            time.sleep(random.uniform(1, 2))
            
            # Wait for page to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
                time.sleep(0.5)
            except TimeoutException:
                detail["error"] = "Page load timeout"
                return detail
            
            page_text = driver.find_element(By.TAG_NAME, "body").text
            page_source = driver.page_source.lower()
            
            # ========== CONTRIBUTOR EXTRACTION ==========
            contributor_selectors = [
                "a[href*='/contributor/']",
            ]
            
            for selector in contributor_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        href = el.get_attribute("href") or ""
                        contrib_match = re.search(r'/contributor/(\d+)', href)
                        if contrib_match:
                            detail["contributor_id"] = contrib_match.group(1)
                            name = el.text.strip()
                            if name and len(name) > 1 and len(name) < 100:
                                detail["contributor_name"] = name
                            detail["contributor_url"] = href
                            break
                    if detail.get("contributor_id"):
                        break
                except:
                    continue
            
            # ========== PRICE EXTRACTION ==========
            price_patterns = [
                r'(?:buy|download|license|price)[^$]*\$(\d+(?:\.\d{2})?)',
                r'from\s+\$(\d+(?:\.\d{2})?)',
                r'\$(\d+(?:\.\d{2})?)\s*(?:USD|for)',
            ]
            for pattern in price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        price_val = float(match.group(1))
                        if 5 <= price_val <= 500:
                            detail["price"] = price_val
                            break
                    except:
                        continue
            
            # ========== CONTENT TYPE FLAGS ==========
            # Premium
            detail["is_premium"] = any(ind in page_source for ind in [
                "class=\"premium", "premium-badge", "data-premium=\"true\""
            ])
            
            # Editorial
            detail["is_editorial"] = any(ind in page_source for ind in [
                "editorial-badge", "editorial use only", "for editorial use"
            ])
            
            # AI Generated
            detail["is_ai_generated"] = any(ind in page_source for ind in [
                "ai-generated-badge", "aiGenerated", '"isAiGenerated":true'
            ])
            
            # ========== KEYWORDS ==========
            keywords = []
            try:
                kw_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='k=']")[:20]
                for el in kw_elements:
                    text = el.text.strip()
                    if text and len(text) > 1 and len(text) < 50:
                        keywords.append(text)
            except:
                pass
            detail["keywords"] = keywords[:15]
            
            # ========== DIMENSIONS ==========
            dim_match = re.search(r'(\d{3,5})\s*[x×]\s*(\d{3,5})', page_text)
            if dim_match:
                detail["width"] = int(dim_match.group(1))
                detail["height"] = int(dim_match.group(2))
                detail["orientation"] = "horizontal" if detail["width"] > detail["height"] else \
                                        "vertical" if detail["height"] > detail["width"] else "square"
            
            # ========== UPLOAD DATE ==========
            date_patterns = [
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    detail["upload_date"] = match.group(1)
                    break
            
            # ========== SIMILAR ASSETS ==========
            similar_ids = []
            try:
                similar_links = driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='similar'] a[href*='/images/'], [class*='related'] a[href*='/images/']")[:10]
                for link in similar_links:
                    href = link.get_attribute("href") or ""
                    match = re.search(r'/images/[^/]*/(\d+)', href)
                    if match and match.group(1) != asset.get("asset_id"):
                        similar_ids.append(match.group(1))
            except:
                pass
            detail["similar_asset_ids"] = list(set(similar_ids))[:5]
            
        except Exception as e:
            detail["error"] = str(e)
        
        return detail
    
    def _scrape_single_asset_detail(self, asset: Dict) -> Dict[str, Any]:
        """Scrape detailed information for a single asset - ENHANCED VERSION"""
        detail = {**asset}
        
        try:
            self.driver.get(asset["asset_url"])
            self._random_delay(1.5, 3)
            
            # Wait for page to fully load
            try:
                WebDriverWait(self.driver, 12).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
                # Wait a bit more for dynamic content
                time.sleep(1)
            except TimeoutException:
                detail["error"] = "Page load timeout"
                return detail
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            page_source = self.driver.page_source.lower()
            
            # ========== CONTRIBUTOR EXTRACTION (CRITICAL) ==========
            # This is the main fix - extract contributor from detail page
            contributor_selectors = [
                "a[href*='/contributor/'][class*='author']",
                "a[href*='/contributor/'][class*='Artist']",
                "a[href*='/contributor/'][class*='creator']",
                "[class*='contributor'] a[href*='/contributor/']",
                "[class*='author'] a[href*='/contributor/']",
                "[class*='by-line'] a[href*='/contributor/']",
                "[class*='artist'] a[href*='/contributor/']",
                "a[href*='/contributor/']",  # Fallback - any contributor link
            ]
            
            for selector in contributor_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        href = el.get_attribute("href") or ""
                        contrib_match = re.search(r'/contributor/(\d+)', href)
                        if contrib_match:
                            detail["contributor_id"] = contrib_match.group(1)
                            # Get contributor name from link text or nearby
                            name = el.text.strip()
                            if name and len(name) > 1 and len(name) < 100:
                                detail["contributor_name"] = name
                            detail["contributor_url"] = href
                            break
                    if detail.get("contributor_id"):
                        break
                except:
                    continue
            
            # ========== PRICE EXTRACTION (ENHANCED) ==========
            # Adobe Stock shows pricing in various formats, try multiple approaches
            price_selectors = [
                "[data-t='price']",
                "[class*='Price'] [class*='amount']",
                "[class*='price-amount']",
                "[class*='LicensePrice']",
                "[class*='license-price']",
                "[class*='asset-price']",
                "[class*='buy-button'] span",
                "[class*='price'] span",
            ]
            
            for selector in price_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        text = el.text.strip()
                        # Match price patterns like $29.99, $299, etc
                        price_match = re.search(r'\$(\d+(?:\.\d{2})?)', text)
                        if price_match:
                            detail["price"] = float(price_match.group(1))
                            break
                    if detail.get("price"):
                        break
                except:
                    continue
            
            # Fallback: search in page text for price patterns
            if not detail.get("price"):
                # Look for standard Adobe Stock price patterns in page text
                # Be more specific to avoid matching random numbers
                price_patterns = [
                    r'(?:buy|download|license|price)[^$]*\$(\d+(?:\.\d{2})?)',
                    r'(?:standard|extended)[^$]*\$(\d+(?:\.\d{2})?)',
                    r'from\s+\$(\d+(?:\.\d{2})?)',
                    r'\$(\d+(?:\.\d{2})?)\s*(?:USD|for)',
                    r'(\d+)\s*credits?\s*(?:or|\|)\s*\$(\d+(?:\.\d{2})?)',
                ]
                for pattern in price_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        # Get the last group (actual price)
                        price_str = match.groups()[-1] if match.groups() else match.group(1)
                        try:
                            price_val = float(price_str)
                            # Sanity check - Adobe Stock prices typically range $9.99 - $499
                            if 5 <= price_val <= 500:
                                detail["price"] = price_val
                                break
                        except:
                            continue
            
            # Extract credits
            credits_patterns = [
                r'(\d+)\s*credits?',
                r'credits?[:\s]+(\d+)',
            ]
            for pattern in credits_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    detail["credits"] = int(match.group(1))
                    break
            
            # ========== PREMIUM/EDITORIAL/AI DETECTION (ACCURATE) ==========
            # Check for actual badges and indicators, not just text mentions
            
            # Premium detection
            premium_indicators = [
                "class=\"premium",
                "class='premium",
                "premium-badge",
                "premium-icon",
                "data-premium=\"true\"",
                "ispremium",
            ]
            detail["is_premium"] = any(ind in page_source for ind in premium_indicators)
            
            # Also check visible text for Premium label
            if not detail["is_premium"]:
                try:
                    premium_badges = self.driver.find_elements(By.CSS_SELECTOR, 
                        "[class*='premium'], [class*='Premium'], [data-testid*='premium']")
                    detail["is_premium"] = len(premium_badges) > 0
                except:
                    pass
            
            # Editorial detection - more specific
            editorial_indicators = [
                "editorial-badge",
                "editorial-icon",
                "class=\"editorial",
                "class='editorial",
                "editorial use only",
                "for editorial use",
                "iseditorial",
            ]
            detail["is_editorial"] = any(ind in page_source for ind in editorial_indicators)
            
            # AI Generated detection - more specific to avoid false positives
            # Only flag if explicit AI/generated badge indicators present
            ai_indicators = [
                "ai-generated-badge",
                "aiGenerated",  # camelCase class names
                "ai_generated",  # snake_case
                'class="ai-generated',
                "class='ai-generated",
                "generated-by-ai",
                "data-ai-generated",
                '"isAiGenerated":true',
                "generative-ai-badge",
            ]
            detail["is_ai_generated"] = any(ind in page_source for ind in ai_indicators)
            
            # Additional check for visible AI badge
            if not detail["is_ai_generated"]:
                try:
                    ai_badges = self.driver.find_elements(By.CSS_SELECTOR, 
                        "[class*='ai-generated'], [class*='AiGenerated'], [data-ai-generated='true']")
                    detail["is_ai_generated"] = len(ai_badges) > 0
                except:
                    pass
            
            # ========== KEYWORDS EXTRACTION ==========
            detail["keywords"] = self._extract_asset_keywords()
            
            # ========== DIMENSIONS ==========
            dim_patterns = [
                r'(\d{3,5})\s*[x×]\s*(\d{3,5})\s*(?:px|pixels)?',
                r'(\d{3,5})\s*by\s*(\d{3,5})',
            ]
            for pattern in dim_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    detail["width"] = int(match.group(1))
                    detail["height"] = int(match.group(2))
                    detail["orientation"] = "horizontal" if detail["width"] > detail["height"] else \
                                            "vertical" if detail["height"] > detail["width"] else "square"
                    break
            
            # ========== UPLOAD DATE ==========
            date_patterns = [
                r'(?:uploaded|created|added|date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})',
                r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    detail["upload_date"] = match.group(1)
                    break
            
            # ========== SIMILAR ASSETS ==========
            similar_selectors = [
                "[class*='similar'] a[href*='/images/']",
                "[class*='Similar'] a[href*='/images/']",
                "[class*='related'] a[href*='/images/']",
                "[class*='recommend'] a[href*='/images/']",
                "[data-testid*='similar'] a[href*='/images/']",
            ]
            
            similar_ids = []
            for selector in similar_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links[:15]:
                        href = link.get_attribute("href") or ""
                        match = re.search(r'/images/[^/]*/(\d+)', href)
                        if match and match.group(1) != asset.get("asset_id"):
                            similar_ids.append(match.group(1))
                    if similar_ids:
                        break
                except:
                    continue
            
            detail["similar_asset_ids"] = list(set(similar_ids))[:10]
            
            # ========== LICENSE INFO ==========
            detail["has_model_release"] = "model release" in page_text.lower()
            detail["has_property_release"] = "property release" in page_text.lower()
            
            # License type
            if "extended license" in page_text.lower():
                detail["license_type"] = "Extended"
            elif "standard license" in page_text.lower():
                detail["license_type"] = "Standard"
            else:
                detail["license_type"] = "Standard"  # Default
            
            # ========== FILE FORMAT ==========
            format_match = re.search(r'\b(JPEG|JPG|PNG|EPS|AI|SVG|MP4|MOV|PSD|TIFF|RAW)\b', page_text, re.IGNORECASE)
            if format_match:
                detail["file_format"] = format_match.group(1).upper()
            
            # ========== DPI ==========
            dpi_match = re.search(r'(\d+)\s*(?:dpi|ppi)', page_text, re.IGNORECASE)
            if dpi_match:
                detail["dpi"] = int(dpi_match.group(1))
            
            # ========== DOWNLOADS COUNT (if available) ==========
            downloads_patterns = [
                r'(\d[\d,]*)\s*downloads?',
                r'downloaded\s*(\d[\d,]*)',
            ]
            for pattern in downloads_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    detail["downloads"] = int(match.group(1).replace(",", ""))
                    break
            
            logger.info(f"Asset {asset.get('asset_id')}: contributor={detail.get('contributor_id')}, price=${detail.get('price')}, premium={detail.get('is_premium')}")
            
        except Exception as e:
            logger.warning(f"Error in asset detail scraping: {e}")
            detail["error"] = str(e)
        
        return detail
    
    def _extract_asset_keywords(self) -> List[str]:
        """Extract keywords from asset page"""
        keywords = []
        
        try:
            selectors = [
                "a[href*='k=']",
                "[class*='keyword'] a",
                "[class*='tag'] a",
            ]
            
            seen = set()
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements[:50]:
                    try:
                        text = el.text.strip()
                        if text and len(text) > 1 and len(text) < 50 and text.lower() not in seen:
                            seen.add(text.lower())
                            keywords.append(text)
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"Could not extract keywords: {e}")
        
        return keywords[:30]
    
    def _extract_unique_contributors(self, assets: List[Dict]) -> List[str]:
        """Extract unique contributor IDs from assets - checks both search results and detail pages"""
        contributors = []
        seen = set()
        
        for asset in assets:
            cid = asset.get("contributor_id")
            if cid and cid not in seen:
                seen.add(cid)
                contributors.append(cid)
        
        logger.info(f"Found {len(contributors)} unique contributors from {len(assets)} assets")
        return contributors
    
    def _scrape_contributor_profiles(self, contributor_ids: List[str]) -> List[Dict[str, Any]]:
        """Scrape profiles for multiple contributors - ENHANCED VERSION"""
        profiles = []
        
        for i, cid in enumerate(contributor_ids):
            try:
                logger.info(f"Scraping contributor {i+1}/{len(contributor_ids)}: {cid}")
                profile = self._scrape_contributor_profile(cid)
                profiles.append(profile)
                self._random_delay(1.5, 3)
            except Exception as e:
                logger.warning(f"Error scraping contributor {cid}: {e}")
                profiles.append({"adobe_id": cid, "error": str(e)})
        
        return profiles
    
    def _scrape_contributor_profile(self, contributor_id: str) -> Dict[str, Any]:
        """Scrape a single contributor profile - ENHANCED VERSION with full portfolio analysis"""
        profile = {
            "adobe_id": contributor_id,
            "name": None,
            "profile_url": f"{CONTRIBUTOR_URL}/{contributor_id}",
            "portfolio_url": None,
            "total_assets": 0,
            "total_photos": 0,
            "total_vectors": 0,
            "total_videos": 0,
            "total_templates": 0,
            "total_3d": 0,
            "premium_count": 0,
            "premium_ratio": 0.0,
            "top_categories": [],
            "top_keywords": [],
            "category_distribution": {},
            "estimated_join_date": None,
            "upload_frequency_monthly": 0,
            "niches": [],
            "competition_level": "unknown",
            "sample_assets": [],
            "scraped_at": datetime.utcnow().isoformat(),
        }
        
        try:
            self.driver.get(profile["profile_url"])
            self._random_delay(2, 4)
            
            # Wait for page to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
                time.sleep(1.5)
            except TimeoutException:
                profile["error"] = "Page load timeout"
                return profile
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            page_source = self.driver.page_source.lower()
            
            # ========== NAME EXTRACTION ==========
            name_selectors = [
                "h1",
                "[class*='contributor-name']",
                "[class*='profile-name']",
                "[class*='artist-name']",
                "[class*='AuthorName']",
                "[class*='author-name']",
            ]
            for selector in name_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        text = el.text.strip()
                        # Filter out generic headers
                        if (text and len(text) > 1 and len(text) < 100 
                            and "Adobe" not in text and "Stock" not in text
                            and "Portfolio" not in text and "assets" not in text.lower()):
                            profile["name"] = text
                            break
                    if profile["name"]:
                        break
                except:
                    continue
            
            # ========== TOTAL ASSETS COUNT ==========
            # Look for various patterns
            count_patterns = [
                r'(\d[\d,]*)\s*(?:total\s*)?(?:assets?|items?|images?|works?)',
                r'(?:portfolio|collection)[:\s]+(\d[\d,]*)',
                r'showing\s+\d+\s*(?:of|from)\s*(\d[\d,]*)',
            ]
            
            for pattern in count_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    profile["total_assets"] = int(match.group(1).replace(",", ""))
                    break
            
            # ========== PORTFOLIO BREAKDOWN BY TYPE ==========
            # Look for tabs or filters with counts
            type_patterns = {
                "photos": [r'photos?\s*[:\(]?\s*(\d[\d,]*)', r'(\d[\d,]*)\s*photos?'],
                "vectors": [r'vectors?\s*[:\(]?\s*(\d[\d,]*)', r'(\d[\d,]*)\s*vectors?', r'illustrations?\s*[:\(]?\s*(\d[\d,]*)'],
                "videos": [r'videos?\s*[:\(]?\s*(\d[\d,]*)', r'(\d[\d,]*)\s*videos?'],
                "templates": [r'templates?\s*[:\(]?\s*(\d[\d,]*)', r'(\d[\d,]*)\s*templates?'],
                "3d": [r'3d\s*[:\(]?\s*(\d[\d,]*)', r'(\d[\d,]*)\s*3d'],
            }
            
            for type_name, patterns in type_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        count = int(match.group(1).replace(",", ""))
                        profile[f"total_{type_name}"] = count
                        break
            
            # ========== PREMIUM CONTENT DETECTION ==========
            # Look for visible premium badges in portfolio
            try:
                premium_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='premium'], [class*='Premium'], [data-premium='true']")
                profile["premium_count"] = len(premium_elements)
            except:
                pass
            
            # Estimate premium ratio from visible items
            try:
                all_items = self.driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='AssetCard'], [class*='asset-card'], a[href*='/images/']")
                visible_count = len(all_items)
                if visible_count > 0:
                    profile["premium_ratio"] = profile["premium_count"] / visible_count
            except:
                pass
            
            # ========== SAMPLE ASSETS ==========
            # Collect info about visible assets for niche detection
            sample_assets = []
            try:
                asset_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/images/']")[:20]
                for link in asset_links:
                    try:
                        href = link.get_attribute("href") or ""
                        match = re.search(r'/images/[^/]*/(\d+)', href)
                        if match:
                            # Try to get title from nearby img
                            title = None
                            try:
                                img = link.find_element(By.CSS_SELECTOR, "img")
                                title = img.get_attribute("alt")
                            except:
                                pass
                            
                            sample_assets.append({
                                "asset_id": match.group(1),
                                "url": href,
                                "title": title,
                            })
                    except:
                        continue
                profile["sample_assets"] = sample_assets
            except:
                pass
            
            # ========== TOP KEYWORDS FROM SAMPLE ASSETS ==========
            keywords_from_titles = []
            for asset in profile["sample_assets"]:
                if asset.get("title"):
                    words = asset["title"].lower().split()
                    keywords_from_titles.extend([w for w in words if len(w) > 3 and w.isalpha()])
            
            # Count keyword frequency
            keyword_counts = {}
            for kw in keywords_from_titles:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
            
            # Get top keywords
            sorted_kw = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
            profile["top_keywords"] = [kw for kw, _ in sorted_kw[:10]]
            
            # ========== NICHE DETECTION ==========
            # Determine niches based on top keywords and categories
            niche_indicators = {
                "technology": ["computer", "laptop", "phone", "digital", "tech", "software", "device"],
                "business": ["office", "business", "corporate", "meeting", "professional", "team"],
                "nature": ["nature", "landscape", "forest", "mountain", "ocean", "sky", "tree"],
                "lifestyle": ["people", "lifestyle", "happy", "family", "friends", "smile"],
                "food": ["food", "cooking", "restaurant", "meal", "kitchen", "delicious"],
                "travel": ["travel", "vacation", "tourism", "destination", "adventure"],
                "health": ["health", "fitness", "medical", "wellness", "healthcare"],
                "abstract": ["abstract", "pattern", "texture", "background", "geometric"],
            }
            
            detected_niches = []
            for niche, indicators in niche_indicators.items():
                score = sum(1 for kw in profile["top_keywords"] if any(ind in kw for ind in indicators))
                if score >= 2:
                    detected_niches.append(niche)
            profile["niches"] = detected_niches[:5]
            
            # ========== COMPETITION LEVEL ==========
            total = profile["total_assets"]
            premium_ratio = profile["premium_ratio"]
            
            if total >= 10000 and premium_ratio >= 0.2:
                profile["competition_level"] = "very_high"
            elif total >= 5000 or (total >= 1000 and premium_ratio >= 0.3):
                profile["competition_level"] = "high"
            elif total >= 1000 or (total >= 500 and premium_ratio >= 0.2):
                profile["competition_level"] = "medium"
            elif total >= 100:
                profile["competition_level"] = "low"
            else:
                profile["competition_level"] = "very_low"
            
            # ========== FALLBACK: Count visible items if total is 0 ==========
            if profile["total_assets"] == 0:
                try:
                    items = self.driver.find_elements(By.CSS_SELECTOR, 
                        "[class*='AssetCard'], [class*='asset-card'], a[href*='/images/']")
                    # Estimate total based on visible items (usually shows 20-30 per page)
                    profile["total_assets"] = len(items) * 10 if items else 0
                except:
                    pass
            
            logger.info(f"Contributor {contributor_id}: name={profile['name']}, assets={profile['total_assets']}, premium_ratio={profile['premium_ratio']:.2%}")
            
        except Exception as e:
            logger.warning(f"Error scraping contributor profile: {e}")
            profile["error"] = str(e)
        
        return profile
    
    def _scrape_similar_assets(self, asset_details: List[Dict], max_per_asset: int) -> List[Dict[str, Any]]:
        """Scrape similar assets for market network analysis - ENHANCED with price extraction"""
        similar = []
        seen_ids = set()
        
        # Collect all similar asset IDs first
        all_similar_ids = []
        for asset in asset_details:
            similar_ids = asset.get("similar_asset_ids", [])[:max_per_asset]
            for sid in similar_ids:
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    all_similar_ids.append({
                        "asset_id": sid,
                        "related_to": asset.get("asset_id"),
                    })
        
        # Limit total similar assets to scrape
        max_similar_total = min(len(all_similar_ids), 30)
        similar_to_scrape = all_similar_ids[:max_similar_total]
        
        logger.info(f"Scraping {len(similar_to_scrape)} similar assets for price comparison...")
        
        for i, sim_info in enumerate(similar_to_scrape):
            sid = sim_info["asset_id"]
            
            try:
                url = f"{BASE_URL}/images/asset/{sid}"
                
                # Navigate to similar asset page for price extraction
                self.driver.get(url)
                self._random_delay(1, 2)
                
                similar_asset = {
                    "asset_id": sid,
                    "asset_url": url,
                    "related_to": sim_info["related_to"],
                    "price": None,
                    "contributor_id": None,
                    "is_premium": False,
                }
                
                try:
                    WebDriverWait(self.driver, 6).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                    )
                    
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    page_source = self.driver.page_source.lower()
                    
                    # Extract price
                    price_match = re.search(r'\$(\d+(?:\.\d{2})?)', page_text)
                    if price_match:
                        similar_asset["price"] = float(price_match.group(1))
                    
                    # Extract contributor
                    contrib_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/contributor/']")
                    for link in contrib_links:
                        href = link.get_attribute("href") or ""
                        match = re.search(r'/contributor/(\d+)', href)
                        if match:
                            similar_asset["contributor_id"] = match.group(1)
                            break
                    
                    # Check premium
                    similar_asset["is_premium"] = "premium" in page_source
                    
                except TimeoutException:
                    similar_asset["error"] = "timeout"
                
                similar.append(similar_asset)
                
                if i % 5 == 0:
                    logger.info(f"Similar assets progress: {i+1}/{len(similar_to_scrape)}")
                
            except Exception as e:
                logger.warning(f"Error with similar asset {sid}: {e}")
        
        return similar
    
    def _analyze_market(self, analysis: Dict) -> Dict[str, Any]:
        """Analyze market dynamics from collected data - ENHANCED VERSION"""
        
        # Use detailed assets if available, else fall back to search results
        assets = analysis.get("asset_details", []) or analysis.get("assets", [])
        similar_assets = analysis.get("similar_assets", [])
        contributor_profiles = analysis.get("contributor_profiles", [])
        
        # Combine assets for contributor counting
        all_asset_sources = assets + similar_assets
        
        # Count unique contributors from all sources
        all_contributor_ids = set()
        for a in all_asset_sources:
            cid = a.get("contributor_id")
            if cid:
                all_contributor_ids.add(cid)
        
        market = {
            "total_results": analysis["search_results"].get("nb_results", 0),
            "sample_size": len(assets),
            "unique_contributors": len(all_contributor_ids),
            "premium_ratio": 0.0,
            "editorial_ratio": 0.0,
            "ai_generated_ratio": 0.0,
            "price_analysis": {},
            "price_distribution": [],
            "dimension_analysis": {},
            "upload_date_analysis": {},
            "keyword_frequency": {},
            "contributor_concentration": 0.0,
            "contributor_analysis": {},
            "format_distribution": {},
            "content_type_distribution": {},
        }
        
        if not assets:
            return market
        
        # ========== CONTENT TYPE RATIOS ==========
        premium_count = sum(1 for a in assets if a.get("is_premium"))
        editorial_count = sum(1 for a in assets if a.get("is_editorial"))
        ai_count = sum(1 for a in assets if a.get("is_ai_generated"))
        
        market["premium_ratio"] = premium_count / len(assets) if assets else 0
        market["editorial_ratio"] = editorial_count / len(assets) if assets else 0
        market["ai_generated_ratio"] = ai_count / len(assets) if assets else 0
        
        # Standard = not premium, not editorial, not AI
        standard_count = len(assets) - premium_count - editorial_count
        market["content_type_distribution"] = {
            "premium": premium_count,
            "editorial": editorial_count,
            "ai_generated": ai_count,
            "standard": max(0, len(assets) - premium_count),
        }
        
        # ========== PRICE ANALYSIS (Enhanced) ==========
        # Collect prices from both main assets and similar assets
        all_prices = []
        for a in assets:
            if a.get("price"):
                all_prices.append(a["price"])
        for a in similar_assets:
            if a.get("price"):
                all_prices.append(a["price"])
        
        if all_prices:
            sorted_prices = sorted(all_prices)
            market["price_analysis"] = {
                "min": min(all_prices),
                "max": max(all_prices),
                "avg": sum(all_prices) / len(all_prices),
                "median": sorted_prices[len(sorted_prices) // 2],
                "count": len(all_prices),
            }
            
            # Price distribution buckets
            price_buckets = {
                "Under $25": 0,
                "$25-$50": 0,
                "$50-$100": 0,
                "$100-$200": 0,
                "Over $200": 0,
            }
            for p in all_prices:
                if p < 25:
                    price_buckets["Under $25"] += 1
                elif p < 50:
                    price_buckets["$25-$50"] += 1
                elif p < 100:
                    price_buckets["$50-$100"] += 1
                elif p < 200:
                    price_buckets["$100-$200"] += 1
                else:
                    price_buckets["Over $200"] += 1
            
            market["price_distribution"] = [
                {"range": k, "count": v, "percentage": round(v / len(all_prices) * 100, 1)}
                for k, v in price_buckets.items() if v > 0
            ]
        
        # ========== DIMENSION ANALYSIS ==========
        dimensions = [(a.get("width"), a.get("height")) for a in assets if a.get("width") and a.get("height")]
        if dimensions:
            widths = [d[0] for d in dimensions]
            heights = [d[1] for d in dimensions]
            market["dimension_analysis"] = {
                "avg_width": round(sum(widths) / len(widths)),
                "avg_height": round(sum(heights) / len(heights)),
                "orientations": {
                    "horizontal": sum(1 for w, h in dimensions if w > h),
                    "vertical": sum(1 for w, h in dimensions if h > w),
                    "square": sum(1 for w, h in dimensions if w == h),
                },
            }
        
        # ========== KEYWORD FREQUENCY ==========
        all_keywords = []
        for asset in assets:
            keywords = asset.get("keywords", [])
            if isinstance(keywords, list):
                all_keywords.extend(keywords)
        
        keyword_counts = {}
        for kw in all_keywords:
            if isinstance(kw, str):
                kw_lower = kw.lower().strip()
                if len(kw_lower) > 2:  # Filter very short keywords
                    keyword_counts[kw_lower] = keyword_counts.get(kw_lower, 0) + 1
        
        market["keyword_frequency"] = dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:30])
        
        # ========== CONTRIBUTOR ANALYSIS (Enhanced) ==========
        contributor_counts = {}
        for asset in assets:
            cid = asset.get("contributor_id")
            if cid:
                contributor_counts[cid] = contributor_counts.get(cid, 0) + 1
        
        # Add contributors from similar assets
        for asset in similar_assets:
            cid = asset.get("contributor_id")
            if cid and cid not in contributor_counts:
                contributor_counts[cid] = 1
        
        market["unique_contributors"] = len(contributor_counts)
        
        if contributor_counts:
            sorted_counts = sorted(contributor_counts.values(), reverse=True)
            total_count = sum(sorted_counts)
            top_5_share = sum(sorted_counts[:5]) / total_count if total_count > 0 else 0
            market["contributor_concentration"] = top_5_share
            
            # Build contributor analysis with profile data
            top_contributors = []
            sorted_contributors = sorted(contributor_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            for cid, count in sorted_contributors:
                # Find profile if we have it
                profile = next((p for p in contributor_profiles if str(p.get("adobe_id")) == str(cid)), None)
                
                contrib_info = {
                    "contributor_id": cid,
                    "assets_in_results": count,
                    "market_share": round(count / total_count * 100, 1) if total_count > 0 else 0,
                }
                
                if profile and not profile.get("error"):
                    contrib_info.update({
                        "name": profile.get("name"),
                        "total_portfolio": profile.get("total_assets", 0),
                        "premium_ratio": profile.get("premium_ratio", 0),
                        "competition_level": profile.get("competition_level", "unknown"),
                        "niches": profile.get("niches", []),
                    })
                
                top_contributors.append(contrib_info)
            
            market["contributor_analysis"] = {
                "total_unique": len(contributor_counts),
                "top_contributors": top_contributors,
                "concentration_top5": round(top_5_share * 100, 1),
                "avg_assets_per_contributor": round(total_count / len(contributor_counts), 1) if contributor_counts else 0,
            }
        
        # ========== FORMAT DISTRIBUTION ==========
        format_counts = {}
        for asset in assets:
            fmt = asset.get("file_format", "Unknown")
            if fmt:
                format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        market["format_distribution"] = format_counts
        
        # ========== UPLOAD DATE ANALYSIS ==========
        dates = []
        for asset in assets:
            date_str = asset.get("upload_date")
            if date_str:
                dates.append(date_str)
        
        if dates:
            market["upload_date_analysis"] = {
                "assets_with_dates": len(dates),
                "date_coverage": round(len(dates) / len(assets) * 100, 1) if assets else 0,
            }
        
        logger.info(f"Market analysis: {market['unique_contributors']} contributors, "
                   f"premium_ratio={market['premium_ratio']:.1%}, "
                   f"prices={market['price_analysis'].get('count', 0)} collected")
        
        return market
    
    def _calculate_enhanced_scores(self, analysis: Dict) -> Dict[str, Any]:
        """Calculate enhanced opportunity scores"""
        market = analysis["market_analysis"]
        
        nb_results = market.get("total_results", 0)
        unique_contributors = market.get("unique_contributors", 0)
        sample_size = market.get("sample_size", 20)
        premium_ratio = market.get("premium_ratio", 0)
        contributor_concentration = market.get("contributor_concentration", 0.5)
        
        # Enhanced Demand Score
        if nb_results >= 1000000:
            demand_score = 95 + min((nb_results - 1000000) / 10000000 * 5, 5)
        elif nb_results >= 100000:
            demand_score = 80 + (nb_results - 100000) / 900000 * 15
        elif nb_results >= 10000:
            demand_score = 60 + (nb_results - 10000) / 90000 * 20
        elif nb_results >= 1000:
            demand_score = 40 + (nb_results - 1000) / 9000 * 20
        elif nb_results >= 100:
            demand_score = 20 + (nb_results - 100) / 900 * 20
        elif nb_results > 0:
            demand_score = nb_results / 100 * 20
        else:
            demand_score = 0
        
        # Adjust demand based on premium ratio (higher premium = proven demand)
        demand_score = demand_score * 0.8 + premium_ratio * 100 * 0.2
        
        # Enhanced Competition Score
        if nb_results >= 1000000:
            base_competition = 90 + min((nb_results - 1000000) / 10000000 * 10, 10)
        elif nb_results >= 100000:
            base_competition = 70 + (nb_results - 100000) / 900000 * 20
        elif nb_results >= 10000:
            base_competition = 50 + (nb_results - 10000) / 90000 * 20
        elif nb_results >= 1000:
            base_competition = 30 + (nb_results - 1000) / 9000 * 20
        elif nb_results >= 100:
            base_competition = 10 + (nb_results - 100) / 900 * 20
        else:
            base_competition = nb_results / 100 * 10 if nb_results > 0 else 0
        
        # Adjust for contributor diversity
        if unique_contributors > 0 and sample_size > 0:
            diversity = unique_contributors / sample_size
            diversity_factor = diversity * 20
            competition_score = base_competition * 0.6 + diversity_factor * 0.2 + premium_ratio * 100 * 0.2
        else:
            competition_score = base_competition
        
        competition_score = min(100, max(0, competition_score))
        
        # Gap Score based on contributor concentration
        # Lower concentration = more opportunity
        gap_score = (1 - contributor_concentration) * 100
        gap_score = max(10, min(100, gap_score))
        
        # Freshness Score from upload dates
        assets = analysis.get("asset_details", [])
        recent_count = sum(1 for a in assets if a.get("upload_date"))
        if assets:
            freshness_score = 40 + (recent_count / len(assets)) * 40
        else:
            freshness_score = 50
        
        # Quality Gap Score
        # Higher premium ratio = saturated with quality, less gap
        quality_gap = 100 - premium_ratio * 100
        quality_gap = max(10, min(100, quality_gap))
        
        # Final Opportunity Score
        opportunity_score = (
            demand_score * 0.30 +
            (100 - competition_score) * 0.25 +
            gap_score * 0.20 +
            freshness_score * 0.10 +
            quality_gap * 0.15
        )
        
        # Trend
        if demand_score > competition_score * 1.2 and demand_score >= 60:
            trend = "up"
        elif demand_score < competition_score * 0.8 or demand_score < 30:
            trend = "down"
        else:
            trend = "stable"
        
        # Urgency
        if opportunity_score >= 70:
            urgency = "high"
        elif opportunity_score >= 45:
            urgency = "medium"
        else:
            urgency = "low"
        
        return {
            "demand_score": round(demand_score, 2),
            "competition_score": round(competition_score, 2),
            "gap_score": round(gap_score, 2),
            "freshness_score": round(freshness_score, 2),
            "quality_gap_score": round(quality_gap, 2),
            "opportunity_score": round(opportunity_score, 2),
            "trend": trend,
            "urgency": urgency,
            "factors": {
                "premium_ratio": round(premium_ratio, 3),
                "contributor_concentration": round(contributor_concentration, 3),
                "unique_contributors": unique_contributors,
                "total_results": nb_results,
            }
        }
    
    def _generate_visualization_data(self, analysis: Dict) -> Dict[str, Any]:
        """Generate data formatted for frontend visualizations - ENHANCED VERSION"""
        market = analysis["market_analysis"]
        scoring = analysis["scoring"]
        assets = analysis.get("asset_details", []) or analysis.get("assets", [])
        contributor_profiles = analysis.get("contributor_profiles", [])
        
        viz = {
            "score_breakdown": {
                "labels": ["Demand", "Competition", "Gap", "Freshness", "Quality Gap"],
                "values": [
                    scoring.get("demand_score", 0),
                    scoring.get("competition_score", 0),
                    scoring.get("gap_score", 0),
                    scoring.get("freshness_score", 0),
                    scoring.get("quality_gap_score", 0),
                ],
            },
            "price_distribution": [],
            "format_distribution": [],
            "orientation_distribution": [],
            "content_type_distribution": [],
            "contributor_chart": [],
            "keyword_cloud": [],
            "freshness_timeline": [],
            "price_summary": {},
        }
        
        # ========== PRICE DISTRIBUTION ==========
        # Use actual price distribution from market analysis
        price_dist = market.get("price_distribution", [])
        if price_dist:
            viz["price_distribution"] = price_dist
        else:
            # Fallback: calculate from assets
            price_buckets = {"Under $25": 0, "$25-$50": 0, "$50-$100": 0, "$100-$200": 0, "Over $200": 0}
            prices = [a.get("price") for a in assets if a.get("price")]
            for p in prices:
                if p < 25:
                    price_buckets["Under $25"] += 1
                elif p < 50:
                    price_buckets["$25-$50"] += 1
                elif p < 100:
                    price_buckets["$50-$100"] += 1
                elif p < 200:
                    price_buckets["$100-$200"] += 1
                else:
                    price_buckets["Over $200"] += 1
            viz["price_distribution"] = [{"range": k, "count": v} for k, v in price_buckets.items() if v > 0]
        
        # Price summary for display
        price_analysis = market.get("price_analysis", {})
        if price_analysis:
            viz["price_summary"] = {
                "min": price_analysis.get("min"),
                "max": price_analysis.get("max"),
                "avg": round(price_analysis.get("avg", 0), 2),
                "median": price_analysis.get("median"),
                "sample_count": price_analysis.get("count", 0),
            }
        
        # ========== FORMAT DISTRIBUTION ==========
        for fmt, count in market.get("format_distribution", {}).items():
            if fmt and fmt != "Unknown":
                viz["format_distribution"].append({"name": fmt, "value": count})
        
        # ========== ORIENTATION DISTRIBUTION ==========
        dim_analysis = market.get("dimension_analysis", {})
        orientations = dim_analysis.get("orientations", {})
        for orient, count in orientations.items():
            if count > 0:
                viz["orientation_distribution"].append({"name": orient.capitalize(), "value": count})
        
        # ========== CONTENT TYPE DISTRIBUTION ==========
        content_types = market.get("content_type_distribution", {})
        if content_types:
            for ct, count in content_types.items():
                if count > 0:
                    viz["content_type_distribution"].append({
                        "name": ct.replace("_", " ").title(),
                        "value": count,
                    })
        else:
            # Calculate from market ratios
            sample_size = market.get("sample_size", 0)
            if sample_size > 0:
                viz["content_type_distribution"] = [
                    {"name": "Premium", "value": round(market.get("premium_ratio", 0) * sample_size)},
                    {"name": "Editorial", "value": round(market.get("editorial_ratio", 0) * sample_size)},
                    {"name": "AI Generated", "value": round(market.get("ai_generated_ratio", 0) * sample_size)},
                    {"name": "Standard", "value": round((1 - market.get("premium_ratio", 0)) * sample_size)},
                ]
        
        # ========== CONTRIBUTOR CHART ==========
        # Use contributor profiles for detailed chart
        for p in contributor_profiles[:10]:
            if not p.get("error"):
                viz["contributor_chart"].append({
                    "name": p.get("name") or f"Contributor {p.get('adobe_id', 'Unknown')[:8]}",
                    "adobe_id": p.get("adobe_id"),
                    "portfolio_size": p.get("total_assets", 0),
                    "premium_ratio": round(p.get("premium_ratio", 0), 3),
                    "competition_level": p.get("competition_level", "unknown"),
                    "niches": p.get("niches", []),
                })
        
        # If no profiles, use contributor analysis from market data
        if not viz["contributor_chart"]:
            contrib_analysis = market.get("contributor_analysis", {})
            top_contributors = contrib_analysis.get("top_contributors", [])
            for c in top_contributors[:10]:
                viz["contributor_chart"].append({
                    "name": c.get("name") or f"Contributor {str(c.get('contributor_id', 'Unknown'))[:8]}",
                    "adobe_id": c.get("contributor_id"),
                    "portfolio_size": c.get("total_portfolio", 0),
                    "premium_ratio": c.get("premium_ratio", 0),
                    "market_share": c.get("market_share", 0),
                    "assets_in_results": c.get("assets_in_results", 0),
                })
        
        # ========== KEYWORD CLOUD ==========
        keyword_freq = market.get("keyword_frequency", {})
        for kw, count in list(keyword_freq.items())[:30]:
            viz["keyword_cloud"].append({"text": kw, "value": count})
        
        # ========== FRESHNESS TIMELINE ==========
        # Group assets by month for timeline
        monthly_uploads = {}
        for asset in assets:
            date_str = asset.get("upload_date")
            if date_str:
                # Try to parse and group by month
                try:
                    # Handle various date formats
                    month_key = None
                    if re.match(r'\d{4}[/-]\d{1,2}', date_str):
                        month_key = date_str[:7]  # YYYY-MM
                    elif re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', date_str):
                        parts = re.split(r'[/-]', date_str)
                        month_key = f"{parts[2]}-{parts[0].zfill(2)}"
                    
                    if month_key:
                        monthly_uploads[month_key] = monthly_uploads.get(month_key, 0) + 1
                except:
                    continue
        
        # Convert to list for chart
        sorted_months = sorted(monthly_uploads.items())
        for month, count in sorted_months[-12:]:  # Last 12 months
            viz["freshness_timeline"].append({
                "month": month,
                "uploads": count,
            })
        
        logger.info(f"Visualization data: {len(viz['contributor_chart'])} contributors, "
                   f"{len(viz['keyword_cloud'])} keywords, {len(viz['price_distribution'])} price buckets")
        
        return viz
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def analyze_keyword_deep(
    keyword: str,
    depth: str = "medium",
    output_file: str = None,
    headless: bool = True,
    progress_callback: Callable = None,
) -> Dict[str, Any]:
    """
    Run deep analysis on a keyword.
    
    Args:
        keyword: Keyword to analyze
        depth: Analysis depth (simple, medium, deep)
        output_file: Optional output JSON file
        headless: Run browser in headless mode
        progress_callback: Optional callback for progress updates
    
    Returns:
        Comprehensive analysis results
    """
    with DeepAnalyzer(headless=headless, progress_callback=progress_callback) as analyzer:
        results = analyzer.analyze_keyword_deep(keyword, depth)
        
        if output_file:
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Results saved to {output_file}")
        
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Deep keyword analysis for Adobe Stock")
    parser.add_argument("keyword", help="Keyword to analyze")
    parser.add_argument("-d", "--depth", choices=["simple", "medium", "deep"], default="medium",
                        help="Analysis depth")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run with visible browser")
    
    args = parser.parse_args()
    
    def print_progress(p):
        print(f"  [{p['progress']:3d}%] {p['step']}: {p['message']}")
    
    print(f"\nAnalyzing '{args.keyword}' with {args.depth} depth...")
    print("=" * 60)
    
    results = analyze_keyword_deep(
        keyword=args.keyword,
        depth=args.depth,
        output_file=args.output,
        headless=args.headless,
        progress_callback=print_progress,
    )
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    scoring = results.get("scoring", {})
    print(f"\nKeyword: {results['keyword']}")
    print(f"Total Results: {results['search_results'].get('nb_results', 0):,}")
    print(f"Assets Analyzed: {len(results.get('asset_details', []))}")
    print(f"Contributors Profiled: {len(results.get('contributor_profiles', []))}")
    
    print(f"\nSCORES:")
    print(f"  Demand Score:      {scoring.get('demand_score', 0):.1f}")
    print(f"  Competition Score: {scoring.get('competition_score', 0):.1f}")
    print(f"  Gap Score:         {scoring.get('gap_score', 0):.1f}")
    print(f"  Freshness Score:   {scoring.get('freshness_score', 0):.1f}")
    print(f"  Quality Gap Score: {scoring.get('quality_gap_score', 0):.1f}")
    print(f"  ─────────────────────")
    print(f"  OPPORTUNITY SCORE: {scoring.get('opportunity_score', 0):.1f}")
    print(f"  Trend: {scoring.get('trend', 'unknown')} | Urgency: {scoring.get('urgency', 'unknown')}")
    
    market = results.get("market_analysis", {})
    print(f"\nMARKET INSIGHTS:")
    print(f"  Premium Ratio: {market.get('premium_ratio', 0):.1%}")
    print(f"  Contributor Concentration: {market.get('contributor_concentration', 0):.1%}")
    print(f"  Unique Contributors: {market.get('unique_contributors', 0)}")
    
    if args.output:
        print(f"\nFull results saved to: {args.output}")
