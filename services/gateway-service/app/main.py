import hmac
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select,text
from app.core.config import settings
from app.db.session import engine,SessionLocal
from app.models.account import User,VehicleOwner
from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.insights import router as insights_router
from app.api.routes.resources import router as resources_router

app=FastAPI(
    title=settings.app_name,
    version="1.1.0",
    description=("API REST pública de MiGaraje. Regístrate o inicia sesión en **Auth y perfil**, "
                 "copia el campo `token` y pulsa **Authorize** (HTTP Bearer) para probar "
                 "vehículos, mantenimientos, reglas, tareas, estadísticas y notificaciones. "
                 "Los recursos normales están aislados por usuario; los reportes globales requieren rol admin. No pegues claves internas en Swagger."),
    openapi_tags=[
        {"name": "Administración", "description": "Consultas globales de solo lectura, exclusivas del administrador"},
        {"name": "Auth y perfil", "description": "Cuenta, inicio de sesión y datos personales"},
        {"name": "Vehículos", "description": "Crear, listar, actualizar y eliminar vehículos propios"},
        {"name": "Mantenimientos", "description": "Historial de intervenciones y sus costes"},
        {"name": "Reglas periódicas", "description": "Periodicidad y generación automática de tareas"},
        {"name": "Tareas", "description": "Vencimientos y ejecución de tareas"},
        {"name": "Estadísticas", "description": "Resumen y análisis de gastos"},
        {"name": "Notificaciones", "description": "Avisos y configuración de recordatorios"},
        {"name": "Estado del sistema", "description": "Comprobaciones de salud"},
    ],
)
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:8080","http://localhost:8081"],allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type"],allow_credentials=False)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(insights_router)
app.include_router(resources_router)

@app.get("/health/live", tags=["Estado del sistema"], summary="Comprobar que la API responde")
def live():return {"status":"ok","service":"gateway-service"}
@app.get("/health/ready", tags=["Estado del sistema"], summary="Comprobar conexión a base de datos")
def ready():
    with engine.connect() as conn:conn.execute(text("SELECT 1"))
    return {"status":"ok","database":"ok"}

def check_internal(key:str|None):
    if not settings.internal_api_key or not hmac.compare_digest(key or "",settings.internal_api_key):
        raise HTTPException(401,"No autorizado")

@app.get("/internal/users", include_in_schema=False)
def internal_users(x_internal_key:str|None=Header(default=None)):
    check_internal(x_internal_key)
    with SessionLocal() as db:
        return [{"user_id":u.id,"email":u.email,"vehicle_ids":list(db.scalars(select(VehicleOwner.vehicle_id).where(VehicleOwner.user_id==u.id)).all())} for u in db.scalars(select(User)).all()]
