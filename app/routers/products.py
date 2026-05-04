from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional
from decimal import Decimal
from uuid import UUID

from app.database import get_db
from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.models.product_image import ProductImage
from app.models.specifier import Specifier
from app.schemas.product import (
    ProductListResponse,
    ProductListItem,
    ProductDetail,
    ProductFilterParams,
    ManufacturerSummary,
    CertificationOut,
    ImageOut,
)
from app.dependencies import get_current_specifier

router = APIRouter(prefix="/products", tags=["products"])


def mask_price(
    price: Optional[Decimal],
    visibility: str,
    specifier: Optional[Specifier],
) -> Optional[Decimal]:
    if visibility == "public":
        return price
    if visibility == "on_request":
        return None
    if visibility == "trade_only" and specifier and specifier.verified:
        return price
    if visibility == "trade_only":
        return None
    if visibility == "registered" and specifier:
        return price
    return None


@router.get("", response_model=ProductListResponse)
async def list_products(
    filters: ProductFilterParams = Depends(),
    specifier: Optional[Specifier] = Depends(get_current_specifier),
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).where(Product.is_active == True)

    if filters.category:
        query = query.where(Product.category == filters.category)

    if filters.manufacturer_id:
        query = query.where(Product.manufacturer_id == filters.manufacturer_id)

    if filters.fire_class_eu:
        query = query.where(Product.fire_class_eu == filters.fire_class_eu)

    if filters.fire_smoke_class_eu:
        query = query.where(Product.fire_smoke_class_eu == filters.fire_smoke_class_eu)

    if filters.fire_droplet_class_eu:
        query = query.where(Product.fire_droplet_class_eu == filters.fire_droplet_class_eu)

    if filters.commercial_grade:
        query = query.where(Product.commercial_grade.any(filters.commercial_grade))

    if filters.nrc_value_min is not None:
        query = query.where(Product.nrc_value >= filters.nrc_value_min)

    if filters.nrc_value_max is not None:
        query = query.where(Product.nrc_value <= filters.nrc_value_max)

    if filters.lead_time_weeks_max is not None:
        query = query.where(Product.lead_time_weeks_min <= filters.lead_time_weeks_max)

    if filters.custom_colorway is not None:
        query = query.where(Product.custom_colorway == filters.custom_colorway)

    if filters.sample_available is not None:
        query = query.where(Product.sample_available == filters.sample_available)

    if filters.is_featured is not None:
        query = query.where(Product.is_featured == filters.is_featured)

    if filters.collection:
        query = query.where(Product.suitable_environments.contains(filters.collection))

    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.where(
            or_(
                Product.name.ilike(search_term),
                Product.long_description.ilike(search_term),
                Product.primary_material.ilike(search_term),
            )
        )

    query = query.options(
        selectinload(Product.manufacturer),
        selectinload(Product.images),
    )

    sort_column = {
        "name": Product.name,
        "created_at": Product.created_at,
        "lead_time_weeks_min": Product.lead_time_weeks_min,
        "indicative_price_eur": Product.indicative_price_eur,
    }.get(filters.sort_by, Product.name)

    if filters.sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    total_result = await db.execute(select(func.count()).select_from(Product).where(Product.is_active == True))
    total = total_result.scalar() or 0

    offset = (filters.page - 1) * filters.page_size
    query = query.offset(offset).limit(filters.page_size)

    result = await db.execute(query)
    products = result.unique().scalars().all()

    items = []
    for product in products:
        primary_image = next((img for img in product.images if img.is_primary), None)
        primary_image_url = primary_image.url if primary_image else None

        item = ProductListItem(
            id=product.id,
            manufacturer_id=product.manufacturer_id,
            manufacturer_name=product.manufacturer.name,
            sku=product.sku,
            name=product.name,
            slug=product.slug,
            category=product.category,
            subcategory=product.subcategory,
            collection=None,
            commercial_grade=product.commercial_grade or [],
            fire_class_eu=product.fire_class_eu,
            fire_smoke_class_eu=product.fire_smoke_class_eu,
            fire_droplet_class_eu=product.fire_droplet_class_eu,
            nrc_value=product.nrc_value,
            acoustic_class=product.acoustic_class,
            custom_colorway=product.custom_colorway,
            lead_time_weeks_min=product.lead_time_weeks_min,
            lead_time_weeks_max=product.lead_time_weeks_max,
            sample_available=product.sample_available,
            sample_type=product.sample_type,
            indicative_price_eur=mask_price(product.indicative_price_eur, product.price_visibility, specifier),
            price_unit=product.price_unit,
            price_currency="EUR",
            price_visibility=product.price_visibility,
            is_featured=product.is_featured,
            primary_image_url=primary_image_url,
        )
        items.append(item)

    total_pages = (total + filters.page_size - 1) // filters.page_size

    return ProductListResponse(
        items=items,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages,
    )


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(
    product_id: UUID,
    specifier: Optional[Specifier] = Depends(get_current_specifier),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Product)
        .where(and_(Product.id == product_id, Product.is_active == True))
        .options(
            selectinload(Product.manufacturer),
            selectinload(Product.certifications),
            selectinload(Product.images),
        )
    )

    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    manufacturer = ManufacturerSummary.model_validate(product.manufacturer)
    certifications = [CertificationOut.model_validate(cert) for cert in product.certifications]
    images = [ImageOut.model_validate(img) for img in sorted(product.images, key=lambda x: x.sort_order)]

    price = mask_price(product.indicative_price_eur, product.price_visibility, specifier)

    return ProductDetail(
        id=product.id,
        manufacturer_id=product.manufacturer_id,
        sku=product.sku,
        name=product.name,
        slug=product.slug,
        category=product.category,
        subcategory=product.subcategory,
        short_description=product.short_description,
        long_description=product.long_description,
        primary_material=product.primary_material,
        secondary_material=product.secondary_material,
        finish_type=product.finish_type,
        colorway_name=product.colorway_name,
        colorway_count=product.colorway_count,
        custom_colorway=product.custom_colorway,
        width_mm=product.width_mm,
        height_mm=product.height_mm,
        thickness_mm=product.thickness_mm,
        weight_value=product.weight_value,
        weight_unit=product.weight_unit,
        repeat_width_mm=product.repeat_width_mm,
        repeat_height_mm=product.repeat_height_mm,
        fire_class_eu=product.fire_class_eu,
        fire_smoke_class_eu=product.fire_smoke_class_eu,
        fire_droplet_class_eu=product.fire_droplet_class_eu,
        fire_class_us=product.fire_class_us,
        nrc_value=product.nrc_value,
        acoustic_class=product.acoustic_class,
        commercial_grade=product.commercial_grade or [],
        suitable_environments=product.suitable_environments,
        recycled_content_pct=product.recycled_content_pct,
        voc_class=product.voc_class,
        price_visibility=product.price_visibility,
        indicative_price_eur=price,
        price_unit=product.price_unit,
        moq=product.moq,
        moq_unit=product.moq_unit,
        lead_time_weeks_min=product.lead_time_weeks_min,
        lead_time_weeks_max=product.lead_time_weeks_max,
        sample_available=product.sample_available,
        sample_type=product.sample_type,
        made_to_order=product.made_to_order,
        is_featured=product.is_featured,
        manufacturer=manufacturer,
        certifications=certifications,
        images=images,
    )
