import logging
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.specifier import Specifier
from app.models.product import Product
from app.models.project import Project
from app.models.sample_request import SampleRequest
from app.models.quote_request import QuoteRequest
from app.schemas.requests import (
    SampleRequestCreate,
    SampleRequestOut,
    SampleRequestAdminUpdate,
    SampleRequestListResponse,
    QuoteRequestCreate,
    QuoteRequestOut,
    QuoteResponseProvide,
    QuoteRequestAdminUpdate,
    QuoteRequestListResponse,
    SpecifierListOut,
    SpecifierVerify,
    SpecifierListResponse,
)
from app.dependencies import require_specifier, require_admin
from app.services.events import emit_event
from app.services.email import send_magic_link_email
from app.config import get_settings
import httpx
import asyncio

router = APIRouter(prefix="", tags=["requests"])
settings = get_settings()
logger = logging.getLogger(__name__)


async def send_notification_email(to_email: str, first_name: str, subject: str, html_body: str) -> bool:
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }

    async def attempt():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
            )
            return response.status_code < 300

    try:
        success = await attempt()
        if not success:
            await asyncio.sleep(0.5)
            success = await attempt()
        if not success:
            logger.error(f"Failed to send notification email to {to_email}")
        return success
    except Exception as e:
        logger.error(f"Error sending notification email to {to_email}: {e}")
        return False


def build_sample_request_out(
    sample_request: SampleRequest,
    product_name: str,
    product_slug: str,
    manufacturer_name: str,
    project_name: Optional[str] = None,
) -> SampleRequestOut:
    return SampleRequestOut(
        id=sample_request.id,
        specifier_id=sample_request.specifier_id,
        product_id=sample_request.product_id,
        product_name=product_name,
        product_slug=product_slug,
        manufacturer_name=manufacturer_name,
        project_id=sample_request.project_id,
        project_name=project_name,
        status=sample_request.status,
        shipping_address=sample_request.shipping_address,
        notes=sample_request.notes,
        tracking_number=sample_request.tracking_number,
        shipped_at=sample_request.shipped_at,
        created_at=sample_request.created_at,
        updated_at=sample_request.updated_at,
    )


def build_quote_request_out(
    quote_request: QuoteRequest,
    product_name: str,
    product_slug: str,
    manufacturer_name: str,
    project_name: Optional[str] = None,
) -> QuoteRequestOut:
    return QuoteRequestOut(
        id=quote_request.id,
        specifier_id=quote_request.specifier_id,
        product_id=quote_request.product_id,
        product_name=product_name,
        product_slug=product_slug,
        manufacturer_name=manufacturer_name,
        project_id=quote_request.project_id,
        project_name=project_name,
        status=quote_request.status,
        quantity=quote_request.quantity,
        quantity_unit=quote_request.quantity_unit,
        specifications=quote_request.specifications,
        notes=quote_request.notes,
        quoted_price=quote_request.quoted_price,
        quoted_currency=quote_request.quoted_currency,
        lead_time_weeks=quote_request.lead_time_weeks,
        terms_notes=quote_request.terms_notes,
        quoted_at=quote_request.quoted_at,
        created_at=quote_request.created_at,
        updated_at=quote_request.updated_at,
    )


@router.post("/samples", response_model=SampleRequestOut, status_code=status.HTTP_201_CREATED)
async def create_sample_request(
    body: SampleRequestCreate,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Product).where(Product.id == body.product_id).options(selectinload(Product.manufacturer))
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if not product.sample_available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Samples not available for this product")

    if body.project_id:
        project = await db.get(Project, body.project_id)
        if not project or project.specifier_id != specifier.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    existing = await db.execute(
        select(SampleRequest).where(
            and_(
                SampleRequest.specifier_id == specifier.id,
                SampleRequest.product_id == body.product_id,
                SampleRequest.status.in_(["pending", "approved"]),
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active sample request for this product",
        )

    rate_limit_key = f"sample_request:{specifier.id}"
    count_stmt = select(func.count(SampleRequest.id)).where(
        and_(
            SampleRequest.specifier_id == specifier.id,
            SampleRequest.created_at > func.now() - text("INTERVAL '1 day'"),
        )
    )
    count_result = await db.execute(count_stmt)
    count = count_result.scalar_one()
    if count >= 10:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    sample_request = SampleRequest(
        id=uuid4(),
        specifier_id=specifier.id,
        product_id=body.product_id,
        project_id=body.project_id,
        status="pending",
        shipping_address=body.shipping_address,
        notes=body.notes,
    )
    db.add(sample_request)
    await db.flush()

    manufacturer_name = product.manufacturer.name if product.manufacturer else ""

    await emit_event(
        db,
        "sample_request.created",
        specifier_id=specifier.id,
        product_id=body.product_id,
        properties={
            "product_name": product.name,
            "manufacturer_name": manufacturer_name,
            "has_project": body.project_id is not None,
        },
    )
    await db.commit()

    return build_sample_request_out(
        sample_request,
        product.name,
        product.slug,
        manufacturer_name,
    )


@router.get("/samples", response_model=SampleRequestListResponse)
async def list_sample_requests(
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    stmt = (
        select(SampleRequest)
        .where(SampleRequest.specifier_id == specifier.id)
        .options(selectinload(SampleRequest.product).selectinload(Product.manufacturer), selectinload(SampleRequest.project))
        .order_by(SampleRequest.created_at.desc())
    )

    total_result = await db.execute(select(func.count(SampleRequest.id)).where(SampleRequest.specifier_id == specifier.id))
    total = total_result.scalar() or 0

    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    sample_requests = result.scalars().all()

    items = []
    for sr in sample_requests:
        product = sr.product
        manufacturer_name = product.manufacturer.name if product.manufacturer else ""
        project_name = sr.project.name if sr.project else None

        items.append(
            build_sample_request_out(
                sr,
                product.name,
                product.slug,
                manufacturer_name,
                project_name,
            )
        )

    return SampleRequestListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/samples/{sample_id}", response_model=SampleRequestOut)
async def get_sample_request(
    sample_id: UUID,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SampleRequest)
        .where(SampleRequest.id == sample_id)
        .options(selectinload(SampleRequest.product).selectinload(Product.manufacturer), selectinload(SampleRequest.project))
    )
    sample_request = result.scalar_one_or_none()

    if not sample_request or sample_request.specifier_id != specifier.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample request not found")

    product = sample_request.product
    manufacturer_name = product.manufacturer.name if product.manufacturer else ""
    project_name = sample_request.project.name if sample_request.project else None

    return build_sample_request_out(
        sample_request,
        product.name,
        product.slug,
        manufacturer_name,
        project_name,
    )


@router.post("/quotes", response_model=QuoteRequestOut, status_code=status.HTTP_201_CREATED)
async def create_quote_request(
    body: QuoteRequestCreate,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Product).where(Product.id == body.product_id).options(selectinload(Product.manufacturer))
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if body.project_id:
        project = await db.get(Project, body.project_id)
        if not project or project.specifier_id != specifier.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    existing = await db.execute(
        select(QuoteRequest).where(
            and_(
                QuoteRequest.specifier_id == specifier.id,
                QuoteRequest.product_id == body.product_id,
                QuoteRequest.status == "pending",
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending quote request for this product",
        )

    count_stmt = select(func.count(QuoteRequest.id)).where(
        and_(
            QuoteRequest.specifier_id == specifier.id,
            QuoteRequest.created_at > func.now() - text("INTERVAL '1 day'"),
        )
    )
    count_result = await db.execute(count_stmt)
    count = count_result.scalar_one()
    if count >= 10:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    quote_request = QuoteRequest(
        id=uuid4(),
        specifier_id=specifier.id,
        product_id=body.product_id,
        project_id=body.project_id,
        quantity=Decimal(str(body.quantity)),
        quantity_unit=body.quantity_unit,
        specifications=body.specifications,
        notes=body.notes,
        status="pending",
    )
    db.add(quote_request)
    await db.flush()

    manufacturer_name = product.manufacturer.name if product.manufacturer else ""

    await emit_event(
        db,
        "quote_request.created",
        specifier_id=specifier.id,
        product_id=body.product_id,
        properties={
            "product_name": product.name,
            "manufacturer_name": manufacturer_name,
            "quantity": str(body.quantity) if body.quantity else None,
            "has_project": body.project_id is not None,
        },
    )
    await db.commit()

    return build_quote_request_out(
        quote_request,
        product.name,
        product.slug,
        manufacturer_name,
    )


@router.get("/quotes", response_model=QuoteRequestListResponse)
async def list_quote_requests(
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    stmt = (
        select(QuoteRequest)
        .where(QuoteRequest.specifier_id == specifier.id)
        .options(selectinload(QuoteRequest.product).selectinload(Product.manufacturer), selectinload(QuoteRequest.project))
        .order_by(QuoteRequest.created_at.desc())
    )

    total_result = await db.execute(select(func.count(QuoteRequest.id)).where(QuoteRequest.specifier_id == specifier.id))
    total = total_result.scalar() or 0

    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    quote_requests = result.scalars().all()

    items = []
    for qr in quote_requests:
        product = qr.product
        manufacturer_name = product.manufacturer.name if product.manufacturer else ""
        project_name = qr.project.name if qr.project else None

        items.append(
            build_quote_request_out(
                qr,
                product.name,
                product.slug,
                manufacturer_name,
                project_name,
            )
        )

    return QuoteRequestListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/quotes/{quote_id}", response_model=QuoteRequestOut)
async def get_quote_request(
    quote_id: UUID,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QuoteRequest)
        .where(QuoteRequest.id == quote_id)
        .options(selectinload(QuoteRequest.product).selectinload(Product.manufacturer), selectinload(QuoteRequest.project))
    )
    quote_request = result.scalar_one_or_none()

    if not quote_request or quote_request.specifier_id != specifier.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote request not found")

    product = quote_request.product
    manufacturer_name = product.manufacturer.name if product.manufacturer else ""
    project_name = quote_request.project.name if quote_request.project else None

    return build_quote_request_out(
        quote_request,
        product.name,
        product.slug,
        manufacturer_name,
        project_name,
    )


@router.get("/admin/samples", response_model=SampleRequestListResponse)
async def list_admin_samples(
    admin: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status"),
    manufacturer_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    stmt = select(SampleRequest).options(selectinload(SampleRequest.product).selectinload(Product.manufacturer), selectinload(SampleRequest.project))

    if status_filter:
        stmt = stmt.where(SampleRequest.status == status_filter)

    if manufacturer_id:
        stmt = stmt.where(Product.manufacturer_id == manufacturer_id).outerjoin(Product)

    stmt = stmt.order_by(SampleRequest.created_at.desc())

    total_stmt = select(func.count(SampleRequest.id))
    if status_filter:
        total_stmt = total_stmt.where(SampleRequest.status == status_filter)
    if manufacturer_id:
        total_stmt = total_stmt.where(Product.manufacturer_id == manufacturer_id).select_from(SampleRequest).outerjoin(Product)

    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    sample_requests = result.scalars().all()

    items = []
    for sr in sample_requests:
        product = sr.product
        manufacturer_name = product.manufacturer.name if product.manufacturer else ""
        project_name = sr.project.name if sr.project else None

        items.append(
            build_sample_request_out(
                sr,
                product.name,
                product.slug,
                manufacturer_name,
                project_name,
            )
        )

    return SampleRequestListResponse(items=items, total=total, page=page, page_size=page_size)


@router.put("/admin/samples/{sample_id}", response_model=SampleRequestOut)
async def update_admin_sample(
    sample_id: UUID,
    body: SampleRequestAdminUpdate,
    admin: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SampleRequest)
        .where(SampleRequest.id == sample_id)
        .options(selectinload(SampleRequest.product).selectinload(Product.manufacturer), selectinload(SampleRequest.project), selectinload(SampleRequest.specifier))
    )
    sample_request = result.scalar_one_or_none()

    if not sample_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample request not found")

    old_status = sample_request.status

    if body.status is not None:
        sample_request.status = body.status
    if body.tracking_number is not None:
        sample_request.tracking_number = body.tracking_number

    if body.status == "shipped":
        sample_request.shipped_at = datetime.utcnow()

    await db.flush()

    if body.status == "shipped":
        specifier = sample_request.specifier
        product = sample_request.product
        tracking_line = f" Tracking: {body.tracking_number}" if body.tracking_number else ""
        html_body = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.5; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p>Hi {specifier.first_name or specifier.email},</p>
                <p>Your sample of <strong>{product.name}</strong> has been shipped.{tracking_line}</p>
                <p>Expected delivery within 5 business days.</p>
            </div>
        </body>
        </html>
        """
        asyncio.create_task(
            send_notification_email(
                specifier.email,
                specifier.first_name or "there",
                "Your sample has shipped",
                html_body,
            )
        )

    await emit_event(
        db,
        "sample_request.status_changed",
        specifier_id=sample_request.specifier_id,
        project_id=sample_request.project_id,
        properties={
            "old_status": old_status,
            "new_status": sample_request.status,
            "product_name": sample_request.product.name,
        },
    )
    await db.commit()

    product = sample_request.product
    manufacturer_name = product.manufacturer.name if product.manufacturer else ""
    project_name = sample_request.project.name if sample_request.project else None

    return build_sample_request_out(
        sample_request,
        product.name,
        product.slug,
        manufacturer_name,
        project_name,
    )


@router.get("/admin/quotes", response_model=QuoteRequestListResponse)
async def list_admin_quotes(
    admin: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status"),
    manufacturer_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    stmt = select(QuoteRequest).options(selectinload(QuoteRequest.product).selectinload(Product.manufacturer), selectinload(QuoteRequest.project))

    if status_filter:
        stmt = stmt.where(QuoteRequest.status == status_filter)

    if manufacturer_id:
        stmt = stmt.where(Product.manufacturer_id == manufacturer_id).outerjoin(Product)

    stmt = stmt.order_by(QuoteRequest.created_at.desc())

    total_stmt = select(func.count(QuoteRequest.id))
    if status_filter:
        total_stmt = total_stmt.where(QuoteRequest.status == status_filter)
    if manufacturer_id:
        total_stmt = total_stmt.where(Product.manufacturer_id == manufacturer_id).select_from(QuoteRequest).outerjoin(Product)

    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    quote_requests = result.scalars().all()

    items = []
    for qr in quote_requests:
        product = qr.product
        manufacturer_name = product.manufacturer.name if product.manufacturer else ""
        project_name = qr.project.name if qr.project else None

        items.append(
            build_quote_request_out(
                qr,
                product.name,
                product.slug,
                manufacturer_name,
                project_name,
            )
        )

    return QuoteRequestListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/admin/quotes/{quote_id}/respond", response_model=QuoteRequestOut)
async def respond_to_quote(
    quote_id: UUID,
    body: QuoteResponseProvide,
    admin: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QuoteRequest)
        .where(QuoteRequest.id == quote_id)
        .options(selectinload(QuoteRequest.product).selectinload(Product.manufacturer), selectinload(QuoteRequest.project), selectinload(QuoteRequest.specifier))
    )
    quote_request = result.scalar_one_or_none()

    if not quote_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote request not found")

    if quote_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot respond to already-quoted request",
        )

    quote_request.quoted_price = body.quoted_price
    quote_request.quoted_currency = body.quoted_currency
    quote_request.lead_time_weeks = body.lead_time_weeks
    quote_request.terms_notes = body.terms_notes
    quote_request.status = "quoted"
    quote_request.quoted_at = datetime.utcnow()

    await db.flush()

    specifier = quote_request.specifier
    product = quote_request.product
    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.5; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <p>Hi {specifier.first_name or specifier.email},</p>
            <p>We have provided a quote for <strong>{product.name}</strong>.</p>
            <p><strong>Price:</strong> {body.quoted_price} {body.quoted_currency}<br><strong>Lead time:</strong> {body.lead_time_weeks} weeks</p>
            {f'<p><strong>Terms:</strong> {body.terms_notes}</p>' if body.terms_notes else ''}
            <p>Log in to Specifio to view full details.</p>
        </div>
    </body>
    </html>
    """
    asyncio.create_task(
        send_notification_email(
            specifier.email,
            specifier.first_name or "there",
            f"Quote provided for {product.name}",
            html_body,
        )
    )

    await emit_event(
        db,
        "quote_request.responded",
        specifier_id=quote_request.specifier_id,
        product_id=quote_request.product_id,
        properties={
            "product_name": product.name,
            "quoted_price": str(body.quoted_price),
            "lead_time_weeks": body.lead_time_weeks,
        },
    )
    await db.commit()

    manufacturer_name = product.manufacturer.name if product.manufacturer else ""
    project_name = quote_request.project.name if quote_request.project else None

    return build_quote_request_out(
        quote_request,
        product.name,
        product.slug,
        manufacturer_name,
        project_name,
    )


@router.put("/admin/quotes/{quote_id}", response_model=QuoteRequestOut)
async def update_admin_quote(
    quote_id: UUID,
    body: QuoteRequestAdminUpdate,
    admin: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QuoteRequest)
        .where(QuoteRequest.id == quote_id)
        .options(selectinload(QuoteRequest.product).selectinload(Product.manufacturer), selectinload(QuoteRequest.project))
    )
    quote_request = result.scalar_one_or_none()

    if not quote_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote request not found")

    old_status = quote_request.status

    if body.status is not None:
        quote_request.status = body.status

    await db.flush()

    await emit_event(
        db,
        "quote_request.status_changed",
        specifier_id=quote_request.specifier_id,
        product_id=quote_request.product_id,
        properties={
            "old_status": old_status,
            "new_status": quote_request.status,
            "product_name": quote_request.product.name,
        },
    )
    await db.commit()

    product = quote_request.product
    manufacturer_name = product.manufacturer.name if product.manufacturer else ""
    project_name = quote_request.project.name if quote_request.project else None

    return build_quote_request_out(
        quote_request,
        product.name,
        product.slug,
        manufacturer_name,
        project_name,
    )


@router.get("/admin/specifiers", response_model=SpecifierListResponse)
async def list_admin_specifiers(
    admin: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    verified: Optional[bool] = Query(None),
    role: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    stmt = select(Specifier)

    if verified is not None:
        stmt = stmt.where(Specifier.verified == verified)

    if role is not None:
        stmt = stmt.where(Specifier.role_type == role)

    stmt = stmt.order_by(Specifier.created_at.desc())

    total_stmt = select(func.count(Specifier.id))
    if verified is not None:
        total_stmt = total_stmt.where(Specifier.verified == verified)
    if role is not None:
        total_stmt = total_stmt.where(Specifier.role_type == role)

    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    specifiers = result.scalars().all()

    items = [SpecifierListOut.from_orm(s) for s in specifiers]

    return SpecifierListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/admin/specifiers/{specifier_id}/verify", response_model=SpecifierListOut)
async def verify_specifier(
    specifier_id: UUID,
    body: SpecifierVerify,
    admin: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    specifier = await db.get(Specifier, specifier_id)

    if not specifier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specifier not found")

    specifier.verified = True
    specifier.verified_at = datetime.utcnow()
    specifier.verified_by_admin_id = admin.id
    specifier.verification_notes = body.verification_notes

    await db.flush()

    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.5; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <p>Hi {specifier.first_name or specifier.email},</p>
            <p>Your Specifio account has been verified. You now have access to trade pricing across all products.</p>
        </div>
    </body>
    </html>
    """
    asyncio.create_task(
        send_notification_email(
            specifier.email,
            specifier.first_name or "there",
            "Your Specifio account has been verified",
            html_body,
        )
    )

    await emit_event(
        db,
        "specifier.verified",
        specifier_id=specifier_id,
        properties={
            "specifier_email": specifier.email,
            "specifier_firm": specifier.firm_name or "",
        },
    )
    await db.commit()

    return SpecifierListOut.from_orm(specifier)


@router.delete("/admin/specifiers/{specifier_id}/verify", response_model=SpecifierListOut)
async def unverify_specifier(
    specifier_id: UUID,
    admin: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    specifier = await db.get(Specifier, specifier_id)

    if not specifier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specifier not found")

    specifier.verified = False
    specifier.verified_at = None
    specifier.verified_by_admin_id = None
    specifier.verification_notes = None

    await db.flush()

    await emit_event(
        db,
        "specifier.unverified",
        specifier_id=specifier_id,
        properties={
            "specifier_email": specifier.email,
        },
    )
    await db.commit()

    return SpecifierListOut.from_orm(specifier)
