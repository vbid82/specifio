from sqlalchemy import Column, String, Text, Integer, DateTime, UUID, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class ProjectProduct(Base):
    __tablename__ = "project_products"

    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    notes = Column(Text)
    sort_order = Column(Integer, nullable=False, default=0)
    added_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    project = relationship("Project", back_populates="project_products")
    product = relationship("Product")
