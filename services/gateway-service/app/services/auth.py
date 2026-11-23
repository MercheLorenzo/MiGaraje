"""Hashing scrypt con salt aleatorio; tokens JWT firmados con expiración."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.account import User

ITERATIONS_N=2**14

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode("utf8"), salt=salt, n=ITERATIONS_N, r=8, p=1)
    return f"scrypt${salt.hex()}${derived.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = stored.split("$")
        if algorithm != "scrypt":return False
        derived = hashlib.scrypt(password.encode("utf8"), salt=bytes.fromhex(salt_hex), n=ITERATIONS_N, r=8, p=1)
        return hmac.compare_digest(derived, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False

def create_token(user_id: int, token_version: int=0) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "ver":token_version, "iat": now, "exp":now+timedelta(hours=8), "iss":"migaraje"}, settings.jwt_secret, algorithm="HS256")

bearer_scheme = HTTPBearer(auto_error=False, description="Pega el token devuelto por /api/auth/login o /api/auth/register (sin escribir Bearer).")

def current_user(credentials: HTTPAuthorizationCredentials | None=Depends(bearer_scheme), db:Session=Depends(get_db)) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Inicia sesión para continuar", headers={"WWW-Authenticate":"Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"], issuer="migaraje")
        user = db.get(User, int(payload["sub"]))
        if user and user.token_version != payload.get("ver"):
            user = None
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        user = None
    if not user:
        raise HTTPException(401, "Sesión no válida o caducada")
    return user

def user_view(user:User):
    return {"id":user.id, "email":user.email, "full_name":user.full_name, "created_at":user.created_at}
