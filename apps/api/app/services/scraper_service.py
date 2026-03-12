"""Adobe Stock Scraper Service using Playwright"""

import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode, quote_plus

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
import structlog

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.scrape import ScrapeJob, ScrapeJobStatus, ScrapeJobType, ScrapeResult
from app.models.keyword import Keyword, KeywordRanking
from app.models.asset import Asset
from app.models.portfolio import Portfolio

logger = structlog.get_logger()


class AdobeStockScraper:
    BASE_URL = "https://stock.adobe.com"
    SEARCH_URL = f"{BASE_URL}/search"
    CONTRIBUTOR_URL = f"{BASE_URL}/contributor"
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def init_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        
        self.page = await context.new_page()
        
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
    
    async def close(self):
        if self.browser:
            await self.browser.close()
    
    async def random_delay(self):
        delay = random.uniform(settings.SCRAPE_DELAY_MIN, settings.SCRAPE_DELAY_MAX)
        await asyncio.sleep(delay)
    
    async def search_keyword(
        self,
        keyword: str,
        max_results: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.page:
            await self.init_browser()
        
        params = {
            "k": keyword,
            "search_type": "usertyped",
        }
        
        if filters:
            if filters.get("content_type"):
                params["filters[content_type:photo]"] = "1" if "photo" in filters["content_type"] else "0"
                params["filters[content_type:illustration]"] = "1" if "illustration" in filters["content_type"] else "0"
                params["filters[content_type:vector]"] = "1" if "vector" in filters["content_type"] else "0"
        
        url = f"{self.SEARCH_URL}?{urlencode(params)}"
        
        logger.info("Scraping keyword search", keyword=keyword, url=url)
        
        await self.page.goto(url, wait_until="networkidle")
        await self.random_delay()
        
        results = []
        page_num = 1
        
        while len(results) < max_results:
            await self.page.wait_for_selector("[data-testid='search-result-item']", timeout=10000)
            
            content = await self.page.content()
            soup = BeautifulSoup(content, "lxml")
            
            items = soup.select("[data-testid='search-result-item']")
            
            for item in items:
                if len(results) >= max_results:
                    break
                
                asset_data = self._parse_search_item(item, len(results) + 1)
                if asset_data:
                    results.append(asset_data)
            
            next_button = await self.page.query_selector("[data-testid='pagination-next']")
            if next_button and len(results) < max_results:
                await next_button.click()
                await self.random_delay()
                page_num += 1
            else:
                break
        
        return {
            "keyword": keyword,
            "total_results": len(results),
            "results": results,
            "scraped_at": datetime.utcnow().isoformat(),
        }
    
    def _parse_search_item(self, item, position: int) -> Optional[Dict[str, Any]]:
        try:
            link = item.select_one("a[href*='/images/']") or item.select_one("a[href*='/video/']")
            if not link:
                return None
            
            href = link.get("href", "")
            asset_id = href.split("/")[-1].split("-")[0] if href else None
            
            img = item.select_one("img")
            thumbnail_url = img.get("src") if img else None
            title = img.get("alt", "") if img else ""
            
            contributor_link = item.select_one("a[href*='/contributor/']")
            contributor_id = None
            contributor_name = None
            if contributor_link:
                contributor_href = contributor_link.get("href", "")
                contributor_id = contributor_href.split("/")[-1].split("?")[0]
                contributor_name = contributor_link.get_text(strip=True)
            
            asset_type = "photo"
            if "/video/" in href:
                asset_type = "video"
            elif "/vectors/" in href or "vector" in href.lower():
                asset_type = "vector"
            elif "/illustrations/" in href:
                asset_type = "illustration"
            
            return {
                "position": position,
                "asset_id": asset_id,
                "title": title,
                "thumbnail_url": thumbnail_url,
                "contributor_id": contributor_id,
                "contributor_name": contributor_name,
                "asset_type": asset_type,
            }
        except Exception as e:
            logger.error("Error parsing search item", error=str(e))
            return None
    
    async def scrape_portfolio(self, contributor_id: str) -> Dict[str, Any]:
        if not self.page:
            await self.init_browser()
        
        url = f"{self.CONTRIBUTOR_URL}/{contributor_id}"
        
        logger.info("Scraping portfolio", contributor_id=contributor_id, url=url)
        
        await self.page.goto(url, wait_until="networkidle")
        await self.random_delay()
        
        content = await self.page.content()
        soup = BeautifulSoup(content, "lxml")
        
        name_elem = soup.select_one("h1, .contributor-name")
        contributor_name = name_elem.get_text(strip=True) if name_elem else None
        
        stats = {
            "total_assets": 0,
            "photos": 0,
            "vectors": 0,
            "videos": 0,
        }
        
        stat_elements = soup.select(".stat-value, [data-testid='portfolio-stat']")
        for elem in stat_elements:
            text = elem.get_text(strip=True).lower()
            try:
                num = int("".join(filter(str.isdigit, text)))
                if "photo" in text:
                    stats["photos"] = num
                elif "vector" in text or "illustration" in text:
                    stats["vectors"] = num
                elif "video" in text:
                    stats["videos"] = num
            except:
                pass
        
        stats["total_assets"] = stats["photos"] + stats["vectors"] + stats["videos"]
        
        assets = []
        items = soup.select("[data-testid='portfolio-item'], .portfolio-item")
        for item in items[:50]:
            asset_data = self._parse_search_item(item, len(assets) + 1)
            if asset_data:
                assets.append(asset_data)
        
        return {
            "contributor_id": contributor_id,
            "contributor_name": contributor_name,
            "stats": stats,
            "sample_assets": assets,
            "scraped_at": datetime.utcnow().isoformat(),
        }
    
    async def scrape_asset_detail(self, asset_id: str) -> Dict[str, Any]:
        if not self.page:
            await self.init_browser()
        
        url = f"{self.BASE_URL}/images/{asset_id}"
        
        logger.info("Scraping asset detail", asset_id=asset_id, url=url)
        
        await self.page.goto(url, wait_until="networkidle")
        await self.random_delay()
        
        content = await self.page.content()
        soup = BeautifulSoup(content, "lxml")
        
        title_elem = soup.select_one("h1, .asset-title")
        title = title_elem.get_text(strip=True) if title_elem else None
        
        keywords = []
        keyword_links = soup.select("a[href*='k='], .keyword-tag")
        for link in keyword_links:
            kw = link.get_text(strip=True)
            if kw and len(kw) > 1:
                keywords.append(kw)
        
        category = None
        category_elem = soup.select_one(".category-link, [data-testid='category']")
        if category_elem:
            category = category_elem.get_text(strip=True)
        
        contributor_link = soup.select_one("a[href*='/contributor/']")
        contributor_id = None
        contributor_name = None
        if contributor_link:
            href = contributor_link.get("href", "")
            contributor_id = href.split("/")[-1].split("?")[0]
            contributor_name = contributor_link.get_text(strip=True)
        
        return {
            "asset_id": asset_id,
            "title": title,
            "keywords": keywords[:50],
            "category": category,
            "contributor_id": contributor_id,
            "contributor_name": contributor_name,
            "scraped_at": datetime.utcnow().isoformat(),
        }


async def execute_scrape_job(job_id: int):
    """Execute a scrape job in the background"""
    async with async_session_maker() as db:
        from sqlalchemy import select
        
        result = await db.execute(select(ScrapeJob).where(ScrapeJob.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error("Scrape job not found", job_id=job_id)
            return
        
        job.status = ScrapeJobStatus.RUNNING
        job.started_at = datetime.utcnow()
        await db.commit()
        
        scraper = AdobeStockScraper()
        
        try:
            if job.job_type == ScrapeJobType.KEYWORD_SEARCH:
                max_results = job.parameters.get("max_results", 100) if job.parameters else 100
                data = await scraper.search_keyword(job.target, max_results=max_results)
                
                kw_result = await db.execute(
                    select(Keyword).where(Keyword.term == job.target)
                )
                keyword = kw_result.scalar_one_or_none()
                
                if not keyword:
                    keyword = Keyword(
                        term=job.target,
                        normalized_term=job.target.lower().strip(),
                    )
                    db.add(keyword)
                    await db.commit()
                    await db.refresh(keyword)
                
                for item in data["results"]:
                    ranking = KeywordRanking(
                        keyword_id=keyword.id,
                        position=item["position"],
                        asset_id=item["asset_id"],
                        title=item.get("title"),
                        contributor_id=item.get("contributor_id"),
                        asset_type=item.get("asset_type"),
                    )
                    db.add(ranking)
                
                keyword.last_scraped_at = datetime.utcnow()
                job.results_count = len(data["results"])
            
            elif job.job_type == ScrapeJobType.PORTFOLIO:
                data = await scraper.scrape_portfolio(job.target)
                
                portfolio_result = await db.execute(
                    select(Portfolio).where(Portfolio.adobe_contributor_id == job.target)
                )
                portfolio = portfolio_result.scalar_one_or_none()
                
                if not portfolio:
                    portfolio = Portfolio(adobe_contributor_id=job.target)
                    db.add(portfolio)
                
                portfolio.contributor_name = data.get("contributor_name")
                portfolio.total_assets = data["stats"]["total_assets"]
                portfolio.total_photos = data["stats"]["photos"]
                portfolio.total_vectors = data["stats"]["vectors"]
                portfolio.total_videos = data["stats"]["videos"]
                portfolio.last_scraped_at = datetime.utcnow()
                
                job.results_count = len(data.get("sample_assets", []))
            
            elif job.job_type == ScrapeJobType.ASSET_DETAIL:
                data = await scraper.scrape_asset_detail(job.target)
                
                asset_result = await db.execute(
                    select(Asset).where(Asset.adobe_id == job.target)
                )
                asset = asset_result.scalar_one_or_none()
                
                if not asset:
                    asset = Asset(
                        adobe_id=job.target,
                        asset_type="photo",
                    )
                    db.add(asset)
                
                asset.title = data.get("title")
                asset.keywords = data.get("keywords")
                asset.contributor_id = data.get("contributor_id")
                asset.contributor_name = data.get("contributor_name")
                asset.scraped_at = datetime.utcnow()
                
                job.results_count = 1
            
            scrape_result = ScrapeResult(
                job_id=job.id,
                result_type=job.job_type.value,
                data=data,
            )
            db.add(scrape_result)
            
            job.status = ScrapeJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(
                "Scrape job completed",
                job_id=job.id,
                job_type=job.job_type.value,
                results_count=job.results_count,
            )
        
        except Exception as e:
            logger.error("Scrape job failed", job_id=job.id, error=str(e))
            job.status = ScrapeJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await db.commit()
        
        finally:
            await scraper.close()
