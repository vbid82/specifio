from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import INET
from datetime import datetime

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID, primary_key=True)
    event_type = Column(String(100), nullable=False, index=True)

    specifier_id = Column(UUID, ForeignKey("specifiers.id", ondelete="SET NULL"), index=True)
    session_id = Column(String(64), index=True)
    product_id = Column(UUID, ForeignKey("products.id", ondelete="SET NULL"), index=True)
    project_id = Column(UUID, ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    manufacturer_id = Column(UUID, ForeignKey("manufacturers.id", ondelete="SET NULL"), index=True)

    properties = Column(JSON, nullable=False, default=dict)
    ip_address = Column(INET)
    user_agent = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
