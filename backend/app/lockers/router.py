
from datetime import UTC, datetime, timezone
from typing import Any

from app.db import get_db
from app.lockers.db import (
    Activity,
    Locker,
)
from app.lockers.models import (
    ActivityEventType,
    ActivityListResponse,
    ActivityResponse,
    AllocationCreateRequest,
    AllocationReleaseRequest,
    AllocationResponse,
    LockerResponse,
    LockerStatus,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

router = APIRouter(prefix="/api", tags=["Lockers"])


# ---------- Helpers ----------

def now_utc() -> datetime:
    return datetime.now(UTC)


def log_activity(
    db: Session,
    event_type: ActivityEventType,
    user_id: str | None = None,
    locker_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        Activity(
            user_id=user_id,
            locker_id=locker_id,
            event_type=event_type,
            timestamp=now_utc(),
            details=details,
        )
    )


def get_locker_or_404(db: Session, locker_id: str) -> Locker:
    locker = db.get(Locker, locker_id)
    if locker is None:
        raise HTTPException(404, "Locker not found")
    return locker


def get_active_allocation(db: Session, locker_id: str, user_id: str):
    return db.scalar(
        select(Locker).where(
            Locker.locker_id == locker_id,
            Locker.allocated_user_id == user_id,
        )
    )


# ---------- Locker endpoints ----------

@router.get("/lockers", response_model=list[LockerResponse])
def list_lockers(db: Session = Depends(get_db)):
    """Return the current state of every locker."""
    return db.scalars(
        select(Locker).order_by(Locker.locker_id)
    ).all()


@router.get("/lockers/{locker_id}", response_model=LockerResponse)
def get_locker(
    locker_id: str,
    db: Session = Depends(get_db),
):
    """Return the current state of one locker."""
    return get_locker_or_404(db, locker_id)


# ---------- Allocation endpoints ----------

@router.post(
    "/allocations",
    response_model=AllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_allocation(
    request: AllocationCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Allocate the requested locker, or the first free locker
    when locker_id is omitted.
    """
    try:
        if request.locker_id is not None:
            locker = get_locker_or_404(db, request.locker_id)

            if locker.state != "unalloted":
                raise HTTPException(409, "Locker is already allocated")
        else:
            locker = db.scalar(
                select(Locker)
                .where(
                    Locker.state == "unalloted"
                )
                .order_by(Locker.locker_id)
                .limit(1)
            )

            if locker is None:
                raise HTTPException(409, "No free lockers available")

        # Do not allow the same user to have multiple active allocations.
        existing = db.scalar(
            select(Locker).where(
                Locker.allocated_user_id == request.user_id,
            )
        )
        if existing is not None:
            raise HTTPException(
                409, "User already has an active allocation"
            )

        timestamp = now_utc()

        allocation = Locker(
            user_id=request.user_id,
            locker_id=locker.locker_id,
            allocated_at=timestamp,
            released_at=None,
        )

        locker.state = "alloted_open"
        locker.updated_at = timestamp

        db.add(allocation)
        db.flush()

        log_activity(
            db,
            ActivityEventType.ALLOCATION_CREATED,
            user_id=request.user_id,
            locker_id=locker.locker_id,
            details={"locker_code": locker.locker_id},
        )

        db.commit()

        # Reload relationship for AllocationResponse.locker.
        return db.scalar(
            select(Locker)
            .options(joinedload(Locker.locker_id))
            .where(Locker.locker_id == allocation.locker_id)
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.post(
    "/allocations/{allocation_id}/release",
    response_model=AllocationResponse,
)
def release_allocation(
    allocation_id: int,
    request: AllocationReleaseRequest,
    db: Session = Depends(get_db),
):
    """Release an active allocation belonging to the requesting user."""
    locker = db.scalar(
        select(Locker)
        .where(Locker.locker_id == allocation_id)
    )

    if locker is None:
        raise HTTPException(404, "Allocation not found")

    if locker.allocated_user_id != request.user_id:
        raise HTTPException(403, "Allocation belongs to another user")

    timestamp = now_utc()

    locker.updated_at = timestamp
    locker.state = "unalloted"
    locker.updated_at = timestamp

    log_activity(
        db,
        ActivityEventType.ALLOCATION_RELEASED,
        user_id=request.user_id,
        locker_id=locker.locker_id,
        details={"locker_code": locker.locker_id},
    )

    db.commit()
    db.refresh(locker)

    return db.scalar(
        select(Locker.locker_id)
        .where(Locker.locker_id == allocation_id)
    )


# ---------- Activity history ----------

@router.get("/activity", response_model=ActivityListResponse)
def list_activity(
    user_id: int | None = None,
    locker_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return paginated activity history, newest first."""
    query = select(Activity)

    if user_id is not None:
        query = query.where(Activity.user_id == user_id)

    if locker_id is not None:
        query = query.where(Activity.locker_id == locker_id)

    total_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(total_query) or 0

    items = db.scalars(
        query.order_by(Activity.timestamp.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return {"items": items, "total": total}


@router.get("/activity", response_model=ActivityListResponse)
def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(Activity)

    total = db.scalar(
        select(func.count()).select_from(Activity)
    ) or 0

    items = db.scalars(
        query.order_by(
            Activity.timestamp.desc(),
            Activity.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()

    return {"items": items, "total": total}
