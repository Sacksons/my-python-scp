from sqlmodel import create_engine, Session
from models import SQLModel  # Absolute import to avoid package assumption


engine = create_engine("sqlite:///database.db", echo=True)  # SQLite file for MVP

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session