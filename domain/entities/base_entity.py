from abc import ABC, abstractmethod
from datetime import datetime

class BaseEntity(ABC):
    """Base class for all entities"""
    _id: int | None
    _created_at: datetime

    def __init__(self, id: int | None, created_at: datetime):
        self._id = id
        self._created_at = datetime.now()

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

