"""Cálculo agregado sin acceso directo a la BD de otros microservicios."""
from collections import defaultdict
from decimal import Decimal
from app.clients.data_client import get_data

def rows(ids:list[int],year:int|None=None):
    all_vehicles,all_maintenance=get_data()
    ids=set(ids)
    vehicles=[v for v in all_vehicles if v["id"] in ids]
    actual_ids={v["id"] for v in vehicles}
    records=[r for r in all_maintenance if r["vehicle_id"] in actual_ids and (year is None or int(r["date"][:4])==year)]
    return vehicles,records

def amount(value):return Decimal(str(value))
def money(value):return float(round(value,2))

def summary(ids:list[int],year:int|None=None):
    vehicles,records=rows(ids,year)
    total=sum((amount(r["cost"]) for r in records),Decimal("0"))
    return {"year":year,"vehicle_count":len(vehicles),"maintenance_count":len(records),"total_cost":money(total),"average_cost":money(total/len(records)) if records else 0,"most_expensive":max(records,key=lambda x:amount(x["cost"])) if records else None}

def categories(ids:list[int],year:int|None=None):
    _,records=rows(ids,year)
    result=defaultdict(lambda:{"count":0,"total":Decimal("0")})
    for r in records:
        cat=r["maintenance_type"];result[cat]["count"]+=1;result[cat]["total"]+=amount(r["cost"])
    return [{"category":c,"count":v["count"],"total":money(v["total"])} for c,v in sorted(result.items(),key=lambda item:item[1]["total"],reverse=True)]

def monthly(ids:list[int],year:int|None=None):
    _,records=rows(ids,year)
    counts=defaultdict(int);totals=defaultdict(lambda:Decimal("0"))
    for r in records:
        key=r["date"][:7];counts[key]+=1;totals[key]+=amount(r["cost"])
    months=(sorted(totals) if year is None else [f"{year}-{n:02d}" for n in range(1,13)])
    return [{"month":m,"total":money(totals[m]),"count":counts[m]} for m in months]

def comparison(ids:list[int],year:int|None=None):
    vehicles,records=rows(ids,year)
    totals=defaultdict(lambda:Decimal("0"));counts=defaultdict(int)
    for r in records:totals[r["vehicle_id"]]+=amount(r["cost"]);counts[r["vehicle_id"]]+=1
    return [{"vehicle_id":v["id"],"label":f"{v['brand']} {v['model']}","total":money(totals[v["id"]]),"count":counts[v["id"]]} for v in sorted(vehicles,key=lambda v:totals[v["id"]],reverse=True)]

def vehicle(id:int,year:int|None=None):
    return {"summary":summary([id],year),"monthly":monthly([id],year),"categories":categories([id],year)}
