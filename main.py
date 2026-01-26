"""
Kazi - SCP Deal Intelligence Platform

Entry point for the FastAPI backend application.
Built for Phase 1 MVP: Mandate intake, verification, pipeline, deal rooms, tasks, and IC memo builder.
"""

from contextlib import asynccontextmanager
from datetime import timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from auth import (
    create_access_token,
    get_current_active_admin,
    get_current_user,
    get_password_hash,
    verify_password,
)
from config import get_settings
from database import close_connections, create_db_and_tables, get_session
from intelligence import intelligence_router
from models import (
    Company,
    Contact,
    Deal,
    Document,
    ICWorkflow,
    Intelligence,
    Mandate,
    Organization,
    Task,
    User,
)
from schemas import (
    CompanyCreate,
    CompanyResponse,
    ContactCreate,
    ContactResponse,
    DealCreate,
    DealResponse,
    DealUpdate,
    DocumentCreate,
    DocumentResponse,
    ICMemo,
    ICWorkflowCreate,
    ICWorkflowResponse,
    ICWorkflowUpdate,
    IntelligenceCreate,
    IntelligenceResponse,
    MandateCreate,
    MandateResponse,
    OrganizationCreate,
    OrganizationResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    create_db_and_tables()
    yield
    close_connections()


app = FastAPI(
    title="Kazi - SCP Deal Intelligence Platform",
    description="Backend API for mandate verification, pipeline management, and execution workflows.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Authentication
@app.post("/token", response_model=Token, tags=["Authentication"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """Authenticate user and return JWT token."""
    user = session.exec(select(User).where(User.username == form_data.username)).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


# Users
@app.post("/users/", response_model=UserResponse, tags=["Users"])
def create_user(
    user: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_admin),
):
    """Create a new user (Admin/Owner only)."""
    existing = session.exec(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.get("/users/me", response_model=UserResponse, tags=["Users"])
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@app.get("/users/", response_model=List[UserResponse], tags=["Users"])
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_admin),
):
    """List all users (Admin/Owner only)."""
    users = session.exec(select(User)).all()
    return users


# Organizations
@app.post("/organizations/", response_model=OrganizationResponse, tags=["Organizations"])
def create_organization(
    org: OrganizationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_admin),
):
    """Create a new organization (Admin/Owner only)."""
    existing = session.exec(select(Organization).where(Organization.name == org.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization name already exists",
        )

    db_org = Organization(**org.model_dump())
    session.add(db_org)
    session.commit()
    session.refresh(db_org)
    return db_org


@app.get("/organizations/", response_model=List[OrganizationResponse], tags=["Organizations"])
def list_organizations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all organizations."""
    return session.exec(select(Organization)).all()


# Companies
@app.post("/companies/", response_model=CompanyResponse, tags=["Companies"])
def create_company(
    company: CompanyCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new company."""
    existing = session.exec(select(Company).where(Company.name == company.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name already exists",
        )

    db_company = Company(**company.model_dump())
    session.add(db_company)
    session.commit()
    session.refresh(db_company)
    return db_company


@app.get("/companies/", response_model=List[CompanyResponse], tags=["Companies"])
def list_companies(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all companies."""
    return session.exec(select(Company)).all()


@app.get("/companies/{company_id}", response_model=CompanyResponse, tags=["Companies"])
def get_company(
    company_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a company by ID."""
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# Contacts
@app.post("/contacts/", response_model=ContactResponse, tags=["Contacts"])
def create_contact(
    contact: ContactCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new contact."""
    db_contact = Contact(**contact.model_dump())
    session.add(db_contact)
    session.commit()
    session.refresh(db_contact)
    return db_contact


@app.get("/contacts/", response_model=List[ContactResponse], tags=["Contacts"])
def list_contacts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all contacts."""
    return session.exec(select(Contact)).all()


# Mandates
@app.post("/mandates/", response_model=MandateResponse, tags=["Mandates"])
def create_mandate(
    mandate: MandateCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new mandate with verification scoring."""
    db_mandate = Mandate(
        **mandate.model_dump(),
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
    )
    session.add(db_mandate)
    session.commit()
    session.refresh(db_mandate)
    return db_mandate


@app.get("/mandates/", response_model=List[MandateResponse], tags=["Mandates"])
def list_mandates(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List mandates for current user's organization."""
    return session.exec(
        select(Mandate).where(Mandate.organization_id == current_user.organization_id)
    ).all()


@app.get("/mandates/{mandate_id}", response_model=MandateResponse, tags=["Mandates"])
def get_mandate(
    mandate_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a mandate by ID."""
    mandate = session.get(Mandate, mandate_id)
    if not mandate or mandate.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Mandate not found")
    return mandate


# Deals
@app.post("/deals/", response_model=DealResponse, tags=["Deals"])
def create_deal(
    deal: DealCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new deal."""
    db_deal = Deal(
        **deal.model_dump(),
        owner_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    session.add(db_deal)
    session.commit()
    session.refresh(db_deal)
    return db_deal


@app.get("/deals/", response_model=List[DealResponse], tags=["Deals"])
def list_deals(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List deals for current user's organization."""
    return session.exec(
        select(Deal).where(Deal.organization_id == current_user.organization_id)
    ).all()


@app.get("/deals/{deal_id}", response_model=DealResponse, tags=["Deals"])
def get_deal(
    deal_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a deal by ID."""
    deal = session.get(Deal, deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@app.put("/deals/{deal_id}", response_model=DealResponse, tags=["Deals"])
def update_deal(
    deal_id: int,
    deal_update: DealUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a deal."""
    db_deal = session.get(Deal, deal_id)
    if not db_deal or db_deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    update_data = deal_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_deal, key, value)

    session.add(db_deal)
    session.commit()
    session.refresh(db_deal)
    return db_deal


@app.delete("/deals/{deal_id}", tags=["Deals"])
def delete_deal(
    deal_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a deal."""
    db_deal = session.get(Deal, deal_id)
    if not db_deal or db_deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    session.delete(db_deal)
    session.commit()
    return {"status": "Deal deleted"}


# Tasks
@app.post("/deals/{deal_id}/tasks/", response_model=TaskResponse, tags=["Tasks"])
def create_task(
    deal_id: int,
    task: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a task for a deal."""
    deal = session.get(Deal, deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    db_task = Task(**task.model_dump(), deal_id=deal_id)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@app.get("/deals/{deal_id}/tasks/", response_model=List[TaskResponse], tags=["Tasks"])
def list_tasks(
    deal_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List tasks for a deal."""
    deal = session.get(Deal, deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    return session.exec(select(Task).where(Task.deal_id == deal_id)).all()


@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a task."""
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    deal = session.get(Deal, db_task.deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


# Documents (Data Room)
@app.post("/deals/{deal_id}/documents/", response_model=DocumentResponse, tags=["Documents"])
def create_document(
    deal_id: int,
    document: DocumentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Upload a document to a deal's data room."""
    deal = session.get(Deal, deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    db_document = Document(**document.model_dump(), deal_id=deal_id)
    session.add(db_document)
    session.commit()
    session.refresh(db_document)
    return db_document


@app.get("/deals/{deal_id}/documents/", response_model=List[DocumentResponse], tags=["Documents"])
def list_documents(
    deal_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List documents in a deal's data room."""
    deal = session.get(Deal, deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    return session.exec(select(Document).where(Document.deal_id == deal_id)).all()


# IC Workflows
@app.post("/ic-workflows/", response_model=ICWorkflowResponse, tags=["IC Workflows"])
def create_ic_workflow(
    workflow: ICWorkflowCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create an IC workflow for deal approval."""
    deal = session.get(Deal, workflow.deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    db_workflow = ICWorkflow(**workflow.model_dump())
    session.add(db_workflow)
    session.commit()
    session.refresh(db_workflow)
    return db_workflow


@app.get("/ic-workflows/", response_model=List[ICWorkflowResponse], tags=["IC Workflows"])
def list_ic_workflows(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List IC workflows for current user's organization."""
    return session.exec(
        select(ICWorkflow).join(Deal).where(
            Deal.organization_id == current_user.organization_id
        )
    ).all()


@app.put("/ic-workflows/{workflow_id}", response_model=ICWorkflowResponse, tags=["IC Workflows"])
def update_ic_workflow(
    workflow_id: int,
    workflow_update: ICWorkflowUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update an IC workflow."""
    db_workflow = session.get(ICWorkflow, workflow_id)
    if not db_workflow:
        raise HTTPException(status_code=404, detail="IC Workflow not found")

    deal = session.get(Deal, db_workflow.deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="IC Workflow not found")

    update_data = workflow_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_workflow, key, value)

    session.add(db_workflow)
    session.commit()
    session.refresh(db_workflow)
    return db_workflow


@app.delete("/ic-workflows/{workflow_id}", tags=["IC Workflows"])
def delete_ic_workflow(
    workflow_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete an IC workflow."""
    db_workflow = session.get(ICWorkflow, workflow_id)
    if not db_workflow:
        raise HTTPException(status_code=404, detail="IC Workflow not found")

    deal = session.get(Deal, db_workflow.deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="IC Workflow not found")

    session.delete(db_workflow)
    session.commit()
    return {"status": "IC Workflow deleted"}


# Intelligence
@app.post("/intelligence/", response_model=IntelligenceResponse, tags=["Intelligence"])
def create_intelligence(
    intel: IntelligenceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create intelligence data."""
    if intel.deal_id:
        deal = session.get(Deal, intel.deal_id)
        if not deal or deal.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Deal not found")

    db_intel = Intelligence(**intel.model_dump())
    session.add(db_intel)
    session.commit()
    session.refresh(db_intel)
    return db_intel


@app.get("/intelligence/", response_model=List[IntelligenceResponse], tags=["Intelligence"])
def list_intelligence(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all intelligence data."""
    return session.exec(select(Intelligence)).all()


@app.delete("/intelligence/{intel_id}", tags=["Intelligence"])
def delete_intelligence(
    intel_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete intelligence data."""
    db_intel = session.get(Intelligence, intel_id)
    if not db_intel:
        raise HTTPException(status_code=404, detail="Intelligence not found")

    session.delete(db_intel)
    session.commit()
    return {"status": "Intelligence deleted"}


# IC Memo Builder
@app.get("/deals/{deal_id}/ic-memo", response_model=ICMemo, tags=["IC Memo"])
def generate_ic_memo(
    deal_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Generate an IC memo for a deal (basic template, expand with AI in Phase 2)."""
    deal = session.get(Deal, deal_id)
    if not deal or deal.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Deal not found")

    mandate = session.get(Mandate, deal.mandate_id) if deal.mandate_id else None
    company = session.get(Company, deal.company_id) if deal.company_id else None

    return ICMemo(
        thesis_fit=f"Based on mandate scope: {mandate.scope if mandate else 'N/A'}",
        market=f"Sector: {company.sector if company else deal.company_name}",
        business_model=deal.description,
        financial_snapshot="High-level metrics to be populated from data room",
        risks="Key risks to be identified during diligence",
        valuation="Valuation range to be determined",
        diligence_plan=f"Next steps for {deal.stage} stage",
    )


# Include intelligence router
app.include_router(intelligence_router, prefix="/intelligence", tags=["Intelligence AI"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
