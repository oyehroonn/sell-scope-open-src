"""
Deep Analysis Service - Orchestrates comprehensive keyword analysis with caching
Integrates with the scraper's DeepAnalyzer for multi-page data collection
"""

import os
import sys
import json
import subprocess
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from app.core.config import settings


def _get_scraper_dir() -> Path:
    """Get the scraper directory path."""
    api_dir = Path(__file__).resolve().parent.parent.parent
    scraper_dir = api_dir.parent.parent / "scraper"
    return scraper_dir


class DeepAnalysisService:
    """Service for orchestrating deep keyword analysis with caching."""
    
    def __init__(self, store):
        self.store = store
    
    def _calculate_trend(self, demand_score: float, competition_score: float) -> str:
        """Calculate trend based on demand vs competition."""
        if demand_score > competition_score * 1.2 and demand_score >= 60:
            return "up"
        elif demand_score < competition_score * 0.8 or demand_score < 30:
            return "down"
        return "stable"
    
    async def analyze_keyword_deep(
        self,
        keyword: str,
        depth: str = "medium",
        force_refresh: bool = False,
        progress_callback: Callable = None,
    ) -> Dict[str, Any]:
        """
        Perform deep analysis on a keyword.
        
        Args:
            keyword: Keyword to analyze
            depth: Analysis depth (simple, medium, deep)
            force_refresh: Skip cache and force new analysis
            progress_callback: Optional callback for progress updates
        
        Returns:
            Comprehensive analysis results
        """
        keyword_lower = keyword.lower().strip()
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = self.store.get_market_analysis(keyword_lower, depth)
            if cached:
                if progress_callback:
                    progress_callback({
                        "step": "cache",
                        "progress": 100,
                        "message": "Retrieved from cache",
                    })
                cached["source"] = "cache"
                return cached
        
        # Run deep analysis via subprocess
        result = await self._run_deep_analysis(keyword, depth, progress_callback)
        
        # Store in cache
        if not result.get("error"):
            self.store.upsert_market_analysis(result)
            
            # Also store contributor profiles
            for profile in result.get("contributor_profiles", []):
                if not profile.get("error"):
                    self.store.upsert_contributor_profile(profile)
            
            # Update keyword metrics with enhanced scores
            scoring = result.get("scoring", {})
            search_results = result.get("search_results", {})
            market_analysis = result.get("market_analysis", {})
            visualizations = result.get("visualizations", {})
            
            # Get categories from market analysis (more comprehensive than search_results)
            categories = market_analysis.get("top_categories", []) or search_results.get("categories", [])
            
            self.store.upsert_keyword_metrics({
                "keyword": keyword_lower,
                "nb_results": search_results.get("nb_results", 0),
                "unique_contributors": market_analysis.get("unique_contributors", 0),
                "demand_score": scoring.get("demand_score", 0),
                "competition_score": scoring.get("competition_score", 0),
                "gap_score": scoring.get("gap_score", 0),
                "freshness_score": scoring.get("freshness_score", 0),
                "opportunity_score": scoring.get("opportunity_score", 0),
                "trend": scoring.get("trend", "stable"),
                "urgency": scoring.get("urgency", "medium"),
                "related_searches": search_results.get("related_searches", []),
                "categories": categories,
                "scraped_at": result.get("scraped_at"),
            })
            
            # Store niche scores from visualization data (using actual scraped metrics)
            niche_analysis = visualizations.get("niche_analysis", [])
            for niche in niche_analysis:
                if niche.get("name"):
                    # Use actual scraped data - no hardcoded values
                    self.store.upsert_niche_score({
                        "name": niche.get("name"),
                        "total_assets": niche.get("asset_count", 0),
                        "total_keywords": niche.get("keyword_count", 0),
                        "avg_opportunity_score": niche.get("opportunity_score", 0),
                        "avg_demand_score": niche.get("demand_score", 0),
                        "avg_competition_score": niche.get("competition_score", 0),
                        "top_keywords": niche.get("keywords", []),
                        "trend": self._calculate_trend(
                            niche.get("demand_score", 0),
                            niche.get("competition_score", 0)
                        ),
                        "unique_contributors": niche.get("unique_contributors", 0),
                        "premium_ratio": niche.get("premium_ratio", 0),
                        "avg_price": niche.get("avg_price"),
                        "category": niche.get("category", ""),
                        "source_keyword": keyword_lower,
                    })
            
            # Store category heatmap data (using actual scraped metrics)
            category_heatmap = visualizations.get("category_heatmap", [])
            for cat in category_heatmap:
                if cat.get("name"):
                    # Use actual category-specific metrics from scraping
                    self.store.upsert_niche_score({
                        "name": cat.get("name"),
                        "total_assets": cat.get("count", 0),
                        "total_keywords": cat.get("keyword_count", 0),
                        "avg_opportunity_score": cat.get("opportunity_score", 0),
                        "avg_demand_score": cat.get("demand_score", 0),
                        "avg_competition_score": cat.get("competition_score", 0),
                        "top_keywords": cat.get("top_keywords", []),
                        "trend": self._calculate_trend(
                            cat.get("demand_score", 0),
                            cat.get("competition_score", 0)
                        ),
                        "unique_contributors": cat.get("unique_contributors", 0),
                        "premium_ratio": cat.get("premium_ratio", 0),
                        "estimated_results": cat.get("estimated_results", 0),
                        "price_analysis": cat.get("price_analysis", {}),
                        "source_keyword": keyword_lower,
                    })
        
        result["source"] = "live"
        return result
    
    async def _run_deep_analysis(
        self,
        keyword: str,
        depth: str,
        progress_callback: Callable = None,
    ) -> Dict[str, Any]:
        """Run deep analysis via subprocess."""
        scraper_dir = _get_scraper_dir()
        
        if not scraper_dir.exists():
            return {
                "keyword": keyword,
                "error": f"Scraper directory not found: {scraper_dir}",
                "scraped_at": datetime.utcnow().isoformat(),
            }
        
        try:
            # Ensure output directory exists
            output_dir = scraper_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            safe_keyword = keyword.replace(' ', '_').replace('/', '_').replace('\\', '_')[:50]
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"deep_analysis_{safe_keyword}_{timestamp}.json"
            
            # Use python3 directly instead of sys.executable (which might be the venv python)
            import shutil
            python_path = shutil.which("python3") or sys.executable or "python3"
            
            cmd = [
                python_path,
                "deep_analyzer.py",
                keyword,
                "-d", depth,
                "-o", str(output_file),
                "--headless",
            ]
            
            if progress_callback:
                progress_callback({
                    "step": "starting",
                    "progress": 5,
                    "message": f"Starting {depth} analysis for '{keyword}'...",
                })
            
            # Run with timeout based on depth (increased for parallel browser startup)
            timeout = {"simple": 90, "medium": 240, "deep": 420}.get(depth, 240)
            
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                cwd=str(scraper_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            if output_file.exists():
                with open(output_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if progress_callback:
                    progress_callback({
                        "step": "complete",
                        "progress": 100,
                        "message": "Analysis complete",
                    })
                
                return data
            
            # Include more debug info in error
            return {
                "keyword": keyword,
                "error": "Analysis output not found",
                "debug": {
                    "python_path": python_path,
                    "scraper_dir": str(scraper_dir),
                    "output_file": str(output_file),
                    "return_code": result.returncode,
                    "stdout": result.stdout[:500] if result.stdout else None,
                    "stderr": result.stderr[:1000] if result.stderr else None,
                },
                "scraped_at": datetime.utcnow().isoformat(),
            }
            
        except subprocess.TimeoutExpired:
            return {
                "keyword": keyword,
                "error": f"Analysis timed out after {timeout}s",
                "scraped_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "keyword": keyword,
                "error": str(e),
                "scraped_at": datetime.utcnow().isoformat(),
            }
    
    def get_cached_analysis(self, keyword: str, depth: str = "medium") -> Optional[Dict]:
        """Get cached deep analysis if available and not expired."""
        return self.store.get_market_analysis(keyword.lower().strip(), depth)
    
    def get_analysis_features(self, depth: str) -> Dict[str, Any]:
        """Get features available for each analysis depth."""
        features = {
            "simple": {
                "name": "Simple Research",
                "estimated_time": "30-60 seconds",
                "max_assets": 20,
                "features": [
                    "Search results analysis",
                    "Basic demand & competition scores",
                    "Related keywords",
                    "Category detection",
                ],
                "not_included": [
                    "Asset detail pages",
                    "Contributor profiling",
                    "Similar asset analysis",
                    "Price analysis",
                    "Upload date analysis",
                    "Advanced visualizations",
                ],
            },
            "medium": {
                "name": "Deep Research",
                "estimated_time": "2-3 minutes",
                "max_assets": 30,
                "features": [
                    "Everything in Simple Research",
                    "30 asset detail pages (parallel)",
                    "8 contributor profiles",
                    "Similar asset network",
                    "Price distribution analysis",
                    "Upload date freshness",
                    "Premium/editorial ratio",
                    "Format distribution",
                    "Competitor landscape chart",
                    "Market distribution charts",
                ],
                "not_included": [
                    "Extended similar network",
                ],
            },
            "deep": {
                "name": "Comprehensive Research",
                "estimated_time": "5-7 minutes",
                "max_assets": 60,
                "features": [
                    "Everything in Deep Research",
                    "60 asset detail pages (parallel)",
                    "15 contributor profiles",
                    "Extended similar asset network",
                    "Full contributor portfolio analysis",
                    "Keyword network graph",
                    "Quality gap analysis",
                ],
                "not_included": [],
            },
        }
        return features.get(depth, features["medium"])
    
    def get_comparison_data(self) -> Dict[str, Any]:
        """Get comparison data for depth selector UI."""
        return {
            "depths": ["simple", "medium", "deep"],
            "features": {
                "simple": self.get_analysis_features("simple"),
                "medium": self.get_analysis_features("medium"),
                "deep": self.get_analysis_features("deep"),
            },
            "recommended": "medium",
        }


# Module-level functions for direct import

async def analyze_keyword_deep(
    keyword: str,
    depth: str = "medium",
    store = None,
    force_refresh: bool = False,
    progress_callback: Callable = None,
) -> Dict[str, Any]:
    """
    Convenience function to run deep analysis.
    
    Args:
        keyword: Keyword to analyze
        depth: Analysis depth (simple, medium, deep)
        store: PandasStore instance (will be imported if not provided)
        force_refresh: Skip cache
        progress_callback: Progress callback
    
    Returns:
        Deep analysis results
    """
    if store is None:
        from app.store import get_store
        store = get_store()
    
    service = DeepAnalysisService(store)
    return await service.analyze_keyword_deep(
        keyword=keyword,
        depth=depth,
        force_refresh=force_refresh,
        progress_callback=progress_callback,
    )


def get_analysis_comparison() -> Dict[str, Any]:
    """Get analysis depth comparison for UI."""
    service = DeepAnalysisService(None)
    return service.get_comparison_data()
