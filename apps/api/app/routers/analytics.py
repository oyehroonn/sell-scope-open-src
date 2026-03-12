"""Analytics router"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.keyword import Keyword, KeywordRanking
from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.opportunity import OpportunityScore

router = APIRouter()


class TrendingKeyword(BaseModel):
    term: str
    search_volume: Optional[int]
    change_pct: Optional[float]
    opportunity_score: Optional[float]


class CategoryStats(BaseModel):
    category_id: int
    category_name: str
    total_assets: int
    avg_competition: float
    top_keywords: List[str]


class MarketOverview(BaseModel):
    total_keywords_tracked: int
    total_portfolios_tracked: int
    total_assets_indexed: int
    avg_opportunity_score: float
    top_categories: List[CategoryStats]


class SeasonalTrend(BaseModel):
    keyword: str
    peak_months: List[int]
    current_demand: float
    next_peak_in_days: Optional[int]


@router.get("/overview", response_model=MarketOverview)
async def get_market_overview(
    db: AsyncSession = Depends(get_db),
):
    keywords_count = await db.execute(select(func.count()).select_from(Keyword))
    portfolios_count = await db.execute(select(func.count()).select_from(Portfolio))
    assets_count = await db.execute(select(func.count()).select_from(Asset))
    
    avg_score = await db.execute(
        select(func.avg(OpportunityScore.overall_score))
    )
    
    return MarketOverview(
        total_keywords_tracked=keywords_count.scalar() or 0,
        total_portfolios_tracked=portfolios_count.scalar() or 0,
        total_assets_indexed=assets_count.scalar() or 0,
        avg_opportunity_score=avg_score.scalar() or 0,
        top_categories=[],
    )


@router.get("/trending", response_model=List[TrendingKeyword])
async def get_trending_keywords(
    period: str = Query("week", enum=["day", "week", "month"]),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Keyword)
        .order_by(Keyword.search_volume_estimate.desc().nullslast())
        .limit(limit)
    )
    
    keywords = result.scalars().all()
    
    trending = []
    for kw in keywords:
        score_result = await db.execute(
            select(OpportunityScore.overall_score)
            .where(OpportunityScore.keyword_id == kw.id)
            .order_by(OpportunityScore.created_at.desc())
            .limit(1)
        )
        score = score_result.scalar_one_or_none()
        
        trending.append(TrendingKeyword(
            term=kw.term,
            search_volume=kw.search_volume_estimate,
            change_pct=None,
            opportunity_score=score,
        ))
    
    return trending


@router.get("/seasonal", response_model=List[SeasonalTrend])
async def get_seasonal_trends(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    seasonal_keywords = [
        {"keyword": "christmas", "peak_months": [11, 12], "current_demand": 0.3},
        {"keyword": "valentine", "peak_months": [1, 2], "current_demand": 0.8},
        {"keyword": "summer", "peak_months": [5, 6, 7], "current_demand": 0.5},
        {"keyword": "halloween", "peak_months": [9, 10], "current_demand": 0.2},
        {"keyword": "easter", "peak_months": [3, 4], "current_demand": 0.4},
        {"keyword": "thanksgiving", "peak_months": [10, 11], "current_demand": 0.3},
        {"keyword": "new year", "peak_months": [12, 1], "current_demand": 0.6},
        {"keyword": "spring", "peak_months": [3, 4, 5], "current_demand": 0.7},
        {"keyword": "autumn", "peak_months": [9, 10, 11], "current_demand": 0.4},
        {"keyword": "winter", "peak_months": [11, 12, 1, 2], "current_demand": 0.5},
    ]
    
    now = datetime.now()
    current_month = now.month
    
    trends = []
    for sk in seasonal_keywords[:limit]:
        next_peak = None
        for peak_month in sk["peak_months"]:
            if peak_month >= current_month:
                days_until = (peak_month - current_month) * 30
                if next_peak is None or days_until < next_peak:
                    next_peak = days_until
            else:
                days_until = (12 - current_month + peak_month) * 30
                if next_peak is None or days_until < next_peak:
                    next_peak = days_until
        
        trends.append(SeasonalTrend(
            keyword=sk["keyword"],
            peak_months=sk["peak_months"],
            current_demand=sk["current_demand"],
            next_peak_in_days=next_peak,
        ))
    
    return trends


@router.get("/categories")
async def get_category_analytics(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            Asset.category_id,
            Asset.category_name,
            func.count(Asset.id).label("count"),
        )
        .where(Asset.category_id.isnot(None))
        .group_by(Asset.category_id, Asset.category_name)
        .order_by(func.count(Asset.id).desc())
        .limit(50)
    )
    
    categories = []
    for row in result.all():
        categories.append({
            "category_id": row.category_id,
            "category_name": row.category_name,
            "asset_count": row.count,
        })
    
    return {"categories": categories}


@router.get("/benchmark")
async def get_benchmark_data(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_portfolios = await db.execute(
        select(func.count()).select_from(Portfolio)
    )
    
    avg_assets = await db.execute(
        select(func.avg(Portfolio.total_assets))
    )
    
    return {
        "total_contributors_in_network": total_portfolios.scalar() or 0,
        "avg_portfolio_size": avg_assets.scalar() or 0,
        "percentiles": {
            "assets": {
                "p25": 50,
                "p50": 200,
                "p75": 800,
                "p90": 2000,
            },
        },
        "top_categories_distribution": [],
        "avg_time_to_first_sale_days": 14,
    }


@router.get("/live-pulse")
async def get_live_market_pulse(
    db: AsyncSession = Depends(get_db),
):
    recent_rankings = await db.execute(
        select(KeywordRanking)
        .order_by(KeywordRanking.scraped_at.desc())
        .limit(100)
    )
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "trending_now": [],
        "recent_uploads": [],
        "ranking_changes": [],
        "seasonal_countdown": {
            "event": "Valentine's Day",
            "days_until": 30,
            "recommended_upload_deadline": 14,
        },
    }
