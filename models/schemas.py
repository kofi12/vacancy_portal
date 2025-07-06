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
    role: str = "scworker"

class UserUpdate(BaseModel):
    name: str | None = None
    organization: str | None = None

class OrganizationBase(BaseModel):
    business_name: str
    address: str
    number_of_beds: int | None = None
    role: str = "owner"

class OrganizationUpdate(BaseModel):
    number_of_beds: int | None = None

class DocumentDown (BaseModel):
    file_name: str
    url: str