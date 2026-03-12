"""Insights API: top keywords, top contributors, summary stats"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.get("/summary", response_model=InsightsSummary)
async def get_insights_summary(db: AsyncSession = Depends(get_db)):
    """Summary counts for the entire scraped dataset."""
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
    """Most-used keywords across all assets."""
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
