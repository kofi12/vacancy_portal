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
    first_name: str
    last_name: str
    email: str
    organization: str | None = None
    role: str = 'member'

class UserUpdate(BaseModel):
    name: str | None = None
    organization: str | None = None
    role: str | None = 'member'

class DocumentDown (BaseModel):
    file_name: str
    url: str