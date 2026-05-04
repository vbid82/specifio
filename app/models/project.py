from sqlalchemy import Column, String, Text, Boolean, DateTime, UUID, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID, primary_key=True)
    specifier_id = Column(UUID, ForeignKey("specifiers.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(300), nullable=False)
    description = Column(Text)
    client_name = Column(String(300))
    project_type = Column(String(50))

    status = Column(String(30), nullable=False, default="active")
    share_token = Column(String(64), unique=True)
    is_shared = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    specifier = relationship("Specifier", back_populates="projects")
    project_products = relationship("ProjectProduct", back_populates="project", cascade="all, delete-orphan")
    sample_requests = relationship("SampleRequest", back_populates="project", cascade="all, delete-orphan")
    quote_requests = relationship("QuoteRequest", back_populates="project", cascade="all, delete-orphan")
