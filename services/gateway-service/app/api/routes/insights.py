from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.account import User
from app.services.auth import current_user
from app.api.routes.resources import owned_ids, assert_owned
from app.clients.services_client import call

router=APIRouter(prefix="/api",tags=["Estadísticas y avisos"])
@router.get("/statistics/{report}")
def statistics(report:str,year:int|None=Query(default=None,ge=1900,le=2100),vehicle_id:int|None=None,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if report not in ("summary","monthly","categories","comparison"):raise HTTPException(404)
    ids=owned_ids(db,user)
    if vehicle_id is not None:assert_owned(db,user,vehicle_id);ids=[vehicle_id]
    return call("statistics","GET",f"/statistics/{report}",params={"vehicle_ids":",".join(map(str,ids)),"year":year})

@router.get("/statistics/vehicles/{vehicle_id}")
def stats_vehicle(vehicle_id:int,year:int|None=None,user:User=Depends(current_user),db:Session=Depends(get_db)):
    assert_owned(db,user,vehicle_id)
    return call("statistics","GET",f"/statistics/vehicles/{vehicle_id}",params={"year":year})

@router.get("/notifications")
def notifications(user:User=Depends(current_user)):
    return call("notifications","GET",f"/notifications/{user.id}")

@router.post("/notifications/scan")
def scan(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return call("notifications","POST",f"/notifications/{user.id}/scan",data={"vehicle_ids":owned_ids(db,user),"email":user.email})

@router.get("/notifications/preferences")
def get_prefs(user:User=Depends(current_user)):
    return call("notifications","GET",f"/notifications/{user.id}/preferences")

@router.put("/notifications/preferences")
def set_prefs(body:dict,user:User=Depends(current_user)):
    return call("notifications","PUT",f"/notifications/{user.id}/preferences",data=body)

@router.patch("/notifications/{notification_id}/read")
def mark_read(notification_id:int,user:User=Depends(current_user)):
    return call("notifications","PATCH",f"/notifications/{user.id}/{notification_id}/read")

@router.post("/notifications/test")
def test_mail(user:User=Depends(current_user)):
    return call("notifications","POST",f"/notifications/{user.id}/test",data={"email":user.email})
