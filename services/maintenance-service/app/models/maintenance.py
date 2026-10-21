from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Maintenance(Base):
    __tablename__ = "maintenances"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Identificador del vehículo en vehicles-service.
    # Es una referencia lógica, no una clave foránea entre servicios.
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    maintenance_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    mileage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    products_used: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
