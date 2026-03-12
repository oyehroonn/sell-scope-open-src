"""Similar asset relationship"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SimilarAsset(Base):
    __tablename__ = "similar_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    similar_to_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", foreign_keys=[asset_id], back_populates="similar_from")
    similar_to_asset = relationship("Asset", foreign_keys=[similar_to_asset_id], back_populates="similar_to")
