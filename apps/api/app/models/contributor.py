"""Contributor (creator) model"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Contributor(Base):
    __tablename__ = "contributors"

    id: Mapped[int] = mapped_column(primary_key=True)
    adobe_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    highlights = relationship("ContributorHighlight", back_populates="contributor")
