import logging
import secrets
import string
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.payment_link import PaymentLink
from app.models.payment import Payment, PaymentStatus, PaymentType, PaymentMethod
from app.models.merchant import Merchant
from app.schemas.payment_link import PaymentLinkCreate, CustomerPaymentInfo
from app.services.payment_processor import PaymentProcessor
from app.services.qr_generator import generate_upi_qr

logger = logging.getLogger(__name__)


class PaymentLinkService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_processor = PaymentProcessor(db)
    
    def create_payment_link(self, merchant_id: str, payload: PaymentLinkCreate) -> PaymentLink:
        """
        Create a new payment link
        
        Args:
            merchant_id: ID of the merchant creating the link
            payload: Payment link details
            
        Returns:
            Created payment link
        """
        # Generate unique code for payment link
        unique_code = self._generate_unique_code()
        
        # Create payment link
        payment_link = PaymentLink(
            merchant_id=merchant_id,
            title=payload.title,
            description=payload.description,
            unique_code=unique_code,
            amount=payload.amount,
            currency=payload.currency,
            payment_type=payload.payment_type,
            allowed_methods=payload.allowed_methods,
            expires_at=payload.expires_at,
            max_uses=payload.max_uses,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            metadata=payload.metadata
        )
        
        self.db.add(payment_link)
        self.db.commit()
        self.db.refresh(payment_link)
        
        return payment_link
    
    def get_payment_link(self, unique_code: str) -> Optional[PaymentLink]:
        """
        Get payment link by unique code
        
        Args:
            unique_code: Unique code of the payment link
            
        Returns:
            Payment link if found, None otherwise
        """
        return self.db.query(PaymentLink).filter(
            PaymentLink.unique_code == unique_code,
            PaymentLink.is_active == True
        ).first()
    
    def validate_payment_link(self, payment_link: PaymentLink) -> Tuple[bool, Optional[str]]:
        """
        Validate if a payment link is usable
        
        Args:
            payment_link: Payment link to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if link is active
        if not payment_link.is_active:
            return False, "This payment link is no longer active"
        
        # Check expiration
        if payment_link.expires_at and payment_link.expires_at < datetime.utcnow():
            return False, "This payment link has expired"
        
        # Check max uses
        if payment_link.max_uses and payment_link.used_count >= payment_link.max_uses:
            return False, "This payment link has reached its maximum usage limit"
        
        return True, None
    
    def process_payment(
        self, 
        payment_link: PaymentLink, 
        customer_info: CustomerPaymentInfo
    ) -> Tuple[Payment, Dict[str, Any]]:
        """
        Process a payment using a payment link
        
        Args:
            payment_link: Payment link to use
            customer_info: Customer payment information
            
        Returns:
            Tuple of (payment, response_data)
        """
        # Get merchant
        merchant = self.db.query(Merchant).filter(Merchant.id == payment_link.merchant_id).first()
        if not merchant:
            raise ValueError("Merchant not found")
        
        # Validate amount
        amount = customer_info.custom_amount if customer_info.custom_amount else payment_link.amount
        if not amount:
            raise ValueError("Amount is required")
        
        if merchant.min_deposit and amount < merchant.min_deposit:
            raise ValueError(f"Amount must be at least ₹{merchant.min_deposit / 100}")
        
        if merchant.max_deposit and amount > merchant.max_deposit:
            raise ValueError(f"Amount cannot exceed ₹{merchant.max_deposit / 100}")
        
        # Generate reference
        reference = f"PLINK-{payment_link.unique_code[:8]}-{secrets.token_hex(4)}"
        
        # Determine payment method
        payment_method = PaymentMethod(customer_info.payment_method)
        
        # Create payment
        payment = Payment(
            merchant_id=payment_link.merchant_id,
            payment_link_id=payment_link.id,
            reference=reference,
            trxn_hash_key=self._generate_transaction_hash(reference, str(merchant.id), amount),
            payment_type=payment_link.payment_type,
            payment_method=payment_method,
            amount=amount,
            currency=payment_link.currency,
            status=PaymentStatus.PENDING,
            customer_name=customer_info.name,
            customer_email=customer_info.email,
            customer_phone=customer_info.phone,
            request_data={
                "payment_link_id": str(payment_link.id),
                "customer_info": customer_info.dict()
            }
        )
        
        # Set payment method specific data
        response_data = {}
        if payment_method == PaymentMethod.UPI:
            if not merchant.upi_details:
                raise ValueError("Merchant UPI details not configured")
            
            # Generate QR code for UPI payment
            upi_id = merchant.upi_details.get("upi_id")
            name = merchant.upi_details.get("name", merchant.business_name)
            qr_data = generate_upi_qr(
                upi_id=upi_id,
                name=name,
                amount=amount,
                transaction_ref=payment.trxn_hash_key
            )
            
            payment.upi_id = upi_id
            payment.qr_code_data = qr_data
            
            response_data = {
                "paymentMethod": "UPI",
                "receiverInfo": {
                    "upi_id": upi_id,
                    "name": name
                },
                "qrCode": qr_data,
                "trxnHashKey": payment.trxn_hash_key,
                "amount": str(amount),
                "requestedDate": datetime.utcnow().isoformat()
            }
        elif payment_method == PaymentMethod.BANK_TRANSFER:
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
                "trxnHashKey": payment.trxn_hash_key,
                "amount": str(amount),
                "requestedDate": datetime.utcnow().isoformat()
            }
        
        # Save payment and update link usage count
        self.db.add(payment)
        payment_link.used_count += 1
        self.db.add(payment_link)
        self.db.commit()
        self.db.refresh(payment)
        
        return payment, response_data
    
    def submit_utr_for_payment(self, payment_id: str, utr_number: str) -> Payment:
        """
        Submit UTR number for payment verification
        
        Args:
            payment_id: ID of the payment
            utr_number: UTR number to verify
            
        Returns:
            Updated payment
        """
        # Get payment
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError("Payment not found")
        
        # Check if payment is pending
        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Payment is already in {payment.status} status")
        
        # Save UTR number for admin verification
        payment.utr_number = utr_number
        payment.remarks = "UTR number submitted by customer, awaiting verification"
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    def _generate_unique_code(self, length: int = 10) -> str:
        """Generate a unique code for payment links"""
        # Use uppercase letters and digits, excluding similar looking characters
        characters = string.ascii_uppercase + string.digits
        characters = characters.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        
        # Generate random code
        code = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Check if code already exists
        exists = self.db.query(PaymentLink).filter(PaymentLink.unique_code == code).first()
        if exists:
            # Recursively generate a new code
            return self._generate_unique_code(length)
        
        return code
    
    def _generate_transaction_hash(self, reference: str, merchant_id: str, amount: int) -> str:
        """Generate a transaction hash for payment"""
        from app.utils.security import generate_transaction_hash
        return generate_transaction_hash(reference, merchant_id, amount)