from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, Text, ForeignKey, CHAR, UUID
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID, primary_key=True)
    manufacturer_id = Column(UUID, ForeignKey("manufacturers.id", ondelete="CASCADE"), nullable=False, index=True)

    sku = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(300), nullable=False)
    slug = Column(String(300), nullable=False, unique=True, index=True)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(100))

    short_description = Column(String(500), nullable=False)
    long_description = Column(Text)

    primary_material = Column(String(100), nullable=False)
    secondary_material = Column(String(100))
    finish_type = Column(String(50))
    colorway_name = Column(String(100))
    colorway_count = Column(Integer)
    custom_colorway = Column(Boolean, default=False)

    width_mm = Column(Numeric(10, 2))
    height_mm = Column(Numeric(10, 2))
    thickness_mm = Column(Numeric(10, 2))
    weight_value = Column(Numeric(10, 2))
    weight_unit = Column(String(20))
    repeat_width_mm = Column(Numeric(10, 2))
    repeat_height_mm = Column(Numeric(10, 2))

    fire_class_eu = Column(String(5), index=True)
    fire_smoke_class_eu = Column(String(5))
    fire_droplet_class_eu = Column(String(5))
    fire_class_us = Column(String(20))

    nrc_value = Column(Numeric(4, 2))
    acoustic_class = Column(CHAR(1))

    commercial_grade = Column(ARRAY(Text), nullable=False, default=list, index=True)
    suitable_environments = Column(Text)

    recycled_content_pct = Column(Integer)
    voc_class = Column(String(5))

    price_visibility = Column(String(20), nullable=False, default="on_request", index=True)
    indicative_price_eur = Column(Numeric(10, 2))
    price_unit = Column(String(20))
    moq = Column(Integer, nullable=False, default=1)
    moq_unit = Column(String(20))

    lead_time_weeks_min = Column(Integer, nullable=False)
    lead_time_weeks_max = Column(Integer)
    sample_available = Column(Boolean, nullable=False, default=False)
    sample_type = Column(String(30))
    made_to_order = Column(Boolean, default=True)

    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_featured = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    manufacturer = relationship("Manufacturer", back_populates="products")
    certifications = relationship("ProductCertification", back_populates="product", cascade="all, delete-orphan")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    sample_requests = relationship("SampleRequest", back_populates="product", cascade="all, delete-orphan")
    quote_requests = relationship("QuoteRequest", back_populates="product", cascade="all, delete-orphan")
