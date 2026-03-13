"""
Contributor Profile Scraper - Scrapes Adobe Stock contributor pages for portfolio analysis
Used for competitor profiling and market intelligence
"""

import os
import re
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import (
    HEADLESS, DELAY_MIN, DELAY_MAX, PAGE_LOAD_TIMEOUT,
    BASE_URL, CONTRIBUTOR_URL, OUTPUT_DIR
)
from adobe_stock_scraper import find_chromedriver, get_user_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContributorScraper:
    """Scrapes Adobe Stock contributor profile pages for competitive analysis"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Initialize Selenium WebDriver with English locale"""
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
        
        # Force English (US) locale
        options.add_argument("--lang=en-US")
        options.add_argument("--accept-language=en-US,en;q=0.9")
        
        chromedriver_path = find_chromedriver()
        service = Service(chromedriver_path)
        
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'language', {get: () => 'en-US'});
            """
        })
        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        logger.info("WebDriver initialized for contributor scraping (English locale)")
    
    def _random_delay(self, min_delay: float = None, max_delay: float = None):
        """Add random delay to avoid detection"""
        min_d = min_delay or DELAY_MIN
        max_d = max_delay or DELAY_MAX
        time.sleep(random.uniform(min_d, max_d))
    
    def scrape_contributor_profile(self, contributor_id: str) -> Dict[str, Any]:
        """
        Scrape a contributor's profile page for detailed information.
        
        Args:
            contributor_id: Adobe Stock contributor ID
            
        Returns:
            Dict with contributor profile data
        """
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
            "upload_frequency_monthly": 0.0,
            "avg_dimensions": None,
            "quality_indicators": {},
            "niches": [],
            "sample_assets": [],
            "scraped_at": datetime.utcnow().isoformat(),
            "error": None,
        }
        
        try:
            url = f"{CONTRIBUTOR_URL}/{contributor_id}"
            logger.info(f"Scraping contributor profile: {contributor_id}")
            
            self.driver.get(url)
            self._random_delay(2, 4)
            
            # Wait for page to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
            except TimeoutException:
                profile["error"] = "Page load timeout"
                return profile
            
            # Scroll to load more content
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 500)")
                time.sleep(0.5)
            
            # Extract contributor name
            profile["name"] = self._extract_contributor_name()
            
            # Extract portfolio stats
            portfolio_stats = self._extract_portfolio_stats()
            profile.update(portfolio_stats)
            
            # Extract top categories
            profile["top_categories"] = self._extract_top_categories()
            
            # Extract category distribution
            profile["category_distribution"] = self._extract_category_distribution()
            
            # Extract sample assets for keyword analysis
            sample_assets = self._extract_sample_assets(limit=20)
            profile["sample_assets"] = sample_assets
            
            # Extract top keywords from sample assets
            profile["top_keywords"] = self._extract_keywords_from_samples(sample_assets)
            
            # Estimate join date from oldest visible content
            profile["estimated_join_date"] = self._estimate_join_date()
            
            # Calculate upload frequency
            if profile["total_assets"] > 0 and profile["estimated_join_date"]:
                profile["upload_frequency_monthly"] = self._calculate_upload_frequency(
                    profile["total_assets"], 
                    profile["estimated_join_date"]
                )
            
            # Determine niches based on categories and keywords
            profile["niches"] = self._determine_niches(
                profile["top_categories"], 
                profile["top_keywords"]
            )
            
            # Calculate premium ratio
            if profile["total_assets"] > 0:
                profile["premium_ratio"] = profile["premium_count"] / profile["total_assets"]
            
            logger.info(f"Scraped contributor {contributor_id}: {profile['name']}, {profile['total_assets']} assets")
            
        except Exception as e:
            logger.error(f"Error scraping contributor {contributor_id}: {e}")
            profile["error"] = str(e)
        
        return profile
    
    def _extract_contributor_name(self) -> Optional[str]:
        """Extract contributor name from profile page"""
        try:
            selectors = [
                "h1[class*='contributor']",
                "h1[class*='profile']",
                "[class*='ContributorName']",
                "[class*='contributor-name']",
                "h1",
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    text = el.text.strip()
                    if text and len(text) > 1 and len(text) < 100:
                        return text
            
            # Try from page title
            title = self.driver.title
            if title:
                # Common patterns: "Name - Adobe Stock Contributor"
                match = re.search(r'^([^-|]+)', title)
                if match:
                    name = match.group(1).strip()
                    if name and "Adobe" not in name:
                        return name
                        
        except Exception as e:
            logger.warning(f"Could not extract contributor name: {e}")
        
        return None
    
    def _extract_portfolio_stats(self) -> Dict[str, Any]:
        """Extract portfolio statistics from profile page"""
        stats = {
            "total_assets": 0,
            "total_photos": 0,
            "total_vectors": 0,
            "total_videos": 0,
            "total_templates": 0,
            "total_3d": 0,
            "premium_count": 0,
        }
        
        try:
            # Look for asset count indicators
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Try to find total count patterns
            patterns = [
                r'(\d[\d,]*)\s*(?:assets?|items?|images?|photos?|stock)',
                r'(?:portfolio|collection).*?(\d[\d,]*)',
                r'(\d[\d,]*)\s*(?:results?|works?)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    count_str = match.group(1).replace(",", "")
                    count = int(count_str)
                    if count > stats["total_assets"]:
                        stats["total_assets"] = count
            
            # Look for type-specific counts
            type_patterns = {
                "total_photos": r'(\d[\d,]*)\s*(?:photos?|images?)',
                "total_vectors": r'(\d[\d,]*)\s*(?:vectors?|illustrations?)',
                "total_videos": r'(\d[\d,]*)\s*(?:videos?|footage)',
                "total_templates": r'(\d[\d,]*)\s*(?:templates?)',
                "total_3d": r'(\d[\d,]*)\s*(?:3d|three.?d)',
            }
            
            for key, pattern in type_patterns.items():
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    count_str = match.group(1).replace(",", "")
                    stats[key] = int(count_str)
            
            # Look for premium indicators
            premium_match = re.search(r'(\d[\d,]*)\s*premium', page_text, re.IGNORECASE)
            if premium_match:
                stats["premium_count"] = int(premium_match.group(1).replace(",", ""))
            
            # Try to count from filter tabs/buttons
            filter_selectors = [
                "button[class*='filter']",
                "a[class*='filter']",
                "[data-testid*='filter']",
                "[class*='FilterTab']",
            ]
            
            for selector in filter_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    text = el.text.lower()
                    count_match = re.search(r'(\d[\d,]*)', text)
                    if count_match:
                        count = int(count_match.group(1).replace(",", ""))
                        if "photo" in text or "image" in text:
                            stats["total_photos"] = max(stats["total_photos"], count)
                        elif "vector" in text or "illustrat" in text:
                            stats["total_vectors"] = max(stats["total_vectors"], count)
                        elif "video" in text or "footage" in text:
                            stats["total_videos"] = max(stats["total_videos"], count)
                        elif "template" in text:
                            stats["total_templates"] = max(stats["total_templates"], count)
                        elif "3d" in text:
                            stats["total_3d"] = max(stats["total_3d"], count)
            
            # If no total, sum up the types
            if stats["total_assets"] == 0:
                stats["total_assets"] = (
                    stats["total_photos"] + 
                    stats["total_vectors"] + 
                    stats["total_videos"] + 
                    stats["total_templates"] +
                    stats["total_3d"]
                )
            
            # Fallback: count visible items
            if stats["total_assets"] == 0:
                items = self.driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='AssetCard'], [class*='asset-card'], a[href*='/images/']"
                )
                if items:
                    stats["total_assets"] = len(items) * 10  # Estimate
            
        except Exception as e:
            logger.warning(f"Could not extract portfolio stats: {e}")
        
        return stats
    
    def _extract_top_categories(self) -> List[str]:
        """Extract top categories from contributor's portfolio"""
        categories = []
        
        try:
            selectors = [
                "[class*='category'] a",
                "a[href*='/category/']",
                "[class*='CategoryFilter'] a",
                "[class*='tag']",
            ]
            
            seen = set()
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements[:30]:
                    try:
                        text = el.text.strip()
                        if text and len(text) > 1 and len(text) < 50:
                            text_lower = text.lower()
                            if text_lower not in seen:
                                seen.add(text_lower)
                                categories.append(text)
                    except:
                        continue
            
        except Exception as e:
            logger.warning(f"Could not extract categories: {e}")
        
        return categories[:15]
    
    def _extract_category_distribution(self) -> Dict[str, int]:
        """Extract category distribution with counts"""
        distribution = {}
        
        try:
            page_source = self.driver.page_source
            
            # Look for category counts in JSON data
            json_patterns = [
                r'"category":\s*"([^"]+)"[^}]*"count":\s*(\d+)',
                r'"name":\s*"([^"]+)"[^}]*"asset_count":\s*(\d+)',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, page_source)
                for name, count in matches:
                    if name and name not in distribution:
                        distribution[name] = int(count)
            
            # Try from visible category elements with counts
            elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "[class*='category'], [class*='CategoryItem']"
            )
            
            for el in elements[:20]:
                try:
                    text = el.text
                    match = re.search(r'([A-Za-z\s&]+)\s*\((\d+)\)', text)
                    if match:
                        name = match.group(1).strip()
                        count = int(match.group(2))
                        if name and name not in distribution:
                            distribution[name] = count
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not extract category distribution: {e}")
        
        return distribution
    
    def _extract_sample_assets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Extract sample assets from contributor's portfolio"""
        samples = []
        
        try:
            selectors = [
                "[class*='AssetCard']",
                "[class*='asset-card']",
                "[data-testid='search-result-item']",
                "a[href*='/images/']",
            ]
            
            items = []
            for selector in selectors:
                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    break
            
            for item in items[:limit]:
                try:
                    asset = {
                        "asset_id": None,
                        "title": None,
                        "thumbnail_url": None,
                        "asset_type": "photo",
                        "is_premium": False,
                        "keywords": [],
                    }
                    
                    # Get asset ID
                    links = item.find_elements(By.CSS_SELECTOR, "a[href*='/images/'], a[href*='/video/']")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        match = re.search(r'/(?:images|video)/[^/]*/(\d+)', href)
                        if match:
                            asset["asset_id"] = match.group(1)
                            if "/video/" in href:
                                asset["asset_type"] = "video"
                            break
                    
                    if not asset["asset_id"]:
                        continue
                    
                    # Get title and thumbnail
                    imgs = item.find_elements(By.CSS_SELECTOR, "img")
                    for img in imgs:
                        alt = img.get_attribute("alt") or ""
                        if alt and len(alt) > 2:
                            asset["title"] = alt
                            # Extract keywords from title
                            words = re.findall(r'[a-zA-Z]{3,}', alt.lower())
                            asset["keywords"] = list(set(words))[:10]
                        src = img.get_attribute("src") or ""
                        if "ftcdn" in src:
                            asset["thumbnail_url"] = src
                        if asset["title"]:
                            break
                    
                    # Check premium
                    item_html = item.get_attribute("innerHTML") or ""
                    if "premium" in item_html.lower():
                        asset["is_premium"] = True
                    
                    samples.append(asset)
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not extract sample assets: {e}")
        
        return samples
    
    def _extract_keywords_from_samples(self, samples: List[Dict]) -> List[str]:
        """Extract and aggregate keywords from sample assets"""
        keyword_counts = {}
        
        for sample in samples:
            for kw in sample.get("keywords", []):
                kw_lower = kw.lower()
                keyword_counts[kw_lower] = keyword_counts.get(kw_lower, 0) + 1
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in sorted_keywords[:20]]
    
    def _estimate_join_date(self) -> Optional[str]:
        """Estimate when contributor joined based on oldest content"""
        try:
            # Look for date indicators
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Common patterns
            patterns = [
                r'(?:member since|joined|since)\s*(\d{4})',
                r'(\d{4})\s*(?:-|to)\s*(?:present|now)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    year = int(match.group(1))
                    if 2000 <= year <= datetime.now().year:
                        return f"{year}-01-01"
            
            # Default estimate based on typical contributor tenure
            return None
            
        except Exception as e:
            logger.warning(f"Could not estimate join date: {e}")
            return None
    
    def _calculate_upload_frequency(self, total_assets: int, join_date_str: str) -> float:
        """Calculate average monthly upload frequency"""
        try:
            join_date = datetime.fromisoformat(join_date_str.replace("Z", ""))
            months_active = max(1, (datetime.now() - join_date).days / 30)
            return round(total_assets / months_active, 2)
        except:
            return 0.0
    
    def _determine_niches(self, categories: List[str], keywords: List[str]) -> List[str]:
        """Determine contributor's niches based on categories and keywords"""
        niches = []
        
        # Common niche patterns
        niche_keywords = {
            "business": ["business", "office", "corporate", "meeting", "professional"],
            "nature": ["nature", "landscape", "mountain", "forest", "ocean", "sky"],
            "people": ["people", "woman", "man", "family", "portrait", "lifestyle"],
            "technology": ["technology", "computer", "digital", "phone", "tech", "data"],
            "food": ["food", "cooking", "restaurant", "healthy", "meal", "kitchen"],
            "travel": ["travel", "vacation", "tourism", "adventure", "destination"],
            "healthcare": ["health", "medical", "doctor", "hospital", "wellness"],
            "education": ["education", "school", "learning", "student", "teacher"],
            "finance": ["finance", "money", "banking", "investment", "economy"],
            "creative": ["art", "creative", "design", "abstract", "artistic"],
        }
        
        all_terms = [c.lower() for c in categories] + keywords
        
        for niche, niche_kws in niche_keywords.items():
            score = sum(1 for term in all_terms if any(kw in term for kw in niche_kws))
            if score >= 2:
                niches.append(niche)
        
        return niches[:5]
    
    def scrape_multiple_contributors(self, contributor_ids: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple contributor profiles"""
        profiles = []
        
        for i, cid in enumerate(contributor_ids):
            logger.info(f"Scraping contributor {i+1}/{len(contributor_ids)}: {cid}")
            try:
                profile = self.scrape_contributor_profile(cid)
                profiles.append(profile)
                self._random_delay(2, 4)
            except Exception as e:
                logger.error(f"Error scraping contributor {cid}: {e}")
                profiles.append({
                    "adobe_id": cid,
                    "error": str(e),
                    "scraped_at": datetime.utcnow().isoformat(),
                })
        
        return profiles
    
    def analyze_competition(self, contributor_ids: List[str]) -> Dict[str, Any]:
        """Analyze competition among a set of contributors"""
        profiles = self.scrape_multiple_contributors(contributor_ids)
        
        analysis = {
            "total_contributors": len(profiles),
            "successful_scrapes": sum(1 for p in profiles if not p.get("error")),
            "total_combined_assets": 0,
            "avg_portfolio_size": 0,
            "avg_premium_ratio": 0,
            "common_categories": {},
            "common_keywords": {},
            "niche_distribution": {},
            "top_contributors": [],
            "market_concentration": 0,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
        
        valid_profiles = [p for p in profiles if not p.get("error")]
        
        if not valid_profiles:
            return analysis
        
        # Aggregate stats
        total_assets = sum(p.get("total_assets", 0) for p in valid_profiles)
        analysis["total_combined_assets"] = total_assets
        analysis["avg_portfolio_size"] = total_assets / len(valid_profiles)
        
        premium_ratios = [p.get("premium_ratio", 0) for p in valid_profiles]
        analysis["avg_premium_ratio"] = sum(premium_ratios) / len(premium_ratios)
        
        # Aggregate categories
        for profile in valid_profiles:
            for cat in profile.get("top_categories", []):
                cat_lower = cat.lower()
                analysis["common_categories"][cat_lower] = \
                    analysis["common_categories"].get(cat_lower, 0) + 1
        
        # Aggregate keywords
        for profile in valid_profiles:
            for kw in profile.get("top_keywords", []):
                analysis["common_keywords"][kw] = \
                    analysis["common_keywords"].get(kw, 0) + 1
        
        # Niche distribution
        for profile in valid_profiles:
            for niche in profile.get("niches", []):
                analysis["niche_distribution"][niche] = \
                    analysis["niche_distribution"].get(niche, 0) + 1
        
        # Top contributors by portfolio size
        sorted_profiles = sorted(valid_profiles, 
                                  key=lambda x: x.get("total_assets", 0), 
                                  reverse=True)
        analysis["top_contributors"] = [
            {
                "adobe_id": p["adobe_id"],
                "name": p.get("name"),
                "total_assets": p.get("total_assets", 0),
                "premium_ratio": p.get("premium_ratio", 0),
            }
            for p in sorted_profiles[:10]
        ]
        
        # Market concentration (top 5 share)
        if total_assets > 0:
            top_5_assets = sum(p.get("total_assets", 0) for p in sorted_profiles[:5])
            analysis["market_concentration"] = top_5_assets / total_assets
        
        return analysis
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def scrape_contributor(contributor_id: str, output_file: str = None, headless: bool = True) -> Dict[str, Any]:
    """
    Scrape a single contributor profile.
    
    Args:
        contributor_id: Adobe Stock contributor ID
        output_file: Optional output JSON file path
        headless: Run browser in headless mode
    
    Returns:
        Contributor profile data
    """
    with ContributorScraper(headless=headless) as scraper:
        profile = scraper.scrape_contributor_profile(contributor_id)
        
        if output_file:
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            logger.info(f"Profile saved to {output_file}")
        
        return profile


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Adobe Stock contributor profiles")
    parser.add_argument("contributor_ids", nargs="+", help="Contributor IDs to scrape")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run with visible browser")
    parser.add_argument("--analyze", action="store_true", help="Analyze competition among contributors")
    
    args = parser.parse_args()
    
    with ContributorScraper(headless=args.headless) as scraper:
        if args.analyze:
            analysis = scraper.analyze_competition(args.contributor_ids)
            print(json.dumps(analysis, indent=2))
        else:
            for cid in args.contributor_ids:
                profile = scraper.scrape_contributor_profile(cid)
                print(f"\n{'='*50}")
                print(f"Contributor: {profile.get('name', 'Unknown')} ({cid})")
                print(f"Total Assets: {profile.get('total_assets', 0):,}")
                print(f"Premium Ratio: {profile.get('premium_ratio', 0):.1%}")
                print(f"Top Categories: {', '.join(profile.get('top_categories', [])[:5])}")
                print(f"Top Keywords: {', '.join(profile.get('top_keywords', [])[:5])}")
                print(f"Niches: {', '.join(profile.get('niches', []))}")
                
                if args.output:
                    output_file = args.output if len(args.contributor_ids) == 1 else \
                                  args.output.replace(".json", f"_{cid}.json")
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(profile, f, indent=2, ensure_ascii=False)
                    print(f"Saved to: {output_file}")
