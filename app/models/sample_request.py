from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from app.models.base import Base


class SampleRequest(Base):
    __tablename__ = "sample_requests"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True)
    specifier_id = Column(PostgresUUID(as_uuid=True), ForeignKey("specifiers.id"), nullable=False)
    product_id = Column(PostgresUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    project_id = Column(PostgresUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    status = Column(String(30), default="pending", nullable=False)
    shipping_address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    tracking_number = Column(String(100), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    specifier = relationship("Specifier", back_populates="sample_requests")
    product = relationship("Product", back_populates="sample_requests")
    project = relationship("Project", back_populates="sample_requests")
