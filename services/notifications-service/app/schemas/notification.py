from pydantic import BaseModel,Field
class ScanBody(BaseModel):
    vehicle_ids:list[int]=Field(default_factory=list,max_length=1000)
    email:str=Field(max_length=254)
class PreferencesBody(BaseModel):
    email_enabled:bool=False
    reminder_offsets_days:list[int]=Field(default_factory=lambda:[90,30,7,1],min_length=1,max_length=8)
