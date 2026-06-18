from fastapi import FastAPI, Depends
from app.db.database import engine, Base
from app.models.user import User
from app.routes.auth import router as auth_router
from app.auth.dependencies import get_current_user
from app.models.team import Team
from app.models.task import Task
from app.routes.team import router as team_router
from app.routes.task import router as task_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(team_router)
app.include_router(task_router)

@app.get("/")
def root():
    return {"message": "TaskFlow API running"}

@app.get("/profile")
def profile(current_user: str = Depends(get_current_user)):
    return {
        "user": current_user
    }

