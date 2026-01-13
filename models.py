import os
from sshtunnel import SSHTunnelForwarder
from sqlmodel import create_engine
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
# Environment variables for security (set in .env or os.environ)
PA_USERNAME = os.environ.get('PA_USERNAME', 'sackson')
PA_PASSWORD = os.environ.get('PA_PASSWORD')
PG_HOST = os.environ.get('PG_HOST', 'sackson-1234.postgres.pythonanywhere-services.com')  # Your hostname
PG_PORT = int(os.environ.get('PG_PORT', 1234))  # Your port
PG_USER = os.environ.get('PG_USER')
PG_PASS = os.environ.get('PG_PASS')
PG_DB = os.environ.get('PG_DB')

with SSHTunnelForwarder(
    ('ssh.pythonanywhere.com'),
    ssh_username=PA_USERNAME,
    ssh_password=PA_PASSWORD,
    remote_bind_address=(PG_HOST, PG_PORT)
) as tunnel:
    engine = create_engine(f"postgresql://{PG_USER}:{PG_PASS}@127.0.0.1:{tunnel.local_bind_port}/{PG_DB}")
    # Use engine for sessions or queries
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