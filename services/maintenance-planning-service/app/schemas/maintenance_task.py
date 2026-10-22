from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


TASK_STATUSES = {"pending", "upcoming", "overdue", "completed"}


class MaintenanceTaskCreate(BaseModel):
    vehicle_id: int = Field(gt=0)
    rule_id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None

    due_date: date | None = None
    due_mileage: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_due_limits(self):
        if self.due_date is None and self.due_mileage is None:
            raise ValueError(
                "Debe especificarse una fecha prevista "
                "o un kilometraje previsto."
            )
        return self


class MaintenanceTaskResponse(BaseModel):
    id: int
    vehicle_id: int
    rule_id: int | None
    name: str
    description: str | None
    due_date: date | None
    due_mileage: int | None
    status: str
    completed_date: date | None
    completed_mileage: int | None

    model_config = ConfigDict(from_attributes=True)


class MaintenanceTaskComplete(BaseModel):
    completed_date: date
    completed_mileage: int | None = Field(default=None, ge=0)
