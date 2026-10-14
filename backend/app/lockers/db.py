from datetime import UTC, datetime
from typing import Any, Literal

from app.db import Base
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.lockers.models import ActivityEventType

LockerState = Literal[
    "unallotted",
    "allotted_open",
    "allotted_locked",
]


# ---------- SQLite / SQLAlchemy table ----------

class Locker(Base):
    __tablename__ = "lockers"

    __table_args__ = (
        CheckConstraint(
            "state IN "
            "('unallotted', 'allotted_open', 'allotted_locked')",
            name="ck_locker_state",
        ),
        CheckConstraint(
            "(state = 'unallotted' AND allocated_user_id IS NULL) "
            "OR "
            "(state != 'unallotted' AND allocated_user_id IS NOT NULL)",
            name="ck_locker_allocation",
        ),
    )

    locker_id: Mapped[str] = mapped_column(
        String(10), primary_key=True
    )
    state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unallotted"
    )
    allocated_user_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("users.user_id"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class Activity(Base):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    locker_id: Mapped[int | None] = mapped_column(
        ForeignKey("lockers.id"), nullable=True
    )
    event_type: Mapped[ActivityEventType] = mapped_column(
        SAEnum(
            ActivityEventType,
            native_enum=False,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
