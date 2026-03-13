"""
Keyword Analyzer Service - Analyzes keywords for demand, competition, and opportunity scoring
Integrates with the scraper to fetch real data from Adobe Stock
"""

import os
import sys
import json
import subprocess
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core.config import settings


def _get_scraper_dir() -> Path:
    """Get the scraper directory path."""
    api_dir = Path(__file__).resolve().parent.parent.parent
    scraper_dir = api_dir.parent.parent / "scraper"
    return scraper_dir


def _calculate_opportunity_score(
    nb_results: int,
    unique_contributors: int,
    sample_size: int = 20,
    gap_score: float = None,
    freshness_score: float = None,
) -> Dict[str, Any]:
    """
    Calculate opportunity scores based on demand and competition metrics.
    
    Scoring methodology:
    - Demand Score: Based on total results (market size/interest)
    - Competition Score: Based on market saturation (results volume + contributor diversity)
    - Gap Score: Based on diversity of contributors (opportunity for new entrants)
    - Freshness Score: Estimated based on demand patterns
    - Opportunity Score: Weighted combination favoring high demand + low competition
    """
    # ===== DEMAND SCORE (0-100) =====
    # Based on total results - indicates market interest/search volume
    if nb_results >= 1000000:
        demand_score = 95 + min((nb_results - 1000000) / 10000000 * 5, 5)  # 95-100
    elif nb_results >= 100000:
        demand_score = 80 + (nb_results - 100000) / 900000 * 15  # 80-95
    elif nb_results >= 10000:
        demand_score = 60 + (nb_results - 10000) / 90000 * 20  # 60-80
    elif nb_results >= 1000:
        demand_score = 40 + (nb_results - 1000) / 9000 * 20  # 40-60
    elif nb_results >= 100:
        demand_score = 20 + (nb_results - 100) / 900 * 20  # 20-40
    elif nb_results > 0:
        demand_score = nb_results / 100 * 20  # 0-20
    else:
        demand_score = 0
    
    # ===== COMPETITION SCORE (0-100) =====
    # Based on market saturation - higher = more competitive = harder to rank
    if nb_results == 0:
        competition_score = 0
    else:
        # Base competition from total results
        if nb_results >= 1000000:
            base_competition = 90 + min((nb_results - 1000000) / 10000000 * 10, 10)  # 90-100
        elif nb_results >= 100000:
            base_competition = 70 + (nb_results - 100000) / 900000 * 20  # 70-90
        elif nb_results >= 10000:
            base_competition = 50 + (nb_results - 10000) / 90000 * 20  # 50-70
        elif nb_results >= 1000:
            base_competition = 30 + (nb_results - 1000) / 9000 * 20  # 30-50
        elif nb_results >= 100:
            base_competition = 10 + (nb_results - 100) / 900 * 20  # 10-30
        else:
            base_competition = nb_results / 100 * 10  # 0-10
        
        # Adjust based on contributor diversity
        if unique_contributors > 0 and sample_size > 0:
            diversity = unique_contributors / sample_size
            diversity_factor = diversity * 20
            competition_score = base_competition * 0.7 + diversity_factor * 0.3 + 10
        else:
            competition_score = base_competition
        
        competition_score = min(100, max(0, competition_score))
    
    # ===== GAP SCORE (0-100) =====
    if gap_score is None:
        if unique_contributors > 0 and sample_size > 0:
            concentration = min(unique_contributors / sample_size, 1.0)
            if concentration < 0.3:
                gap_score = 70 + (0.3 - concentration) / 0.3 * 30
            elif concentration < 0.5:
                gap_score = 50 + (0.5 - concentration) / 0.2 * 20
            elif concentration < 0.7:
                gap_score = 35 + (0.7 - concentration) / 0.2 * 15
            else:
                gap_score = 20 + (1.0 - concentration) / 0.3 * 15
            gap_score = max(10, min(100, gap_score))
        else:
            gap_score = 50
    
    # ===== FRESHNESS SCORE (0-100) =====
    if freshness_score is None:
        if demand_score >= 80:
            freshness_score = 60
        elif demand_score >= 50:
            freshness_score = 50
        else:
            freshness_score = 40
    
    # ===== OPPORTUNITY SCORE (0-100) =====
    opportunity_score = (
        demand_score * 0.35 +
        (100 - competition_score) * 0.30 +
        gap_score * 0.20 +
        freshness_score * 0.15
    )
    
    # ===== TREND DETERMINATION =====
    demand_competition_ratio = demand_score / max(competition_score, 1)
    if demand_competition_ratio > 1.2 and demand_score >= 60:
        trend = "up"
    elif demand_competition_ratio < 0.8 or demand_score < 30:
        trend = "down"
    else:
        trend = "stable"
    
    # ===== URGENCY DETERMINATION =====
    if opportunity_score >= 70:
        urgency = "high"
    elif opportunity_score >= 45:
        urgency = "medium"
    else:
        urgency = "low"
    
    return {
        "demand_score": round(demand_score, 2),
        "competition_score": round(competition_score, 2),
        "gap_score": round(gap_score, 2),
        "freshness_score": round(freshness_score, 2),
        "opportunity_score": round(opportunity_score, 2),
        "trend": trend,
        "urgency": urgency,
    }


async def analyze_keyword_live(keyword: str, headless: bool = True) -> Dict[str, Any]:
    """
    Analyze a keyword by scraping Adobe Stock in real-time.
    
    This runs the keyword analyzer scraper as a subprocess.
    """
    scraper_dir = _get_scraper_dir()
    
    if not scraper_dir.exists():
        return {
            "keyword": keyword,
            "error": "Scraper directory not found",
            "nb_results": 0,
            "unique_contributors": 0,
            "demand_score": 0,
            "competition_score": 0,
            "gap_score": 50,
            "freshness_score": 50,
            "opportunity_score": 25,
            "trend": "stable",
            "urgency": "low",
            "related_searches": [],
            "categories": [],
            "scraped_at": datetime.utcnow().isoformat(),
            "source": "error",
        }
    
    try:
        # Ensure output directory exists
        output_dir = scraper_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        safe_keyword = keyword.replace(' ', '_').replace('/', '_').replace('\\', '_')
        output_file = output_dir / f"keyword_analysis_{safe_keyword}.json"
        
        cmd = [
            sys.executable or "python3",
            "keyword_analyzer.py",
            keyword,
            "-o", str(output_file),
        ]
        if headless:
            cmd.append("--headless")
        else:
            cmd.append("--no-headless")
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            cwd=str(scraper_dir),
            capture_output=True,
            text=True,
            timeout=180,  # Increased timeout
        )
        
        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    result_data = data[0]
                else:
                    result_data = data
                
                # Ensure all required fields exist
                result_data.setdefault("keyword", keyword)
                result_data.setdefault("nb_results", 0)
                result_data.setdefault("unique_contributors", 0)
                result_data.setdefault("demand_score", 0)
                result_data.setdefault("competition_score", 0)
                result_data.setdefault("gap_score", 50)
                result_data.setdefault("freshness_score", 50)
                result_data.setdefault("opportunity_score", 0)
                result_data.setdefault("trend", "stable")
                result_data.setdefault("urgency", "medium")
                result_data.setdefault("related_searches", [])
                result_data.setdefault("categories", [])
                result_data["source"] = "live"
                
                return result_data
        
        # If output file not found, return error with default values
        return {
            "keyword": keyword,
            "error": "Analysis output not found",
            "stderr": result.stderr[:500] if result.stderr else None,
            "nb_results": 0,
            "unique_contributors": 0,
            "demand_score": 0,
            "competition_score": 0,
            "gap_score": 50,
            "freshness_score": 50,
            "opportunity_score": 25,
            "trend": "stable",
            "urgency": "low",
            "related_searches": [],
            "categories": [],
            "scraped_at": datetime.utcnow().isoformat(),
            "source": "error",
        }
        
    except subprocess.TimeoutExpired:
        return {
            "keyword": keyword,
            "error": "Analysis timed out - try again or use cached data",
            "nb_results": 0,
            "unique_contributors": 0,
            "demand_score": 0,
            "competition_score": 0,
            "gap_score": 50,
            "freshness_score": 50,
            "opportunity_score": 25,
            "trend": "stable",
            "urgency": "low",
            "related_searches": [],
            "categories": [],
            "scraped_at": datetime.utcnow().isoformat(),
            "source": "timeout",
        }
    except Exception as e:
        return {
            "keyword": keyword,
            "error": str(e),
            "nb_results": 0,
            "unique_contributors": 0,
            "demand_score": 0,
            "competition_score": 0,
            "gap_score": 50,
            "freshness_score": 50,
            "opportunity_score": 25,
            "trend": "stable",
            "urgency": "low",
            "related_searches": [],
            "categories": [],
            "scraped_at": datetime.utcnow().isoformat(),
            "source": "error",
        }


def _parse_list_field(value) -> List:
    """Parse a field that should be a list but might be stored as string."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            import ast
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
        except:
            pass
    return []


def analyze_keyword_from_scraped_data(keyword: str, store) -> Dict[str, Any]:
    """
    Analyze a keyword using already-scraped data from the store.
    
    This provides instant results without scraping.
    """
    keyword_lower = keyword.lower().strip()
    
    # Check if we have metrics for this keyword
    existing = store.get_keyword_metrics(keyword_lower)
    if existing:
        # Ensure list fields are properly parsed
        existing["related_searches"] = _parse_list_field(existing.get("related_searches"))
        existing["categories"] = _parse_list_field(existing.get("categories"))
        return existing
    
    # Calculate from asset keywords
    asset_keywords_df = store._asset_keywords
    assets_df = store._assets
    
    # Find assets with this keyword
    matching = asset_keywords_df[
        asset_keywords_df["keyword_term"].str.lower() == keyword_lower
    ]
    
    if matching.empty:
        # Try partial match
        matching = asset_keywords_df[
            asset_keywords_df["keyword_term"].str.lower().str.contains(keyword_lower, na=False)
        ]
    
    if matching.empty:
        return {
            "keyword": keyword,
            "nb_results": 0,
            "unique_contributors": 0,
            "demand_score": 0,
            "competition_score": 0,
            "gap_score": 50,
            "freshness_score": 50,
            "opportunity_score": 25,
            "trend": "down",
            "urgency": "low",
            "related_searches": [],
            "categories": [],
            "scraped_at": datetime.utcnow().isoformat(),
            "source": "no_data",
        }
    
    # Get asset IDs
    asset_ids = matching["asset_adobe_id"].unique().tolist()
    
    # Get asset details
    assets_with_keyword = assets_df[assets_df["adobe_id"].isin(asset_ids)]
    
    # Calculate metrics
    nb_results = len(asset_ids) * 100  # Estimate based on our sample
    unique_contributors = assets_with_keyword["contributor_id"].nunique()
    
    # Get related keywords (co-occurring keywords)
    related = []
    for aid in asset_ids[:20]:
        kws = asset_keywords_df[asset_keywords_df["asset_adobe_id"] == aid]["keyword_term"].tolist()
        for kw in kws:
            if kw.lower() != keyword_lower and kw not in related:
                related.append(kw)
    
    # Get categories
    categories = []
    asset_cats = store._asset_categories[store._asset_categories["asset_adobe_id"].isin(asset_ids)]
    for cat in asset_cats["category_name"].unique()[:10]:
        if cat:
            categories.append({"name": cat})
    
    # Calculate scores
    scores = _calculate_opportunity_score(nb_results, unique_contributors)
    
    result = {
        "keyword": keyword,
        "nb_results": nb_results,
        "unique_contributors": unique_contributors,
        **scores,
        "related_searches": related[:15],
        "categories": categories[:10],
        "scraped_at": datetime.utcnow().isoformat(),
        "source": "scraped_data",
    }
    
    # Store the metrics
    store.upsert_keyword_metrics(result)
    
    return result


def get_trending_keywords_from_store(store, limit: int = 20) -> List[Dict[str, Any]]:
    """Get trending keywords from the store."""
    # First check keyword_metrics
    trending = store.get_trending_keywords(limit=limit)
    
    if trending:
        return trending
    
    # Fall back to top keywords from asset_keywords
    top_keywords = store.get_top_keywords(limit=limit * 2)
    
    results = []
    for kw in top_keywords[:limit]:
        term = kw.get("term", "")
        if not term:
            continue
        
        # Calculate basic scores
        asset_count = kw.get("asset_count", 0)
        scores = _calculate_opportunity_score(
            nb_results=asset_count * 100,
            unique_contributors=min(asset_count, 50),
        )
        
        results.append({
            "keyword": term,
            "nb_results": asset_count * 100,
            "asset_count": asset_count,
            **scores,
            "source": "top_keywords",
        })
    
    return results


def get_keyword_suggestions(store, query: str, limit: int = 10) -> List[str]:
    """Get keyword suggestions based on a query."""
    query_lower = query.lower().strip()
    
    # Search in asset_keywords
    df = store._asset_keywords
    matching = df[df["keyword_term"].str.lower().str.startswith(query_lower, na=False)]
    
    # Get unique keywords sorted by frequency
    counts = matching["keyword_term"].value_counts()
    suggestions = counts.head(limit).index.tolist()
    
    return suggestions


def calculate_category_opportunities(store) -> List[Dict[str, Any]]:
    """Calculate opportunity scores for each category/niche."""
    # Recalculate niche scores
    store.calculate_niche_scores_from_keywords()
    
    # Get all niche scores
    niches = store.get_all_niche_scores(limit=100)
    
    if not niches:
        # Generate from asset categories
        categories_df = store._asset_categories
        if categories_df.empty:
            return []
        
        category_counts = categories_df["category_name"].value_counts()
        
        results = []
        for cat_name, count in category_counts.items():
            if not cat_name:
                continue
            
            # Calculate basic scores
            scores = _calculate_opportunity_score(
                nb_results=count * 500,
                unique_contributors=min(count, 30),
            )
            
            results.append({
                "name": cat_name,
                "slug": cat_name.lower().replace(" ", "-").replace("&", "and"),
                "total_assets": count,
                "total_keywords": 0,
                "avg_opportunity_score": scores["opportunity_score"],
                "avg_demand_score": scores["demand_score"],
                "avg_competition_score": scores["competition_score"],
                "trend": scores["trend"],
            })
        
        # Sort by opportunity score
        results.sort(key=lambda x: x["avg_opportunity_score"], reverse=True)
        return results[:50]
    
    return niches


def get_opportunity_heatmap(store) -> Dict[str, Any]:
    """Get heatmap data for opportunities visualization."""
    # Get niche scores
    niches = store.get_niche_heatmap()
    
    if not niches:
        # Generate from categories
        categories = calculate_category_opportunities(store)
        niches = [
            {
                "name": c["name"],
                "slug": c["slug"],
                "score": c["avg_opportunity_score"],
                "assets": c["total_assets"],
                "competition": c["avg_competition_score"],
            }
            for c in categories
        ]
    
    return {
        "heatmap": niches,
        "generated_at": datetime.utcnow().isoformat(),
    }
