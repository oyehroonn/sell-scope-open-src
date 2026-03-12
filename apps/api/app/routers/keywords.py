"""Keywords router"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.keyword import Keyword, KeywordRanking

router = APIRouter()


class KeywordResponse(BaseModel):
    id: int
    term: str
    search_volume_estimate: Optional[int]
    competition_level: Optional[float]
    category_name: Optional[str]
    related_keywords: Optional[dict]
    last_scraped_at: Optional[datetime]

    class Config:
        from_attributes = True


class KeywordSearchResult(BaseModel):
    keywords: List[KeywordResponse]
    total: int
    page: int
    page_size: int


class KeywordRankingResponse(BaseModel):
    position: int
    asset_id: str
    title: Optional[str]
    contributor_id: Optional[str]
    asset_type: Optional[str]
    scraped_at: datetime

    class Config:
        from_attributes = True


@router.get("/search", response_model=KeywordSearchResult)
async def search_keywords(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    
    query = select(Keyword).where(
        Keyword.term.ilike(f"%{q}%")
    ).order_by(Keyword.search_volume_estimate.desc().nullslast())
    
    count_query = select(func.count()).select_from(Keyword).where(
        Keyword.term.ilike(f"%{q}%")
    )
    
    result = await db.execute(query.offset(offset).limit(page_size))
    keywords = result.scalars().all()
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    return KeywordSearchResult(
        keywords=keywords,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    return keyword


@router.get("/{keyword_id}/rankings", response_model=List[KeywordRankingResponse])
async def get_keyword_rankings(
    keyword_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KeywordRanking)
        .where(KeywordRanking.keyword_id == keyword_id)
        .order_by(KeywordRanking.position)
        .limit(limit)
    )
    
    return result.scalars().all()


@router.get("/trending/", response_model=List[KeywordResponse])
async def get_trending_keywords(
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Keyword).order_by(
        Keyword.search_volume_estimate.desc().nullslast()
    )
    
    if category_id:
        query = query.where(Keyword.category_id == category_id)
    
    result = await db.execute(query.limit(limit))
    
    return result.scalars().all()


@router.get("/suggestions/", response_model=List[str])
async def get_keyword_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Keyword.term)
        .where(Keyword.term.ilike(f"{q}%"))
        .order_by(Keyword.search_volume_estimate.desc().nullslast())
        .limit(limit)
    )
    
    return [row[0] for row in result.all()]
