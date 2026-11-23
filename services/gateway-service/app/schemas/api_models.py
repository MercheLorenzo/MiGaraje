"""Public API contracts used by the Gateway and its Swagger UI.

These models mirror the public payloads accepted by the business microservices.
They do not introduce cross-service Python imports or database coupling.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VehicleIn(BaseModel):
    brand: str = Field(min_length=1, max_length=100, examples=["Seat"])
    model: str = Field(min_length=1, max_length=100, examples=["Ibiza"])
    year: int = Field(ge=1886, le=2100, examples=[2021])
    license_plate: str | None = Field(default=None, max_length=20, examples=["1234ABC"])
    current_mileage: int = Field(default=0, ge=0, examples=[62000])
    vehicle_type: str = Field(default="car", max_length=32, examples=["car"])
    fuel_type: str | None = Field(default=None, max_length=32, examples=["gasoline"])
    registration_date: date | None = None
    nickname: str | None = Field(default=None, max_length=80)
    notes: str | None = None


class VehicleOut(VehicleIn):
    id: int


class MaintenanceIn(BaseModel):
    vehicle_id: int = Field(gt=0, examples=[1])
    maintenance_type: str = Field(min_length=1, max_length=50, examples=["oil_change"])
    date: date
    mileage: int = Field(ge=0)
    description: str = Field(min_length=1, examples=["Cambio de aceite y filtro"])
    cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2, examples=[89.90])
    products_used: str | None = None
    workshop: str | None = Field(default=None, max_length=120)
    parts_cost: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    labor_cost: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    part_brand: str | None = Field(default=None, max_length=120)
    part_model: str | None = Field(default=None, max_length=120)
    notes: str | None = None


class MaintenanceOut(MaintenanceIn):
    id: int


class RuleIn(BaseModel):
    vehicle_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100, examples=["Cambio de aceite"])
    maintenance_type: str = Field(min_length=1, max_length=50, examples=["oil_change"])
    description: str | None = None
    interval_days: int | None = Field(default=None, gt=0)
    interval_months: int | None = Field(default=None, gt=0, examples=[12])
    interval_kilometers: int | None = Field(default=None, gt=0, examples=[15000])
    last_performed_date: date | None = None
    last_performed_mileage: int | None = Field(default=None, ge=0)
    reminder_days_before: int = Field(default=7, ge=0)
    is_active: bool = True

    @model_validator(mode="after")
    def at_least_one_interval(self):
        if all(v is None for v in (self.interval_days, self.interval_months, self.interval_kilometers)):
            raise ValueError("Debes indicar un intervalo de días, meses o kilómetros")
        return self


class RuleOut(RuleIn):
    id: int


class TaskIn(BaseModel):
    vehicle_id: int = Field(gt=0)
    rule_id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1, max_length=100, examples=["Pasar ITV"])
    description: str | None = None
    due_date: date | None = None
    due_mileage: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def at_least_one_due(self):
        if self.due_date is None and self.due_mileage is None:
            raise ValueError("Debes indicar fecha o kilometraje de vencimiento")
        return self


class TaskOut(TaskIn):
    id: int
    status: Literal["pending", "upcoming", "overdue", "completed"]
    completed_date: date | None = None
    completed_mileage: int | None = None


class CompleteTaskIn(BaseModel):
    completed_date: date
    completed_mileage: int | None = Field(default=None, ge=0)


class PreferencesIn(BaseModel):
    email_enabled: bool = False
    reminder_offsets_days: list[Literal[1, 7, 30, 90]] = Field(
        default_factory=lambda: [90, 30, 7, 1], min_length=1, max_length=4
    )

    @model_validator(mode="after")
    def unique_offsets(self):
        if len(set(self.reminder_offsets_days)) != len(self.reminder_offsets_days):
            raise ValueError("Los plazos de aviso no pueden repetirse")
        return self


class NotificationOut(BaseModel):
    id: int
    task_id: int
    vehicle_id: int
    title: str
    body: str
    level: str
    is_read: bool
    email_status: str
    created_at: datetime


class ScanResult(BaseModel):
    created: int
    scanned: int


class MailTestResult(BaseModel):
    message: str


class SummaryOut(BaseModel):
    year: int | None
    vehicle_count: int
    maintenance_count: int
    total_cost: float
    average_cost: float
    most_expensive: MaintenanceOut | None


class MonthlyOut(BaseModel):
    month: str
    total: float
    count: int


class CategoryOut(BaseModel):
    category: str
    count: int
    total: float


class ComparisonOut(BaseModel):
    vehicle_id: int
    label: str
    total: float
    count: int


class VehicleStatsOut(BaseModel):
    summary: SummaryOut
    monthly: list[MonthlyOut]
    categories: list[CategoryOut]
