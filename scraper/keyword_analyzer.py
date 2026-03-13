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
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            patterns = [
                r'([\d,]+)\s*(?:results?|resultados?|résultats?)',
                r'(?:of|de)\s*([\d,]+)\s*(?:results?|assets?)',
                r'([\d,]+)\s*(?:stock|assets?|images?|photos?)',
                r'Showing\s+\d+[-–]\d+\s+of\s+([\d,]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    count_str = match.group(1).replace(",", "").replace(".", "")
                    return int(count_str)
            
            # Fallback: count visible items and estimate
            items = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='search-result-item'], [class*='AssetCard'], a[href*='/images/']")
            if items:
                return len(items) * 10  # Rough estimate
            
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
        """Extract top search results"""
        results = []
        
        try:
            selectors = [
                "[data-testid='search-result-item']",
                "[class*='AssetCard']",
                "[class*='SearchResultItem']",
            ]
            
            items = []
            for selector in selectors:
                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    break
            
            if not items:
                items = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/images/']")
            
            for item in items[:limit]:
                try:
                    result = self._parse_result_item(item)
                    if result and result.get("asset_id"):
                        results.append(result)
                except Exception as e:
                    continue
            
        except Exception as e:
            logger.warning(f"Could not extract top results: {e}")
        
        return results
    
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
            
            # Get title from image alt
            imgs = item.find_elements(By.CSS_SELECTOR, "img")
            for img in imgs:
                alt = img.get_attribute("alt") or ""
                if alt and len(alt) > 2:
                    result["title"] = alt
                    break
                src = img.get_attribute("src") or ""
                if src and "ftcdn" in src:
                    result["thumbnail_url"] = src
            
            # Get contributor
            contrib_links = item.find_elements(By.CSS_SELECTOR, "a[href*='/contributor/']")
            for link in contrib_links:
                href = link.get_attribute("href") or ""
                match = re.search(r'/contributor/(\d+)', href)
                if match:
                    result["contributor_id"] = match.group(1)
                    result["contributor_name"] = link.text.strip() or None
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
        
        # Calculate opportunity score
        analysis = {
            "keyword": keyword,
            "nb_results": relevance_metrics["nb_results"],
            "unique_contributors": relevance_metrics["unique_contributors"],
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
        """Calculate demand, competition, and opportunity scores"""
        nb_results = analysis.get("nb_results", 0)
        unique_contributors = analysis.get("unique_contributors", 0)
        
        # Demand Score (0-100): Based on number of results
        # 0-1000 = low, 1000-10000 = medium, 10000+ = high
        if nb_results >= 100000:
            demand_score = 100
        elif nb_results >= 10000:
            demand_score = 70 + (min(nb_results, 100000) - 10000) / 90000 * 30
        elif nb_results >= 1000:
            demand_score = 40 + (nb_results - 1000) / 9000 * 30
        else:
            demand_score = nb_results / 1000 * 40
        
        # Competition Score (0-100): Based on unique contributors
        # Fewer contributors = less competition = higher opportunity
        if unique_contributors == 0:
            competition_score = 0
        elif unique_contributors >= 100:
            competition_score = 100
        else:
            competition_score = unique_contributors
        
        # Gap Score (0-100): Placeholder - would need quality analysis
        gap_score = 50
        
        # Freshness Score (0-100): Placeholder - would need date analysis
        freshness_score = 50
        
        # Opportunity Score: Weighted combination
        # High demand + low competition = high opportunity
        opportunity_score = (
            demand_score * 0.35 +
            (100 - competition_score) * 0.25 +
            gap_score * 0.20 +
            freshness_score * 0.20
        )
        
        # Determine trend based on demand level
        if demand_score >= 70:
            trend = "up"
        elif demand_score >= 40:
            trend = "stable"
        else:
            trend = "down"
        
        # Determine urgency
        if opportunity_score >= 75:
            urgency = "high"
        elif opportunity_score >= 50:
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Adobe Stock keywords for opportunity scoring")
    parser.add_argument("keywords", nargs="+", help="Keywords to analyze")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run with visible browser")
    
    args = parser.parse_args()
    
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
