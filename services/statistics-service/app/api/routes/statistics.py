from fastapi import APIRouter,HTTPException,Query
from app.services import statistics_service as service
router=APIRouter(prefix="/statistics",tags=["Estadísticas"])

def ids(value:str)->list[int]:
    if not value:return []
    try:
        result=[int(i) for i in value.split(",") if i]
        if any(i<=0 for i in result) or len(result)>1000:raise ValueError
        return result
    except ValueError:
        raise HTTPException(422,"Lista de vehículos incorrecta") from None

@router.get("/summary")
def summary(vehicle_ids:str="",year:int|None=Query(None,ge=1900,le=2100)):
    return service.summary(ids(vehicle_ids),year)
@router.get("/monthly")
def monthly(vehicle_ids:str="",year:int|None=Query(None,ge=1900,le=2100)):
    return service.monthly(ids(vehicle_ids),year)
@router.get("/categories")
def categories(vehicle_ids:str="",year:int|None=Query(None,ge=1900,le=2100)):
    return service.categories(ids(vehicle_ids),year)
@router.get("/comparison")
def comparison(vehicle_ids:str="",year:int|None=Query(None,ge=1900,le=2100)):
    return service.comparison(ids(vehicle_ids),year)
@router.get("/vehicles/{vehicle_id}")
def vehicle(vehicle_id:int,year:int|None=None):
    return service.vehicle(vehicle_id,year)
