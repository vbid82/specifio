from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.config import get_settings
from app.database import get_db
from app.services.auth import decode_jwt
from app.models.specifier import Specifier

settings = get_settings()
security = HTTPBearer(auto_error=False)


# --------------------------------------------------------------------------
# JWT auth
# --------------------------------------------------------------------------

async def get_current_specifier(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[Specifier]:
    """Returns specifier ORM object if valid JWT, None if no token."""
    if credentials is None:
        return None

    payload = decode_jwt(credentials.credentials)
    if payload is None:
        return None

    specifier_id = payload.get("sub")
    if specifier_id is None:
        return None

    stmt = select(Specifier).where(Specifier.id == UUID(specifier_id))
    result = await db.execute(stmt)
    specifier = result.scalar_one_or_none()

    return specifier


async def require_specifier(
    specifier: Optional[Specifier] = Depends(get_current_specifier),
) -> Specifier:
    """Raises 401 if not authenticated."""
    if specifier is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return specifier


async def require_verified(
    specifier: Specifier = Depends(require_specifier),
) -> Specifier:
    """Raises 403 if not verified."""
    if not specifier.verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification required for this action")
    return specifier


async def require_admin(
    specifier: Specifier = Depends(require_specifier),
) -> Specifier:
    """Raises 403 if not admin."""
    if specifier.role_type != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return specifier


# --------------------------------------------------------------------------
# ManufacturerScope (Phase 0a: optional filter, Phase 1: forced from JWT)
# --------------------------------------------------------------------------

class ManufacturerScope:
    """Dependency for manufacturer-scoped admin queries.
    Phase 0a: manufacturer_id is optional query param (None = see all).
    Phase 1: forced from JWT claims.
    Code review gate: any admin endpoint missing ManufacturerScope is a build defect.
    """

    def __init__(self, manufacturer_id: Optional[UUID] = None):
        self.manufacturer_id = manufacturer_id

    def filter_clause(self, column: str = "manufacturer_id") -> str:
        if self.manufacturer_id is None:
            return "TRUE"
        return f"{column} = :manufacturer_id"

    def filter_params(self) -> dict:
        if self.manufacturer_id is None:
            return {}
        return {"manufacturer_id": str(self.manufacturer_id)}


# --------------------------------------------------------------------------
# Rate limiting (in-memory, sufficient for Phase 0a scale)
# --------------------------------------------------------------------------

_rate_limit_store: dict[str, list[float]] = {}


def check_rate_limit(key: str, limit: int, window_seconds: int = 86400) -> bool:
    """Returns True if within limit, False if exceeded.
    Simple in-memory store. Resets on process restart. Fine for Phase 0a.
    """
    now = datetime.utcnow().timestamp()
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []

    # Clean expired entries
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < window_seconds]

    if len(_rate_limit_store[key]) >= limit:
        return False

    _rate_limit_store[key].append(now)
    return True
