# app/schemas/admin.py
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from app.schemas.user import User


class AdminBase(BaseModel):
    can_manage_merchants: Optional[bool] = True
    can_verify_transactions: Optional[bool] = True
    can_export_reports: Optional[bool] = True
    phone: Optional[str] = None


class AdminCreate(AdminBase):
    user_id: UUID


class AdminUpdate(AdminBase):
    pass


class AdminInDBBase(AdminBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True


class Admin(AdminInDBBase):
    user: Optional[User] = None


