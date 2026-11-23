from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_db
from app.models.account import User, VehicleOwner
from app.services.auth import hash_password, verify_password, create_token, current_user, user_view

router=APIRouter(prefix="/api/auth",tags=["Auth y perfil"])
class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
class Register(Credentials):
    full_name: str=Field(min_length=2,max_length=120)
class Profile(BaseModel):
    full_name: str=Field(min_length=2,max_length=120)
class ChangePassword(BaseModel):
    current_password: str
    new_password: str=Field(min_length=10,max_length=128)

class PublicUser(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

class AuthSession(BaseModel):
    token: str
    user: PublicUser

class Message(BaseModel):
    message: str

@router.post("/register",status_code=201,response_model=AuthSession,summary="Crear cuenta")
def register(body:Register, db:Session=Depends(get_db)):
    user=User(email=str(body.email).lower(),full_name=body.full_name.strip(),password_hash=hash_password(body.password))
    db.add(user)
    try:db.commit();db.refresh(user)
    except IntegrityError:
        db.rollback();raise HTTPException(409,"Ya existe una cuenta con ese correo") from None
    return {"token":create_token(user.id,user.token_version),"user":user_view(user)}

@router.post("/login",response_model=AuthSession,summary="Iniciar sesión y obtener token JWT")
def login(body:Credentials, db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==str(body.email).lower()))
    if not user or not verify_password(body.password,user.password_hash):
        raise HTTPException(401,"Correo o contraseña incorrectos")
    return {"token":create_token(user.id,user.token_version),"user":user_view(user)}

@router.get("/me",response_model=PublicUser,summary="Consultar mi perfil")
def me(user:User=Depends(current_user)):
    return user_view(user)

@router.put("/me",response_model=PublicUser,summary="Editar mi perfil")
def edit_profile(body:Profile,user:User=Depends(current_user),db:Session=Depends(get_db)):
    user.full_name=body.full_name.strip(); db.commit();db.refresh(user)
    return user_view(user)

@router.post("/change-password",response_model=Message,summary="Cambiar contraseña")
def change_password(body:ChangePassword,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not verify_password(body.current_password,user.password_hash):
        raise HTTPException(400,"La contraseña actual no coincide")
    user.password_hash=hash_password(body.new_password);user.token_version+=1;db.commit()
    return {"message":"Contraseña cambiada. Las sesiones anteriores quedan invalidadas."}
