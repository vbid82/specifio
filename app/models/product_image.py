from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(UUID, primary_key=True)
    product_id = Column(UUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    alt_text = Column(String(300))
    sort_order = Column(Integer, nullable=False, default=0)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    product = relationship("Product", back_populates="images")
