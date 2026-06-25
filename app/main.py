from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, Base
from app.models.user import User
from app.models.team_member import Team
from app.models.task import Task

from app.routes.auth import router as auth_router
from app.routes.team import router as team_router
from app.routes.task import router as task_router
from app.routes.backlog import router as backlog_router

from app.auth.dependencies import get_current_user


app = FastAPI()


# ==========================
# CORS
# ==========================
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://taskflow-frontend-taupe.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================
# Routers
# ==========================
app.include_router(auth_router)
app.include_router(team_router)
app.include_router(task_router)
app.include_router(backlog_router)


# ==========================
# Endpoints básicos
# ==========================
@app.get("/")
def root():
    return {"message": "TaskFlow API running"}


@app.get("/profile")
def profile(current_user: str = Depends(get_current_user)):
    return {"user": current_user}

import os

@app.get("/debug-env")
def debug_env():
    key = os.getenv("RESEND_API_KEY", "")
    return {
        "resend_key_set":    bool(key),
        "resend_key_prefix": key[:8] if key else "VACÍA",
        "from_email":        os.getenv("FROM_EMAIL", "NO CONFIGURADO"),
        "app_url":           os.getenv("APP_URL",    "NO CONFIGURADO"),
    }