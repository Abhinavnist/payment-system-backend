from sqlalchemy import Boolean, Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    api_key = Column(String, unique=True, index=True, nullable=True)


