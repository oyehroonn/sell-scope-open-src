"""Contributors router - Contributor profile and competition analysis endpoints"""

import sys
import json
import subprocess
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.core.config import settings
from app.store import get_store

router = APIRouter()


def _get_scraper_dir() -> Path:
    """Get the scraper directory path."""
    api_dir = Path(__file__).resolve().parent.parent.parent
    scraper_dir = api_dir.parent.parent / "scraper"
    return scraper_dir


class ContributorProfile(BaseModel):
    adobe_id: str
    name: Optional[str] = None
    profile_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    total_assets: int = 0
    total_photos: int = 0
    total_vectors: int = 0
    total_videos: int = 0
    total_templates: int = 0
    total_3d: int = 0
    premium_count: int = 0
    premium_ratio: float = 0.0
    top_categories: List[str] = []
    top_keywords: List[str] = []
    category_distribution: Dict[str, int] = {}
    estimated_join_date: Optional[str] = None
    upload_frequency_monthly: float = 0.0
    niches: List[str] = []
    competition_level: Optional[str] = None
    scraped_at: Optional[str] = None
    source: Optional[str] = None


class ContributorListResult(BaseModel):
    contributors: List[ContributorProfile]
    total: int
    page: int
    page_size: int


class CompetitionAnalysis(BaseModel):
    total_contributors: int = 0
    successful_scrapes: int = 0
    total_combined_assets: int = 0
    avg_portfolio_size: float = 0.0
    avg_premium_ratio: float = 0.0
    common_categories: Dict[str, int] = {}
    common_keywords: Dict[str, int] = {}
    niche_distribution: Dict[str, int] = {}
    top_contributors: List[Dict[str, Any]] = []
    market_concentration: float = 0.0
    analyzed_at: Optional[str] = None


@router.get("/profile/{contributor_id}", response_model=ContributorProfile)
async def get_contributor_profile(
    contributor_id: str,
    force_refresh: bool = Query(False, description="Force scrape even if cached"),
):
    """
    Get or scrape a contributor's profile.
    
    Returns cached data if available, otherwise scrapes the profile from Adobe Stock.
    """
    store = get_store()
    
    # Check cache first
    if not force_refresh:
        cached = store.get_contributor_profile(contributor_id)
        if cached:
            return ContributorProfile(**cached, source="cache")
    
    # Scrape the profile
    try:
        profile_data = await _scrape_contributor_profile(contributor_id)
        
        if profile_data.get("error"):
            raise HTTPException(status_code=500, detail=profile_data.get("error"))
        
        # Store in cache
        store.upsert_contributor_profile(profile_data)
        
        return ContributorProfile(**profile_data, source="live")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles", response_model=ContributorListResult)
async def list_contributor_profiles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="Filter by keyword specialty"),
    niche: Optional[str] = Query(None, description="Filter by niche"),
):
    """
    List cached contributor profiles.
    
    Returns paginated list of contributor profiles from the cache.
    """
    store = get_store()
    
    if keyword:
        all_profiles = store.get_top_contributors_for_keyword(keyword, limit=100)
    elif niche:
        all_profiles = store.search_contributor_profiles(niche, limit=100)
    else:
        all_profiles = store.get_all_contributor_profiles(limit=100)
    
    total = len(all_profiles)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_profiles[start:end]
    
    return ContributorListResult(
        contributors=[ContributorProfile(**p, source="cache") for p in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/top", response_model=List[ContributorProfile])
async def get_top_contributors(
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get top contributors by portfolio size.
    
    Optionally filter by keyword specialty.
    """
    store = get_store()
    
    if keyword:
        profiles = store.get_top_contributors_for_keyword(keyword, limit=limit)
    else:
        profiles = store.get_all_contributor_profiles(limit=limit)
    
    return [ContributorProfile(**p, source="cache") for p in profiles]


@router.post("/analyze-competition", response_model=CompetitionAnalysis)
async def analyze_competition(
    contributor_ids: List[str],
    background_tasks: BackgroundTasks,
):
    """
    Analyze competition among a set of contributors.
    
    Scrapes and compares multiple contributor profiles for market analysis.
    """
    if len(contributor_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 contributors to compare")
    
    if len(contributor_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 contributors per analysis")
    
    try:
        analysis = await _analyze_competition(contributor_ids)
        return CompetitionAnalysis(**analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/for-keyword/{keyword}")
async def get_contributors_for_keyword(
    keyword: str,
    scrape: bool = Query(False, description="Scrape fresh data"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get top contributors for a specific keyword.
    
    Returns cached data or optionally scrapes fresh data.
    """
    store = get_store()
    
    # Check if we have keyword analysis with contributor data
    market_analysis = store.get_market_analysis(keyword.lower())
    
    if market_analysis and market_analysis.get("contributor_profiles"):
        profiles = market_analysis["contributor_profiles"][:limit]
        return {
            "keyword": keyword,
            "contributors": profiles,
            "source": "cache",
            "total": len(profiles),
        }
    
    # Return cached contributor profiles that match the keyword
    profiles = store.get_top_contributors_for_keyword(keyword, limit=limit)
    
    if profiles:
        return {
            "keyword": keyword,
            "contributors": profiles,
            "source": "cache",
            "total": len(profiles),
        }
    
    # If scrape is requested, get fresh data
    if scrape:
        # This would trigger a deep analysis, but we'll just return empty for now
        return {
            "keyword": keyword,
            "contributors": [],
            "source": "pending",
            "message": "Run deep keyword analysis to get contributor data",
            "total": 0,
        }
    
    return {
        "keyword": keyword,
        "contributors": [],
        "source": "none",
        "total": 0,
    }


async def _scrape_contributor_profile(contributor_id: str) -> Dict[str, Any]:
    """Run contributor profile scraper via subprocess."""
    scraper_dir = _get_scraper_dir()
    
    if not scraper_dir.exists():
        return {
            "adobe_id": contributor_id,
            "error": "Scraper directory not found",
        }
    
    output_dir = scraper_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"contributor_{contributor_id}_{timestamp}.json"
    
    cmd = [
        sys.executable or "python3",
        "contributor_scraper.py",
        contributor_id,
        "-o", str(output_file),
        "--headless",
    ]
    
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            cwd=str(scraper_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                return json.load(f)
        
        return {
            "adobe_id": contributor_id,
            "error": "Profile scrape output not found",
            "stderr": result.stderr[:500] if result.stderr else None,
        }
        
    except subprocess.TimeoutExpired:
        return {
            "adobe_id": contributor_id,
            "error": "Profile scrape timed out",
        }
    except Exception as e:
        return {
            "adobe_id": contributor_id,
            "error": str(e),
        }


async def _analyze_competition(contributor_ids: List[str]) -> Dict[str, Any]:
    """Run competition analysis via subprocess."""
    scraper_dir = _get_scraper_dir()
    
    if not scraper_dir.exists():
        return {
            "error": "Scraper directory not found",
            "total_contributors": len(contributor_ids),
            "successful_scrapes": 0,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    output_dir = scraper_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"competition_analysis_{timestamp}.json"
    
    cmd = [
        sys.executable or "python3",
        "contributor_scraper.py",
        *contributor_ids,
        "--analyze",
        "--headless",
    ]
    
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            cwd=str(scraper_dir),
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        # Parse JSON from stdout
        if result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass
        
        return {
            "error": "Competition analysis failed",
            "total_contributors": len(contributor_ids),
            "successful_scrapes": 0,
            "stderr": result.stderr[:500] if result.stderr else None,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
        
    except subprocess.TimeoutExpired:
        return {
            "error": "Competition analysis timed out",
            "total_contributors": len(contributor_ids),
            "successful_scrapes": 0,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_contributors": len(contributor_ids),
            "successful_scrapes": 0,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
