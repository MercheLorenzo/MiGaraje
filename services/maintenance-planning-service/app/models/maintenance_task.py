from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Referencias lógicas: no se crean claves foráneas entre microservicios.
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    # Referencia a una regla local, opcional para tareas manuales.
    rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("maintenance_rules.id"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    due_mileage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    completed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    completed_mileage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
