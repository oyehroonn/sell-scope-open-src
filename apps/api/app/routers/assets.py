"""Assets router for scraped Adobe Stock assets"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.models.asset import Asset
from app.models.asset_keyword import AssetKeyword
from app.models.keyword import Keyword
from app.models.similar import SimilarAsset

router = APIRouter()


def _safe_int(val) -> Optional[int]:
    """Convert value to int safely, returning None for empty/invalid values."""
    if val is None or val == "" or val == "None":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _safe_bool(val) -> bool:
    """Convert value to bool safely."""
    if val is None or val == "" or val == "None":
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return bool(val)


def _asset_row_to_response(row: dict) -> "AssetResponse":
    """Build AssetResponse from CSV/Pandas store row (synthetic id for API compatibility)."""
    sid = abs(hash(row.get("adobe_id") or "")) % 2147483647
    return AssetResponse(
        id=sid,
        adobe_id=row.get("adobe_id") or "",
        title=row.get("title") or None,
        asset_type=row.get("asset_type") or "photo",
        contributor_id=row.get("contributor_id") or None,
        contributor_name=row.get("contributor_name") or None,
        thumbnail_url=row.get("thumbnail_url") or None,
        preview_url=row.get("preview_url") or None,
        keywords=row.get("keywords") if isinstance(row.get("keywords"), list) else None,
        category=row.get("category") or None,
        width=_safe_int(row.get("width")),
        height=_safe_int(row.get("height")),
        orientation=row.get("orientation") or None,
        is_premium=_safe_bool(row.get("is_premium")),
        similar_count=_safe_int(row.get("similar_count")),
        in_library=_safe_bool(row.get("in_library")),
        scraped_at=row.get("scraped_at") or datetime.utcnow(),
    )


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
    in_library: bool = False
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
    in_library: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all scraped assets with optional filtering"""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        offset = (page - 1) * page_size
        items, total = store.get_all_assets(offset=offset, limit=page_size, asset_type=asset_type, contributor_id=contributor_id, is_premium=is_premium, search=search, in_library=in_library)
        return AssetListResponse(
            assets=[_asset_row_to_response(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )
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
    in_library: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get statistics about assets. Use in_library=true to get stats for library only."""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        from collections import Counter
        store = get_store()
        all_items = store.get_all_asset_rows()
        
        # Filter by library status if specified
        if in_library is not None:
            items = [a for a in all_items if _safe_bool(a.get("in_library")) == in_library]
        else:
            items = all_items
        
        total = len(items)
        by_type = dict(Counter(a.get("asset_type") or "photo" for a in items))
        
        # Count premium assets - handle both bool and string "True"/"False"
        premium_c = sum(1 for a in items if a.get("is_premium") in (True, "True", "true", 1, "1"))
        by_premium = {"premium": premium_c, "standard": total - premium_c}
        
        contributor_count = len({a.get("contributor_id") for a in items if a.get("contributor_id")})
        
        # Get latest scrape/add - handle string dates
        scrape_dates = []
        for a in items:
            # Use added_to_library_at if filtering by library, otherwise scraped_at
            date_field = "added_to_library_at" if in_library else "scraped_at"
            sa = a.get(date_field) or a.get("scraped_at")
            if sa and sa not in (None, "", "None"):
                scrape_dates.append(str(sa))
        latest_scrape = max(scrape_dates, default=None) if scrape_dates else None
        
        return AssetStats(
            total_assets=total,
            by_type=by_type,
            by_premium=by_premium,
            by_contributor=contributor_count,
            latest_scrape=latest_scrape,
        )
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


class LibraryActionResponse(BaseModel):
    success: bool
    message: str
    adobe_id: str
    in_library: bool


@router.post("/{asset_id}/library", response_model=LibraryActionResponse)
async def add_to_library(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Add an asset to the user's library"""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        success = store.add_to_library(asset_id)
        if not success:
            raise HTTPException(status_code=404, detail="Asset not found")
        return LibraryActionResponse(
            success=True,
            message="Asset added to library",
            adobe_id=asset_id,
            in_library=True,
        )
    raise HTTPException(status_code=501, detail="Library feature requires Pandas store")


@router.delete("/{asset_id}/library", response_model=LibraryActionResponse)
async def remove_from_library(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Remove an asset from the user's library"""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        success = store.remove_from_library(asset_id)
        if not success:
            raise HTTPException(status_code=404, detail="Asset not found")
        return LibraryActionResponse(
            success=True,
            message="Asset removed from library",
            adobe_id=asset_id,
            in_library=False,
        )
    raise HTTPException(status_code=501, detail="Library feature requires Pandas store")


@router.get("/{asset_id}/library-status")
async def get_library_status(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Check if an asset is in the library"""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        in_library = store.is_in_library(asset_id)
        return {"adobe_id": asset_id, "in_library": in_library}
    raise HTTPException(status_code=501, detail="Library feature requires Pandas store")


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific asset by Adobe ID"""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        row = store.get_asset(asset_id)
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        return _asset_row_to_response(row)
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
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        row = store.get_asset(asset_id)
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        base = _asset_row_to_response(row)
        keyword_terms = store.get_asset_keywords(asset_id)
        similar_assets = store.get_similar(asset_id, limit=20)
        return AssetFullResponse(
            **base.model_dump(),
            description=row.get("description"),
            asset_url=row.get("asset_url"),
            file_format=row.get("file_format"),
            keyword_terms=keyword_terms,
            similar_assets=similar_assets,
        )
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


@router.get("/{asset_id}/scraped")
async def get_asset_scraped_data(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the full scraped payload for an asset (all scraped fields). Only when using Pandas store."""
    if getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        if hasattr(store, "get_asset_full_scraped"):
            full = store.get_asset_full_scraped(asset_id)
            if full is None:
                raise HTTPException(status_code=404, detail="Asset not found")
            return full
    raise HTTPException(status_code=404, detail="Asset not found or scraped data only available with Pandas store")


@router.get("/contributor/{contributor_id}", response_model=AssetListResponse)
async def get_contributor_assets(
    contributor_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get all assets from a specific contributor"""
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        offset = (page - 1) * page_size
        items, total = store.get_all_assets(offset=offset, limit=page_size, contributor_id=contributor_id)
        return AssetListResponse(
            assets=[_asset_row_to_response(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )
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
    if getattr(settings, "USE_CSV_STORE", False) or getattr(settings, "USE_PANDAS_STORE", False):
        from app.store import get_store
        store = get_store()
        if not store.delete_asset(asset_id):
            raise HTTPException(status_code=404, detail="Asset not found")
        return {"status": "deleted", "asset_id": asset_id}
    result = await db.execute(
        select(Asset).where(Asset.adobe_id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.delete(asset)
    await db.commit()
    return {"status": "deleted", "asset_id": asset_id}
