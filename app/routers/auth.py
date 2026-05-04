import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.config import get_settings
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    MagicLinkResponse,
    TokenVerifyResponse,
    SpecifierProfile,
)
from app.models.specifier import Specifier
from app.services.auth import (
    create_magic_link_token,
    verify_magic_link_token,
    create_jwt,
    decode_jwt,
)
from app.services.email import send_magic_link_email
from app.middleware.rate_limit import registration_limiter, magic_link_limiter
from app.dependencies import get_current_specifier

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host


@router.post("/register", response_model=MagicLinkResponse)
async def register(request: RegisterRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = get_client_ip(http_request)

    if not registration_limiter.check(client_ip, settings.registration_rate_limit_per_ip, 86400):
        raise HTTPException(status_code=429, detail="Too many registration attempts. Try again later.")

    stmt = select(Specifier).where(Specifier.email == request.email)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        token = await create_magic_link_token(db, existing.id, existing.email, "login")
        await send_magic_link_email(existing.email, existing.first_name, token)
        await db.commit()
        return MagicLinkResponse(message="Check your email for a sign-in link.")

    try:
        specifier = Specifier(
            id=uuid4(),
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            firm_name=request.firm_name,
            role=request.role,
            country=request.country,
            phone=request.phone,
            specialization=request.specialization,
        )
        db.add(specifier)
        await db.flush()

        token = await create_magic_link_token(db, specifier.id, specifier.email, "register")
        await send_magic_link_email(specifier.email, specifier.first_name, token)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        stmt = select(Specifier).where(Specifier.email == request.email)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            token = await create_magic_link_token(db, existing.id, existing.email, "login")
            await send_magic_link_email(existing.email, existing.first_name, token)
            await db.commit()

    return MagicLinkResponse(message="Check your email for a sign-in link.")


@router.post("/login", response_model=MagicLinkResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    if not magic_link_limiter.check(request.email, settings.magic_link_rate_limit_per_email, 3600):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    stmt = select(Specifier).where(Specifier.email == request.email)
    result = await db.execute(stmt)
    specifier = result.scalar_one_or_none()

    if specifier:
        token = await create_magic_link_token(db, specifier.id, specifier.email, "login")
        await send_magic_link_email(specifier.email, specifier.first_name, token)
        await db.commit()

    return MagicLinkResponse(message="If this email is registered, you will receive a sign-in link.")


@router.get("/verify", response_model=TokenVerifyResponse)
async def verify(token: str, db: AsyncSession = Depends(get_db)):
    specifier = await verify_magic_link_token(db, token)

    if specifier is None:
        raise HTTPException(status_code=401, detail="Invalid or expired link. Please request a new one.")

    await db.commit()

    access_token = create_jwt(specifier.id, specifier.email)

    return TokenVerifyResponse(
        access_token=access_token,
        token_type="bearer",
        specifier_id=str(specifier.id),
    )


@router.get("/me", response_model=SpecifierProfile)
async def get_profile(specifier: Specifier = Depends(get_current_specifier)):
    if specifier is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    return SpecifierProfile.from_orm(specifier)
