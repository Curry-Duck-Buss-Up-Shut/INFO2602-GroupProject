from sqlmodel import SQLModel
from pydantic import EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str
    role: str = "regular_user"

class UserUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
 
class AdminCreate(UserCreate):
    role: str = "admin"

class RegularUserCreate(UserCreate):
    role: str = "regular_user"

class UserResponse(SQLModel):
    id: int
    username:str
    email: EmailStr
    role: str
    created_at: datetime
