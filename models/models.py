from sqlmodel import SQLModel, Field
from datetime import datetime

class Tenant (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    admission_date: datetime = Field()
    discharge_date: datetime | None

class User (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    organization: str
    role: str