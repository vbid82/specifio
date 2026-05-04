from sqlalchemy import Column, String, Boolean, DateTime, UUID, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Specifier(Base):
    __tablename__ = "specifiers"

    id = Column(UUID, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    firm_name = Column(String(300), nullable=False)
    role = Column(String(100))
    country = Column(String(2))
    phone = Column(String(30))
    specialization = Column(String(200))
    firm_website = Column(String(500))
    linkedin_url = Column(String(500))

    verified = Column(Boolean, default=False, index=True)
    verified_at = Column(DateTime(timezone=True))
    verified_by_admin_id = Column(UUID, ForeignKey("specifiers.id"))
    verification_notes = Column(String)

    role_type = Column(String(20), default="specifier", nullable=False)
    last_login_at = Column(DateTime(timezone=True))
    email_send_failed = Column(Boolean, default=False)

    hubspot_contact_id = Column(String(50))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    magic_link_tokens = relationship("MagicLinkToken", back_populates="specifier", cascade="all, delete-orphan")
