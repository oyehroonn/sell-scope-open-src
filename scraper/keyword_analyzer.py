"""
Keyword Analyzer - Scrapes Adobe Stock for keyword demand and competition metrics
Used for opportunity scoring and trend analysis
"""

import os
import re
import json
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlencode, quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import (
    HEADLESS, DELAY_MIN, DELAY_MAX, PAGE_LOAD_TIMEOUT,
    BASE_URL, SEARCH_URL, OUTPUT_DIR
)
from adobe_stock_scraper import find_chromedriver, get_user_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KeywordAnalyzer:
    """Analyzes keywords for demand, competition, and opportunity scoring"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
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
        logger.info("WebDriver initialized for keyword analysis")
    
    def _random_delay(self, min_delay: float = None, max_delay: float = None):
        """Add random delay to avoid detection"""
        min_d = min_delay or DELAY_MIN
        max_d = max_delay or DELAY_MAX
        time.sleep(random.uniform(min_d, max_d))
    
    def get_search_metrics(self, keyword: str, sort_order: str = "relevance") -> Dict[str, Any]:
        """
        Get search metrics for a keyword
        
        Args:
            keyword: Search term
            sort_order: One of 'relevance', 'nb_downloads', 'creation', 'featured', 'undiscovered'
        
        Returns:
            Dict with nb_results, top_results, related_searches, etc.
        """
        metrics = {
            "keyword": keyword,
            "sort_order": sort_order,
            "nb_results": 0,
            "top_results": [],
            "related_searches": [],
            "categories": [],
            "unique_contributors": set(),
            "avg_upload_recency_days": None,
            "scraped_at": datetime.utcnow().isoformat(),
        }
        
        try:
            params = {
                "k": keyword,
                "search_type": "usertyped",
            }
            
            if sort_order and sort_order != "relevance":
                params["order"] = sort_order
            
            url = f"{SEARCH_URL}?{urlencode(params)}"
            logger.info(f"Fetching keyword metrics: {keyword} (sort: {sort_order})")
            
            self.driver.get(url)
            self._random_delay(2, 4)
            
            # Wait for results to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='search-result-item'], [class*='AssetCard'], a[href*='/images/']"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for results for '{keyword}'")
            
            # Get total results count (nb_results)
            metrics["nb_results"] = self._extract_total_results()
            
            # Get related searches
            metrics["related_searches"] = self._extract_related_searches()
            
            # Get categories from filters
            metrics["categories"] = self._extract_categories()
            
            # Get top results (first 20)
            top_results = self._extract_top_results(limit=20)
            metrics["top_results"] = top_results
            
            # Calculate unique contributors
            for result in top_results:
                if result.get("contributor_id"):
                    metrics["unique_contributors"].add(result["contributor_id"])
            
            metrics["unique_contributors"] = len(metrics["unique_contributors"])
            
            # Calculate average upload recency
            metrics["avg_upload_recency_days"] = self._calculate_avg_recency(top_results)
            
            logger.info(f"Keyword '{keyword}': {metrics['nb_results']} results, {metrics['unique_contributors']} contributors")
            
        except Exception as e:
            logger.error(f"Error analyzing keyword '{keyword}': {e}")
        
        return metrics
    
    def _extract_total_results(self) -> int:
        """Extract total number of results from the page"""
        try:
            # First try to find specific elements that show result count
            selectors = [
                "[data-testid='search-results-count']",
                "[class*='ResultsCount']",
                "[class*='results-count']",
                "[class*='SearchHeader'] span",
                "h1[class*='Search']",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    text = el.text
                    # Look for numbers in the text
                    match = re.search(r'([\d,\.]+)\s*(?:results?|resultados?|résultats?|assets?|images?|photos?|stock)', text, re.IGNORECASE)
                    if match:
                        count_str = match.group(1).replace(",", "").replace(".", "")
                        count = int(count_str)
                        if count > 0:
                            return count
            
            # Try page text patterns
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            patterns = [
                r'([\d,]+)\s*(?:results?|resultados?|résultats?)\s*(?:for|para|pour)?',
                r'(?:of|de)\s*([\d,]+)\s*(?:results?|assets?)',
                r'([\d,]+)\s*(?:stock|assets?|images?|photos?)',
                r'Showing\s+\d+[-–]\d+\s+of\s+([\d,]+)',
                r'([\d,]+)\s+(?:free|premium)?\s*(?:stock)',
                r'(?:Found|Encontrado|Trouvé)\s*([\d,]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    count_str = match.group(1).replace(",", "").replace(".", "")
                    count = int(count_str)
                    if count > 100:  # Reasonable minimum
                        return count
            
            # Try to extract from page source/scripts
            try:
                page_source = self.driver.page_source
                # Look for JSON data in scripts
                json_patterns = [
                    r'"nb_results":\s*(\d+)',
                    r'"totalResults":\s*(\d+)',
                    r'"total_count":\s*(\d+)',
                    r'"count":\s*(\d+)',
                ]
                for pattern in json_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        count = int(match.group(1))
                        if count > 100:
                            return count
            except:
                pass
            
            # Fallback: count visible items and estimate based on pagination
            items = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='search-result-item'], [class*='AssetCard'], a[href*='/images/']")
            if items:
                # Check for pagination to estimate total
                pagination = self.driver.find_elements(By.CSS_SELECTOR, "[class*='Pagination'] a, [class*='pagination'] a")
                if pagination:
                    # Try to find the last page number
                    max_page = 1
                    for p in pagination:
                        try:
                            page_num = int(p.text)
                            max_page = max(max_page, page_num)
                        except:
                            pass
                    return len(items) * max_page
                return len(items) * 100  # Estimate 100 pages minimum for popular terms
            
        except Exception as e:
            logger.warning(f"Could not extract total results: {e}")
        
        return 0
    
    def _extract_related_searches(self) -> List[str]:
        """Extract related/suggested searches from the page"""
        related = []
        
        try:
            selectors = [
                "[class*='RelatedSearch'] a",
                "[class*='related-search'] a",
                "[data-testid*='related'] a",
                "[class*='SuggestedSearch'] a",
                "a[href*='/search?k=']",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements[:20]:
                    try:
                        text = el.text.strip()
                        href = el.get_attribute("href") or ""
                        
                        if text and len(text) > 1 and len(text) < 50:
                            if text.lower() not in [r.lower() for r in related]:
                                if not any(skip in text.lower() for skip in ["filter", "sort", "view", "show"]):
                                    related.append(text)
                        elif "k=" in href:
                            from urllib.parse import parse_qs, urlparse
                            parsed = urlparse(href)
                            qs = parse_qs(parsed.query)
                            if "k" in qs:
                                kw = qs["k"][0]
                                if kw and kw.lower() not in [r.lower() for r in related]:
                                    related.append(kw)
                    except:
                        continue
                
                if len(related) >= 10:
                    break
            
        except Exception as e:
            logger.warning(f"Could not extract related searches: {e}")
        
        return related[:15]
    
    def _extract_categories(self) -> List[Dict[str, Any]]:
        """Extract category information from filters"""
        categories = []
        
        try:
            selectors = [
                "[class*='CategoryFilter'] a",
                "[class*='category'] a",
                "[data-testid*='category'] a",
                "a[href*='filters[category]']",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements[:15]:
                    try:
                        text = el.text.strip()
                        if text and len(text) > 1:
                            count_match = re.search(r'\((\d+)\)', text)
                            count = int(count_match.group(1)) if count_match else None
                            name = re.sub(r'\s*\(\d+\)\s*', '', text).strip()
                            
                            if name and name.lower() not in [c["name"].lower() for c in categories]:
                                categories.append({
                                    "name": name,
                                    "count": count,
                                })
                    except:
                        continue
            
        except Exception as e:
            logger.warning(f"Could not extract categories: {e}")
        
        return categories[:10]
    
    def _extract_top_results(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Extract top search results with contributor info"""
        results = []
        
        try:
            # Scroll to load more items
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800)")
                time.sleep(0.5)
            
            # Try multiple selectors for result items
            selectors = [
                "[data-testid='search-result-item']",
                "[class*='AssetCard']",
                "[class*='SearchResultItem']",
                "div[class*='search-result']",
                "figure[class*='asset']",
            ]
            
            items = []
            for selector in selectors:
                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    logger.info(f"Found {len(items)} items with selector: {selector}")
                    break
            
            if not items:
                # Fallback: find all image links
                items = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/images/']")
                logger.info(f"Fallback: found {len(items)} image links")
            
            for item in items[:limit]:
                try:
                    result = self._parse_result_item(item)
                    if result and result.get("asset_id"):
                        results.append(result)
                except Exception as e:
                    continue
            
            # If we didn't get contributors from cards, try to extract from page
            if results and all(r.get("contributor_id") is None for r in results):
                logger.info("No contributors found in cards, trying page-level extraction")
                contributors = self._extract_contributors_from_page()
                # Assign contributors to results (best effort)
                for i, contrib in enumerate(contributors[:len(results)]):
                    if i < len(results):
                        results[i]["contributor_id"] = contrib.get("id")
                        results[i]["contributor_name"] = contrib.get("name")
            
        except Exception as e:
            logger.warning(f"Could not extract top results: {e}")
        
        return results
    
    def _extract_contributors_from_page(self) -> List[Dict[str, Any]]:
        """Extract contributor information from the entire page"""
        contributors = []
        seen_ids = set()
        
        try:
            # Look for contributor links anywhere on page
            selectors = [
                "a[href*='/contributor/']",
                "[class*='contributor'] a",
                "[class*='author'] a",
                "[class*='Creator'] a",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements[:50]:
                    try:
                        href = el.get_attribute("href") or ""
                        match = re.search(r'/contributor/(\d+)', href)
                        if match:
                            contrib_id = match.group(1)
                            if contrib_id not in seen_ids:
                                seen_ids.add(contrib_id)
                                contributors.append({
                                    "id": contrib_id,
                                    "name": el.text.strip() or None,
                                })
                    except:
                        continue
            
            # Also try to extract from page source
            if not contributors:
                page_source = self.driver.page_source
                # Look for contributor IDs in JSON data
                contrib_matches = re.findall(r'"creator_id":\s*"?(\d+)"?', page_source)
                for cid in contrib_matches[:30]:
                    if cid not in seen_ids:
                        seen_ids.add(cid)
                        contributors.append({"id": cid, "name": None})
                
                # Also try contributor patterns
                contrib_matches = re.findall(r'/contributor/(\d+)', page_source)
                for cid in contrib_matches[:30]:
                    if cid not in seen_ids:
                        seen_ids.add(cid)
                        contributors.append({"id": cid, "name": None})
            
        except Exception as e:
            logger.warning(f"Could not extract contributors from page: {e}")
        
        logger.info(f"Extracted {len(contributors)} unique contributors from page")
        return contributors
    
    def _parse_result_item(self, item) -> Dict[str, Any]:
        """Parse a single search result item"""
        result = {
            "asset_id": None,
            "title": None,
            "thumbnail_url": None,
            "contributor_id": None,
            "contributor_name": None,
            "is_premium": False,
            "asset_type": "photo",
        }
        
        try:
            # Get asset ID from link
            links = item.find_elements(By.CSS_SELECTOR, "a[href*='/images/']")
            for link in links:
                href = link.get_attribute("href") or ""
                match = re.search(r'/images/[^/]*/(\d+)', href)
                if match:
                    result["asset_id"] = match.group(1)
                    break
            
            if not result["asset_id"]:
                href = item.get_attribute("href") or ""
                match = re.search(r'/images/[^/]*/(\d+)', href)
                if match:
                    result["asset_id"] = match.group(1)
            
            # Also try data attributes
            if not result["asset_id"]:
                data_id = item.get_attribute("data-asset-id") or item.get_attribute("data-id")
                if data_id:
                    result["asset_id"] = data_id
            
            # Get title from image alt
            imgs = item.find_elements(By.CSS_SELECTOR, "img")
            for img in imgs:
                alt = img.get_attribute("alt") or ""
                if alt and len(alt) > 2:
                    result["title"] = alt
                src = img.get_attribute("src") or ""
                if src and "ftcdn" in src:
                    result["thumbnail_url"] = src
                if result["title"]:
                    break
            
            # Get contributor - try multiple selectors
            contrib_selectors = [
                "a[href*='/contributor/']",
                "[class*='contributor'] a",
                "[class*='author'] a",
                "[class*='creator'] a",
            ]
            
            for selector in contrib_selectors:
                contrib_links = item.find_elements(By.CSS_SELECTOR, selector)
                for link in contrib_links:
                    href = link.get_attribute("href") or ""
                    match = re.search(r'/contributor/(\d+)', href)
                    if match:
                        result["contributor_id"] = match.group(1)
                        result["contributor_name"] = link.text.strip() or None
                        break
                if result["contributor_id"]:
                    break
            
            # Check premium
            item_html = item.get_attribute("innerHTML") or ""
            if "premium" in item_html.lower():
                result["is_premium"] = True
            
        except Exception as e:
            pass
        
        return result
    
    def _calculate_avg_recency(self, results: List[Dict]) -> Optional[float]:
        """Calculate average upload recency (placeholder - would need detail page scraping)"""
        return None
    
    def analyze_keyword(self, keyword: str) -> Dict[str, Any]:
        """
        Full keyword analysis including demand, competition, and opportunity score
        
        Returns comprehensive metrics for a keyword
        """
        logger.info(f"Starting full analysis for keyword: {keyword}")
        
        # Get metrics with relevance sort (default)
        relevance_metrics = self.get_search_metrics(keyword, sort_order="relevance")
        self._random_delay(1, 2)
        
        # Get metrics sorted by downloads (popularity)
        downloads_metrics = self.get_search_metrics(keyword, sort_order="nb_downloads")
        
        # Use the maximum nb_results from both searches (more accurate)
        nb_results = max(relevance_metrics["nb_results"], downloads_metrics["nb_results"])
        
        # Combine unique contributors from both searches
        unique_contributors = max(
            relevance_metrics["unique_contributors"],
            downloads_metrics["unique_contributors"]
        )
        
        # Calculate opportunity score
        analysis = {
            "keyword": keyword,
            "nb_results": nb_results,
            "unique_contributors": unique_contributors,
            "related_searches": relevance_metrics["related_searches"],
            "categories": relevance_metrics["categories"],
            "top_results_relevance": relevance_metrics["top_results"][:10],
            "top_results_downloads": downloads_metrics["top_results"][:10],
            "scraped_at": datetime.utcnow().isoformat(),
        }
        
        # Calculate scores
        scores = self._calculate_scores(analysis)
        analysis.update(scores)
        
        return analysis
    
    def _calculate_scores(self, analysis: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate demand, competition, and opportunity scores.
        
        Scoring methodology:
        - Demand Score: Based on total results (market size/interest)
        - Competition Score: Based on market saturation (results per contributor ratio)
        - Gap Score: Based on diversity of contributors (opportunity for new entrants)
        - Freshness Score: Placeholder for content age analysis
        - Opportunity Score: Weighted combination favoring high demand + low competition
        """
        nb_results = analysis.get("nb_results", 0)
        unique_contributors = analysis.get("unique_contributors", 0)
        top_results = analysis.get("top_results_relevance", []) or analysis.get("top_results", [])
        
        # ===== DEMAND SCORE (0-100) =====
        # Based on total results - indicates market interest/search volume
        # Adobe Stock typically has:
        # - Niche keywords: 100-10,000 results
        # - Popular keywords: 10,000-100,000 results  
        # - Very popular: 100,000-1,000,000 results
        # - Mega popular: 1,000,000+ results
        if nb_results >= 1000000:
            demand_score = 95 + min((nb_results - 1000000) / 10000000 * 5, 5)  # 95-100
        elif nb_results >= 100000:
            demand_score = 80 + (nb_results - 100000) / 900000 * 15  # 80-95
        elif nb_results >= 10000:
            demand_score = 60 + (nb_results - 10000) / 90000 * 20  # 60-80
        elif nb_results >= 1000:
            demand_score = 40 + (nb_results - 1000) / 9000 * 20  # 40-60
        elif nb_results >= 100:
            demand_score = 20 + (nb_results - 100) / 900 * 20  # 20-40
        elif nb_results > 0:
            demand_score = nb_results / 100 * 20  # 0-20
        else:
            demand_score = 0
        
        # ===== COMPETITION SCORE (0-100) =====
        # Based on market saturation - how crowded is this keyword?
        # Higher score = MORE competition = HARDER to rank
        # 
        # We estimate competition by:
        # 1. Total results (more = more competitive)
        # 2. Contributor diversity in top results (fewer unique = dominated by few)
        # 3. Results per contributor ratio
        
        if nb_results == 0:
            competition_score = 0
        else:
            # Base competition from total results
            if nb_results >= 1000000:
                base_competition = 90 + min((nb_results - 1000000) / 10000000 * 10, 10)  # 90-100
            elif nb_results >= 100000:
                base_competition = 70 + (nb_results - 100000) / 900000 * 20  # 70-90
            elif nb_results >= 10000:
                base_competition = 50 + (nb_results - 10000) / 90000 * 20  # 50-70
            elif nb_results >= 1000:
                base_competition = 30 + (nb_results - 1000) / 9000 * 20  # 30-50
            elif nb_results >= 100:
                base_competition = 10 + (nb_results - 100) / 900 * 20  # 10-30
            else:
                base_competition = nb_results / 100 * 10  # 0-10
            
            # Adjust based on contributor diversity in top results
            # If top 20 results are from many different contributors = more competitive
            # If dominated by few contributors = less competitive (opportunity to compete)
            if unique_contributors > 0:
                sample_size = min(len(top_results), 20)
                if sample_size > 0:
                    # Diversity ratio: unique contributors / sample size
                    diversity = unique_contributors / sample_size
                    # High diversity (0.8-1.0) = very competitive
                    # Low diversity (0.1-0.3) = dominated by few, opportunity exists
                    diversity_factor = diversity * 20  # 0-20 adjustment
                    competition_score = base_competition * 0.7 + diversity_factor * 0.3 + 10
                else:
                    competition_score = base_competition
            else:
                # No contributor data, use base only
                competition_score = base_competition
            
            competition_score = min(100, max(0, competition_score))
        
        # ===== GAP SCORE (0-100) =====
        # Opportunity gap - is there room for new content?
        # Higher score = more opportunity
        # Based on inverse of competition and contributor concentration
        if unique_contributors > 0 and len(top_results) > 0:
            # Concentration = unique contributors / sample size
            # Low concentration (few contributors dominate) = HIGH gap (opportunity)
            # High concentration (many contributors) = LOW gap (saturated)
            concentration = min(unique_contributors / max(len(top_results), 1), 1.0)
            
            if concentration < 0.3:  # Highly concentrated - few dominate
                gap_score = 70 + (0.3 - concentration) / 0.3 * 30  # 70-100
            elif concentration < 0.5:
                gap_score = 50 + (0.5 - concentration) / 0.2 * 20  # 50-70
            elif concentration < 0.7:
                gap_score = 35 + (0.7 - concentration) / 0.2 * 15  # 35-50
            else:
                # High concentration - many contributors, saturated
                gap_score = 20 + (1.0 - concentration) / 0.3 * 15  # 20-35
            
            gap_score = max(10, min(100, gap_score))  # Clamp to 10-100
        else:
            # No data, assume moderate gap
            gap_score = 50
        
        # ===== FRESHNESS SCORE (0-100) =====
        # Would need upload date analysis - placeholder
        # For now, estimate based on demand (trending topics get fresh content)
        if demand_score >= 80:
            freshness_score = 60  # High demand = lots of fresh content
        elif demand_score >= 50:
            freshness_score = 50  # Moderate
        else:
            freshness_score = 40  # Low demand = stale content, opportunity
        
        # ===== OPPORTUNITY SCORE (0-100) =====
        # Weighted combination: High demand + Low competition = High opportunity
        # 
        # Formula emphasizes:
        # - Demand (35%): Want keywords people are searching for
        # - Inverse Competition (30%): Want less saturated markets
        # - Gap (20%): Want markets with room for new content
        # - Freshness (15%): Slight preference for active markets
        opportunity_score = (
            demand_score * 0.35 +
            (100 - competition_score) * 0.30 +
            gap_score * 0.20 +
            freshness_score * 0.15
        )
        
        # ===== TREND DETERMINATION =====
        # Based on demand level relative to competition
        demand_competition_ratio = demand_score / max(competition_score, 1)
        if demand_competition_ratio > 1.2 and demand_score >= 60:
            trend = "up"
        elif demand_competition_ratio < 0.8 or demand_score < 30:
            trend = "down"
        else:
            trend = "stable"
        
        # ===== URGENCY DETERMINATION =====
        # Based on opportunity score
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
            "opportunity_score": round(opportunity_score, 2),
            "trend": trend,
            "urgency": urgency,
        }
    
    def analyze_multiple_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple keywords"""
        results = []
        
        for i, keyword in enumerate(keywords):
            logger.info(f"Analyzing keyword {i+1}/{len(keywords)}: {keyword}")
            try:
                analysis = self.analyze_keyword(keyword)
                results.append(analysis)
                self._random_delay(2, 4)
            except Exception as e:
                logger.error(f"Error analyzing '{keyword}': {e}")
                results.append({
                    "keyword": keyword,
                    "error": str(e),
                    "scraped_at": datetime.utcnow().isoformat(),
                })
        
        return results
    
    def get_trending_categories(self) -> List[Dict[str, Any]]:
        """Get trending categories from Adobe Stock homepage"""
        categories = []
        
        try:
            self.driver.get(BASE_URL)
            self._random_delay(2, 3)
            
            # Look for trending/popular sections
            selectors = [
                "[class*='trending'] a",
                "[class*='popular'] a",
                "[class*='category'] a",
                "[class*='Collection'] a",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements[:20]:
                    try:
                        text = el.text.strip()
                        href = el.get_attribute("href") or ""
                        
                        if text and len(text) > 2 and "/search" in href:
                            if text.lower() not in [c["name"].lower() for c in categories]:
                                categories.append({
                                    "name": text,
                                    "url": href,
                                })
                    except:
                        continue
            
        except Exception as e:
            logger.error(f"Error getting trending categories: {e}")
        
        return categories[:20]
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def analyze_keywords_batch(keywords: List[str], output_file: str = None, headless: bool = True) -> List[Dict[str, Any]]:
    """
    Analyze a batch of keywords and optionally save to JSON
    
    Args:
        keywords: List of keywords to analyze
        output_file: Optional output JSON file path
        headless: Run browser in headless mode
    
    Returns:
        List of keyword analysis results
    """
    with KeywordAnalyzer(headless=headless) as analyzer:
        results = analyzer.analyze_multiple_keywords(keywords)
        
        if output_file:
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_file}")
        
        return results


def analyze_keyword_deep(
    keyword: str,
    depth: str = "medium",
    output_file: str = None,
    headless: bool = True,
    progress_callback = None,
) -> Dict[str, Any]:
    """
    Run deep analysis on a keyword using the DeepAnalyzer.
    
    This is a convenience function that imports and uses the DeepAnalyzer
    for comprehensive multi-page scraping and analysis.
    
    Args:
        keyword: Keyword to analyze
        depth: Analysis depth (simple, medium, deep)
        output_file: Optional output JSON file
        headless: Run browser in headless mode
        progress_callback: Optional callback for progress updates
    
    Returns:
        Comprehensive analysis results with market data, 
        contributor profiles, and visualization data
    """
    from deep_analyzer import DeepAnalyzer
    
    with DeepAnalyzer(headless=headless, progress_callback=progress_callback) as analyzer:
        results = analyzer.analyze_keyword_deep(keyword, depth)
        
        if output_file:
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Deep analysis results saved to {output_file}")
        
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Adobe Stock keywords for opportunity scoring")
    parser.add_argument("keywords", nargs="+", help="Keywords to analyze")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run with visible browser")
    parser.add_argument("--deep", action="store_true", help="Run deep analysis")
    parser.add_argument("--depth", choices=["simple", "medium", "deep"], default="medium",
                        help="Analysis depth for deep mode")
    
    args = parser.parse_args()
    
    if args.deep:
        # Run deep analysis for single keyword
        keyword = args.keywords[0]
        print(f"\nRunning DEEP analysis on '{keyword}' (depth: {args.depth})...")
        print("This may take 3-5 minutes...")
        print("=" * 60)
        
        def print_progress(p):
            print(f"  [{p['progress']:3d}%] {p['step']}: {p['message']}")
        
        results = analyze_keyword_deep(
            keyword=keyword,
            depth=args.depth,
            output_file=args.output,
            headless=args.headless,
            progress_callback=print_progress,
        )
        
        scoring = results.get("scoring", {})
        market = results.get("market_analysis", {})
        
        print("\n" + "=" * 60)
        print("DEEP ANALYSIS RESULTS")
        print("=" * 60)
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
        
        print(f"\nMARKET INSIGHTS:")
        print(f"  Premium Ratio: {market.get('premium_ratio', 0):.1%}")
        print(f"  Contributor Concentration: {market.get('contributor_concentration', 0):.1%}")
        
        if args.output:
            print(f"\nFull results saved to: {args.output}")
    else:
        # Run standard batch analysis
        results = analyze_keywords_batch(
            keywords=args.keywords,
            output_file=args.output,
            headless=args.headless,
        )
        
        for r in results:
            print(f"\n{'='*50}")
            print(f"Keyword: {r.get('keyword')}")
            print(f"Results: {r.get('nb_results', 0):,}")
            print(f"Contributors: {r.get('unique_contributors', 0)}")
            print(f"Demand Score: {r.get('demand_score', 0):.1f}")
            print(f"Competition Score: {r.get('competition_score', 0):.1f}")
            print(f"Opportunity Score: {r.get('opportunity_score', 0):.1f}")
            print(f"Trend: {r.get('trend', 'unknown')}")
            print(f"Urgency: {r.get('urgency', 'unknown')}")
            if r.get("related_searches"):
                print(f"Related: {', '.join(r['related_searches'][:5])}")
