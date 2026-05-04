from sqlalchemy import Column, String, DateTime, Date, ForeignKey, UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class ProductCertification(Base):
    __tablename__ = "product_certifications"

    id = Column(UUID, primary_key=True)
    product_id = Column(UUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    certification_code = Column(String(50), nullable=False, index=True)
    certification_name = Column(String(200))
    issued_by = Column(String(200))
    certificate_number = Column(String(100))
    valid_until = Column(Date)
    document_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    product = relationship("Product", back_populates="certifications")
