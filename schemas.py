"""
Pydantic schemas for API request/response validation.
Uses Pydantic v2 syntax.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Token schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None


# User schemas
class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: str = Field(default="Member")
    organization_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    organization_id: Optional[int]
    is_active: bool
    created_at: datetime


# Organization schemas
class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""
    name: str = Field(..., min_length=2, max_length=100)
    type: str = Field(..., description="SCP, SearchCo, or PartnerFirm")


class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    created_at: datetime


# Company schemas
class CompanyCreate(BaseModel):
    """Schema for creating a company."""
    name: str = Field(..., min_length=2, max_length=200)
    website: Optional[str] = None
    location: Optional[str] = None
    sector: Optional[str] = None
    size_estimate: Optional[str] = None
    owner_type: Optional[str] = None


class CompanyResponse(BaseModel):
    """Schema for company response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website: Optional[str]
    location: Optional[str]
    sector: Optional[str]
    size_estimate: Optional[str]
    owner_type: Optional[str]
    created_at: datetime


# Contact schemas
class ContactCreate(BaseModel):
    """Schema for creating a contact."""
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    company_id: Optional[int] = None
    relationship_strength: Optional[str] = Field(
        default=None, pattern="^(Strong|Medium|Weak)$"
    )


class ContactResponse(BaseModel):
    """Schema for contact response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    role: Optional[str]
    company_id: Optional[int]
    relationship_strength: Optional[str]
    created_at: datetime


# Mandate schemas
class MandateCreate(BaseModel):
    """Schema for creating a mandate."""
    type: str = Field(..., pattern="^(buy-side|sell-side|trading)$")
    scope: Optional[str] = None
    timeline: Optional[str] = None
    fee_model: Optional[str] = None
    exclusivity: Optional[str] = None
    confidence_score: str = Field(..., pattern="^[ABC]$")
    proof_documents: Optional[str] = None
    company_id: Optional[int] = None


class MandateResponse(BaseModel):
    """Schema for mandate response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    scope: Optional[str]
    timeline: Optional[str]
    fee_model: Optional[str]
    exclusivity: Optional[str]
    confidence_score: str
    proof_documents: Optional[str]
    organization_id: Optional[int]
    company_id: Optional[int]
    created_by_id: Optional[int]
    created_at: datetime


# Deal schemas
class DealCreate(BaseModel):
    """Schema for creating a deal."""
    company_name: str
    description: str
    stage: str = Field(default="Origination")
    type: Optional[str] = None
    mandate_id: Optional[int] = None
    company_id: Optional[int] = None
    quality_score: Optional[int] = Field(default=None, ge=0, le=100)


class DealUpdate(BaseModel):
    """Schema for updating a deal."""
    company_name: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    quality_score: Optional[int] = Field(default=None, ge=0, le=100)


class DealResponse(BaseModel):
    """Schema for deal response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    description: str
    stage: str
    type: Optional[str]
    status: str
    mandate_id: Optional[int]
    company_id: Optional[int]
    owner_id: Optional[int]
    organization_id: Optional[int]
    quality_score: Optional[int]
    created_at: datetime


# Task schemas
class TaskCreate(BaseModel):
    """Schema for creating a task."""
    description: str
    owner_id: Optional[int] = None
    due_date: Optional[datetime] = None
    status: str = Field(default="Pending", pattern="^(Pending|In Progress|Completed)$")


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    description: Optional[str] = None
    owner_id: Optional[int] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = Field(default=None, pattern="^(Pending|In Progress|Completed)$")


class TaskResponse(BaseModel):
    """Schema for task response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    owner_id: Optional[int]
    deal_id: Optional[int]
    due_date: Optional[datetime]
    status: str
    created_at: datetime


# Document schemas
class DocumentCreate(BaseModel):
    """Schema for creating a document."""
    name: str
    path: str
    version: int = Field(default=1, ge=1)
    permissions: Optional[str] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    path: str
    version: int
    deal_id: Optional[int]
    permissions: Optional[str]
    created_at: datetime


# IC Workflow schemas
class ICWorkflowCreate(BaseModel):
    """Schema for creating an IC workflow."""
    deal_id: int
    approver: str
    notes: Optional[str] = None
    approved: bool = False


class ICWorkflowUpdate(BaseModel):
    """Schema for updating an IC workflow."""
    notes: Optional[str] = None
    approved: Optional[bool] = None


class ICWorkflowResponse(BaseModel):
    """Schema for IC workflow response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    deal_id: int
    approver: str
    notes: Optional[str]
    approved: bool
    updated_at: datetime


# Intelligence schemas
class IntelligenceCreate(BaseModel):
    """Schema for creating intelligence data."""
    deal_id: Optional[int] = None
    source: str
    content: str


class IntelligenceResponse(BaseModel):
    """Schema for intelligence response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    deal_id: Optional[int]
    source: str
    content: str
    ingested_at: datetime


# IC Memo schema
class ICMemo(BaseModel):
    """Schema for generated IC memo."""
    thesis_fit: str
    market: str
    business_model: str
    financial_snapshot: str
    risks: str
    valuation: str
    diligence_plan: str
