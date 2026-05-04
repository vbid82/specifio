from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Index
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class MagicLinkToken(Base):
    __tablename__ = "magic_link_tokens"

    id = Column(UUID, primary_key=True)
    email = Column(String(320), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    intent = Column(String(20), nullable=False)
    specifier_id = Column(UUID, ForeignKey("specifiers.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at = Column(DateTime(timezone=True))
    ip_address = Column(INET)
    user_agent = Column(String)

    specifier = relationship("Specifier", back_populates="magic_link_tokens")
