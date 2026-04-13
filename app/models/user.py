from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import EmailStr
from datetime import datetime, timezone

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password_hash: str
    role:str = Field(default="regular_user", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
