from fastapi import HTTPException
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from auth import get_current_user, get_password_hash, verify_password, create_access_token, User
from sqlmodel import Session
from database import create_db_and_tables, get_session  # Assuming absolute imports from earlier fix
from models import Deal, ICWorkflow, Intelligence
from pydantic import BaseModel, field_validator
from typing import List, Optional  # Add or confirm Optional here
from datetime import datetime
from intelligence import intelligence_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  # Initializes tables on startup
    yield  # App runs here; add shutdown if needed
app = FastAPI(lifespan=lifespan)
origins = [
    "http://localhost:3000",  # Frontend URL
    "http://127.0.0.1:3000",  # Alternative
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers (e.g., Authorization for JWT)
)



app = FastAPI(lifespan=lifespan)  # Pass lifespan to the app


class DealCreate(BaseModel):
    company_name: str
    description: str


class DealRead(DealCreate):
    id: int
    status: str
    created_at: datetime


class ICWorkflowCreate(BaseModel):
    deal_id: int
    approver: str
    notes: Optional[str]  # This line was the error spot
    approved: bool


class ICWorkflowRead(ICWorkflowCreate):
    id: int
    updated_at: datetime


class IntelligenceCreate(BaseModel):
    deal_id: Optional[int]
    source: str
    content: str


class IntelligenceRead(IntelligenceCreate):
    id: int
    ingested_at: datetime



class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator('password', mode='before')  # Use 'before' for pre-processing (e.g., hashing)
    def validate_password(cls, v):
        # Retain existing logic
        return v


# ... (imports, lifespan, app = FastAPI, Pydantic classes like UserCreate)

@app.post("/users/")
# ... (imports, lifespan, app = FastAPI, Pydantic classes like UserCreate)

@app.post("/users/")
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/")
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # ... (function body)
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/deals/", response_model=DealRead)
def create_deal(deal: DealCreate, session: Session = Depends(get_session),
                current_user: User = Depends(get_current_user)):
    db_deal = Deal(**deal.dict())
    session.add(db_deal)
    session.commit()
    session.refresh(db_deal)
    return db_deal


@app.get("/deals/", response_model=List[DealRead])
def read_deals(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return session.query(Deal).all()


@app.post("/ic-workflows/", response_model=ICWorkflowRead)
def create_ic_workflow(workflow: ICWorkflowCreate, session: Session = Depends(get_session),
                       current_user: User = Depends(get_current_user)):
    db_workflow = ICWorkflow(**workflow.dict())
    session.add(db_workflow)
    session.commit()
    session.refresh(db_workflow)
    return db_workflow


@app.put("/ic-workflows/{workflow_id}", response_model=ICWorkflowRead)
def update_ic_workflow(workflow_id: int, workflow: ICWorkflowCreate, session: Session = Depends(get_session),
                       current_user: User = Depends(get_current_user)):
    db_workflow = session.get(ICWorkflow, workflow_id)
    if not db_workflow:
        raise HTTPException(status_code=404, detail="IC Workflow not found")
    workflow_data = workflow.dict(exclude_unset=True)
    for key, value in workflow_data.items():
        setattr(db_workflow, key, value)
    session.add(db_workflow)
    session.commit()
    session.refresh(db_workflow)
    return db_workflow


@app.put("/deals/{deal_id}", response_model=DealRead)
def update_deal(deal_id: int, deal: DealCreate, session: Session = Depends(get_session),
                current_user: User = Depends(get_current_user)):
    db_deal = session.get(Deal, deal_id)
    if not db_deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    deal_data = deal.dict(exclude_unset=True)
    for key, value in deal_data.items():
        setattr(db_deal, key, value)
    session.add(db_deal)
    session.commit()
    session.refresh(db_deal)
    return db_deal


@app.delete("/deals/{deal_id}")
def delete_deal(deal_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_deal = session.get(Deal, deal_id)
    if not db_deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    session.delete(db_deal)
    session.commit()
    return {"status": "Deal deleted"}


@app.get("/ic-workflows/", response_model=List[ICWorkflowRead])
def read_ic_workflows(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return session.query(ICWorkflow).all()


@app.post("/intelligence/", response_model=IntelligenceRead)
def create_intelligence(intel: IntelligenceCreate, session: Session = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    db_intel = Intelligence(**intel.dict())
    session.add(db_intel)
    session.commit()
    session.refresh(db_intel)
    return db_intel


@app.get("/intelligence/", response_model=List[IntelligenceRead])
def read_intelligence(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return session.query(Intelligence).all()


# Add PUT and DELETE similarly, using id
@app.put("/intelligence/{intel_id}", response_model=IntelligenceRead)
def update_intelligence(intel_id: int, intel: IntelligenceCreate, session: Session = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    db_intel = session.get(Intelligence, intel_id)
    if not db_intel:
        raise HTTPException(status_code=404, detail="Intelligence not found")
    intel_data = intel.dict(exclude_unset=True)
    for key, value in intel_data.items():
        setattr(db_intel, key, value)
    session.add(db_intel)
    session.commit()
    session.refresh(db_intel)
    return db_intel


@app.delete("/ic-workflows/{workflow_id}")
def delete_ic_workflow(workflow_id: int, session: Session = Depends(get_session),
                       current_user: User = Depends(get_current_user)):
    db_workflow = session.get(ICWorkflow, workflow_id)
    if not db_workflow:
        raise HTTPException(status_code=404, detail="IC Workflow not found")
    session.delete(db_workflow)
    session.commit()
    return {"status": "IC Workflow deleted"}


@app.delete("/intelligence/{intel_id}")
def delete_intelligence(intel_id: int, session: Session = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    db_intel = session.get(Intelligence, intel_id)
    if not db_intel:
        raise HTTPException(status_code=404, detail="Intelligence not found")
    session.delete(db_intel)
    session.commit()
    return {"status": "Intelligence deleted"}


app.include_router(intelligence_router, prefix="/intelligence")
