"""Keyword and ranking models"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    term: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    normalized_term: Mapped[str] = mapped_column(String(500), index=True)
    type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # search, asset, hashtag
    
    search_volume_estimate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    competition_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    related_keywords: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    rankings = relationship("KeywordRanking", back_populates="keyword")
    opportunity_scores = relationship("OpportunityScore", back_populates="keyword")
    asset_keywords = relationship("AssetKeyword", back_populates="keyword")


class KeywordRanking(Base):
    __tablename__ = "keyword_rankings"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    
    position: Mapped[int] = mapped_column(Integer)
    asset_id: Mapped[str] = mapped_column(String(50), index=True)
    
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contributor_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    asset_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    keyword = relationship("Keyword", back_populates="rankings")
