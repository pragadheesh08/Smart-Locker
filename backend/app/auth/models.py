
# Authentication

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Pydantic API models ----------

class UserCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=50)
    display_name: str = Field(min_length=1, max_length=100)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    display_name: str
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
