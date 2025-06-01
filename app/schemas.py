# schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class LocationBase(BaseModel):
    name: str

class LocationResponse(LocationBase):
    id: int
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    location_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    location_id: Optional[int]
    location: Optional[LocationResponse]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str