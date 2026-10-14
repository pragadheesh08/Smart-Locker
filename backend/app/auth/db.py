
# app/models/auth.py

from datetime import UTC, datetime

from app.db import Base
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

# ---------- SQLite / SQLAlchemy table ----------

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        String(50), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
