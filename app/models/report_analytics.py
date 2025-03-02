from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.payment import PaymentType, PaymentMethod, PaymentStatus


class ReportAnalytics(Base):
    """Report analytics model for tracking payment statistics"""
    
    # Reference to merchant
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchant.id"), nullable=False)
    merchant = relationship("Merchant", backref="analytics")
    
    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Transaction counts
    total_transactions = Column(Integer, default=0)
    successful_transactions = Column(Integer, default=0)
    failed_transactions = Column(Integer, default=0)
    pending_transactions = Column(Integer, default=0)
    
    # Amount statistics
    total_amount = Column(Integer, default=0)  # In paisa
    successful_amount = Column(Integer, default=0)
    failed_amount = Column(Integer, default=0)
    pending_amount = Column(Integer, default=0)
    
    # Payment type statistics
    deposit_count = Column(Integer, default=0)
    withdrawal_count = Column(Integer, default=0)
    deposit_amount = Column(Integer, default=0)
    withdrawal_amount = Column(Integer, default=0)
    
    # Payment method statistics
    payment_method_stats = Column(JSON, nullable=True)  # Breakdown by payment method
    
    # Success rate
    success_rate = Column(Integer, default=0)  # Percentage * 100 (e.g., 9850 = 98.5%)
    
    # Average processing time (in seconds)
    avg_processing_time = Column(Integer, default=0)
    
    # Report metadata
    report_type = Column(String, nullable=False)  # daily, weekly, monthly
    is_final = Column(Boolean, default=False)  # Whether the report period is complete
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    class Config:
        from_attributes = True 