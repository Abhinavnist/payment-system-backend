import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.payment import PaymentType, PaymentMethod, PaymentStatus


class PaymentLink(Base):
    """Payment link model for direct customer payments"""
    
    # Basic info
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchant.id"), nullable=False)
    merchant = relationship("Merchant", backref="payment_links")
    
    # Link details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    unique_code = Column(String, unique=True, index=True, nullable=False)
    
    # Payment details
    amount = Column(Integer, nullable=True)  # Amount in paisa (INR), null for custom amount
    currency = Column(String, default="INR")
    payment_type = Column(Enum(PaymentType), default=PaymentType.DEPOSIT, nullable=False)
    allowed_methods = Column(JSONB, nullable=True)  # List of allowed payment methods
    
    # Status and expiry
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Usage limits
    max_uses = Column(Integer, nullable=True)  # Null means unlimited
    used_count = Column(Integer, default=0)
    
    # Redirect URLs
    success_url = Column(String, nullable=True)
    cancel_url = Column(String, nullable=True)
    
    # Additional metadata
    link_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    payments = relationship("Payment", back_populates="payment_link")