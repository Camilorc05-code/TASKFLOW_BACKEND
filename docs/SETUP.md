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
    return {"message": "TaskFlow API"}

## Step 9 — JWT Environment Variables
File: .env  
Add JWT configuration variables:

env
SECRET_KEY=supersecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
(Later you can generate a stronger key using openssl rand -hex 32 or python -c "import secrets; print(secrets.token_hex(32))")

## Step 10 — JWT Utility
File: app/auth/jwt_handler.py  
Create a helper to generate JWT tokens:

python
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
## Step 11 — Login Endpoint
File: app/routes/auth.py  
Add a /login route below /register:

python
from fastapi import HTTPException
from app.schemas.user import UserLogin
from app.auth.hash import verify_password
from app.auth.jwt_handler import create_access_token

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}
## Step 12 — Test Login
In Swagger UI:
POST /login with:

json
{
  "email": "camilo@test.com",
  "password": "123456"
}
Expected response:

json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
## Step 13 — Auth Dependency
File: app/auth/dependencies.py  
Create a dependency to validate JWT tokens:

python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception
## Step 14 — Protected Route
File: app/main.py  
Add a protected route:

python
from app.auth.dependencies import get_current_user
from fastapi import Depends

@app.get("/profile")
def profile(current_user: str = Depends(get_current_user)):
    return {"user": current_user}
## Step 15 — Test Authorization
Login and copy the token.

In Swagger UI → Authorize → paste Bearer <your_token>.

Call /profile.
Expected: returns the user’s email.

## Step 16 — Team Model
File: app/models/team.py

python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tasks = relationship("Task", back_populates="team")
## Step 17 — Task Model
File: app/models/task.py

python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="pending")
    team_id = Column(Integer, ForeignKey("teams.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    team = relationship("Team", back_populates="tasks")
## Step 18 — Relate User with Task
File: app/models/user.py  
Add:

python
from sqlalchemy.orm import relationship

tasks = relationship("Task")
## 19 — Import Models
File: app/main.py

python
from app.models.team import Team
from app.models.task import Task
Step 37 — Restart Server
Run:

bash
uvicorn app.main:app --reload
SQLAlchemy will create teams and tasks.

## Step 20 — Verify Tables
In PostgreSQL:

sql
\dt
Tables should exist: users, teams, tasks.

## Step 21 — Schemas
File: app/schemas/team.py

python
from pydantic import BaseModel
class TeamCreate(BaseModel):
    name: str
File: app/schemas/task.py

python
from pydantic import BaseModel
class TaskCreate(BaseModel):
    title: str
    description: str
    team_id: int
## Step 22 — Team Routes
File: app/routes/team.py

python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.team import TeamCreate
from app.models.team import Team
from app.db.dependencies import get_db

router = APIRouter(prefix="/teams")

@router.post("/")
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    new_team = Team(name=team.name)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team
## Step 23 — Connect Team Router
File: app/main.py

python
from app.routes.team import router as team_router
app.include_router(team_router)
## Step 24 — Task Routes
File: app/routes/task.py

python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.task import TaskCreate
from app.models.task import Task
from app.db.dependencies import get_db

router = APIRouter(prefix="/tasks")

@router.post("/")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(title=task.title, description=task.description, team_id=task.team_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task
## Step 25 — Connect Task Router
File: app/main.py

python
from app.routes.task import router as task_router
app.include_router(task_router)