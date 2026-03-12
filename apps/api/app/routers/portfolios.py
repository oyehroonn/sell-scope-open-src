"""Portfolios router"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.portfolio import Portfolio, PortfolioAsset
from app.models.asset import Asset

router = APIRouter()


class PortfolioResponse(BaseModel):
    id: int
    adobe_contributor_id: str
    contributor_name: Optional[str]
    total_assets: int
    total_photos: int
    total_vectors: int
    total_videos: int
    estimated_total_downloads: Optional[int]
    top_categories: Optional[List[dict]]
    top_keywords: Optional[List[str]]
    is_owned: bool
    is_tracked: bool
    last_scraped_at: Optional[datetime]

    class Config:
        from_attributes = True


class PortfolioAssetResponse(BaseModel):
    id: int
    asset_id: int
    adobe_id: str
    title: Optional[str]
    thumbnail_url: Optional[str]
    downloads: Optional[int]
    revenue: Optional[float]
    impressions: Optional[int]
    performance_score: Optional[float]

    class Config:
        from_attributes = True


class PortfolioCoachInsight(BaseModel):
    insight_type: str
    title: str
    description: str
    affected_assets: List[str]
    recommendation: str
    priority: str


class TrackPortfolioRequest(BaseModel):
    contributor_id: str


@router.get("/my", response_model=List[PortfolioResponse])
async def get_my_portfolios(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.user_id == int(current_user["user_id"])
        )
    )
    return result.scalars().all()


@router.get("/tracked", response_model=List[PortfolioResponse])
async def get_tracked_portfolios(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.user_id == int(current_user["user_id"]),
            Portfolio.is_tracked == True,
        )
    )
    return result.scalars().all()


@router.post("/track", response_model=PortfolioResponse)
async def track_portfolio(
    request: TrackPortfolioRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.adobe_contributor_id == request.contributor_id
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if portfolio:
        portfolio.is_tracked = True
        portfolio.user_id = int(current_user["user_id"])
    else:
        portfolio = Portfolio(
            adobe_contributor_id=request.contributor_id,
            user_id=int(current_user["user_id"]),
            is_tracked=True,
        )
        db.add(portfolio)
    
    await db.commit()
    await db.refresh(portfolio)
    
    return portfolio


@router.delete("/track/{contributor_id}")
async def untrack_portfolio(
    contributor_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.adobe_contributor_id == contributor_id,
            Portfolio.user_id == int(current_user["user_id"]),
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio.is_tracked = False
    await db.commit()
    
    return {"status": "untracked"}


@router.get("/{contributor_id}", response_model=PortfolioResponse)
async def get_portfolio(
    contributor_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(Portfolio.adobe_contributor_id == contributor_id)
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return portfolio


@router.get("/{contributor_id}/assets", response_model=List[PortfolioAssetResponse])
async def get_portfolio_assets(
    contributor_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("downloads", enum=["downloads", "revenue", "performance_score"]),
    db: AsyncSession = Depends(get_db),
):
    portfolio_result = await db.execute(
        select(Portfolio).where(Portfolio.adobe_contributor_id == contributor_id)
    )
    portfolio = portfolio_result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    offset = (page - 1) * page_size
    
    sort_column = getattr(PortfolioAsset, sort_by)
    
    result = await db.execute(
        select(PortfolioAsset, Asset)
        .join(Asset, PortfolioAsset.asset_id == Asset.id)
        .where(PortfolioAsset.portfolio_id == portfolio.id)
        .order_by(sort_column.desc().nullslast())
        .offset(offset)
        .limit(page_size)
    )
    
    assets = []
    for pa, asset in result.all():
        assets.append({
            "id": pa.id,
            "asset_id": pa.asset_id,
            "adobe_id": asset.adobe_id,
            "title": asset.title,
            "thumbnail_url": asset.thumbnail_url,
            "downloads": pa.downloads,
            "revenue": pa.revenue,
            "impressions": pa.impressions,
            "performance_score": pa.performance_score,
        })
    
    return assets


@router.get("/{contributor_id}/coach", response_model=List[PortfolioCoachInsight])
async def get_portfolio_coach_insights(
    contributor_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.portfolio_coach import generate_insights
    
    insights = await generate_insights(contributor_id, db)
    return insights


@router.get("/{contributor_id}/compare/{other_contributor_id}")
async def compare_portfolios(
    contributor_id: str,
    other_contributor_id: str,
    db: AsyncSession = Depends(get_db),
):
    p1_result = await db.execute(
        select(Portfolio).where(Portfolio.adobe_contributor_id == contributor_id)
    )
    p1 = p1_result.scalar_one_or_none()
    
    p2_result = await db.execute(
        select(Portfolio).where(Portfolio.adobe_contributor_id == other_contributor_id)
    )
    p2 = p2_result.scalar_one_or_none()
    
    if not p1 or not p2:
        raise HTTPException(status_code=404, detail="One or both portfolios not found")
    
    return {
        "portfolio_1": {
            "contributor_id": p1.adobe_contributor_id,
            "total_assets": p1.total_assets,
            "top_categories": p1.top_categories,
        },
        "portfolio_2": {
            "contributor_id": p2.adobe_contributor_id,
            "total_assets": p2.total_assets,
            "top_categories": p2.top_categories,
        },
        "comparison": {
            "asset_difference": p1.total_assets - p2.total_assets,
            "common_categories": [],
            "style_similarity": 0.0,
        },
    }
