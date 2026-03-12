"""Automation and webhook models"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, JSON, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class WebhookEvent(str, enum.Enum):
    OPPORTUNITY_ALERT = "opportunity_alert"
    RANKING_CHANGE = "ranking_change"
    PORTFOLIO_UPDATE = "portfolio_update"
    BRIEF_GENERATED = "brief_generated"
    SCRAPE_COMPLETED = "scrape_completed"
    TREND_SPIKE = "trend_spike"


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    
    events: Mapped[List[str]] = mapped_column(JSON)
    
    secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="webhooks")


class AutomationConfig(Base):
    __tablename__ = "automation_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    name: Mapped[str] = mapped_column(String(255))
    automation_type: Mapped[str] = mapped_column(String(50))
    
    trigger_conditions: Mapped[dict] = mapped_column(JSON)
    
    actions: Mapped[List[dict]] = mapped_column(JSON)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
