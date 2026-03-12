"""Opportunities router"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.opportunity import OpportunityScore, Niche
from app.models.keyword import Keyword

router = APIRouter()


class OpportunityScoreResponse(BaseModel):
    id: int
    keyword_id: int
    keyword_term: Optional[str] = None
    overall_score: float
    demand_signal: float
    competition_index: float
    freshness_bonus: float
    seasonal_factor: float
    style_gap_score: float
    production_cost: float
    review_risk: float
    recommendation: Optional[str]
    urgency_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class NicheResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    total_assets: int
    avg_competition: Optional[float]
    opportunity_score: Optional[float]
    dominant_styles: Optional[List[dict]]
    seasonal_patterns: Optional[dict]

    class Config:
        from_attributes = True


class OpportunityRequest(BaseModel):
    keyword: str
    include_visual_analysis: bool = True


@router.get("/score/{keyword}", response_model=OpportunityScoreResponse)
async def get_opportunity_score(
    keyword: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Keyword).where(Keyword.term.ilike(keyword))
    )
    kw = result.scalar_one_or_none()
    
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found. Try scraping it first.")
    
    score_result = await db.execute(
        select(OpportunityScore)
        .where(OpportunityScore.keyword_id == kw.id)
        .order_by(OpportunityScore.created_at.desc())
        .limit(1)
    )
    score = score_result.scalar_one_or_none()
    
    if not score:
        raise HTTPException(
            status_code=404,
            detail="No opportunity score calculated yet. Trigger analysis first."
        )
    
    response = OpportunityScoreResponse.model_validate(score)
    response.keyword_term = kw.term
    return response


@router.post("/analyze", response_model=OpportunityScoreResponse)
async def analyze_opportunity(
    request: OpportunityRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.opportunity_engine import calculate_opportunity_score
    
    score = await calculate_opportunity_score(
        keyword=request.keyword,
        include_visual=request.include_visual_analysis,
        db=db,
    )
    
    return score


@router.get("/top", response_model=List[OpportunityScoreResponse])
async def get_top_opportunities(
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0, ge=0, le=100),
    urgency: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(OpportunityScore)
        .where(OpportunityScore.overall_score >= min_score)
        .order_by(OpportunityScore.overall_score.desc())
    )
    
    if urgency:
        query = query.where(OpportunityScore.urgency_level == urgency)
    
    result = await db.execute(query.limit(limit))
    scores = result.scalars().all()
    
    responses = []
    for score in scores:
        kw_result = await db.execute(
            select(Keyword.term).where(Keyword.id == score.keyword_id)
        )
        term = kw_result.scalar_one_or_none()
        
        resp = OpportunityScoreResponse.model_validate(score)
        resp.keyword_term = term
        responses.append(resp)
    
    return responses


@router.get("/niches", response_model=List[NicheResponse])
async def get_niches(
    limit: int = Query(50, ge=1, le=200),
    min_opportunity: float = Query(0, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Niche)
        .where(Niche.opportunity_score >= min_opportunity)
        .order_by(Niche.opportunity_score.desc().nullslast())
        .limit(limit)
    )
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/niches/{slug}", response_model=NicheResponse)
async def get_niche(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Niche).where(Niche.slug == slug))
    niche = result.scalar_one_or_none()
    
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    return niche


@router.get("/heatmap")
async def get_opportunity_heatmap(
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(
        Niche.name,
        Niche.slug,
        Niche.opportunity_score,
        Niche.total_assets,
        Niche.avg_competition,
    ).order_by(Niche.opportunity_score.desc().nullslast())
    
    result = await db.execute(query.limit(100))
    niches = result.all()
    
    return {
        "heatmap": [
            {
                "name": n.name,
                "slug": n.slug,
                "score": n.opportunity_score or 0,
                "assets": n.total_assets,
                "competition": n.avg_competition or 0,
            }
            for n in niches
        ]
    }
