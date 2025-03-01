# app/schemas/merchant.py
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.schemas.user import User


class BankDetails(BaseModel):
    bank_name: str
    account_name: str
    account_number: str
    ifsc_code: str


class UpiDetails(BaseModel):
    upi_id: str
    name: str
    description: Optional[str] = None


class MerchantBase(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    webhook_url: Optional[str] = None
    callback_url: Optional[str] = None
    is_active: Optional[bool] = True
    whitelist_ips: Optional[List[str]] = None
    bank_details: Optional[BankDetails] = None
    upi_details: Optional[UpiDetails] = None
    min_deposit: Optional[int] = 500
    max_deposit: Optional[int] = 300000
    min_withdrawal: Optional[int] = 1000
    max_withdrawal: Optional[int] = 1000000


class MerchantCreate(MerchantBase):
    business_name: str
    contact_phone: str
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    password: Optional[str] = None


class MerchantUpdate(MerchantBase):
    api_key: Optional[str] = None


class MerchantInDBBase(MerchantBase):
    id: UUID
    api_key: str
    user_id: UUID

    class Config:
        from_attributes = True


class Merchant(MerchantInDBBase):
    user: Optional[User] = None


