# app/models/payment.py
from sqlalchemy import Column, String, ForeignKey, Integer, Enum, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base


class PaymentType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class PaymentMethod(str, enum.Enum):
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


class Payment(Base):
    # Basic payment info
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchant.id"), nullable=False)
    merchant = relationship("Merchant", backref="payments")
    
    reference = Column(String, nullable=False, index=True)  # Merchant reference
    trxn_hash_key = Column(String, nullable=False, unique=True, index=True)  # System generated hash
    
    payment_type = Column(Enum(PaymentType), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    amount = Column(Integer, nullable=False)  # Amount in paisa (INR)
    currency = Column(String, default="INR")
    
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # UPI specific data
    upi_id = Column(String, nullable=True)
    qr_code_data = Column(Text, nullable=True)  # URL or base64 encoded QR
    
    # Bank transfer data
    bank_name = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    
    # Verification data
    utr_number = Column(String, nullable=True)  # UTR reference provided by user
    verified_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)  # Admin who verified
    verification_method = Column(String, nullable=True)  # "AUTOMATIC", "MANUAL"
    
    # Additional data
    user_data = Column(JSONB, nullable=True)  # Additional user data sent by merchant
    request_data = Column(JSONB, nullable=True)  # Original request data
    response_data = Column(JSONB, nullable=True)  # Response sent back to merchant
    callback_sent = Column(Boolean, default=False)
    remarks = Column(Text, nullable=True)

    # Add these fields to the Payment model
    payment_link_id = Column(UUID(as_uuid=True), ForeignKey("paymentlink.id"), nullable=True)
    payment_link = relationship("PaymentLink", back_populates="payments")
    customer_email = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)