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
    gap_score: float = 50,
    freshness_score: float = 50,
) -> Dict[str, Any]:
    """
    Calculate opportunity scores based on demand and competition metrics.
    
    Formula:
    - Demand Score: Based on nb_results (more results = more demand)
    - Competition Score: Based on unique contributors (more = higher competition)
    - Opportunity = (Demand * 0.35) + (100 - Competition) * 0.25 + Gap * 0.20 + Freshness * 0.20
    """
    # Demand Score (0-100): Based on number of results
    if nb_results >= 100000:
        demand_score = 100
    elif nb_results >= 10000:
        demand_score = 70 + (min(nb_results, 100000) - 10000) / 90000 * 30
    elif nb_results >= 1000:
        demand_score = 40 + (nb_results - 1000) / 9000 * 30
    elif nb_results > 0:
        demand_score = nb_results / 1000 * 40
    else:
        demand_score = 0
    
    # Competition Score (0-100): Based on unique contributors
    if unique_contributors == 0:
        competition_score = 0
    elif unique_contributors >= 100:
        competition_score = 100
    else:
        competition_score = unique_contributors
    
    # Opportunity Score: Weighted combination
    opportunity_score = (
        demand_score * 0.35 +
        (100 - competition_score) * 0.25 +
        gap_score * 0.20 +
        freshness_score * 0.20
    )
    
    # Determine trend based on demand level
    if demand_score >= 70:
        trend = "up"
    elif demand_score >= 40:
        trend = "stable"
    else:
        trend = "down"
    
    # Determine urgency
    if opportunity_score >= 75:
        urgency = "high"
    elif opportunity_score >= 50:
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
            "scraped_at": datetime.utcnow().isoformat(),
        }
    
    try:
        cmd = [
            sys.executable or "python3",
            "keyword_analyzer.py",
            keyword,
            "-o", f"output/keyword_analysis_{keyword.replace(' ', '_')}.json",
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
            timeout=120,
        )
        
        output_file = scraper_dir / "output" / f"keyword_analysis_{keyword.replace(' ', '_')}.json"
        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                return data
        
        return {
            "keyword": keyword,
            "error": "Analysis output not found",
            "stderr": result.stderr[:500] if result.stderr else None,
            "scraped_at": datetime.utcnow().isoformat(),
        }
        
    except subprocess.TimeoutExpired:
        return {
            "keyword": keyword,
            "error": "Analysis timed out",
            "scraped_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "keyword": keyword,
            "error": str(e),
            "scraped_at": datetime.utcnow().isoformat(),
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
