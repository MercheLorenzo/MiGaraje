from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    brand: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    license_plate: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
    )

    current_mileage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )