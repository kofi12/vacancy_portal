from pydantic import BaseModel
from datetime import datetime

class TenantBase(BaseModel):
    name: str

class TenantUpdate(BaseModel):
    name: str | None = None
    admission_date: datetime | None = None
    discharge_date: datetime | None = None

class UserBase(BaseModel):
    name: str
    organization: str
    role: str
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    admission_date: datetime | None = None
    discharge_date: datetime | None = None