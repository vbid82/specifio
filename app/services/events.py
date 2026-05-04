import logging
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event

logger = logging.getLogger(__name__)


async def emit_event(
    db: AsyncSession,
    event_type: str,
    specifier_id: Optional[UUID] = None,
    session_id: Optional[str] = None,
    product_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    manufacturer_id: Optional[UUID] = None,
    properties: Optional[dict] = None,
) -> None:
    try:
        event = Event(
            id=uuid4(),
            event_type=event_type,
            specifier_id=specifier_id,
            session_id=session_id,
            product_id=product_id,
            project_id=project_id,
            manufacturer_id=manufacturer_id,
            properties=properties or {},
        )
        db.add(event)
        await db.flush()
    except Exception as e:
        logger.error(f"Failed to emit event {event_type}: {str(e)}")
