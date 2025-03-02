# app/services/payment_processor.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import urllib.parse

from app.models.payment import Payment, PaymentStatus, PaymentType, PaymentMethod
from app.models.merchant import Merchant
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.utils.security import generate_transaction_hash
from app.services.qr_generator import generate_upi_qr

logger = logging.getLogger(__name__)


class PaymentProcessor:
    def __init__(self, db: Session):
        self.db = db
    
    def process_deposit_request(self, 
                               merchant: Merchant, 
                               payment_data: PaymentCreate) -> Tuple[Payment, Dict[str, Any]]:
        """Process a deposit request from a merchant"""
        
        # Validate amount
        if payment_data.amount < merchant.min_deposit or payment_data.amount > merchant.max_deposit:
            raise ValueError(
                f"Deposit amount must be between ₹ {merchant.min_deposit} and ₹ {merchant.max_deposit}."
            )
        
        # Generate transaction hash
        trxn_hash_key = generate_transaction_hash(
            payment_data.reference, str(merchant.id), payment_data.amount
        )
        
        # Determine payment method (UPI or bank transfer)
        payment_method = PaymentMethod.UPI
        if payment_data.bank and payment_data.account_number:
            payment_method = PaymentMethod.BANK_TRANSFER
        
        # Create payment record
        payment = Payment(
            merchant_id=merchant.id,
            reference=payment_data.reference,
            trxn_hash_key=trxn_hash_key,
            payment_type=PaymentType.DEPOSIT,
            payment_method=payment_method,
            amount=payment_data.amount,
            currency=payment_data.currency,
            status=PaymentStatus.PENDING,
            request_data=payment_data.dict(),
            user_data=payment_data.user_data
        )
        
        # Set payment method specific data
        response_data = {}
        if payment_method == PaymentMethod.UPI:
            if not merchant.upi_details:
                raise ValueError("Merchant UPI details not configured")
            
            # Generate QR code for UPI payment
            upi_id = merchant.upi_details.get("upi_id")
            name = merchant.upi_details.get("name", merchant.business_name)
            amount=payment_data.amount
            upi_payment_string = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(name)}&am={amount}&tr={payment.trxn_hash_key}&cu=INR"
            # upi_link, qr_data = generate_upi_qr(
            #     upi_id=upi_id,
            #     name=name,
            #     amount=payment_data.amount,
            #     transaction_ref=trxn_hash_key
            # )
            
            payment.upi_id = upi_id
            payment.upi_payment_string = upi_payment_string
            
            response_data = {
                "paymentMethod": "UPI",
                "receiverInfo": {
                    "upi_id": upi_id,
                    "name": name
                },
                # "upiLink": upi_link,
                "upiString": upi_payment_string,
                # "qrCode": qr_data,
                "trxnHashKey": trxn_hash_key,
                "amount": str(payment_data.amount),
                "requestedDate": datetime.utcnow().isoformat()
            }
        else:
            # Bank transfer
            if not merchant.bank_details:
                raise ValueError("Merchant bank details not configured")
            
            bank_name = merchant.bank_details.get("bank_name")
            account_name = merchant.bank_details.get("account_name")
            account_number = merchant.bank_details.get("account_number")
            ifsc_code = merchant.bank_details.get("ifsc_code")
            
            payment.bank_name = bank_name
            payment.account_name = account_name
            payment.account_number = account_number
            payment.ifsc_code = ifsc_code
            
            response_data = {
                "paymentMethod": "BANK_TRANSFER",
                "receiverBankInfo": {
                    "bank": bank_name,
                    "account_name": account_name,
                    "account_number": account_number,
                    "bank_ifsc": ifsc_code
                },
                "trxnHashKey": trxn_hash_key,
                "amount": str(payment_data.amount),
                "requestedDate": datetime.utcnow().isoformat()
            }
        
        # Save payment record
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        return payment, response_data
    
    def process_withdrawal_request(self,
                                  merchant: Merchant,
                                  payment_data: PaymentCreate) -> Tuple[Payment, Dict[str, Any]]:
        """Process a withdrawal request from a merchant"""
        
        # Validate amount
        if payment_data.amount < merchant.min_withdrawal or payment_data.amount > merchant.max_withdrawal:
            raise ValueError(
                f"Withdrawal amount must be between ₹ {merchant.min_withdrawal} and ₹ {merchant.max_withdrawal}."
            )
        
        # Validate bank details for withdrawal
        if not payment_data.account_name or not payment_data.account_number or not payment_data.bank or not payment_data.bank_ifsc:
            raise ValueError("Bank account details are required for withdrawal.")
        
        # Generate transaction hash
        trxn_hash_key = generate_transaction_hash(
            payment_data.reference, str(merchant.id), payment_data.amount
        )
        
        # Create payment record
        payment = Payment(
            merchant_id=merchant.id,
            reference=payment_data.reference,
            trxn_hash_key=trxn_hash_key,
            payment_type=PaymentType.WITHDRAWAL,
            payment_method=PaymentMethod.BANK_TRANSFER,
            amount=payment_data.amount,
            currency=payment_data.currency,
            status=PaymentStatus.PENDING,
            bank_name=payment_data.bank,
            account_name=payment_data.account_name,
            account_number=payment_data.account_number,
            ifsc_code=payment_data.bank_ifsc,
            request_data=payment_data.dict(),
            user_data=payment_data.user_data
        )
        
        # Create response data
        response_data = {
            "receiverBankInfo": {
                "bank": payment_data.bank,
                "bank_ifsc": payment_data.bank_ifsc,
                "account_name": payment_data.account_name,
                "account_number": payment_data.account_number,
            },
            "trxnHashKey": trxn_hash_key,
            "amount": str(payment_data.amount),
            "requestedDate": datetime.utcnow().isoformat()
        }
        
        # Save payment record
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        return payment, response_data
    
    def verify_payment(self, payment_id: str, utr_number: str, verified_by: str) -> Payment:
        """Verify a payment with UTR number"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")
        
        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Payment is already in {payment.status} status")
        
        payment.utr_number = utr_number
        payment.verified_by = verified_by
        payment.status = PaymentStatus.CONFIRMED
        payment.verification_method = "MANUAL"
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def decline_payment(self, payment_id: str, remarks: str, verified_by: str) -> Payment:
        """Decline a payment"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")
        
        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Payment is already in {payment.status} status")
        
        payment.status = PaymentStatus.DECLINED
        payment.remarks = remarks
        payment.verified_by = verified_by
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def get_payment_by_hash(self, trxn_hash_key: str) -> Optional[Payment]:
        """Get payment by transaction hash key"""
        return self.db.query(Payment).filter(Payment.trxn_hash_key == trxn_hash_key).first()


