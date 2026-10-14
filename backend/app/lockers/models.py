
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class LockerStatus(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    UNKNOWN = "UNKNOWN"


class ActivityEventType(str, Enum):
    ALLOCATION_CREATED = "ALLOCATION_CREATED"
    ALLOCATION_RELEASED = "ALLOCATION_RELEASED"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"


class AllocationCreateRequest(BaseModel):
    user_id: str
    locker_id: str | None = None


class AllocationReleaseRequest(BaseModel):
    user_id: str


# Lockers

class LockerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    locker_code: str
    rack_id: str
    status: LockerStatus
    updated_at: datetime


# Allocations

class AllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    locker: LockerResponse
    allocated_at: datetime
    released_at: datetime | None


# Activity history

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    locker_id: int | None
    event_type: ActivityEventType
    timestamp: datetime
    details: dict[str, Any] | None


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
