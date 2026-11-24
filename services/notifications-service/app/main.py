import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import engine,SessionLocal
from app.api.routes.notifications import router
from app.clients.planning_client import users, tasks, vehicles
from app.services.notification_service import scan
from app.core.config import settings
from app.core.internal_auth import require_internal_key

async def periodic_scan():
    while True:
        await asyncio.sleep(max(60,settings.notification_interval_seconds))
        try:
            accounts=await asyncio.to_thread(users)
            all_tasks=await asyncio.to_thread(tasks)
            all_vehicles=await asyncio.to_thread(vehicles)
            for account in accounts:
                with SessionLocal() as db:
                    await asyncio.to_thread(scan,db,account["user_id"],account["vehicle_ids"],account["email"],all_tasks=all_tasks,all_vehicles=all_vehicles)
        except Exception:
            # Errores temporales en servicios externos no deben tumbar el proceso.
            import logging
            logging.getLogger(__name__).exception("Fallo en el escaneo periódico")

@asynccontextmanager
async def lifespan(app):
    worker=asyncio.create_task(periodic_scan())
    yield
    worker.cancel()
    try:await worker
    except asyncio.CancelledError:pass

app=FastAPI(title=settings.app_name,version="1.0.0",lifespan=lifespan)
app.middleware("http")(require_internal_key)
app.include_router(router)
@app.get("/health/live")
def live():return {"status":"ok","service":"notifications-service"}
@app.get("/health/ready")
def ready():
    with engine.connect() as c:c.execute(text("SELECT 1"))
    return {"status":"ok","database":"ok"}
