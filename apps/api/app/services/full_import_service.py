"""Full import of scraped data into nested schema: Search, Contributor, Asset, Keyword, SimilarAsset, etc."""

from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search import Search, SearchResult
from app.models.contributor import Contributor
from app.models.asset import Asset
from app.models.keyword import Keyword
from app.models.asset_keyword import AssetKeyword
from app.models.similar import SimilarAsset
from app.models.category import Category, AssetCategory


async def _get_or_create_contributor(db: AsyncSession, adobe_id: str, name: str = None, profile_url: str = None) -> Contributor:
    if not adobe_id:
        return None
    r = await db.execute(select(Contributor).where(Contributor.adobe_id == adobe_id))
    c = r.scalar_one_or_none()
    if c:
        if name:
            c.name = name
        return c
    c = Contributor(adobe_id=adobe_id, name=name, profile_url=profile_url, scraped_at=datetime.utcnow())
    db.add(c)
    await db.flush()
    return c


async def _get_or_create_keyword(db: AsyncSession, term: str, kw_type: str = "asset") -> Keyword:
    term = (term or "").strip().lower()
    if not term or len(term) > 500:
        return None
    r = await db.execute(select(Keyword).where(Keyword.term == term))
    k = r.scalar_one_or_none()
    if k:
        return k
    k = Keyword(term=term, normalized_term=term, type=kw_type)
    db.add(k)
    await db.flush()
    return k


async def _get_or_create_category(db: AsyncSession, name: str) -> Category:
    name = (name or "").strip()
    if not name:
        return None
    r = await db.execute(select(Category).where(Category.name == name))
    c = r.scalar_one_or_none()
    if c:
        return c
    c = Category(name=name)
    db.add(c)
    await db.flush()
    return c


async def _asset_from_item(item: Dict[str, Any]) -> Dict:
    keywords_list = item.get("keywords_list")
    if not keywords_list and item.get("keywords"):
        keywords_list = [k.strip() for k in str(item["keywords"]).split("|") if k.strip()]
    return {
        "adobe_id": str(item.get("asset_id", "")),
        "title": item.get("title"),
        "description": item.get("description"),
        "asset_type": item.get("asset_type", "photo"),
        "thumbnail_url": item.get("thumbnail_url"),
        "preview_url": item.get("preview_url") or item.get("asset_url"),
        "asset_url": item.get("asset_url"),
        "file_format": item.get("file_format"),
        "contributor_id": item.get("contributor_id"),
        "contributor_name": item.get("contributor_name"),
        "keywords": keywords_list[:100] if keywords_list else None,
        "category": item.get("category"),
        "width": item.get("width"),
        "height": item.get("height"),
        "orientation": item.get("orientation"),
        "is_premium": item.get("is_premium", False),
        "similar_count": item.get("similar_count"),
        "source": item.get("source", "search"),
        "scraped_data": item,
    }


async def full_import(
    db: AsyncSession,
    query: str,
    results: List[Dict[str, Any]],
    similar_results: List[Dict[str, Any]] = None,
) -> Dict[str, int]:
    """
    Import search results and optional similar results into full schema.
    Returns counts: searches, contributors, assets, search_results, keywords, asset_keywords, similar_assets, categories.
    """
    similar_results = similar_results or []
    counts = {
        "searches": 0,
        "contributors": 0,
        "assets": 0,
        "search_results": 0,
        "keywords": 0,
        "asset_keywords": 0,
        "similar_assets": 0,
        "categories": 0,
        "asset_categories": 0,
        "errors": [],
    }
    term = (query or "").strip().lower()
    if not term:
        counts["errors"].append("query is required")
        return counts

    search = Search(
        term=term,
        total_results_available=len(results),
        scraped_at=datetime.utcnow(),
    )
    db.add(search)
    await db.flush()
    counts["searches"] = 1

    asset_id_to_db_id: Dict[str, int] = {}

    for item in results:
        try:
            adobe_id = str(item.get("asset_id", ""))
            if not adobe_id:
                continue

            contrib_adobe = item.get("contributor_id")
            if contrib_adobe:
                await _get_or_create_contributor(
                    db,
                    contrib_adobe,
                    name=item.get("contributor_name"),
                )

            r = await db.execute(select(Asset).where(Asset.adobe_id == adobe_id))
            asset = r.scalar_one_or_none()
            data = await _asset_from_item(item)
            if not asset:
                asset = Asset(**{k: v for k, v in data.items() if k != "scraped_data"})
                if data.get("scraped_data"):
                    asset.scraped_data = data["scraped_data"]
                db.add(asset)
                await db.flush()
                counts["assets"] += 1
            else:
                for k, v in data.items():
                    if k != "scraped_data" and hasattr(asset, k):
                        setattr(asset, k, v)
                if data.get("scraped_data"):
                    asset.scraped_data = data["scraped_data"]

            asset_id_to_db_id[adobe_id] = asset.id

            sr = SearchResult(
                search_id=search.id,
                asset_id=asset.id,
                position=item.get("position", 0),
                page=item.get("search_page", 1),
                scraped_at=datetime.utcnow(),
            )
            db.add(sr)
            counts["search_results"] += 1

            keywords_list = item.get("keywords_list") or (item.get("keywords") and [k.strip() for k in str(item["keywords"]).split("|") if k.strip()]) or []
            for kw_term in keywords_list[:100]:
                kw = await _get_or_create_keyword(db, kw_term, "asset")
                if kw:
                    ak = AssetKeyword(asset_id=asset.id, keyword_id=kw.id, source="meta")
                    db.add(ak)
                    counts["asset_keywords"] += 1

            cat_name = item.get("category")
            if cat_name:
                cat = await _get_or_create_category(db, cat_name)
                if cat:
                    ac = AssetCategory(asset_id=asset.id, category_id=cat.id)
                    db.add(ac)
                    counts["asset_categories"] += 1

        except Exception as e:
            counts["errors"].append(f"asset {item.get('asset_id')}: {str(e)}")

    for item in similar_results:
        try:
            adobe_id = str(item.get("asset_id", ""))
            similar_to_adobe = str(item.get("similar_to_asset_id", ""))
            if not adobe_id or not similar_to_adobe:
                continue

            main_asset_id = asset_id_to_db_id.get(similar_to_adobe)
            if not main_asset_id:
                r = await db.execute(select(Asset).where(Asset.adobe_id == similar_to_adobe))
                a = r.scalar_one_or_none()
                if a:
                    main_asset_id = a.id
                else:
                    continue

            if contrib_adobe := item.get("contributor_id"):
                await _get_or_create_contributor(db, contrib_adobe, name=item.get("contributor_name"))

            r = await db.execute(select(Asset).where(Asset.adobe_id == adobe_id))
            asset = r.scalar_one_or_none()
            data = await _asset_from_item(item)
            if not asset:
                asset = Asset(**{k: v for k, v in data.items() if k != "scraped_data"})
                if data.get("scraped_data"):
                    asset.scraped_data = data["scraped_data"]
                db.add(asset)
                await db.flush()
                counts["assets"] += 1
            asset_id_to_db_id[adobe_id] = asset.id

            sim = SimilarAsset(
                asset_id=main_asset_id,
                similar_to_asset_id=asset.id,
                rank=item.get("rank", 0),
                scraped_at=datetime.utcnow(),
            )
            db.add(sim)
            counts["similar_assets"] += 1

            keywords_list = item.get("keywords_list") or (item.get("keywords") and [k.strip() for k in str(item["keywords"]).split("|") if k.strip()]) or []
            for kw_term in keywords_list[:50]:
                kw = await _get_or_create_keyword(db, kw_term, "asset")
                if kw:
                    ak = AssetKeyword(asset_id=asset.id, keyword_id=kw.id, source="meta")
                    db.add(ak)
                    counts["asset_keywords"] += 1

            if cat_name := item.get("category"):
                cat = await _get_or_create_category(db, cat_name)
                if cat:
                    ac = AssetCategory(asset_id=asset.id, category_id=cat.id)
                    db.add(ac)
                    counts["asset_categories"] += 1

        except Exception as e:
            counts["errors"].append(f"similar {item.get('asset_id')}: {str(e)}")

    return counts


def full_import_csv(store, query: str, results: List[Dict[str, Any]], similar_results: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Full import using CSV store (no DB). Same logic as full_import; returns counts dict with errors list.
    """
    similar_results = similar_results or []
    counts = {
        "searches": 0,
        "contributors": 0,
        "assets": 0,
        "search_results": 0,
        "keywords": 0,
        "asset_keywords": 0,
        "similar_assets": 0,
        "categories": 0,
        "asset_categories": 0,
        "errors": [],
    }
    term = (query or "").strip().lower()
    if not term:
        counts["errors"].append("query is required")
        return counts

    store.upsert_search(term, total_results_available=len(results), scraped_at=datetime.utcnow())
    counts["searches"] = 1

    for item in results:
        try:
            adobe_id = str(item.get("asset_id", ""))
            if not adobe_id:
                continue

            contrib_adobe = item.get("contributor_id")
            if contrib_adobe:
                store.upsert_contributor(contrib_adobe, name=item.get("contributor_name"))

            data = _asset_from_item_sync(item)
            if not store.get_asset(adobe_id):
                counts["assets"] += 1
            store.upsert_asset(data, scraped_data=item)

            store.add_search_result(term, adobe_id, position=item.get("position", 0), page=item.get("search_page", 1))
            counts["search_results"] += 1

            keywords_list = item.get("keywords_list")
            # Handle string representation of list
            if isinstance(keywords_list, str):
                try:
                    import ast
                    keywords_list = ast.literal_eval(keywords_list)
                except:
                    keywords_list = None
            if not keywords_list and item.get("keywords"):
                kw_val = item["keywords"]
                if isinstance(kw_val, str):
                    keywords_list = [k.strip() for k in kw_val.split("|") if k.strip()]
                elif isinstance(kw_val, list):
                    keywords_list = kw_val
            keywords_list = keywords_list or []
            for kw_term in keywords_list[:100]:
                if isinstance(kw_term, str) and len(kw_term) > 1:
                    if store.upsert_keyword(kw_term, "asset"):
                        store.add_asset_keyword(adobe_id, kw_term, "meta")
                        counts["asset_keywords"] += 1

            cat_name = item.get("category")
            if cat_name:
                store.upsert_category(cat_name)
                store.add_asset_category(adobe_id, cat_name)
                counts["asset_categories"] += 1

        except Exception as e:
            counts["errors"].append(f"asset {item.get('asset_id')}: {str(e)}")

    for item in similar_results:
        try:
            adobe_id = str(item.get("asset_id", ""))
            similar_to_adobe = str(item.get("similar_to_asset_id", ""))
            if not adobe_id or not similar_to_adobe:
                continue

            if item.get("contributor_id"):
                store.upsert_contributor(item["contributor_id"], name=item.get("contributor_name"))

            data = _asset_from_item_sync(item)
            if not store.get_asset(adobe_id):
                counts["assets"] += 1
            store.upsert_asset(data, scraped_data=item)

            store.add_similar(similar_to_adobe, adobe_id, rank=item.get("rank", 0))
            counts["similar_assets"] += 1

            keywords_list = item.get("keywords_list")
            if isinstance(keywords_list, str):
                try:
                    import ast
                    keywords_list = ast.literal_eval(keywords_list)
                except:
                    keywords_list = None
            if not keywords_list and item.get("keywords"):
                kw_val = item["keywords"]
                if isinstance(kw_val, str):
                    keywords_list = [k.strip() for k in kw_val.split("|") if k.strip()]
                elif isinstance(kw_val, list):
                    keywords_list = kw_val
            keywords_list = keywords_list or []
            for kw_term in keywords_list[:50]:
                if isinstance(kw_term, str) and len(kw_term) > 1:
                    if store.upsert_keyword(kw_term, "asset"):
                        store.add_asset_keyword(adobe_id, kw_term, "meta")
                        counts["asset_keywords"] += 1

            if item.get("category"):
                store.upsert_category(item["category"])
                store.add_asset_category(adobe_id, item["category"])
                counts["asset_categories"] += 1

        except Exception as e:
            counts["errors"].append(f"similar {item.get('asset_id')}: {str(e)}")

    return counts


def _asset_from_item_sync(item: Dict[str, Any]) -> Dict:
    """Sync version of asset dict from scraper item (no async). Maps ALL scraped fields."""
    keywords_list = item.get("keywords_list")
    if not keywords_list and item.get("keywords"):
        keywords_list = [k.strip() for k in str(item["keywords"]).split("|") if k.strip()]
    
    return {
        # Core identifiers
        "adobe_id": str(item.get("asset_id", "")),
        "title": item.get("title"),
        "description": item.get("description"),
        "asset_type": item.get("asset_type", "photo"),
        "source": item.get("source", "search"),
        # Contributor
        "contributor_id": item.get("contributor_id"),
        "contributor_name": item.get("contributor_name"),
        "contributor_url": item.get("contributor_url"),
        # Licensing
        "is_premium": item.get("is_premium", False),
        "is_editorial": item.get("is_editorial", False),
        "is_ai_generated": item.get("is_ai_generated", False),
        "license_type": item.get("license_type"),
        "has_model_release": item.get("has_model_release"),
        "has_property_release": item.get("has_property_release"),
        # Dimensions
        "width": item.get("width"),
        "height": item.get("height"),
        "orientation": item.get("orientation"),
        "aspect_ratio": item.get("aspect_ratio"),
        "megapixels": item.get("megapixels"),
        # Keywords and categories
        "keywords": keywords_list[:100] if keywords_list else None,
        "keywords_list": keywords_list[:100] if keywords_list else None,
        "keyword_count": item.get("keyword_count"),
        "category": item.get("category"),
        "categories": item.get("categories"),
        # Similar assets
        "similar_count": item.get("similar_count"),
        "similar_asset_ids": item.get("similar_asset_ids"),
        # File info
        "file_format": item.get("file_format"),
        "file_size": item.get("file_size"),
        "dpi": item.get("dpi"),
        # Pricing
        "price": item.get("price"),
        "credits": item.get("credits"),
        # Colors and dates
        "color_palette": item.get("color_palette"),
        "upload_date": item.get("upload_date"),
        # Video-specific
        "video_duration_seconds": item.get("video_duration_seconds"),
        "video_fps": item.get("video_fps"),
        # URLs
        "asset_url": item.get("asset_url"),
        "thumbnail_url": item.get("thumbnail_url"),
        "preview_url": item.get("preview_url") or item.get("asset_url"),
        # Search context
        "search_query": item.get("search_query"),
        # Timestamps
        "scraped_at": item.get("scraped_at"),
        "search_page": item.get("search_page"),
        "position": item.get("position"),
    }
