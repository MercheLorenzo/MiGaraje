from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MaintenanceRuleCreate(BaseModel):
    vehicle_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    maintenance_type: str = Field(min_length=1, max_length=50)
    description: str | None = None

    interval_days: int | None = Field(default=None, gt=0)
    interval_months: int | None = Field(default=None, gt=0)
    interval_kilometers: int | None = Field(default=None, gt=0)

    last_performed_date: date | None = None
    last_performed_mileage: int | None = Field(default=None, ge=0)

    reminder_days_before: int = Field(default=7, ge=0)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_intervals(self):
        if (
            self.interval_days is None
            and self.interval_months is None
            and self.interval_kilometers is None
        ):
            raise ValueError(
                "Debe especificarse al menos un intervalo temporal "
                "o de kilometraje."
            )
        return self


class MaintenanceRuleUpdate(MaintenanceRuleCreate):
    pass


class MaintenanceRuleResponse(MaintenanceRuleCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
