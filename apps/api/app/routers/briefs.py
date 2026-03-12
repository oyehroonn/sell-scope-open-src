"""AI Brief Generator router"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter()


class BriefRequest(BaseModel):
    keyword: str
    style_preferences: Optional[List[str]] = None
    asset_types: Optional[List[str]] = None
    num_ideas: int = 20
    include_prompts: bool = True


class ShotIdea(BaseModel):
    title: str
    description: str
    composition: str
    lighting: str
    props: List[str]
    mood: str


class KeywordStrategy(BaseModel):
    name: str
    keywords: List[str]
    description: str


class BriefResponse(BaseModel):
    keyword: str
    opportunity_score: float
    shot_ideas: List[ShotIdea]
    style_direction: dict
    color_palette: List[str]
    aspect_ratios: dict
    ai_prompts: Optional[List[str]]
    keyword_strategies: List[KeywordStrategy]
    compliance_notes: List[str]
    time_to_money: dict


@router.post("/generate", response_model=BriefResponse)
async def generate_brief(
    request: BriefRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.brief_generator import generate_production_brief
    
    brief = await generate_production_brief(
        keyword=request.keyword,
        style_preferences=request.style_preferences,
        asset_types=request.asset_types,
        num_ideas=request.num_ideas,
        include_prompts=request.include_prompts,
        db=db,
    )
    
    return brief


@router.post("/shot-ideas")
async def generate_shot_ideas(
    keyword: str,
    num_ideas: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.brief_generator import generate_shot_ideas
    
    ideas = await generate_shot_ideas(keyword, num_ideas, db)
    return {"keyword": keyword, "ideas": ideas}


@router.post("/keywords")
async def generate_keyword_strategies(
    keyword: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.brief_generator import generate_keyword_strategies
    
    strategies = await generate_keyword_strategies(keyword, db)
    return {"keyword": keyword, "strategies": strategies}


@router.post("/compliance-check")
async def check_compliance(
    title: str,
    keywords: List[str],
    description: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    from app.services.compliance_checker import check_metadata_compliance
    
    result = check_metadata_compliance(
        title=title,
        keywords=keywords,
        description=description,
    )
    
    return result


@router.post("/prompts")
async def generate_ai_prompts(
    keyword: str,
    style: Optional[str] = None,
    num_prompts: int = 5,
    current_user: dict = Depends(get_current_user),
):
    from app.services.brief_generator import generate_ai_prompts
    
    prompts = await generate_ai_prompts(keyword, style, num_prompts)
    return {"keyword": keyword, "prompts": prompts}
