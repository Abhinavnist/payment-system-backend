from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, validator, Field

from app.schemas.payment import PaymentType


class PaymentLinkBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: Optional[int] = None  # Optional for custom amount
    currency: str = "INR"
    payment_type: PaymentType = PaymentType.DEPOSIT
    allowed_methods: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentLinkCreate(PaymentLinkBase):
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v
    
    @validator('max_uses')
    def validate_max_uses(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Max uses must be greater than 0")
        return v


class PaymentLinkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[int] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v
    
    @validator('max_uses')
    def validate_max_uses(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Max uses must be greater than 0")
        return v


class PaymentLinkInDBBase(PaymentLinkBase):
    id: UUID
    merchant_id: UUID
    unique_code: str
    is_active: bool
    used_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentLink(PaymentLinkInDBBase):
    payment_url: str = Field(None, exclude=True)
    
    @validator('payment_url', always=True)
    def set_payment_url(cls, v, values):
        if 'unique_code' in values:
            # This would be replaced with your actual frontend URL
            return f"/payment/{values['unique_code']}"
        return v


class CustomerPaymentInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    custom_amount: Optional[int] = None
    payment_method: str
    utr_number: Optional[str] = None