# app/schemas/payment.py
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, validator


class PaymentType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


class PaymentBase(BaseModel):
    reference: str
    payment_type: PaymentType
    payment_method: Optional[PaymentMethod] = None
    amount: int
    currency: str = "INR"


class PaymentCreate(PaymentBase):
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    bank: Optional[str] = None
    bank_ifsc: Optional[str] = None
    upi_id: Optional[str] = None
    callback_url: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None
    
    @validator('amount')
    def validate_amount(cls, v, values):
        if 'payment_type' in values:
            if values['payment_type'] == PaymentType.DEPOSIT and (v < 500 or v > 300000):
                raise ValueError(f"Deposit amount must be between ₹ 500 and ₹ 300,000. Got: {v}")
            if values['payment_type'] == PaymentType.WITHDRAWAL and (v < 1000 or v > 1000000):
                raise ValueError(f"Withdrawal amount must be between ₹ 1,000 and ₹ 1,000,000. Got: {v}")
        return v


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    utr_number: Optional[str] = None
    remarks: Optional[str] = None


class PaymentInDBBase(PaymentBase):
    id: UUID
    merchant_id: UUID
    trxn_hash_key: str
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Payment(PaymentInDBBase):
    upi_id: Optional[str] = None
    qr_code_data: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    utr_number: Optional[str] = None
    verified_by: Optional[UUID] = None
    verification_method: Optional[str] = None
    remarks: Optional[str] = None


class PaymentVerify(BaseModel):
    utr_number: str
    payment_id: UUID


class PaymentResponse(BaseModel):
    message: str
    status: int
    response: Dict[str, Any]


class CheckRequest(BaseModel):
    trxnHashKey: str


class CheckRequestResponse(BaseModel):
    message: str
    status: int
    response: Dict[str, Any]


class CallbackData(BaseModel):
    reference_id: str
    status: int  # 2: Confirmed, 3: Declined
    remarks: str
    amount: str


