from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceCreate(BaseModel):
    vehicle_id: int = Field(gt=0)
    maintenance_type: str = Field(min_length=1, max_length=50)
    date: date
    mileage: int = Field(ge=0)
    description: str = Field(min_length=1)
    cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    products_used: str | None = None
    workshop: str | None = Field(default=None,max_length=120)
    parts_cost: Decimal | None = Field(default=None,ge=0,max_digits=10,decimal_places=2)
    labor_cost: Decimal | None = Field(default=None,ge=0,max_digits=10,decimal_places=2)
    part_brand: str | None = Field(default=None,max_length=120)
    part_model: str | None = Field(default=None,max_length=120)
    notes: str | None = None


class MaintenanceUpdate(MaintenanceCreate):
    pass


class MaintenanceResponse(MaintenanceCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
