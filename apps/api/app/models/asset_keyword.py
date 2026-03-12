"""Asset-Keyword many-to-many (keywords/hashtags per asset)"""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssetKeyword(Base):
    __tablename__ = "asset_keywords"
    __table_args__ = (UniqueConstraint("asset_id", "keyword_id", "source", name="uq_asset_keyword_source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    source: Mapped[str] = mapped_column(String(50), default="meta")  # title, description, meta, hashtag
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="asset_keywords")
    keyword = relationship("Keyword", back_populates="asset_keywords")
