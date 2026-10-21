from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import HTTPException
from sqlalchemy import text

from app.api.routes.vehicles import router as vehicles_router
from app.core.config import settings
from app.db.session import Base, engine
from app.models.vehicle import Vehicle  # Registra el modelo


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(vehicles_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

@app.get("/health/live")
def health_live():
    return {"status": "ok", "service": "vehicles-service"}

@app.get("/health/ready")
def health_ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "service": "vehicles-service",
            "database": "ok",
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "service": "vehicles-service",
                "database": "unavailable",
            },
        )