"""
Database models for the Kazi SCP Deal Intelligence Platform.
Uses SQLModel for SQLAlchemy + Pydantic integration.
"""

from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Organization(SQLModel, table=True):
    """Organization entity (SCP, SearchCo, PartnerFirm)."""
    __tablename__ = "organizations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    type: str = Field(description="e.g., 'SCP', 'SearchCo', 'PartnerFirm'")
    created_at: datetime = Field(default_factory=utc_now)

    users: List["User"] = Relationship(back_populates="organization")
    mandates: List["Mandate"] = Relationship(back_populates="organization")
    deals: List["Deal"] = Relationship(back_populates="organization")


class User(SQLModel, table=True):
    """User entity with authentication and RBAC."""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: str = Field(default="Member", description="Owner, Admin, Member, Viewer")
    organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)

    organization: Optional[Organization] = Relationship(back_populates="users")
    mandates: List["Mandate"] = Relationship(back_populates="created_by")
    owned_deals: List["Deal"] = Relationship(back_populates="owner")


class Company(SQLModel, table=True):
    """Company entity for deals and contacts."""
    __tablename__ = "companies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    website: Optional[str] = None
    location: Optional[str] = None
    sector: Optional[str] = None
    size_estimate: Optional[str] = None
    owner_type: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

    contacts: List["Contact"] = Relationship(back_populates="company")
    mandates: List["Mandate"] = Relationship(back_populates="company")
    deals: List["Deal"] = Relationship(back_populates="company")


class Contact(SQLModel, table=True):
    """Contact entity for relationship management."""
    __tablename__ = "contacts"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    relationship_strength: Optional[str] = Field(
        default=None, description="Strong, Medium, Weak"
    )
    created_at: datetime = Field(default_factory=utc_now)

    company: Optional[Company] = Relationship(back_populates="contacts")


class Mandate(SQLModel, table=True):
    """Mandate entity for deal mandates."""
    __tablename__ = "mandates"

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(description="buy-side, sell-side, trading")
    scope: Optional[str] = None
    timeline: Optional[str] = None
    fee_model: Optional[str] = None
    exclusivity: Optional[str] = None
    confidence_score: str = Field(description="A, B, or C")
    proof_documents: Optional[str] = Field(
        default=None, description="JSON or comma-separated file paths"
    )
    organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=utc_now)

    organization: Optional[Organization] = Relationship(back_populates="mandates")
    company: Optional[Company] = Relationship(back_populates="mandates")
    created_by: Optional[User] = Relationship(back_populates="mandates")
    deals: List["Deal"] = Relationship(back_populates="mandate")


class Deal(SQLModel, table=True):
    """Deal entity for pipeline management."""
    __tablename__ = "deals"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str
    description: str
    stage: str = Field(default="Origination", description="Origination, Diligence, Closing")
    type: Optional[str] = Field(default=None, description="Search Fund, M&A, Trading")
    status: str = Field(default="Pending", description="Pending, Approved, Rejected")
    mandate_id: Optional[int] = Field(default=None, foreign_key="mandates.id")
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id")
    organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")
    quality_score: Optional[int] = None
    created_at: datetime = Field(default_factory=utc_now)

    mandate: Optional[Mandate] = Relationship(back_populates="deals")
    company: Optional[Company] = Relationship(back_populates="deals")
    owner: Optional[User] = Relationship(back_populates="owned_deals")
    organization: Optional[Organization] = Relationship(back_populates="deals")
    tasks: List["Task"] = Relationship(back_populates="deal")
    documents: List["Document"] = Relationship(back_populates="deal")
    ic_workflows: List["ICWorkflow"] = Relationship(back_populates="deal")
    intelligence: List["Intelligence"] = Relationship(back_populates="deal")


class Task(SQLModel, table=True):
    """Task entity for deal task management."""
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id")
    deal_id: Optional[int] = Field(default=None, foreign_key="deals.id")
    due_date: Optional[datetime] = None
    status: str = Field(default="Pending", description="Pending, In Progress, Completed")
    created_at: datetime = Field(default_factory=utc_now)

    deal: Optional[Deal] = Relationship(back_populates="tasks")


class Document(SQLModel, table=True):
    """Document entity for data room management."""
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    path: str = Field(description="S3 or storage path")
    version: int = Field(default=1)
    deal_id: Optional[int] = Field(default=None, foreign_key="deals.id")
    permissions: Optional[str] = Field(default=None, description="JSON for ACL")
    created_at: datetime = Field(default_factory=utc_now)

    deal: Optional[Deal] = Relationship(back_populates="documents")


class ICWorkflow(SQLModel, table=True):
    """Investment Committee workflow for deal approvals."""
    __tablename__ = "ic_workflows"

    id: Optional[int] = Field(default=None, primary_key=True)
    deal_id: int = Field(foreign_key="deals.id")
    approver: str = Field(description="SCP Partner name")
    notes: Optional[str] = None
    approved: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=utc_now)

    deal: Deal = Relationship(back_populates="ic_workflows")


class Intelligence(SQLModel, table=True):
    """Intelligence data for deals and market insights."""
    __tablename__ = "intelligence"

    id: Optional[int] = Field(default=None, primary_key=True)
    deal_id: Optional[int] = Field(default=None, foreign_key="deals.id")
    source: str = Field(description="e.g., Manual Entry, API, Scrape")
    content: str
    ingested_at: datetime = Field(default_factory=utc_now)

    deal: Optional[Deal] = Relationship(back_populates="intelligence")
