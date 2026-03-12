"""Opportunity and niche models"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Niche(Base):
    __tablename__ = "niches"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    parent_niche_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("niches.id"), nullable=True
    )
    
    primary_keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    total_assets: Mapped[int] = mapped_column(Integer, default=0)
    avg_competition: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    dominant_styles: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    color_distribution: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    seasonal_patterns: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    opportunity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    
    overall_score: Mapped[float] = mapped_column(Float)
    
    demand_signal: Mapped[float] = mapped_column(Float)
    competition_index: Mapped[float] = mapped_column(Float)
    freshness_bonus: Mapped[float] = mapped_column(Float)
    seasonal_factor: Mapped[float] = mapped_column(Float)
    style_gap_score: Mapped[float] = mapped_column(Float)
    production_cost: Mapped[float] = mapped_column(Float)
    review_risk: Mapped[float] = mapped_column(Float)
    
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    urgency_level: Mapped[str] = mapped_column(String(20), default="medium")
    
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    keyword = relationship("Keyword", back_populates="opportunity_scores")
