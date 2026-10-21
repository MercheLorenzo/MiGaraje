from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1886, le=2100)
    license_plate: str | None = Field(
        default=None,
        max_length=20,
    )
    current_mileage: int = Field(default=0, ge=0)


class VehicleUpdate(VehicleCreate):
    pass


class VehicleResponse(VehicleCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)