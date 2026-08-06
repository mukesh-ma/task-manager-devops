import logging
from datetime import timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models, schemas, crud, auth
from app.config import get_settings
from app.database import engine, get_db, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("task-manager")
settings = get_settings()

# Create tables on startup (a real prod system would use Alembic migrations instead;
# see /alembic for the migration-ready structure this leaves room for).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="A production-style Task Management REST API used as a DevOps reference project.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.enable_metrics:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health", tags=["ops"])
def health_check(db: Session = Depends(get_db)):
    """Liveness/readiness probe target for Kubernetes and load balancers."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception as exc:  # pragma: no cover
        logger.error("DB health check failed: %s", exc)
        db_status = "down"
    return {"status": "ok", "database": db_status, "environment": settings.environment}


@app.post("/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)


@app.post("/auth/login", response_model=schemas.Token, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = auth.create_access_token(
        {"sub": user.email}, expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    return schemas.Token(access_token=token)


@app.post("/tasks", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.create_task(db, task, owner_id=current_user.id)


@app.get("/tasks", response_model=list[schemas.TaskOut], tags=["tasks"])
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.get_tasks(db, owner_id=current_user.id, skip=skip, limit=limit)


@app.get("/tasks/{task_id}", response_model=schemas.TaskOut, tags=["tasks"])
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = crud.get_task(db, task_id, owner_id=current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=schemas.TaskOut, tags=["tasks"])
def update_task(
    task_id: int,
    updates: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = crud.get_task(db, task_id, owner_id=current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return crud.update_task(db, task, updates)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = crud.get_task(db, task_id, owner_id=current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    crud.delete_task(db, task)
