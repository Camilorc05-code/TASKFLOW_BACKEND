from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, Base
from app.models.user import User
from app.models.team_member import Team
from app.models.task import Task

from app.routes.auth import router as auth_router
from app.routes.team import router as team_router
from app.routes.task import router as task_router
from app.auth.dependencies import get_current_user

app = FastAPI()

# ⚡ Configuración de CORS (modo desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # permite cualquier origen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(team_router)
app.include_router(task_router)

@app.get("/")
def root():
    return {"message": "TaskFlow API running"}

@app.get("/profile")
def profile(current_user: str = Depends(get_current_user)):
    return {"user": current_user}

