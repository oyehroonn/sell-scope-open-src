"""Keywords router - Keyword research and analysis with opportunity scoring"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


class KeywordAnalysis(BaseModel):
    keyword: str
    nb_results: int = 0
    unique_contributors: int = 0
    demand_score: float = 0
    competition_score: float = 0
    gap_score: float = 50
    freshness_score: float = 50
    opportunity_score: float = 0
    trend: str = "stable"
    urgency: str = "medium"
    related_searches: List[str] = []
    categories: List[dict] = []
    scraped_at: Optional[str] = None
    source: Optional[str] = None


class KeywordSearchResult(BaseModel):
    keywords: List[KeywordAnalysis]
    total: int
    page: int
    page_size: int


class TrendingKeyword(BaseModel):
    keyword: str
    nb_results: int = 0
    asset_count: int = 0
    demand_score: float = 0
    competition_score: float = 0
    opportunity_score: float = 0
    trend: str = "stable"
    urgency: str = "medium"


@router.get("/analyze/{keyword}", response_model=KeywordAnalysis)
async def analyze_keyword(
    keyword: str,
    live: bool = Query(False, description="Scrape Adobe Stock live (slower but fresh data)"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a keyword for demand, competition, and opportunity score.
    
    - Set `live=true` to scrape Adobe Stock in real-time (takes ~30-60 seconds)
    - Default uses cached/scraped data for instant results
    """
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.keyword_analyzer import (
            analyze_keyword_from_scraped_data,
            analyze_keyword_live,
        )
        
        store = get_store()
        
        if live:
            # Run live scraping from Adobe Stock
            result = await analyze_keyword_live(keyword, headless=True)
            
            # Store the results even if there was an error (for caching)
            if result.get("nb_results", 0) > 0 or result.get("opportunity_score", 0) > 0:
                store.upsert_keyword_metrics(result)
            
            return KeywordAnalysis(**result)
        
        # Use cached/scraped data
        result = analyze_keyword_from_scraped_data(keyword, store)
        return KeywordAnalysis(**result)
    
    raise HTTPException(status_code=501, detail="Keyword analysis requires Pandas store")


@router.get("/search", response_model=KeywordSearchResult)
async def search_keywords(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search keywords with opportunity scores."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.keyword_analyzer import analyze_keyword_from_scraped_data
        
        store = get_store()
        
        # Search in keyword metrics first
        results = store.search_keyword_metrics(q, limit=page_size * 2)
        
        if not results:
            # Search in asset keywords
            df = store._asset_keywords
            matching = df[df["keyword_term"].str.lower().str.contains(q.lower(), na=False)]
            unique_keywords = matching["keyword_term"].value_counts().head(page_size).index.tolist()
            
            for kw in unique_keywords:
                analysis = analyze_keyword_from_scraped_data(kw, store)
                results.append(analysis)
        
        # Paginate
        offset = (page - 1) * page_size
        total = len(results)
        paginated = results[offset:offset + page_size]
        
        return KeywordSearchResult(
            keywords=[KeywordAnalysis(**r) for r in paginated],
            total=total,
            page=page,
            page_size=page_size,
        )
    
    raise HTTPException(status_code=501, detail="Keyword search requires Pandas store")


@router.get("/trending", response_model=List[TrendingKeyword])
async def get_trending_keywords(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get trending keywords with high demand and opportunity scores."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.keyword_analyzer import get_trending_keywords_from_store
        
        store = get_store()
        results = get_trending_keywords_from_store(store, limit=limit)
        
        return [
            TrendingKeyword(
                keyword=r.get("keyword", ""),
                nb_results=r.get("nb_results", 0),
                asset_count=r.get("asset_count", 0),
                demand_score=r.get("demand_score", 0),
                competition_score=r.get("competition_score", 0),
                opportunity_score=r.get("opportunity_score", 0),
                trend=r.get("trend", "stable"),
                urgency=r.get("urgency", "medium"),
            )
            for r in results
        ]
    
    raise HTTPException(status_code=501, detail="Trending keywords requires Pandas store")


@router.get("/suggestions", response_model=List[str])
async def get_keyword_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get keyword suggestions based on a query prefix."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.keyword_analyzer import get_keyword_suggestions
        
        store = get_store()
        return get_keyword_suggestions(store, q, limit=limit)
    
    raise HTTPException(status_code=501, detail="Keyword suggestions requires Pandas store")


@router.get("/top", response_model=List[KeywordAnalysis])
async def get_top_keywords(
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get top keywords by opportunity score."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        
        store = get_store()
        results = store.get_top_opportunities(limit=limit, min_score=min_score)
        
        return [KeywordAnalysis(**r) for r in results]
    
    raise HTTPException(status_code=501, detail="Top keywords requires Pandas store")


@router.post("/analyze-batch")
async def analyze_keywords_batch(
    keywords: List[str],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze multiple keywords in the background.
    Returns immediately, results are stored for later retrieval.
    """
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.keyword_analyzer import analyze_keyword_from_scraped_data
        
        store = get_store()
        
        # Analyze from existing data (fast)
        results = []
        for kw in keywords[:50]:  # Limit to 50
            result = analyze_keyword_from_scraped_data(kw, store)
            results.append(result)
        
        return {
            "status": "completed",
            "analyzed": len(results),
            "keywords": [r["keyword"] for r in results],
        }
    
    raise HTTPException(status_code=501, detail="Batch analysis requires Pandas store")
