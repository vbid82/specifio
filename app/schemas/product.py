from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date


class ManufacturerSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    country: str
    logo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class CertificationOut(BaseModel):
    id: UUID
    certification_code: str
    certification_name: Optional[str] = None
    issued_by: Optional[str] = None
    certificate_number: Optional[str] = None
    valid_until: Optional[date] = None
    document_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ImageOut(BaseModel):
    id: UUID
    url: str
    alt_text: Optional[str] = None
    sort_order: int
    is_primary: bool

    model_config = {"from_attributes": True}


class ProductListItem(BaseModel):
    id: UUID
    manufacturer_id: UUID
    manufacturer_name: str
    sku: str
    name: str
    slug: str
    category: str
    subcategory: Optional[str] = None
    collection: Optional[str] = None
    commercial_grade: List[str] = Field(default_factory=list)
    fire_class_eu: Optional[str] = None
    fire_smoke_class_eu: Optional[str] = None
    fire_droplet_class_eu: Optional[str] = None
    nrc_value: Optional[Decimal] = None
    acoustic_class: Optional[str] = None
    custom_colorway: bool
    lead_time_weeks_min: int
    lead_time_weeks_max: Optional[int] = None
    sample_available: bool
    sample_type: Optional[str] = None
    indicative_price_eur: Optional[Decimal] = None
    price_unit: Optional[str] = None
    price_currency: str = "EUR"
    price_visibility: str
    is_featured: bool
    primary_image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductDetail(BaseModel):
    id: UUID
    manufacturer_id: UUID
    sku: str
    name: str
    slug: str
    category: str
    subcategory: Optional[str] = None
    short_description: str
    long_description: Optional[str] = None
    primary_material: str
    secondary_material: Optional[str] = None
    finish_type: Optional[str] = None
    colorway_name: Optional[str] = None
    colorway_count: Optional[int] = None
    custom_colorway: bool
    width_mm: Optional[Decimal] = None
    height_mm: Optional[Decimal] = None
    thickness_mm: Optional[Decimal] = None
    weight_value: Optional[Decimal] = None
    weight_unit: Optional[str] = None
    repeat_width_mm: Optional[Decimal] = None
    repeat_height_mm: Optional[Decimal] = None
    fire_class_eu: Optional[str] = None
    fire_smoke_class_eu: Optional[str] = None
    fire_droplet_class_eu: Optional[str] = None
    fire_class_us: Optional[str] = None
    nrc_value: Optional[Decimal] = None
    acoustic_class: Optional[str] = None
    commercial_grade: List[str] = Field(default_factory=list)
    suitable_environments: Optional[str] = None
    recycled_content_pct: Optional[int] = None
    voc_class: Optional[str] = None
    price_visibility: str
    indicative_price_eur: Optional[Decimal] = None
    price_unit: Optional[str] = None
    moq: int
    moq_unit: Optional[str] = None
    lead_time_weeks_min: int
    lead_time_weeks_max: Optional[int] = None
    sample_available: bool
    sample_type: Optional[str] = None
    made_to_order: bool
    is_featured: bool
    manufacturer: ManufacturerSummary
    certifications: List[CertificationOut] = Field(default_factory=list)
    images: List[ImageOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: List[ProductListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductFilterParams(BaseModel):
    category: Optional[str] = None
    manufacturer_id: Optional[UUID] = None
    fire_class_eu: Optional[str] = None
    fire_smoke_class_eu: Optional[str] = None
    fire_droplet_class_eu: Optional[str] = None
    commercial_grade: Optional[str] = None
    nrc_value_min: Optional[float] = None
    nrc_value_max: Optional[float] = None
    lead_time_weeks_max: Optional[int] = None
    custom_colorway: Optional[bool] = None
    sample_available: Optional[bool] = None
    is_featured: Optional[bool] = None
    collection: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=100)
    sort_by: str = Field(default="name", pattern="^(name|created_at|lead_time_weeks_min|indicative_price_eur)$")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")

    @field_validator("sort_by", mode="before")
    def normalize_sort_by(cls, v):
        if v is None:
            return "name"
        return v

    @field_validator("sort_order", mode="before")
    def normalize_sort_order(cls, v):
        if v is None:
            return "asc"
        return v.lower()
