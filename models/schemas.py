from pydantic import BaseModel
from datetime import datetime

class TenantBase(BaseModel):
    name: str
    admission_date: datetime | None = None
    waitlist: bool = False

class TenantUpdate(BaseModel):
    name: str | None = None
    admission_date: datetime | None = None
    discharge_date: datetime | None = None
    waitlist: bool = False

class UserBase(BaseModel):
    name: str
    organization: str
    role: str
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    admission_date: datetime | None = None
    discharge_date: datetime | None = None