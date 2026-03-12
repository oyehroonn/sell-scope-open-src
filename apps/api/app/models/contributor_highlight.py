"""Contributor highlight / featured work"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContributorHighlight(Base):
    __tablename__ = "contributor_highlights"

    id: Mapped[int] = mapped_column(primary_key=True)
    contributor_id: Mapped[int] = mapped_column(ForeignKey("contributors.id"), index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    highlight_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # featured, portfolio, etc.
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contributor = relationship("Contributor", back_populates="highlights")
    asset = relationship("Asset", back_populates="contributor_highlights")
