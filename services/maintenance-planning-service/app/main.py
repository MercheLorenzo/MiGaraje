from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.api.routes.maintenance_rules import router as rules_router
from app.api.routes.maintenance_tasks import router as tasks_router
from app.core.config import settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(rules_router)
app.include_router(tasks_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/health/live", tags=["Health"])
def health_live():
    return {
        "status": "ok",
        "service": "maintenance-planning-service",
    }


@app.get("/health/ready", tags=["Health"])
def health_ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "service": "maintenance-planning-service",
            "database": "ok",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "service": "maintenance-planning-service",
                "database": "unavailable",
            },
        ) from exc
