"""Opportunity Score Engine - The core intelligence layer"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.models.keyword import Keyword, KeywordRanking
from app.models.asset import Asset
from app.models.opportunity import OpportunityScore, Niche


SEASONAL_KEYWORDS = {
    "christmas": {"peak_months": [11, 12], "weight": 1.5},
    "valentine": {"peak_months": [1, 2], "weight": 1.3},
    "easter": {"peak_months": [3, 4], "weight": 1.2},
    "summer": {"peak_months": [5, 6, 7], "weight": 1.2},
    "halloween": {"peak_months": [9, 10], "weight": 1.4},
    "thanksgiving": {"peak_months": [10, 11], "weight": 1.2},
    "new year": {"peak_months": [12, 1], "weight": 1.3},
    "spring": {"peak_months": [3, 4, 5], "weight": 1.1},
    "autumn": {"peak_months": [9, 10, 11], "weight": 1.1},
    "fall": {"peak_months": [9, 10, 11], "weight": 1.1},
    "winter": {"peak_months": [11, 12, 1, 2], "weight": 1.1},
    "back to school": {"peak_months": [7, 8], "weight": 1.3},
    "black friday": {"peak_months": [11], "weight": 1.4},
    "cyber monday": {"peak_months": [11], "weight": 1.3},
    "mothers day": {"peak_months": [4, 5], "weight": 1.2},
    "fathers day": {"peak_months": [5, 6], "weight": 1.2},
}

HIGH_RISK_KEYWORDS = {
    "nike", "adidas", "apple", "google", "microsoft", "amazon", "facebook",
    "instagram", "twitter", "tiktok", "youtube", "disney", "marvel", "dc",
    "pokemon", "nintendo", "playstation", "xbox", "coca-cola", "pepsi",
    "mcdonalds", "starbucks", "nfl", "nba", "mlb", "fifa", "olympics",
}


async def calculate_opportunity_score(
    keyword: str,
    include_visual: bool = True,
    db: AsyncSession = None,
) -> OpportunityScore:
    """
    Calculate comprehensive opportunity score for a keyword.
    
    Score = f(
        demand_signal,      // 0-100: Search volume proxy
        competition_index,  // 0-100: Lower is better (less saturated)
        freshness_bonus,    // 0-100: Recency of top results
        seasonal_factor,    // 0-100: Calendar-based demand boost
        style_gap_score,    // 0-100: Visual whitespace in niche
        production_cost,    // 0-100: Lower is easier to produce
        review_risk         // 0-100: Lower is safer
    )
    """
    
    kw_result = await db.execute(
        select(Keyword).where(Keyword.term.ilike(keyword))
    )
    kw = kw_result.scalar_one_or_none()
    
    if not kw:
        kw = Keyword(
            term=keyword,
            normalized_term=keyword.lower().strip(),
        )
        db.add(kw)
        await db.commit()
        await db.refresh(kw)
    
    demand_signal = await _calculate_demand_signal(kw, db)
    competition_index = await _calculate_competition_index(kw, db)
    freshness_bonus = await _calculate_freshness_bonus(kw, db)
    seasonal_factor = _calculate_seasonal_factor(keyword)
    style_gap_score = await _calculate_style_gap(kw, db) if include_visual else 50.0
    production_cost = _estimate_production_cost(keyword)
    review_risk = _assess_review_risk(keyword)
    
    weights = {
        "demand": 0.25,
        "competition": 0.20,
        "freshness": 0.10,
        "seasonal": 0.15,
        "style_gap": 0.15,
        "production": 0.08,
        "review_risk": 0.07,
    }
    
    inverted_competition = 100 - competition_index
    inverted_production = 100 - production_cost
    inverted_risk = 100 - review_risk
    
    overall_score = (
        demand_signal * weights["demand"] +
        inverted_competition * weights["competition"] +
        freshness_bonus * weights["freshness"] +
        seasonal_factor * weights["seasonal"] +
        style_gap_score * weights["style_gap"] +
        inverted_production * weights["production"] +
        inverted_risk * weights["review_risk"]
    )
    
    overall_score = max(0, min(100, overall_score))
    
    urgency_level = "low"
    if seasonal_factor > 70:
        urgency_level = "high"
    elif seasonal_factor > 40 or overall_score > 75:
        urgency_level = "medium"
    
    recommendation = _generate_recommendation(
        overall_score, demand_signal, competition_index,
        seasonal_factor, style_gap_score, review_risk
    )
    
    opportunity = OpportunityScore(
        keyword_id=kw.id,
        overall_score=round(overall_score, 2),
        demand_signal=round(demand_signal, 2),
        competition_index=round(competition_index, 2),
        freshness_bonus=round(freshness_bonus, 2),
        seasonal_factor=round(seasonal_factor, 2),
        style_gap_score=round(style_gap_score, 2),
        production_cost=round(production_cost, 2),
        review_risk=round(review_risk, 2),
        recommendation=recommendation,
        urgency_level=urgency_level,
        score_breakdown={
            "demand_signal": {"value": demand_signal, "weight": weights["demand"]},
            "competition_index": {"value": competition_index, "weight": weights["competition"]},
            "freshness_bonus": {"value": freshness_bonus, "weight": weights["freshness"]},
            "seasonal_factor": {"value": seasonal_factor, "weight": weights["seasonal"]},
            "style_gap_score": {"value": style_gap_score, "weight": weights["style_gap"]},
            "production_cost": {"value": production_cost, "weight": weights["production"]},
            "review_risk": {"value": review_risk, "weight": weights["review_risk"]},
        },
        valid_until=datetime.utcnow() + timedelta(days=7),
    )
    
    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)
    
    return opportunity


async def _calculate_demand_signal(keyword: Keyword, db: AsyncSession) -> float:
    """Estimate demand based on search volume proxy and ranking data"""
    
    if keyword.search_volume_estimate:
        volume = keyword.search_volume_estimate
        score = min(100, math.log10(volume + 1) * 25)
        return score
    
    ranking_count = await db.execute(
        select(func.count()).select_from(KeywordRanking)
        .where(KeywordRanking.keyword_id == keyword.id)
    )
    count = ranking_count.scalar() or 0
    
    if count > 0:
        return min(100, count * 2)
    
    return 50.0


async def _calculate_competition_index(keyword: Keyword, db: AsyncSession) -> float:
    """Calculate competition saturation (0 = no competition, 100 = highly saturated)"""
    
    if keyword.competition_level is not None:
        return keyword.competition_level * 100
    
    ranking_result = await db.execute(
        select(KeywordRanking)
        .where(KeywordRanking.keyword_id == keyword.id)
        .limit(50)
    )
    rankings = ranking_result.scalars().all()
    
    if not rankings:
        return 50.0
    
    unique_contributors = len(set(r.contributor_id for r in rankings if r.contributor_id))
    
    if unique_contributors < 10:
        return 30.0
    elif unique_contributors < 30:
        return 50.0
    elif unique_contributors < 50:
        return 70.0
    else:
        return 85.0


async def _calculate_freshness_bonus(keyword: Keyword, db: AsyncSession) -> float:
    """Bonus for niches with older top content (opportunity for fresh takes)"""
    
    ranking_result = await db.execute(
        select(KeywordRanking)
        .where(KeywordRanking.keyword_id == keyword.id)
        .order_by(KeywordRanking.position)
        .limit(20)
    )
    rankings = ranking_result.scalars().all()
    
    if not rankings:
        return 50.0
    
    asset_ids = [r.asset_id for r in rankings]
    
    asset_result = await db.execute(
        select(Asset).where(Asset.adobe_id.in_(asset_ids))
    )
    assets = asset_result.scalars().all()
    
    if not assets:
        return 50.0
    
    now = datetime.utcnow()
    ages = []
    for asset in assets:
        if asset.creation_date:
            age_days = (now - asset.creation_date).days
            ages.append(age_days)
    
    if not ages:
        return 50.0
    
    avg_age = sum(ages) / len(ages)
    
    if avg_age > 365 * 2:
        return 90.0
    elif avg_age > 365:
        return 70.0
    elif avg_age > 180:
        return 50.0
    elif avg_age > 90:
        return 30.0
    else:
        return 20.0


def _calculate_seasonal_factor(keyword: str) -> float:
    """Calculate seasonal demand boost based on keyword and current date"""
    
    keyword_lower = keyword.lower()
    current_month = datetime.now().month
    
    seasonal_boost = 0.0
    
    for seasonal_kw, data in SEASONAL_KEYWORDS.items():
        if seasonal_kw in keyword_lower:
            peak_months = data["peak_months"]
            weight = data["weight"]
            
            months_to_peak = min(
                (m - current_month) % 12 for m in peak_months
            )
            
            if months_to_peak <= 2:
                seasonal_boost = max(seasonal_boost, 80 * weight)
            elif months_to_peak <= 4:
                seasonal_boost = max(seasonal_boost, 50 * weight)
            else:
                seasonal_boost = max(seasonal_boost, 20)
    
    return min(100, seasonal_boost) if seasonal_boost > 0 else 30.0


async def _calculate_style_gap(keyword: Keyword, db: AsyncSession) -> float:
    """Calculate visual whitespace opportunity (requires embeddings)"""
    
    return 50.0


def _estimate_production_cost(keyword: str) -> float:
    """Estimate how difficult/expensive it is to create content for this keyword"""
    
    high_cost_indicators = [
        "aerial", "drone", "underwater", "studio", "model", "professional",
        "luxury", "exotic", "rare", "action", "sports", "wildlife",
    ]
    
    low_cost_indicators = [
        "flat", "minimal", "simple", "texture", "pattern", "background",
        "abstract", "icon", "vector", "illustration", "graphic",
    ]
    
    keyword_lower = keyword.lower()
    
    for indicator in high_cost_indicators:
        if indicator in keyword_lower:
            return 75.0
    
    for indicator in low_cost_indicators:
        if indicator in keyword_lower:
            return 25.0
    
    return 50.0


def _assess_review_risk(keyword: str) -> float:
    """Assess likelihood of rejection based on keyword"""
    
    keyword_lower = keyword.lower()
    
    for brand in HIGH_RISK_KEYWORDS:
        if brand in keyword_lower:
            return 90.0
    
    sensitive_indicators = [
        "celebrity", "famous", "logo", "brand", "trademark",
        "political", "religion", "nude", "weapon",
    ]
    
    for indicator in sensitive_indicators:
        if indicator in keyword_lower:
            return 70.0
    
    return 20.0


def _generate_recommendation(
    overall_score: float,
    demand: float,
    competition: float,
    seasonal: float,
    style_gap: float,
    risk: float,
) -> str:
    """Generate actionable recommendation based on scores"""
    
    if overall_score >= 80:
        urgency = "HIGH PRIORITY"
        action = "Create content immediately"
    elif overall_score >= 60:
        urgency = "GOOD OPPORTUNITY"
        action = "Add to production queue"
    elif overall_score >= 40:
        urgency = "MODERATE"
        action = "Consider if matches your style"
    else:
        urgency = "LOW PRIORITY"
        action = "Skip unless you have existing assets"
    
    insights = []
    
    if demand >= 70:
        insights.append("High buyer demand detected")
    elif demand <= 30:
        insights.append("Low search volume - niche market")
    
    if competition <= 30:
        insights.append("Low competition - easy to rank")
    elif competition >= 70:
        insights.append("High competition - differentiation needed")
    
    if seasonal >= 70:
        insights.append("Seasonal peak approaching - upload soon")
    
    if style_gap >= 70:
        insights.append("Visual gaps detected - opportunity for unique styles")
    
    if risk >= 60:
        insights.append("Review carefully for trademark/compliance issues")
    
    recommendation = f"{urgency}: {action}."
    if insights:
        recommendation += " " + ". ".join(insights) + "."
    
    return recommendation
