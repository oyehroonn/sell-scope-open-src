"""Opportunities router - Niche discovery and opportunity scoring"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


class OpportunityScore(BaseModel):
    keyword: str
    overall_score: float
    demand_score: float
    competition_score: float
    gap_score: float
    freshness_score: float
    trend: str = "stable"
    urgency: str = "medium"
    recommendation: Optional[str] = None
    nb_results: int = 0
    unique_contributors: int = 0
    related_searches: List[str] = []
    categories: List[dict] = []


class NicheScore(BaseModel):
    name: str
    slug: str
    total_assets: int = 0
    total_keywords: int = 0
    avg_opportunity_score: float = 0
    avg_demand_score: float = 0
    avg_competition_score: float = 0
    top_keywords: List[str] = []
    trend: str = "stable"
    unique_contributors: int = 0
    premium_ratio: float = 0.0
    estimated_results: int = 0


class HeatmapItem(BaseModel):
    name: str
    slug: str
    score: float
    demand: float = 0
    competition: float
    assets: int
    keywords: int = 0
    top_keywords: List[str] = []
    unique_contributors: int = 0
    premium_ratio: float = 0.0
    estimated_results: int = 0
    trend: str = "stable"


class HeatmapResponse(BaseModel):
    heatmap: List[HeatmapItem]
    generated_at: str


def _generate_recommendation(score: float, demand: float, competition: float) -> str:
    """Generate a recommendation based on scores."""
    if score >= 75:
        if competition < 30:
            return "Excellent opportunity! Low competition with high demand. Create content now."
        else:
            return "Strong opportunity. High demand justifies the competition. Focus on quality."
    elif score >= 50:
        if demand >= 70:
            return "Good potential. High demand but moderate competition. Differentiate your style."
        else:
            return "Moderate opportunity. Consider niche variations for better positioning."
    else:
        if demand < 30:
            return "Low demand in this area. Consider more popular keywords."
        else:
            return "High competition relative to demand. Look for less saturated alternatives."


@router.get("/score/{keyword}", response_model=OpportunityScore)
async def get_opportunity_score(
    keyword: str,
    db: AsyncSession = Depends(get_db),
):
    """Get opportunity score for a specific keyword."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.keyword_analyzer import analyze_keyword_from_scraped_data
        
        store = get_store()
        result = analyze_keyword_from_scraped_data(keyword, store)
        
        recommendation = _generate_recommendation(
            result.get("opportunity_score", 0),
            result.get("demand_score", 0),
            result.get("competition_score", 0),
        )
        
        return OpportunityScore(
            keyword=result.get("keyword", keyword),
            overall_score=result.get("opportunity_score", 0),
            demand_score=result.get("demand_score", 0),
            competition_score=result.get("competition_score", 0),
            gap_score=result.get("gap_score", 50),
            freshness_score=result.get("freshness_score", 50),
            trend=result.get("trend", "stable"),
            urgency=result.get("urgency", "medium"),
            recommendation=recommendation,
            nb_results=result.get("nb_results", 0),
            unique_contributors=result.get("unique_contributors", 0),
            related_searches=result.get("related_searches", []),
            categories=result.get("categories", []),
        )
    
    raise HTTPException(status_code=501, detail="Opportunity scoring requires Pandas store")


@router.get("/top", response_model=List[OpportunityScore])
async def get_top_opportunities(
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0, ge=0, le=100),
    urgency: Optional[str] = Query(None, description="Filter by urgency: high, medium, low"),
    db: AsyncSession = Depends(get_db),
):
    """Get top opportunity keywords sorted by score."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        
        store = get_store()
        results = store.get_top_opportunities(limit=limit * 2, min_score=min_score)
        
        # Filter by urgency if specified
        if urgency:
            results = [r for r in results if r.get("urgency") == urgency]
        
        opportunities = []
        for r in results[:limit]:
            recommendation = _generate_recommendation(
                r.get("opportunity_score", 0),
                r.get("demand_score", 0),
                r.get("competition_score", 0),
            )
            
            opportunities.append(OpportunityScore(
                keyword=r.get("keyword", ""),
                overall_score=r.get("opportunity_score", 0),
                demand_score=r.get("demand_score", 0),
                competition_score=r.get("competition_score", 0),
                gap_score=r.get("gap_score", 50),
                freshness_score=r.get("freshness_score", 50),
                trend=r.get("trend", "stable"),
                urgency=r.get("urgency", "medium"),
                recommendation=recommendation,
                nb_results=r.get("nb_results", 0),
                unique_contributors=r.get("unique_contributors", 0),
                related_searches=r.get("related_searches", [])[:5],
                categories=r.get("categories", [])[:3],
            ))
        
        return opportunities
    
    raise HTTPException(status_code=501, detail="Top opportunities requires Pandas store")


@router.get("/niches", response_model=List[NicheScore])
async def get_niches(
    limit: int = Query(50, ge=1, le=200),
    min_opportunity: float = Query(0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get niches/categories with opportunity scores."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.keyword_analyzer import calculate_category_opportunities
        
        store = get_store()
        results = calculate_category_opportunities(store)
        
        # Filter by min opportunity
        results = [r for r in results if r.get("avg_opportunity_score", 0) >= min_opportunity]
        
        return [
            NicheScore(
                name=r.get("name", ""),
                slug=r.get("slug", ""),
                total_assets=r.get("total_assets", 0),
                total_keywords=r.get("total_keywords", 0),
                avg_opportunity_score=r.get("avg_opportunity_score", 0),
                avg_demand_score=r.get("avg_demand_score", 0),
                avg_competition_score=r.get("avg_competition_score", 0),
                top_keywords=r.get("top_keywords", [])[:5],
                trend=r.get("trend", "stable"),
            )
            for r in results[:limit]
        ]
    
    raise HTTPException(status_code=501, detail="Niches requires Pandas store")


@router.get("/niches/{slug}", response_model=NicheScore)
async def get_niche(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get details for a specific niche."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        
        store = get_store()
        result = store.get_niche_score(slug)
        
        if not result:
            raise HTTPException(status_code=404, detail="Niche not found")
        
        return NicheScore(
            name=result.get("name", ""),
            slug=result.get("slug", slug),
            total_assets=result.get("total_assets", 0),
            total_keywords=result.get("total_keywords", 0),
            avg_opportunity_score=result.get("avg_opportunity_score", 0),
            avg_demand_score=result.get("avg_demand_score", 0),
            avg_competition_score=result.get("avg_competition_score", 0),
            top_keywords=result.get("top_keywords", [])[:10],
            trend=result.get("trend", "stable"),
        )
    
    raise HTTPException(status_code=501, detail="Niche details requires Pandas store")


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_opportunity_heatmap(
    db: AsyncSession = Depends(get_db),
):
    """Get category heatmap data for visualization with full metrics."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.keyword_analyzer import get_opportunity_heatmap
        
        store = get_store()
        result = get_opportunity_heatmap(store)
        
        return HeatmapResponse(
            heatmap=[
                HeatmapItem(
                    name=h.get("name", ""),
                    slug=h.get("slug", ""),
                    score=h.get("score", 0),
                    demand=h.get("demand", 0),
                    competition=h.get("competition", 0),
                    assets=h.get("assets", 0),
                    keywords=h.get("keywords", 0),
                    top_keywords=h.get("top_keywords", [])[:5],
                    unique_contributors=h.get("unique_contributors", 0),
                    premium_ratio=h.get("premium_ratio", 0),
                    estimated_results=h.get("estimated_results", 0),
                    trend=h.get("trend", "stable"),
                )
                for h in result.get("heatmap", [])
            ],
            generated_at=result.get("generated_at", datetime.utcnow().isoformat()),
        )
    
    raise HTTPException(status_code=501, detail="Heatmap requires Pandas store")


@router.post("/analyze")
async def analyze_opportunity(
    keyword: str,
    include_visual_analysis: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Analyze opportunity for a keyword (alias for /score/{keyword})."""
    return await get_opportunity_score(keyword, db)
