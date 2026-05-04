from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class RegisterRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    firm_name: str
    role: str
    country: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    message: str


class TokenVerifyResponse(BaseModel):
    access_token: str
    token_type: str
    specifier_id: str


class SpecifierProfile(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    firm_name: str
    role: Optional[str]
    country: Optional[str]
    phone: Optional[str]
    specialization: Optional[str]
    firm_website: Optional[str]
    linkedin_url: Optional[str]
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
