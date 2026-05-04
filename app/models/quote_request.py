from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Integer, CHAR
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from app.models.base import Base


class QuoteRequest(Base):
    __tablename__ = "quote_requests"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True)
    specifier_id = Column(PostgresUUID(as_uuid=True), ForeignKey("specifiers.id"), nullable=False)
    product_id = Column(PostgresUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    project_id = Column(PostgresUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    quantity = Column(Numeric(10, 2), nullable=False)
    quantity_unit = Column(String(20), nullable=False)
    specifications = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(30), default="pending", nullable=False)
    quoted_price = Column(Numeric(10, 2), nullable=True)
    quoted_currency = Column(CHAR(3), default="EUR", nullable=False)
    lead_time_weeks = Column(Integer, nullable=True)
    terms_notes = Column(Text, nullable=True)
    quoted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    specifier = relationship("Specifier", back_populates="quote_requests")
    product = relationship("Product", back_populates="quote_requests")
    project = relationship("Project", back_populates="quote_requests")
