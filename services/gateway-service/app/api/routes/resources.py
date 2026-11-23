from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.account import User, VehicleOwner
from app.services.auth import current_user
from app.clients.services_client import call

router=APIRouter(prefix="/api",tags=["Garaje y mantenimiento"])

def owned_ids(db:Session,user:User)->list[int]:
    return list(db.scalars(select(VehicleOwner.vehicle_id).where(VehicleOwner.user_id==user.id)).all())

def assert_owned(db:Session,user:User, vehicle_id:int):
    if vehicle_id not in owned_ids(db,user): raise HTTPException(404,"Vehículo no encontrado en tu garaje")

def get_owned_resource(db,user,kind,id):
    entity=call(kind,"GET",f"/{'maintenances' if kind=='maintenance' else 'maintenance-rules' if kind=='planning_rules' else 'maintenance-tasks'}/{id}")
    assert_owned(db,user,entity["vehicle_id"])
    return entity

def route(kind:str): return {"maintenance":"maintenances","rules":"maintenance-rules","tasks":"maintenance-tasks"}[kind]
def svc(kind:str):return "maintenance" if kind=="maintenance" else "planning"

def existing(kind:str,id:int,db,user):
    result=call(svc(kind),"GET",f"/{route(kind)}/{id}")
    assert_owned(db,user,result["vehicle_id"])
    return result

@router.get("/vehicles")
def vehicles(user:User=Depends(current_user),db:Session=Depends(get_db)):
    ids=set(owned_ids(db,user))
    return [v for v in call("vehicles","GET","/vehicles") if v["id"] in ids]

@router.post("/vehicles", status_code=201)
def create_vehicle(body:dict,user:User=Depends(current_user),db:Session=Depends(get_db)):
    result=call("vehicles","POST","/vehicles",data=body)
    db.add(VehicleOwner(vehicle_id=result["id"],user_id=user.id))
    try: db.commit()
    except Exception:
        db.rollback()
        call("vehicles","DELETE",f"/vehicles/{result['id']}")
        raise
    return result

@router.get("/vehicles/{vehicle_id}")
def vehicle(vehicle_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    assert_owned(db,user,vehicle_id)
    return call("vehicles","GET",f"/vehicles/{vehicle_id}")

@router.put("/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id:int,body:dict,user:User=Depends(current_user),db:Session=Depends(get_db)):
    assert_owned(db,user,vehicle_id)
    return call("vehicles","PUT",f"/vehicles/{vehicle_id}",data=body)

@router.delete("/vehicles/{vehicle_id}",status_code=204)
def remove_vehicle(vehicle_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    assert_owned(db,user,vehicle_id)
    # Mantener la integridad lógica sin claves foráneas entre bases de datos.
    for t in call("planning","GET","/maintenance-tasks",params={"vehicle_id":vehicle_id}):
        call("planning","DELETE",f"/maintenance-tasks/{t['id']}")
    for r in call("planning","GET","/maintenance-rules",params={"vehicle_id":vehicle_id}):
        call("planning","DELETE",f"/maintenance-rules/{r['id']}")
    for m in call("maintenance","GET",f"/maintenances/vehicle/{vehicle_id}"):
        call("maintenance","DELETE",f"/maintenances/{m['id']}")
    call("vehicles","DELETE",f"/vehicles/{vehicle_id}")
    db.delete(db.get(VehicleOwner,vehicle_id));db.commit()

@router.get("/{kind}")
def list_records(kind:str,vehicle_id:int|None=Query(default=None),user:User=Depends(current_user),db:Session=Depends(get_db)):
    if kind not in ("maintenances","rules","tasks"):raise HTTPException(404)
    ids=owned_ids(db,user)
    if vehicle_id is not None: assert_owned(db,user,vehicle_id);ids=[vehicle_id]
    kind_key={"maintenances":"maintenance","rules":"rules","tasks":"tasks"}[kind]
    if kind_key=="maintenance":records=call("maintenance","GET","/maintenances")
    else:records=call("planning","GET",f"/{route(kind_key)}")
    return [record for record in records if record["vehicle_id"] in ids]

@router.post("/{kind}",status_code=201)
def create_record(kind:str,body:dict,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if kind not in ("maintenances","rules","tasks"):raise HTTPException(404)
    vid=body.get("vehicle_id")
    if not isinstance(vid,int):raise HTTPException(422,"Selecciona un vehículo")
    assert_owned(db,user,vid)
    key={"maintenances":"maintenance","rules":"rules","tasks":"tasks"}[kind]
    if key=="tasks" and body.get("rule_id"):
        rule=existing("rules",body["rule_id"],db,user)
        if rule["vehicle_id"]!=vid:raise HTTPException(422,"La regla no pertenece a ese vehículo")
    return call(svc(key),"POST",f"/{route(key)}",data=body)

@router.get("/{kind}/{record_id}")
def get_record(kind:str,record_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if kind not in ("maintenances","rules","tasks"):raise HTTPException(404)
    key={"maintenances":"maintenance","rules":"rules","tasks":"tasks"}[kind]
    return existing(key,record_id,db,user)

@router.put("/{kind}/{record_id}")
def update_record(kind:str,record_id:int,body:dict,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if kind not in ("maintenances","rules","tasks"):raise HTTPException(404)
    key={"maintenances":"maintenance","rules":"rules","tasks":"tasks"}[kind]
    old=existing(key,record_id,db,user)
    if body.get("vehicle_id")!=old["vehicle_id"]:raise HTTPException(422,"No puedes cambiar el vehículo del registro")
    if key=="tasks" and body.get("rule_id"):
        rule=existing("rules",body["rule_id"],db,user)
        if rule["vehicle_id"]!=old["vehicle_id"]:raise HTTPException(422,"La regla no pertenece al vehículo")
    return call(svc(key),"PUT",f"/{route(key)}/{record_id}",data=body)

@router.delete("/{kind}/{record_id}",status_code=204)
def delete_record(kind:str,record_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if kind not in ("maintenances","rules","tasks"):raise HTTPException(404)
    key={"maintenances":"maintenance","rules":"rules","tasks":"tasks"}[kind]
    existing(key,record_id,db,user)
    if key=="rules":
        tasks=call("planning","GET","/maintenance-tasks",params={"vehicle_id":existing(key,record_id,db,user)["vehicle_id"]})
        for t in tasks:
            if t["rule_id"]==record_id:call("planning","DELETE",f"/maintenance-tasks/{t['id']}")
    return call(svc(key),"DELETE",f"/{route(key)}/{record_id}")

@router.patch("/tasks/{task_id}/complete")
def complete(task_id:int,body:dict,user:User=Depends(current_user),db:Session=Depends(get_db)):
    existing("tasks",task_id,db,user)
    return call("planning","PATCH",f"/maintenance-tasks/{task_id}/complete",data=body)


@router.post("/rules/{rule_id}/generate",status_code=201)
def generate_rule_task(rule_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    existing("rules",rule_id,db,user)
    return call("planning","POST",f"/maintenance-rules/{rule_id}/generate")
