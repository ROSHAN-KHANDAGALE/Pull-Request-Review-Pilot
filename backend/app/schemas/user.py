from datetime import datetime
from pydantic import BaseModel, field_validator
from uuid import UUID

class  UserCreate(BaseModel):
    email: str
    password: str

    @field_validator('password')
    @classmethod
    def password_validator(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long..')
        return v

class UserOut(BaseModel):
    id: UUID
    email: str
    created_at: datetime
    model_config = {"from_attributes": True}

class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'