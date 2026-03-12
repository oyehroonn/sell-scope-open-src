"""Portfolio models"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    adobe_contributor_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    contributor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    total_assets: Mapped[int] = mapped_column(Integer, default=0)
    total_photos: Mapped[int] = mapped_column(Integer, default=0)
    total_vectors: Mapped[int] = mapped_column(Integer, default=0)
    total_videos: Mapped[int] = mapped_column(Integer, default=0)
    total_templates: Mapped[int] = mapped_column(Integer, default=0)
    
    estimated_total_downloads: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    top_categories: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    top_keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    style_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    is_owned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_tracked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="portfolios")
    assets = relationship("PortfolioAsset", back_populates="portfolio")


class PortfolioAsset(Base):
    __tablename__ = "portfolio_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    
    downloads: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    impressions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ctr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    first_sale_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_sale_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    performance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="assets")
    asset = relationship("Asset", back_populates="portfolio_assets")
