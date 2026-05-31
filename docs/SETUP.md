# TaskFlow Backend - Setup Guide

This document provides a step-by-step guide to configure and run the FastAPI backend project with SQLAlchemy and PostgreSQL.

---

## Step 11 — Add `.gitignore`
Create a `.gitignore` file in the project root to exclude unnecessary files:


---

## Step 12 — Create PostgreSQL Database
In PostgreSQL, create a database named: taskflow_db

You can use pgAdmin, DBeaver, or the terminal.

---

## Step 13 — Configure SQLAlchemy and PostgreSQL Connection
File: `app/db/database.py`

Define the database connection using SQLAlchemy:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost/taskflow_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
