# app/services/utr_verifier.py
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.payment import Payment, PaymentStatus


logger = logging.getLogger(__name__)


class UTRVerifier:
    def __init__(self, db: Session):
        self.db = db
    
    def verify_utr(self, utr_number: str, payment_id: str, verified_by: str) -> Optional[Payment]:
        """
        Verify payment using UTR number
        
        This is a manual verification process performed by admin
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            logger.error(f"Payment with ID {payment_id} not found")
            return None
        
        if payment.status != PaymentStatus.PENDING:
            logger.error(f"Payment is already in {payment.status} status")
            return None
        
        # Update payment with UTR number and mark as confirmed
        payment.utr_number = utr_number
        payment.status = PaymentStatus.CONFIRMED
        payment.verified_by = verified_by
        payment.verification_method = "MANUAL"
        
        self.db.commit()
        self.db.refresh(payment)
        
        logger.info(f"Payment {payment_id} verified with UTR {utr_number}")
        return payment
    
    def find_by_utr(self, utr_number: str) -> List[Payment]:
        """Find all payments with a specific UTR number"""
        return self.db.query(Payment).filter(Payment.utr_number == utr_number).all()
    
    def get_pending_payments(self, merchant_id: Optional[str] = None, 
                            days: int = 7) -> List[Payment]:
        """Get list of pending payments for verification"""
        query = self.db.query(Payment).filter(Payment.status == PaymentStatus.PENDING)
        
        if merchant_id:
            query = query.filter(Payment.merchant_id == merchant_id)
        
        # Only get recent payments
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Payment.created_at >= cutoff_date)
        
        return query.all()


