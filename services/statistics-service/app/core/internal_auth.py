"""Clave compartida exclusivamente entre servicios dentro de la red de Docker."""
import hmac
import os
from fastapi import Request
from fastapi.responses import JSONResponse

async def require_internal_key(request: Request, call_next):
    secret = os.getenv("INTERNAL_API_KEY", "")
    if secret and not request.url.path.startswith("/health"):
        supplied = request.headers.get("X-Internal-Key", "")
        if not hmac.compare_digest(supplied, secret):
            return JSONResponse({"detail": "Acceso interno no autorizado"}, status_code=401)
    return await call_next(request)
