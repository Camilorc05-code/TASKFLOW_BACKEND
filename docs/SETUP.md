# TaskFlow Backend - Setup Guide

This document provides a step-by-step guide to configure and run the FastAPI backend project with SQLAlchemy and PostgreSQL.

---

## Step 1 — Add `.gitignore`
Create a `.gitignore` file in the project root to exclude unnecessary files:


---

## Step 1 — Create PostgreSQL Database
In PostgreSQL, create a database named: taskflow_db

You can use pgAdmin, DBeaver, or the terminal.

---

## Step 3 — Configure SQLAlchemy and PostgreSQL Connection
File: `app/db/database.py`

Define the database connection using SQLAlchemy:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost/taskflow_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

## Step 4 — Create Pydantic Schemas
File: app/schemas/user.py  
Define input models for user registration and login. Pydantic validates data types automatically.

python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
## Step 5 — Password Hash Utility
File: app/auth/hash.py  
Use Passlib with bcrypt to hash and verify passwords securely.

python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )
## Step 6 — Database Dependency
File: app/db/dependencies.py  
Create a function to manage database sessions automatically.

python
from app.db.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
## Step 7 — User Registration Route
File: app/routes/auth.py  
Define the /register route to create users with hashed passwords.

python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate
from app.models.user import User
from app.db.dependencies import get_db
from app.auth.hash import hash_password

router = APIRouter()

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully"
    }
## Step 8 — Connect Routes to Main
File: app/main.py  
Include the authentication router in the FastAPI app.

python
from fastapi import FastAPI

from app.db.database import engine, Base
from app.models.user import User
from app.routes.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "TaskFlow API 