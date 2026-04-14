from sqlmodel import SQLModel
from pydantic import EmailStr, Field
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

class UserSelfUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(default=None, min_length=8)

class UserAdminUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

class UserDeleteRequest(SQLModel):
    confirm_username: str
    current_password: str
 
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
