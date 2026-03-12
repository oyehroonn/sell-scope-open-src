"""Portfolio Coach Service - Personal portfolio intelligence"""

from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Portfolio, PortfolioAsset
from app.models.asset import Asset


async def generate_insights(contributor_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    """Generate coaching insights for a portfolio"""
    
    portfolio_result = await db.execute(
        select(Portfolio).where(Portfolio.adobe_contributor_id == contributor_id)
    )
    portfolio = portfolio_result.scalar_one_or_none()
    
    if not portfolio:
        return []
    
    insights = []
    
    underperformers = await _find_underperformers(portfolio, db)
    if underperformers:
        insights.append({
            "insight_type": "underperformer",
            "title": "High Impressions, Low Conversions",
            "description": f"Found {len(underperformers)} assets with high visibility but low download rates. These may need title/keyword optimization.",
            "affected_assets": [a["adobe_id"] for a in underperformers[:5]],
            "recommendation": "Review titles and keywords. Consider if the preview accurately represents the content. Test different keyword strategies.",
            "priority": "high",
        })
    
    stale_winners = await _find_stale_winners(portfolio, db)
    if stale_winners:
        insights.append({
            "insight_type": "stale_winner",
            "title": "Winning Assets Need Fresh Variants",
            "description": f"Found {len(stale_winners)} high-performing assets that haven't been updated with variants. Create variations to capture more searches.",
            "affected_assets": [a["adobe_id"] for a in stale_winners[:5]],
            "recommendation": "Create 3-5 variants of each winning asset: different angles, compositions, color treatments, or contexts.",
            "priority": "high",
        })
    
    cannibalization = await _detect_cannibalization(portfolio, db)
    if cannibalization:
        insights.append({
            "insight_type": "cannibalization",
            "title": "Potential Keyword Cannibalization",
            "description": f"Found {len(cannibalization)} groups of assets that may be competing against each other for the same keywords.",
            "affected_assets": cannibalization[0]["assets"] if cannibalization else [],
            "recommendation": "Differentiate keywords between similar assets. Use more specific long-tail keywords for each variant.",
            "priority": "medium",
        })
    
    category_gaps = await _analyze_category_gaps(portfolio, db)
    if category_gaps:
        insights.append({
            "insight_type": "category_gap",
            "title": "Underrepresented Categories",
            "description": f"Your portfolio has gaps in {len(category_gaps)} high-demand categories that match your style.",
            "affected_assets": [],
            "recommendation": f"Consider expanding into: {', '.join(category_gaps[:3])}. These categories have high demand but low representation in your portfolio.",
            "priority": "medium",
        })
    
    keyword_issues = await _analyze_keyword_health(portfolio, db)
    if keyword_issues:
        insights.append({
            "insight_type": "keyword_health",
            "title": "Keyword Optimization Opportunities",
            "description": f"Found {len(keyword_issues)} assets with suboptimal keyword strategies.",
            "affected_assets": [a["adobe_id"] for a in keyword_issues[:5]],
            "recommendation": "Ensure all assets have 25-45 relevant keywords. Balance generic and specific terms. Include buyer-intent keywords.",
            "priority": "low",
        })
    
    if not insights:
        insights.append({
            "insight_type": "healthy",
            "title": "Portfolio Looking Good!",
            "description": "No major issues detected. Keep up the good work!",
            "affected_assets": [],
            "recommendation": "Continue monitoring performance and expanding into new niches with high opportunity scores.",
            "priority": "low",
        })
    
    return insights


async def _find_underperformers(portfolio: Portfolio, db: AsyncSession) -> List[Dict[str, Any]]:
    """Find assets with high impressions but low downloads"""
    
    result = await db.execute(
        select(PortfolioAsset, Asset)
        .join(Asset, PortfolioAsset.asset_id == Asset.id)
        .where(
            PortfolioAsset.portfolio_id == portfolio.id,
            PortfolioAsset.impressions > 100,
        )
    )
    
    underperformers = []
    for pa, asset in result.all():
        if pa.impressions and pa.downloads:
            ctr = pa.downloads / pa.impressions
            if ctr < 0.01:
                underperformers.append({
                    "adobe_id": asset.adobe_id,
                    "title": asset.title,
                    "impressions": pa.impressions,
                    "downloads": pa.downloads,
                    "ctr": ctr,
                })
    
    return sorted(underperformers, key=lambda x: x["impressions"], reverse=True)


async def _find_stale_winners(portfolio: Portfolio, db: AsyncSession) -> List[Dict[str, Any]]:
    """Find high-performing assets that need variants"""
    
    result = await db.execute(
        select(PortfolioAsset, Asset)
        .join(Asset, PortfolioAsset.asset_id == Asset.id)
        .where(PortfolioAsset.portfolio_id == portfolio.id)
        .order_by(PortfolioAsset.downloads.desc().nullslast())
        .limit(20)
    )
    
    winners = []
    for pa, asset in result.all():
        if pa.downloads and pa.downloads > 5:
            winners.append({
                "adobe_id": asset.adobe_id,
                "title": asset.title,
                "downloads": pa.downloads,
                "keywords": asset.keywords,
            })
    
    return winners[:10]


async def _detect_cannibalization(portfolio: Portfolio, db: AsyncSession) -> List[Dict[str, Any]]:
    """Detect assets that might be cannibalizing each other's rankings"""
    
    result = await db.execute(
        select(PortfolioAsset, Asset)
        .join(Asset, PortfolioAsset.asset_id == Asset.id)
        .where(PortfolioAsset.portfolio_id == portfolio.id)
        .limit(100)
    )
    
    assets_with_keywords = []
    for pa, asset in result.all():
        if asset.keywords:
            assets_with_keywords.append({
                "adobe_id": asset.adobe_id,
                "keywords": set(asset.keywords[:20]),
            })
    
    cannibalization_groups = []
    checked = set()
    
    for i, asset1 in enumerate(assets_with_keywords):
        if asset1["adobe_id"] in checked:
            continue
        
        similar_assets = [asset1["adobe_id"]]
        
        for asset2 in assets_with_keywords[i+1:]:
            if asset2["adobe_id"] in checked:
                continue
            
            overlap = len(asset1["keywords"] & asset2["keywords"])
            similarity = overlap / max(len(asset1["keywords"]), len(asset2["keywords"]))
            
            if similarity > 0.7:
                similar_assets.append(asset2["adobe_id"])
                checked.add(asset2["adobe_id"])
        
        if len(similar_assets) > 1:
            cannibalization_groups.append({
                "assets": similar_assets,
                "overlap_score": len(similar_assets),
            })
            checked.add(asset1["adobe_id"])
    
    return sorted(cannibalization_groups, key=lambda x: x["overlap_score"], reverse=True)


async def _analyze_category_gaps(portfolio: Portfolio, db: AsyncSession) -> List[str]:
    """Find high-opportunity categories missing from portfolio"""
    
    high_demand_categories = [
        "Business", "Technology", "Healthcare", "Food & Drink",
        "Lifestyle", "Nature", "Education", "Sports",
    ]
    
    result = await db.execute(
        select(Asset.category_name, func.count(Asset.id))
        .join(PortfolioAsset, Asset.id == PortfolioAsset.asset_id)
        .where(PortfolioAsset.portfolio_id == portfolio.id)
        .group_by(Asset.category_name)
    )
    
    existing_categories = {row[0] for row in result.all() if row[0]}
    
    gaps = [cat for cat in high_demand_categories if cat not in existing_categories]
    
    return gaps


async def _analyze_keyword_health(portfolio: Portfolio, db: AsyncSession) -> List[Dict[str, Any]]:
    """Analyze keyword health across the portfolio"""
    
    result = await db.execute(
        select(PortfolioAsset, Asset)
        .join(Asset, PortfolioAsset.asset_id == Asset.id)
        .where(PortfolioAsset.portfolio_id == portfolio.id)
        .limit(50)
    )
    
    issues = []
    for pa, asset in result.all():
        keyword_count = len(asset.keywords) if asset.keywords else 0
        
        if keyword_count < 20:
            issues.append({
                "adobe_id": asset.adobe_id,
                "issue": "under_keyworded",
                "keyword_count": keyword_count,
            })
        elif keyword_count > 49:
            issues.append({
                "adobe_id": asset.adobe_id,
                "issue": "over_keyworded",
                "keyword_count": keyword_count,
            })
    
    return issues
