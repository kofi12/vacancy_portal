from datetime import date
from pydantic import BaseModel


class Tenant (BaseModel):
    id: int
    name: str
    admissionDate: date
    
class User (BaseModel):
    id: int
    name: str
    organization: str
    
