from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True
    role: str = "student" # student, teacher, admin

class UserResponse(UserBase):
    id: str
    username: str
    email: str
    role: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str
