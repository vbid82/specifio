import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.config import get_settings
from app.models.magic_link_token import MagicLinkToken
from app.models.specifier import Specifier

settings = get_settings()
logger = logging.getLogger(__name__)


async def create_magic_link_token(db: AsyncSession, specifier_id: UUID, specifier_email: str, intent: str = "login") -> str:
    plaintext_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plaintext_token.encode()).hexdigest()

    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    token = MagicLinkToken(
        id=uuid4(),
        email=specifier_email,
        token_hash=token_hash,
        intent=intent,
        specifier_id=specifier_id,
        expires_at=expires_at,
    )
    db.add(token)
    await db.flush()

    return plaintext_token


async def verify_magic_link_token(db: AsyncSession, plaintext_token: str) -> Specifier | None:
    token_hash = hashlib.sha256(plaintext_token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    stmt = select(MagicLinkToken).where(
        MagicLinkToken.token_hash == token_hash,
        MagicLinkToken.consumed_at.is_(None),
        MagicLinkToken.expires_at > now,
    )
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if token_record is None:
        return None

    token_record.consumed_at = now
    await db.flush()

    stmt = select(Specifier).where(Specifier.id == token_record.specifier_id)
    result = await db.execute(stmt)
    specifier = result.scalar_one_or_none()

    return specifier


def create_jwt(specifier_id: UUID, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(specifier_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.jwt_expiry_hours)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token


def decode_jwt(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        return None
