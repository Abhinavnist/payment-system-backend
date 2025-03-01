# app/models/merchant.py
from sqlalchemy import Column, String, ForeignKey, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Merchant(Base):
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    user = relationship("User", backref="merchant_profile")

    
    business_name = Column(String, nullable=False)
    business_type = Column(String, nullable=True)
    contact_phone = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    
    api_key = Column(String, unique=True, index=True, nullable=False)
    webhook_secret = Column(String, nullable=True)  # Secret key for webhook signature verification
    webhook_url = Column(String, nullable=True)
    callback_url = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    whitelist_ips = Column(JSONB, nullable=True)  # List of allowed IPs
    
    # Payment settings
    bank_details = Column(JSONB, nullable=True)  # Bank account details
    upi_details = Column(JSONB, nullable=True)   # UPI payment details
    
    min_deposit = Column(Integer, default=500)
    max_deposit = Column(Integer, default=300000)
    min_withdrawal = Column(Integer, default=1000)
    max_withdrawal = Column(Integer, default=1000000)