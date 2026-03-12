"""Asset and embedding models"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.core.config import settings


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    adobe_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    contributor_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    contributor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    asset_type: Mapped[str] = mapped_column(String(50))
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    orientation: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    asset_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    creation_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    is_premium: Mapped[bool] = mapped_column(default=False)
    is_editorial: Mapped[bool] = mapped_column(default=False)
    is_ai_generated: Mapped[Optional[bool]] = mapped_column(nullable=True)
    
    estimated_downloads: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    similar_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    color_palette: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    style_tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    scraped_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # search, similar
    
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    embedding = relationship("AssetEmbedding", back_populates="asset", uselist=False)
    portfolio_assets = relationship("PortfolioAsset", back_populates="asset")
    search_results = relationship("SearchResult", back_populates="asset", foreign_keys="SearchResult.asset_id")
    asset_keywords = relationship("AssetKeyword", back_populates="asset")
    asset_categories = relationship("AssetCategory", back_populates="asset")
    contributor_highlights = relationship("ContributorHighlight", back_populates="asset")
    metadata = relationship("AssetMetadata", back_populates="asset")
    similar_from = relationship("SimilarAsset", foreign_keys="SimilarAsset.asset_id", back_populates="asset")
    similar_to = relationship("SimilarAsset", foreign_keys="SimilarAsset.similar_to_asset_id", back_populates="similar_to_asset")


class AssetEmbedding(Base):
    __tablename__ = "asset_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), unique=True, index=True)
    
    embedding = mapped_column(Vector(settings.EMBEDDING_DIMENSION))
    
    model_name: Mapped[str] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="embedding")
