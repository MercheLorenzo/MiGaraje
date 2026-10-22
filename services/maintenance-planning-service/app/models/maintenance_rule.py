from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MaintenanceRule(Base):
    __tablename__ = "maintenance_rules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Referencia lógica al vehículo de vehicles-service.
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    maintenance_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Intervalos opcionales: la regla debe definir al menos uno.
    interval_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    interval_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    interval_kilometers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    last_performed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    last_performed_mileage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    reminder_days_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
