import uuid
from sqlalchemy import DateTime
from sqlalchemy import String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from app.db import Base

class User(Base):
    __tablename__ = 'users'

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = mapped_column(String, unique=True, nullable=False)
    hashed_password  = mapped_column(String, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    is_active = mapped_column(Boolean, default=True)
