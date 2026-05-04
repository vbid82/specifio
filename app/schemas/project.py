from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    client_name: Optional[str] = None
    project_type: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None


class ProjectProductAdd(BaseModel):
    product_id: UUID
    notes: Optional[str] = None


class ProjectProductUpdate(BaseModel):
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class ProjectProductOut(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    product_slug: str
    product_category: str
    manufacturer_name: str
    primary_image_url: Optional[str] = None
    notes: Optional[str] = None
    sort_order: int
    added_at: datetime


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    client_name: Optional[str] = None
    project_type: Optional[str] = None
    status: str
    is_shared: bool
    share_url: Optional[str] = None
    product_count: int
    created_at: datetime
    updated_at: datetime


class ProjectDetailOut(ProjectOut):
    products: List[ProjectProductOut] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    items: List[ProjectOut]
    total: int


class ShareLinkResponse(BaseModel):
    share_url: str
    share_token: str
