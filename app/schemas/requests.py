from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class SampleRequestCreate(BaseModel):
    product_id: UUID
    project_id: Optional[UUID] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class SampleRequestOut(BaseModel):
    id: UUID
    specifier_id: UUID
    product_id: UUID
    product_name: str
    product_slug: str
    manufacturer_name: str
    project_id: Optional[UUID] = None
    project_name: Optional[str] = None
    status: str
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SampleRequestAdminUpdate(BaseModel):
    status: Optional[str] = None
    tracking_number: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ("pending", "approved", "shipped", "delivered", "cancelled"):
            raise ValueError("Invalid status")
        return v


class SampleRequestListResponse(BaseModel):
    items: List[SampleRequestOut]
    total: int
    page: int
    page_size: int


class QuoteRequestCreate(BaseModel):
    product_id: UUID
    project_id: Optional[UUID] = None
    quantity: float
    quantity_unit: str
    specifications: Optional[str] = None
    notes: Optional[str] = None


class QuoteRequestOut(BaseModel):
    id: UUID
    specifier_id: UUID
    product_id: UUID
    product_name: str
    product_slug: str
    manufacturer_name: str
    project_id: Optional[UUID] = None
    project_name: Optional[str] = None
    status: str
    quantity: Decimal
    quantity_unit: str
    specifications: Optional[str] = None
    notes: Optional[str] = None
    quoted_price: Optional[Decimal] = None
    quoted_currency: str
    lead_time_weeks: Optional[int] = None
    terms_notes: Optional[str] = None
    quoted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuoteResponseProvide(BaseModel):
    quoted_price: Decimal = Field(ge=0, le=1000000)
    quoted_currency: str = Field(default="EUR")
    lead_time_weeks: int = Field(ge=1, le=52)
    terms_notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("quoted_currency")
    @classmethod
    def validate_currency(cls, v):
        if v not in ("EUR", "GBP", "USD"):
            raise ValueError("Invalid currency")
        return v


class QuoteRequestAdminUpdate(BaseModel):
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ("pending", "quoted", "accepted", "rejected", "expired"):
            raise ValueError("Invalid status")
        return v


class QuoteRequestListResponse(BaseModel):
    items: List[QuoteRequestOut]
    total: int
    page: int
    page_size: int


class SpecifierListOut(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    firm_name: Optional[str] = None
    role: Optional[str] = None
    verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SpecifierVerify(BaseModel):
    verification_notes: Optional[str] = None


class SpecifierListResponse(BaseModel):
    items: List[SpecifierListOut]
    total: int
    page: int
    page_size: int
