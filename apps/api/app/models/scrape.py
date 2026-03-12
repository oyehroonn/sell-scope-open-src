"""Scraping job models"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base


class ScrapeJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapeJobType(str, enum.Enum):
    KEYWORD_SEARCH = "keyword_search"
    PORTFOLIO = "portfolio"
    ASSET_DETAIL = "asset_detail"
    CATEGORY_TREE = "category_tree"
    TRENDING = "trending"


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    job_type: Mapped[ScrapeJobType] = mapped_column(Enum(ScrapeJobType))
    status: Mapped[ScrapeJobStatus] = mapped_column(
        Enum(ScrapeJobStatus), default=ScrapeJobStatus.PENDING
    )
    
    target: Mapped[str] = mapped_column(String(500))
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    results_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ScrapeResult(Base):
    __tablename__ = "scrape_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, index=True)
    
    result_type: Mapped[str] = mapped_column(String(50))
    data: Mapped[dict] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
