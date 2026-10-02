from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from ..models import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.INVESTIGATOR


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[UserRole] = None
