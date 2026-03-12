"""AI Brief Generator Service"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.keyword import Keyword
from app.models.opportunity import OpportunityScore


STYLE_DIRECTIONS = {
    "business": {
        "lighting": "Clean, professional studio lighting or natural office light",
        "mood": "Confident, productive, collaborative",
        "colors": ["#2563eb", "#1e40af", "#3b82f6", "#f8fafc", "#64748b"],
        "props": ["laptop", "notebook", "coffee", "modern desk", "plants"],
    },
    "lifestyle": {
        "lighting": "Warm, natural golden hour or soft indoor lighting",
        "mood": "Relaxed, authentic, aspirational",
        "colors": ["#f59e0b", "#eab308", "#fef3c7", "#84cc16", "#22c55e"],
        "props": ["casual clothing", "home items", "food", "nature elements"],
    },
    "technology": {
        "lighting": "Cool, modern lighting with subtle gradients",
        "mood": "Innovative, futuristic, clean",
        "colors": ["#06b6d4", "#0ea5e9", "#8b5cf6", "#1e1e1e", "#ffffff"],
        "props": ["devices", "screens", "abstract shapes", "data visualizations"],
    },
    "nature": {
        "lighting": "Natural outdoor lighting, golden hour preferred",
        "mood": "Peaceful, serene, vibrant",
        "colors": ["#22c55e", "#16a34a", "#3b82f6", "#f97316", "#fcd34d"],
        "props": ["plants", "water", "sky", "animals", "landscapes"],
    },
    "minimalist": {
        "lighting": "Even, diffused lighting with soft shadows",
        "mood": "Clean, calm, sophisticated",
        "colors": ["#ffffff", "#f5f5f5", "#e5e5e5", "#737373", "#171717"],
        "props": ["single objects", "negative space", "simple geometry"],
    },
}

SHOT_TEMPLATES = [
    {"type": "hero", "description": "Main subject centered, full context visible"},
    {"type": "detail", "description": "Close-up on key element or texture"},
    {"type": "lifestyle", "description": "Subject in use within real environment"},
    {"type": "flat_lay", "description": "Top-down arrangement of related items"},
    {"type": "negative_space", "description": "Subject with ample copy space"},
    {"type": "environmental", "description": "Wide shot showing full context"},
    {"type": "action", "description": "Subject in motion or being used"},
    {"type": "comparison", "description": "Before/after or multiple variants"},
    {"type": "abstract", "description": "Artistic interpretation of concept"},
    {"type": "documentary", "description": "Candid, authentic moment"},
]


async def generate_production_brief(
    keyword: str,
    style_preferences: Optional[List[str]] = None,
    asset_types: Optional[List[str]] = None,
    num_ideas: int = 20,
    include_prompts: bool = True,
    db: AsyncSession = None,
) -> Dict[str, Any]:
    """Generate a comprehensive production brief for a keyword"""
    
    opportunity_score = 65.0
    
    if db:
        kw_result = await db.execute(
            select(Keyword).where(Keyword.term.ilike(keyword))
        )
        kw = kw_result.scalar_one_or_none()
        
        if kw:
            score_result = await db.execute(
                select(OpportunityScore)
                .where(OpportunityScore.keyword_id == kw.id)
                .order_by(OpportunityScore.created_at.desc())
                .limit(1)
            )
            score = score_result.scalar_one_or_none()
            if score:
                opportunity_score = score.overall_score
    
    detected_style = _detect_style(keyword)
    style_direction = STYLE_DIRECTIONS.get(detected_style, STYLE_DIRECTIONS["lifestyle"])
    
    shot_ideas = _generate_shot_ideas(keyword, detected_style, num_ideas)
    
    keyword_strategies = _generate_keyword_strategies(keyword)
    
    ai_prompts = None
    if include_prompts:
        ai_prompts = _generate_ai_prompts(keyword, detected_style, 5)
    
    compliance_notes = _generate_compliance_notes(keyword)
    
    time_to_money = _estimate_time_to_money(keyword, opportunity_score)
    
    return {
        "keyword": keyword,
        "opportunity_score": opportunity_score,
        "shot_ideas": shot_ideas,
        "style_direction": {
            "detected_style": detected_style,
            "lighting": style_direction["lighting"],
            "mood": style_direction["mood"],
            "suggested_props": style_direction["props"],
        },
        "color_palette": style_direction["colors"],
        "aspect_ratios": {
            "horizontal": {"ratio": "16:9", "use_case": "Web banners, presentations"},
            "vertical": {"ratio": "9:16", "use_case": "Mobile, social stories"},
            "square": {"ratio": "1:1", "use_case": "Social posts, thumbnails"},
            "standard": {"ratio": "4:3", "use_case": "General purpose"},
        },
        "ai_prompts": ai_prompts,
        "keyword_strategies": keyword_strategies,
        "compliance_notes": compliance_notes,
        "time_to_money": time_to_money,
    }


def _detect_style(keyword: str) -> str:
    """Detect the most appropriate style based on keyword"""
    keyword_lower = keyword.lower()
    
    style_keywords = {
        "business": ["office", "business", "corporate", "meeting", "professional", "work", "team"],
        "technology": ["tech", "digital", "computer", "phone", "app", "software", "ai", "data"],
        "nature": ["nature", "outdoor", "forest", "beach", "mountain", "landscape", "garden"],
        "lifestyle": ["home", "family", "food", "travel", "wellness", "fitness", "cooking"],
        "minimalist": ["minimal", "simple", "clean", "modern", "abstract", "geometric"],
    }
    
    for style, keywords in style_keywords.items():
        for kw in keywords:
            if kw in keyword_lower:
                return style
    
    return "lifestyle"


def _generate_shot_ideas(keyword: str, style: str, num_ideas: int) -> List[Dict[str, Any]]:
    """Generate specific shot ideas for the keyword"""
    ideas = []
    
    keyword_parts = keyword.lower().split()
    
    for i, template in enumerate(SHOT_TEMPLATES[:num_ideas]):
        props = STYLE_DIRECTIONS.get(style, STYLE_DIRECTIONS["lifestyle"])["props"]
        
        idea = {
            "title": f"{keyword.title()} - {template['type'].replace('_', ' ').title()}",
            "description": f"{template['description']} featuring {keyword}",
            "composition": template["type"],
            "lighting": STYLE_DIRECTIONS.get(style, STYLE_DIRECTIONS["lifestyle"])["lighting"],
            "props": props[:3],
            "mood": STYLE_DIRECTIONS.get(style, STYLE_DIRECTIONS["lifestyle"])["mood"],
        }
        ideas.append(idea)
    
    variations = [
        "morning light", "evening mood", "overhead angle", "side profile",
        "with people", "without people", "close-up detail", "wide context",
        "monochrome option", "vibrant colors", "muted tones", "high contrast",
    ]
    
    while len(ideas) < num_ideas:
        variation = variations[len(ideas) % len(variations)]
        idea = {
            "title": f"{keyword.title()} - {variation.title()}",
            "description": f"Alternative take on {keyword} with {variation}",
            "composition": "variation",
            "lighting": f"Adapted for {variation}",
            "props": STYLE_DIRECTIONS.get(style, STYLE_DIRECTIONS["lifestyle"])["props"][:2],
            "mood": f"{STYLE_DIRECTIONS.get(style, STYLE_DIRECTIONS['lifestyle'])['mood']} with {variation}",
        }
        ideas.append(idea)
    
    return ideas[:num_ideas]


def _generate_keyword_strategies(keyword: str) -> List[Dict[str, Any]]:
    """Generate multiple keyword strategies for the same content"""
    
    base_terms = keyword.lower().split()
    
    strategies = [
        {
            "name": "Literal Descriptive",
            "keywords": [
                keyword,
                f"{keyword} photo",
                f"{keyword} image",
                f"stock {keyword}",
                f"{keyword} background",
                f"{keyword} concept",
            ],
            "description": "Exact match and direct descriptive terms for literal searches",
        },
        {
            "name": "Buyer Intent",
            "keywords": [
                f"{keyword} for business",
                f"professional {keyword}",
                f"{keyword} marketing",
                f"{keyword} advertising",
                f"commercial {keyword}",
                f"{keyword} branding",
            ],
            "description": "Terms that indicate commercial purchase intent",
        },
        {
            "name": "Long-tail Specific",
            "keywords": [
                f"modern {keyword}",
                f"minimalist {keyword}",
                f"{keyword} on white background",
                f"isolated {keyword}",
                f"{keyword} top view",
                f"{keyword} close up",
            ],
            "description": "Specific variations with lower competition",
        },
        {
            "name": "Contextual",
            "keywords": [
                f"{keyword} lifestyle",
                f"{keyword} at home",
                f"{keyword} workspace",
                f"person with {keyword}",
                f"{keyword} in use",
                f"using {keyword}",
            ],
            "description": "Context-based terms showing usage scenarios",
        },
        {
            "name": "Emotional/Mood",
            "keywords": [
                f"happy {keyword}",
                f"peaceful {keyword}",
                f"inspiring {keyword}",
                f"successful {keyword}",
                f"healthy {keyword}",
                f"beautiful {keyword}",
            ],
            "description": "Emotion and mood-based descriptors",
        },
    ]
    
    return strategies


def _generate_ai_prompts(keyword: str, style: str, num_prompts: int) -> List[str]:
    """Generate AI image generation prompts"""
    
    style_direction = STYLE_DIRECTIONS.get(style, STYLE_DIRECTIONS["lifestyle"])
    
    prompts = [
        f"Professional stock photo of {keyword}, {style_direction['lighting']}, {style_direction['mood']} mood, high resolution, commercial quality",
        f"Clean and modern {keyword} photograph, studio lighting, white background, product photography style, 8k quality",
        f"{keyword.title()} in natural setting, lifestyle photography, authentic and candid, warm color grading, editorial quality",
        f"Minimalist {keyword} composition, ample negative space for text overlay, soft shadows, muted color palette, commercial use",
        f"Dynamic {keyword} scene, professional photography, {style_direction['mood']} atmosphere, trending on Adobe Stock",
        f"Abstract interpretation of {keyword}, creative composition, artistic lighting, contemporary style, gallery quality",
        f"Flat lay arrangement featuring {keyword}, top-down view, organized composition, Instagram-worthy, bright and airy",
        f"{keyword.title()} close-up detail shot, macro photography, shallow depth of field, texture focus, premium quality",
    ]
    
    return prompts[:num_prompts]


def _generate_compliance_notes(keyword: str) -> List[str]:
    """Generate compliance and review risk notes"""
    
    notes = []
    keyword_lower = keyword.lower()
    
    brand_risks = ["nike", "apple", "google", "microsoft", "coca-cola", "starbucks"]
    for brand in brand_risks:
        if brand in keyword_lower:
            notes.append(f"HIGH RISK: Contains potential trademark '{brand}' - avoid brand-identifiable elements")
    
    people_keywords = ["person", "people", "man", "woman", "child", "model", "portrait", "face"]
    for pk in people_keywords:
        if pk in keyword_lower:
            notes.append("Model release required for recognizable people")
            break
    
    property_keywords = ["building", "architecture", "interior", "property", "house", "office"]
    for pk in property_keywords:
        if pk in keyword_lower:
            notes.append("Property release may be required for identifiable private properties")
            break
    
    if not notes:
        notes.append("Standard compliance - ensure no identifiable trademarks, logos, or recognizable private property")
    
    notes.append("If AI-generated: Must disclose as AI-generated content per Adobe Stock guidelines")
    notes.append("Ensure keywords accurately describe visible content - avoid keyword stuffing")
    
    return notes


def _estimate_time_to_money(keyword: str, opportunity_score: float) -> Dict[str, Any]:
    """Estimate ROI and time to first sale"""
    
    if opportunity_score >= 80:
        base_days = 7
        monthly_potential = "$20-50"
    elif opportunity_score >= 60:
        base_days = 14
        monthly_potential = "$10-25"
    elif opportunity_score >= 40:
        base_days = 30
        monthly_potential = "$5-15"
    else:
        base_days = 60
        monthly_potential = "$1-5"
    
    return {
        "estimated_time_to_first_sale_days": base_days,
        "monthly_earning_potential": monthly_potential,
        "recommended_batch_size": 10 if opportunity_score >= 60 else 5,
        "priority_level": "high" if opportunity_score >= 70 else "medium" if opportunity_score >= 50 else "low",
        "roi_recommendation": f"At {opportunity_score:.0f} opportunity score, this keyword is {'excellent' if opportunity_score >= 70 else 'good' if opportunity_score >= 50 else 'moderate'} for investment",
    }


async def generate_shot_ideas(keyword: str, num_ideas: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """Standalone shot idea generator"""
    style = _detect_style(keyword)
    return _generate_shot_ideas(keyword, style, num_ideas)


async def generate_keyword_strategies(keyword: str, db: AsyncSession) -> List[Dict[str, Any]]:
    """Standalone keyword strategy generator"""
    return _generate_keyword_strategies(keyword)


async def generate_ai_prompts(keyword: str, style: Optional[str], num_prompts: int) -> List[str]:
    """Standalone AI prompt generator"""
    detected_style = style or _detect_style(keyword)
    return _generate_ai_prompts(keyword, detected_style, num_prompts)
