from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.maintenance import router as maintenance_router
from app.core.config import settings
from app.db.session import Base, engine
from app.models.maintenance import Maintenance


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(maintenance_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/health/live")
def health_live():
    return {"status": "ok", "service": "maintenance-service"}


@app.get("/health/ready")
def health_ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "service": "maintenance-service",
            "database": "ok",
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "service": "maintenance-service",
                "database": "unavailable",
            },
        ) from None
