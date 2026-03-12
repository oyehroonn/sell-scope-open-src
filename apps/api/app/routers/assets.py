"""Assets router for scraped Adobe Stock assets"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.models.asset import Asset
from app.models.asset_keyword import AssetKeyword
from app.models.keyword import Keyword
from app.models.similar import SimilarAsset

router = APIRouter()


class AssetResponse(BaseModel):
    id: int
    adobe_id: str
    title: Optional[str]
    asset_type: str
    contributor_id: Optional[str]
    contributor_name: Optional[str]
    thumbnail_url: Optional[str]
    preview_url: Optional[str]
    keywords: Optional[List[str]]
    category: Optional[str]
    width: Optional[int]
    height: Optional[int]
    orientation: Optional[str]
    is_premium: bool
    similar_count: Optional[int]
    scraped_at: datetime

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    assets: List[AssetResponse]
    total: int
    page: int
    page_size: int


class AssetStats(BaseModel):
    total_assets: int
    by_type: dict
    by_premium: dict
    by_contributor: int
    latest_scrape: Optional[datetime]


class AssetFullResponse(AssetResponse):
    description: Optional[str] = None
    asset_url: Optional[str] = None
    file_format: Optional[str] = None
    keyword_terms: Optional[List[str]] = None
    similar_assets: Optional[List[dict]] = None


@router.get("/", response_model=AssetListResponse)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    asset_type: Optional[str] = None,
    contributor_id: Optional[str] = None,
    is_premium: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all scraped assets with optional filtering"""
    offset = (page - 1) * page_size
    
    query = select(Asset)
    count_query = select(func.count()).select_from(Asset)
    
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)
        count_query = count_query.where(Asset.asset_type == asset_type)
    
    if contributor_id:
        query = query.where(Asset.contributor_id == contributor_id)
        count_query = count_query.where(Asset.contributor_id == contributor_id)
    
    if is_premium is not None:
        query = query.where(Asset.is_premium == is_premium)
        count_query = count_query.where(Asset.is_premium == is_premium)
    
    if search:
        search_filter = or_(
            Asset.title.ilike(f"%{search}%"),
            Asset.contributor_name.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    query = query.order_by(Asset.scraped_at.desc())
    
    result = await db.execute(query.offset(offset).limit(page_size))
    assets = result.scalars().all()
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    return AssetListResponse(
        assets=assets,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=AssetStats)
async def get_asset_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get statistics about scraped assets"""
    total_result = await db.execute(select(func.count()).select_from(Asset))
    total = total_result.scalar() or 0
    
    type_result = await db.execute(
        select(Asset.asset_type, func.count())
        .group_by(Asset.asset_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}
    
    premium_result = await db.execute(
        select(Asset.is_premium, func.count())
        .group_by(Asset.is_premium)
    )
    by_premium = {"premium": 0, "standard": 0}
    for row in premium_result.all():
        if row[0]:
            by_premium["premium"] = row[1]
        else:
            by_premium["standard"] = row[1]
    
    contributor_result = await db.execute(
        select(func.count(func.distinct(Asset.contributor_id)))
    )
    contributor_count = contributor_result.scalar() or 0
    
    latest_result = await db.execute(
        select(func.max(Asset.scraped_at))
    )
    latest_scrape = latest_result.scalar()
    
    return AssetStats(
        total_assets=total,
        by_type=by_type,
        by_premium=by_premium,
        by_contributor=contributor_count,
        latest_scrape=latest_scrape,
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific asset by Adobe ID"""
    result = await db.execute(
        select(Asset).where(Asset.adobe_id == asset_id)
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return asset


@router.get("/{asset_id}/full", response_model=AssetFullResponse)
async def get_asset_full(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get asset with keywords (from AssetKeyword) and similar assets."""
    result = await db.execute(
        select(Asset).where(Asset.adobe_id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    kw_result = await db.execute(
        select(Keyword.term)
        .join(AssetKeyword, AssetKeyword.keyword_id == Keyword.id)
        .where(AssetKeyword.asset_id == asset.id)
    )
    keyword_terms = [r[0] for r in kw_result.all()]

    sim_result = await db.execute(
        select(Asset)
        .join(SimilarAsset, SimilarAsset.similar_to_asset_id == Asset.id)
        .where(SimilarAsset.asset_id == asset.id)
        .limit(20)
    )
    similar_assets = [
        {"adobe_id": a.adobe_id, "title": a.title, "thumbnail_url": a.thumbnail_url, "preview_url": a.preview_url}
        for a in sim_result.scalars().all()
    ]

    base = AssetResponse.model_validate(asset)
    return AssetFullResponse(
        **base.model_dump(),
        description=getattr(asset, "description", None),
        asset_url=getattr(asset, "asset_url", None),
        file_format=getattr(asset, "file_format", None),
        keyword_terms=keyword_terms,
        similar_assets=similar_assets,
    )


@router.get("/contributor/{contributor_id}", response_model=AssetListResponse)
async def get_contributor_assets(
    contributor_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get all assets from a specific contributor"""
    offset = (page - 1) * page_size
    
    query = select(Asset).where(
        Asset.contributor_id == contributor_id
    ).order_by(Asset.scraped_at.desc())
    
    count_query = select(func.count()).select_from(Asset).where(
        Asset.contributor_id == contributor_id
    )
    
    result = await db.execute(query.offset(offset).limit(page_size))
    assets = result.scalars().all()
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    return AssetListResponse(
        assets=assets,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an asset by Adobe ID"""
    result = await db.execute(
        select(Asset).where(Asset.adobe_id == asset_id)
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    await db.delete(asset)
    await db.commit()
    
    return {"status": "deleted", "asset_id": asset_id}
