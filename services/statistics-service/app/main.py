from fastapi import FastAPI
from app.api.routes.statistics import router
from app.core.config import settings
from app.core.internal_auth import require_internal_key
app=FastAPI(title=settings.app_name,version="1.0.0")
app.middleware("http")(require_internal_key)
app.include_router(router)
@app.get("/health/live")
def live():return {"status":"ok","service":"statistics-service"}
@app.get("/health/ready")
def ready():return {"status":"ok","mode":"stateless"}
