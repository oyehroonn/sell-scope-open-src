"""Insights API: top keywords, top contributors, summary stats, trends, and category distribution"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.asset import Asset
from app.models.asset_keyword import AssetKeyword
from app.models.keyword import Keyword
from app.models.contributor import Contributor
from app.models.search import Search
from app.models.similar import SimilarAsset

router = APIRouter()


class TopKeyword(BaseModel):
    term: str
    asset_count: int
    opportunity_score: Optional[float] = None
    trend: Optional[str] = None


class TopContributor(BaseModel):
    adobe_id: str
    name: Optional[str]
    asset_count: int


class InsightsSummary(BaseModel):
    total_assets: int
    total_searches: int
    total_contributors: int
    total_keywords: int
    total_similar_links: int
    total_library_assets: int = 0
    avg_opportunity_score: float = 0


class CategoryDistribution(BaseModel):
    name: str
    count: int
    percentage: float


class TrendingKeyword(BaseModel):
    keyword: str
    demand_score: float
    opportunity_score: float
    trend: str
    asset_count: int = 0


class OpportunityHighlight(BaseModel):
    keyword: str
    opportunity_score: float
    urgency: str
    recommendation: str


class InsightsOverview(BaseModel):
    summary: InsightsSummary
    top_keywords: List[TopKeyword]
    top_contributors: List[TopContributor]
    category_distribution: List[CategoryDistribution]
    trending_keywords: List[TrendingKeyword]
    opportunity_highlights: List[OpportunityHighlight]


@router.get("/summary", response_model=InsightsSummary)
async def get_insights_summary(db: AsyncSession = Depends(get_db)):
    """Summary counts for the entire scraped dataset."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        s = store.get_insights_summary()
        
        # Count library assets
        library_assets = len([a for a in store.get_all_asset_rows() if a.get("in_library")])
        
        # Get average opportunity score
        keyword_metrics = store.get_all_keyword_metrics(limit=100)
        avg_opp = 0
        if keyword_metrics:
            scores = [k.get("opportunity_score", 0) for k in keyword_metrics]
            avg_opp = sum(scores) / len(scores) if scores else 0
        
        return InsightsSummary(
            total_assets=s["total_assets"],
            total_searches=s["total_searches"],
            total_contributors=s["total_contributors"],
            total_keywords=s["total_keywords"],
            total_similar_links=s["total_similar_links"],
            total_library_assets=library_assets,
            avg_opportunity_score=round(avg_opp, 2),
        )
    total_assets = (await db.execute(select(func.count()).select_from(Asset))).scalar() or 0
    total_searches = (await db.execute(select(func.count()).select_from(Search))).scalar() or 0
    total_contributors = (await db.execute(select(func.count()).select_from(Contributor))).scalar() or 0
    total_keywords = (await db.execute(select(func.count()).select_from(Keyword))).scalar() or 0
    total_similar_links = (await db.execute(select(func.count()).select_from(SimilarAsset))).scalar() or 0
    return InsightsSummary(
        total_assets=total_assets,
        total_searches=total_searches,
        total_contributors=total_contributors,
        total_keywords=total_keywords,
        total_similar_links=total_similar_links,
    )


@router.get("/top-keywords", response_model=List[TopKeyword])
async def get_top_keywords(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Most-used keywords across all assets with opportunity scores."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        rows = store.get_top_keywords(limit=limit)
        
        # Enrich with opportunity scores
        results = []
        for r in rows:
            term = r["term"]
            metrics = store.get_keyword_metrics(term)
            
            results.append(TopKeyword(
                term=term,
                asset_count=r["asset_count"],
                opportunity_score=metrics.get("opportunity_score") if metrics else None,
                trend=metrics.get("trend") if metrics else None,
            ))
        
        return results
    q = (
        select(Keyword.term, func.count(AssetKeyword.asset_id).label("asset_count"))
        .join(AssetKeyword, AssetKeyword.keyword_id == Keyword.id)
        .group_by(Keyword.id, Keyword.term)
        .order_by(func.count(AssetKeyword.asset_id).desc())
        .limit(limit)
    )
    result = await db.execute(q)
    return [TopKeyword(term=r[0], asset_count=r[1]) for r in result.all()]


@router.get("/top-contributors", response_model=List[TopContributor])
async def get_top_contributors(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Contributors with most scraped assets."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        rows = store.get_top_contributors(limit=limit)
        return [TopContributor(adobe_id=r["adobe_id"], name=r.get("name"), asset_count=r["asset_count"]) for r in rows]
    q = (
        select(Asset.contributor_id, Asset.contributor_name, func.count(Asset.id).label("asset_count"))
        .where(Asset.contributor_id.isnot(None))
        .group_by(Asset.contributor_id, Asset.contributor_name)
        .order_by(func.count(Asset.id).desc())
        .limit(limit)
    )
    result = await db.execute(q)
    return [
        TopContributor(adobe_id=r[0] or "", name=r[1], asset_count=r[2])
        for r in result.all()
    ]


@router.get("/searches", response_model=List[dict])
async def list_searches(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List recent searches (query terms) with result counts."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        rows = store.get_searches(limit=limit)
        return [
            {
                "id": abs(hash(s.get("term") or "")) % 2147483647,
                "term": s.get("term"),
                "total_results_available": s.get("total_results_available"),
                "scraped_at": s["scraped_at"].isoformat() if s.get("scraped_at") else None,
            }
            for s in rows
        ]
    q = select(Search).order_by(Search.scraped_at.desc().nullslast()).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": s.id,
            "term": s.term,
            "total_results_available": s.total_results_available,
            "scraped_at": s.scraped_at.isoformat() if s.scraped_at else None,
        }
        for s in rows
    ]


@router.get("/category-distribution", response_model=List[CategoryDistribution])
async def get_category_distribution(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get distribution of assets across categories."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        
        # Get category counts
        df = store._asset_categories
        if df.empty:
            return []
        
        counts = df["category_name"].value_counts()
        total = counts.sum()
        
        results = []
        for name, count in counts.head(limit).items():
            if name:
                results.append(CategoryDistribution(
                    name=name,
                    count=int(count),
                    percentage=round(count / total * 100, 2) if total > 0 else 0,
                ))
        
        return results
    
    return []


@router.get("/trending", response_model=List[TrendingKeyword])
async def get_trending_insights(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get trending keywords for insights dashboard."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from app.services.keyword_analyzer import get_trending_keywords_from_store
        
        store = get_store()
        results = get_trending_keywords_from_store(store, limit=limit)
        
        return [
            TrendingKeyword(
                keyword=r.get("keyword", ""),
                demand_score=r.get("demand_score", 0),
                opportunity_score=r.get("opportunity_score", 0),
                trend=r.get("trend", "stable"),
                asset_count=r.get("asset_count", 0),
            )
            for r in results
        ]
    
    return []


@router.get("/opportunity-highlights", response_model=List[OpportunityHighlight])
async def get_opportunity_highlights(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get top opportunity highlights for dashboard."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        
        store = get_store()
        results = store.get_top_opportunities(limit=limit, min_score=50)
        
        highlights = []
        for r in results:
            score = r.get("opportunity_score", 0)
            demand = r.get("demand_score", 0)
            competition = r.get("competition_score", 0)
            
            if score >= 75:
                if competition < 30:
                    rec = "Excellent opportunity! Low competition with high demand."
                else:
                    rec = "Strong opportunity. High demand justifies competition."
            elif score >= 50:
                rec = "Good potential. Consider niche variations."
            else:
                rec = "Moderate opportunity. Look for alternatives."
            
            highlights.append(OpportunityHighlight(
                keyword=r.get("keyword", ""),
                opportunity_score=score,
                urgency=r.get("urgency", "medium"),
                recommendation=rec,
            ))
        
        return highlights
    
    return []


@router.get("/overview", response_model=InsightsOverview)
async def get_insights_overview(
    db: AsyncSession = Depends(get_db),
):
    """Get complete insights overview for dashboard."""
    summary = await get_insights_summary(db)
    top_keywords = await get_top_keywords(limit=10, db=db)
    top_contributors = await get_top_contributors(limit=10, db=db)
    category_distribution = await get_category_distribution(limit=10, db=db)
    trending = await get_trending_insights(limit=5, db=db)
    highlights = await get_opportunity_highlights(limit=5, db=db)
    
    return InsightsOverview(
        summary=summary,
        top_keywords=top_keywords,
        top_contributors=top_contributors,
        category_distribution=category_distribution,
        trending_keywords=trending,
        opportunity_highlights=highlights,
    )
