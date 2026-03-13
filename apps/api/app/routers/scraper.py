"""Scraper router"""

from typing import Optional, List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.scrape import ScrapeJob, ScrapeJobStatus, ScrapeJobType, ScrapeResult
from app.models.keyword import Keyword, KeywordRanking
from app.models.asset import Asset

router = APIRouter()


class ScrapeRequest(BaseModel):
    target: str
    job_type: ScrapeJobType
    parameters: Optional[dict] = None
    priority: int = 0


class ScrapeJobResponse(BaseModel):
    id: int
    job_type: ScrapeJobType
    status: ScrapeJobStatus
    target: str
    results_count: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BulkImportRequest(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    scraped_at: Optional[str] = None


class BulkImportResponse(BaseModel):
    status: str
    message: str
    total_imported: int
    assets_created: int
    rankings_created: int
    errors: List[str]


class FullImportRequest(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    similar_results: Optional[List[Dict[str, Any]]] = None
    scraped_at: Optional[str] = None


class FullImportResponse(BaseModel):
    status: str
    message: str
    counts: Dict[str, Any]
    errors: List[str]


class LiveScrapeRequest(BaseModel):
    query: str
    max_results: int = 20
    scrape_details: bool = True


class LiveScrapeResponse(BaseModel):
    status: str
    message: str
    results_count: int
    assets: List[Dict[str, Any]]
    errors: List[str]


@router.post("/job", response_model=ScrapeJobResponse)
async def create_scrape_job(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = ScrapeJob(
        job_type=request.job_type,
        target=request.target,
        parameters=request.parameters,
        priority=request.priority,
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    from app.services.scraper_service import execute_scrape_job
    background_tasks.add_task(execute_scrape_job, job.id)
    
    return job


@router.get("/job/{job_id}", response_model=ScrapeJobResponse)
async def get_scrape_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ScrapeJob).where(ScrapeJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.get("/jobs", response_model=list[ScrapeJobResponse])
async def list_scrape_jobs(
    status: Optional[ScrapeJobStatus] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ScrapeJob).order_by(ScrapeJob.created_at.desc())
    
    if status:
        query = query.where(ScrapeJob.status == status)
    
    result = await db.execute(query.limit(limit))
    return result.scalars().all()


@router.post("/keyword/{keyword}")
async def scrape_keyword(
    keyword: str,
    max_results: int = 100,
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = ScrapeJob(
        job_type=ScrapeJobType.KEYWORD_SEARCH,
        target=keyword,
        parameters={"max_results": max_results},
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    if background_tasks:
        from app.services.scraper_service import execute_scrape_job
        background_tasks.add_task(execute_scrape_job, job.id)
    
    return {"job_id": job.id, "status": "queued"}


@router.post("/portfolio/{contributor_id}")
async def scrape_portfolio(
    contributor_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = ScrapeJob(
        job_type=ScrapeJobType.PORTFOLIO,
        target=contributor_id,
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    from app.services.scraper_service import execute_scrape_job
    background_tasks.add_task(execute_scrape_job, job.id)
    
    return {"job_id": job.id, "status": "queued"}


@router.delete("/job/{job_id}")
async def cancel_scrape_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ScrapeJob).where(ScrapeJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in [ScrapeJobStatus.COMPLETED, ScrapeJobStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Job already finished")
    
    job.status = ScrapeJobStatus.CANCELLED
    await db.commit()
    
    return {"status": "cancelled"}


@router.post("/bulk-import", response_model=BulkImportResponse)
async def bulk_import_scrape_results(
    request: BulkImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk import scraped results from the Selenium scraper.
    Creates/updates keywords, assets, and keyword rankings.
    """
    errors = []
    assets_created = 0
    rankings_created = 0
    
    keyword_text = request.query.lower().strip()
    result = await db.execute(
        select(Keyword).where(Keyword.term == keyword_text)
    )
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        keyword = Keyword(
            term=keyword_text,
            normalized_term=keyword_text.lower().strip(),
            search_volume_estimate=len(request.results) * 100,
            last_scraped_at=datetime.utcnow(),
        )
        db.add(keyword)
        await db.flush()
    else:
        keyword.last_scraped_at = datetime.utcnow()
        keyword.search_volume_estimate = max(
            keyword.search_volume_estimate or 0,
            len(request.results) * 100
        )
    
    for item in request.results:
        try:
            adobe_id = str(item.get("asset_id", ""))
            if not adobe_id:
                continue
            
            existing = await db.execute(
                select(Asset).where(Asset.adobe_id == adobe_id)
            )
            asset = existing.scalar_one_or_none()
            
            keywords_list = []
            if item.get("keywords"):
                keywords_list = [k.strip() for k in item["keywords"].split("|") if k.strip()]
            
            if not asset:
                asset = Asset(
                    adobe_id=adobe_id,
                    title=item.get("title", ""),
                    asset_type=item.get("asset_type", "photo"),
                    thumbnail_url=item.get("thumbnail_url", ""),
                    preview_url=item.get("asset_url", ""),
                    contributor_id=item.get("contributor_id"),
                    contributor_name=item.get("contributor_name", ""),
                    keywords=keywords_list,
                    category=item.get("category", ""),
                    width=item.get("width"),
                    height=item.get("height"),
                    orientation=item.get("orientation"),
                    is_premium=item.get("is_premium", False),
                    similar_count=item.get("similar_count"),
                    scraped_data=item,
                )
                db.add(asset)
                await db.flush()
                assets_created += 1
            else:
                asset.title = item.get("title", asset.title)
                asset.thumbnail_url = item.get("thumbnail_url", asset.thumbnail_url)
                if keywords_list:
                    asset.keywords = keywords_list
                asset.scraped_data = item
            
            position = item.get("position", 0)
            
            ranking = KeywordRanking(
                keyword_id=keyword.id,
                asset_id=adobe_id,
                position=position,
                title=item.get("title"),
                contributor_id=item.get("contributor_id"),
                asset_type=item.get("asset_type"),
            )
            db.add(ranking)
            rankings_created += 1
            
        except Exception as e:
            errors.append(f"Error processing asset {item.get('asset_id')}: {str(e)}")
    
    job = ScrapeJob(
        job_type=ScrapeJobType.KEYWORD_SEARCH,
        target=request.query,
        status=ScrapeJobStatus.COMPLETED,
        results_count=len(request.results),
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        parameters={"source": "selenium_scraper", "total_results": len(request.results)}
    )
    db.add(job)
    
    await db.commit()
    
    return BulkImportResponse(
        status="success",
        message=f"Imported {len(request.results)} results for '{request.query}'",
        total_imported=len(request.results),
        assets_created=assets_created,
        rankings_created=rankings_created,
        errors=errors[:10],
    )


@router.post("/full-import", response_model=FullImportResponse)
async def full_import_scrape_results(
    request: FullImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Full import: populates Search, Contributor, Asset, Keyword, AssetKeyword,
    SearchResult, SimilarAsset, Category, AssetCategory.
    Send JSON from scraper export (query, results, similar_results).
    Uses CSV store when USE_CSV_STORE=True; otherwise Postgres.
    """
    from app.core.config import settings
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.full_import_service import full_import_csv
        store = get_store()
        counts = full_import_csv(
            store,
            query=request.query,
            results=request.results,
            similar_results=request.similar_results,
        )
    else:
        from app.services.full_import_service import full_import
        counts = await full_import(
            db,
            query=request.query,
            results=request.results,
            similar_results=request.similar_results,
        )
        await db.commit()
    errors = counts.pop("errors", [])
    return FullImportResponse(
        status="success",
        message=f"Imported {len(request.results)} results + {len(request.similar_results or [])} similar for '{request.query}'",
        counts=counts,
        errors=errors[:20],
    )


@router.post("/live-scrape", response_model=LiveScrapeResponse)
async def live_scrape(
    request: LiveScrapeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run the Adobe Stock scraper live and return results.
    This endpoint actually executes the scraper and imports results.
    """
    import subprocess
    import json
    import os
    from pathlib import Path
    from app.core.config import settings
    
    errors = []
    results = []
    
    try:
        scraper_dir = Path(__file__).parent.parent.parent.parent.parent / "scraper"
        if not scraper_dir.exists():
            scraper_dir = Path("/Users/oyehroonn/Downloads/SellScope/sell-scope-open-src/scraper")
        
        cmd = [
            "python3",
            "adobe_stock_scraper.py",
            request.query,
            "-n", str(request.max_results),
            "--headless",
            "--json",
        ]
        if request.scrape_details:
            cmd.append("--details")
        
        result = subprocess.run(
            cmd,
            cwd=str(scraper_dir),
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        if result.returncode != 0:
            errors.append(f"Scraper error: {result.stderr[:500]}")
        
        output_dir = scraper_dir / "output"
        json_files = sorted(output_dir.glob(f"adobe_stock_{request.query.replace(' ', '_')}*.json"), reverse=True)
        
        if json_files:
            with open(json_files[0], "r") as f:
                data = json.load(f)
                results = data.get("results", [])
                similar = data.get("similar_results", [])
        
        if results:
            if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
                from app.store import get_store
                from app.services.full_import_service import full_import_csv
                store = get_store()
                full_import_csv(store, request.query, results, similar)
            else:
                from app.services.full_import_service import full_import
                await full_import(db, request.query, results, similar)
                await db.commit()
        
        mapped_assets = []
        for item in results:
            mapped_assets.append({
                "adobe_id": str(item.get("asset_id", "")),
                "title": item.get("title"),
                "thumbnail_url": item.get("thumbnail_url"),
                "preview_url": item.get("preview_url") or item.get("asset_url"),
                "asset_type": item.get("asset_type", "photo"),
                "contributor_name": item.get("contributor_name"),
                "contributor_id": item.get("contributor_id"),
                "is_premium": item.get("is_premium", False),
                "is_ai_generated": item.get("is_ai_generated", False),
                "is_editorial": item.get("is_editorial", False),
                "width": item.get("width"),
                "height": item.get("height"),
                "orientation": item.get("orientation"),
                "keyword_count": item.get("keyword_count", 0),
            })
        
        return LiveScrapeResponse(
            status="success",
            message=f"Scraped {len(results)} results for '{request.query}'",
            results_count=len(results),
            assets=mapped_assets,
            errors=errors[:10],
        )
        
    except subprocess.TimeoutExpired:
        return LiveScrapeResponse(
            status="error",
            message="Scraper timed out after 5 minutes",
            results_count=0,
            assets=[],
            errors=["Scraper timed out"],
        )
    except Exception as e:
        return LiveScrapeResponse(
            status="error",
            message=str(e),
            results_count=0,
            assets=[],
            errors=[str(e)],
        )


@router.get("/results/{keyword}")
async def get_scraped_results(
    keyword: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get scraped results for a keyword with their rankings"""
    result = await db.execute(
        select(Keyword).where(Keyword.term == keyword.lower().strip())
    )
    kw = result.scalar_one_or_none()
    
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    rankings_result = await db.execute(
        select(KeywordRanking, Asset)
        .join(Asset, KeywordRanking.asset_id == Asset.adobe_id)
        .where(KeywordRanking.keyword_id == kw.id)
        .order_by(KeywordRanking.position)
        .offset(offset)
        .limit(limit)
    )
    
    results = []
    for ranking, asset in rankings_result:
        results.append({
            "position": ranking.position,
            "asset_id": asset.adobe_id,
            "title": asset.title,
            "asset_type": asset.asset_type,
            "thumbnail_url": asset.thumbnail_url,
            "contributor_name": asset.contributor_name,
            "keywords": asset.keywords,
            "is_premium": asset.is_premium,
            "width": asset.width,
            "height": asset.height,
            "orientation": asset.orientation,
            "scraped_at": ranking.scraped_at.isoformat() if ranking.scraped_at else None,
        })
    
    return {
        "keyword": keyword,
        "total_results": len(results),
        "results": results
    }
