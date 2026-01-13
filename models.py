from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
class Deal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str
    description: str
    status: str = "Pending"  # e.g., Pending, Approved, Rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ic_workflows: List["ICWorkflow"] = Relationship(back_populates="deal")  # Link to IC

class ICWorkflow(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        deal_id: int = Field(foreign_key="deal.id")
        approver: str  # e.g., SCP Partner name
        notes: Optional[str]
        approved: bool = False
        updated_at: datetime = Field(default_factory=datetime.utcnow)
        deal: Deal = Relationship(back_populates="ic_workflows")  # Link back to Deal
class Intelligence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    deal_id: Optional[int] = Field(default=None, foreign_key="deal.id")  # Optional link to a deal
    source: str  # e.g., "Manual Entry"
    content: str  # The intelligence data
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
class User(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        username: str = Field(index=True, unique=True)
        hashed_password: str
        is_active: bool = True