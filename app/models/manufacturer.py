from sqlalchemy import Column, String, Boolean, DateTime, Text, CHAR, UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(UUID, primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    country = Column(CHAR(2), nullable=False)
    city = Column(String(100))
    website = Column(String(500))
    logo_url = Column(String(500))
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    products = relationship("Product", back_populates="manufacturer", cascade="all, delete-orphan")
