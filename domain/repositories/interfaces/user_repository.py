from abc import ABC, abstractmethod
from ..entities.user_entity import UserEntity

class UserRepository(ABC):
    """Repository interface for user data I/O"""

@abstractmethod
async def create(self, user: UserEntity) -> UserEntity: # type: ignore
    """Create a new user"""
    pass

@abstractmethod
async def update(self, user: UserEntity):
    """Update a user"""
    pass

@abstractmethod
async def delete(self, user_id: int):
    """Delete a user"""
    pass

@abstractmethod
async def get_by_id(self, user_id: int) -> UserEntity: # type: ignore
    """Get a user by ID"""
    pass

@abstractmethod
async def exists(self, org: UserEntity) -> bool: #type: ignore
    """Check if a user exists"""
    pass