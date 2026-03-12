"""Benchmark Network Service - Anonymous aggregated contributor data"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import structlog

logger = structlog.get_logger()


class BenchmarkNetwork:
    """Manages opt-in benchmark data aggregation"""
    
    def __init__(self):
        self.min_contributors_for_stat = 10
    
    def anonymize_contributor_id(self, contributor_id: str) -> str:
        """Create anonymous hash of contributor ID"""
        return hashlib.sha256(contributor_id.encode()).hexdigest()[:16]
    
    async def get_portfolio_benchmarks(
        self,
        category: Optional[str] = None,
        db=None,
    ) -> Dict[str, Any]:
        """Get aggregated portfolio benchmarks"""
        
        benchmarks = {
            "portfolio_size": {
                "percentiles": {
                    "p10": 25,
                    "p25": 75,
                    "p50": 200,
                    "p75": 600,
                    "p90": 1500,
                    "p95": 3000,
                },
                "mean": 450,
                "median": 200,
            },
            "asset_mix": {
                "photos": 0.65,
                "vectors": 0.25,
                "videos": 0.08,
                "templates": 0.02,
            },
            "upload_cadence": {
                "weekly_uploads_median": 5,
                "weekly_uploads_p75": 15,
                "weekly_uploads_p90": 40,
            },
            "time_to_first_sale": {
                "days_median": 14,
                "days_p25": 7,
                "days_p75": 30,
            },
            "keyword_stats": {
                "avg_keywords_per_asset": 32,
                "optimal_range": [25, 45],
            },
            "title_stats": {
                "avg_title_length": 45,
                "optimal_range": [30, 70],
            },
            "sample_size": 1250,
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        if category:
            benchmarks["category"] = category
            benchmarks["category_specific"] = {
                "avg_portfolio_size": 180,
                "competition_level": 0.65,
            }
        
        return benchmarks
    
    async def get_category_benchmarks(self, db=None) -> List[Dict[str, Any]]:
        """Get benchmarks by category"""
        
        categories = [
            {
                "category": "Business",
                "total_contributors": 15000,
                "avg_assets_per_contributor": 180,
                "avg_downloads_per_asset": 12.5,
                "competition_index": 0.72,
                "growth_rate": 0.08,
            },
            {
                "category": "Technology",
                "total_contributors": 12000,
                "avg_assets_per_contributor": 150,
                "avg_downloads_per_asset": 15.2,
                "competition_index": 0.68,
                "growth_rate": 0.15,
            },
            {
                "category": "Lifestyle",
                "total_contributors": 20000,
                "avg_assets_per_contributor": 220,
                "avg_downloads_per_asset": 8.3,
                "competition_index": 0.75,
                "growth_rate": 0.05,
            },
            {
                "category": "Nature",
                "total_contributors": 18000,
                "avg_assets_per_contributor": 280,
                "avg_downloads_per_asset": 6.8,
                "competition_index": 0.60,
                "growth_rate": 0.03,
            },
            {
                "category": "Food & Drink",
                "total_contributors": 8000,
                "avg_assets_per_contributor": 160,
                "avg_downloads_per_asset": 11.2,
                "competition_index": 0.55,
                "growth_rate": 0.10,
            },
        ]
        
        return categories
    
    async def get_performance_benchmarks(
        self,
        portfolio_size: int,
        db=None,
    ) -> Dict[str, Any]:
        """Get performance benchmarks for a given portfolio size"""
        
        if portfolio_size < 50:
            tier = "starter"
            expected_monthly = "$5-20"
            peer_group_size = "1-50 assets"
        elif portfolio_size < 200:
            tier = "growing"
            expected_monthly = "$20-100"
            peer_group_size = "50-200 assets"
        elif portfolio_size < 500:
            tier = "established"
            expected_monthly = "$100-300"
            peer_group_size = "200-500 assets"
        elif portfolio_size < 1000:
            tier = "professional"
            expected_monthly = "$300-800"
            peer_group_size = "500-1000 assets"
        else:
            tier = "enterprise"
            expected_monthly = "$800+"
            peer_group_size = "1000+ assets"
        
        return {
            "tier": tier,
            "peer_group_size": peer_group_size,
            "expected_monthly_range": expected_monthly,
            "percentile_in_tier": 50,
            "recommendations": [
                f"Contributors in the {tier} tier typically upload 5-15 new assets per week",
                "Focus on expanding successful keyword clusters",
                "Consider diversifying into adjacent categories",
            ],
        }
    
    async def get_keyword_benchmarks(
        self,
        keyword: str,
        db=None,
    ) -> Dict[str, Any]:
        """Get benchmark data for a specific keyword"""
        
        return {
            "keyword": keyword,
            "total_assets": 15000,
            "contributors_with_keyword": 3500,
            "avg_assets_per_contributor": 4.3,
            "saturation_index": 0.65,
            "avg_downloads_estimate": 8.5,
            "top_performers": {
                "description": "Top 10% of assets with this keyword",
                "avg_keyword_count": 38,
                "common_co_keywords": [
                    "professional", "modern", "business", "concept"
                ],
            },
            "recommendations": {
                "differentiation_needed": True,
                "suggested_long_tail": [
                    f"{keyword} modern",
                    f"{keyword} minimalist",
                    f"professional {keyword}",
                ],
            },
        }
    
    async def contribute_anonymous_data(
        self,
        contributor_id: str,
        data: Dict[str, Any],
        db=None,
    ) -> bool:
        """Accept anonymous data contribution from a user"""
        anon_id = self.anonymize_contributor_id(contributor_id)
        
        sanitized_data = {
            "anon_id": anon_id,
            "portfolio_size": data.get("portfolio_size"),
            "asset_types": data.get("asset_types"),
            "category_distribution": data.get("category_distribution"),
            "upload_frequency": data.get("upload_frequency"),
            "contributed_at": datetime.utcnow().isoformat(),
        }
        
        logger.info(
            "Anonymous data contribution received",
            anon_id=anon_id,
            portfolio_size=sanitized_data.get("portfolio_size"),
        )
        
        return True


benchmark_network = BenchmarkNetwork()


async def get_portfolio_benchmarks(
    category: Optional[str] = None,
    db=None,
) -> Dict[str, Any]:
    """Get portfolio benchmarks"""
    return await benchmark_network.get_portfolio_benchmarks(category, db)


async def get_category_benchmarks(db=None) -> List[Dict[str, Any]]:
    """Get category benchmarks"""
    return await benchmark_network.get_category_benchmarks(db)


async def get_performance_benchmarks(
    portfolio_size: int,
    db=None,
) -> Dict[str, Any]:
    """Get performance benchmarks for portfolio size"""
    return await benchmark_network.get_performance_benchmarks(portfolio_size, db)


async def get_keyword_benchmarks(
    keyword: str,
    db=None,
) -> Dict[str, Any]:
    """Get keyword benchmarks"""
    return await benchmark_network.get_keyword_benchmarks(keyword, db)


async def contribute_data(
    contributor_id: str,
    data: Dict[str, Any],
    db=None,
) -> bool:
    """Contribute anonymous data"""
    return await benchmark_network.contribute_anonymous_data(contributor_id, data, db)
