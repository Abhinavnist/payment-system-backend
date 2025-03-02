from typing import Any, Dict, List
import logging
from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session
import requests
from pydantic import ValidationError

from app import models, schemas
from app.api import deps
from app.services.payment_processor import PaymentProcessor
from app.services.utr_verifier import UTRVerifier

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/request", response_model=schemas.PaymentResponse)
def create_payment_request(
    *,
    db: Session = Depends(deps.get_db),
    merchant: models.Merchant = Depends(deps.get_merchant_by_api_key),
    api_key: str = Body(...),
    service_type: int = Body(1),
    currency: str = Body("INR"),
    action: str = Body(...),
    reference: str = Body(...),
    amount: int = Body(...),
    account_name: str = Body(None),
    account_number: str = Body(None),
    bank: str = Body(None),
    bank_ifsc: str = Body(None),
    callback_url: str = Body(None),
    ae_type: str = Body("1"),
    user_data: Dict[str, Any] = Body(None),
) -> Any:
    """
    Create new payment request.
    
    This endpoint follows the documentation requirements.
    """
    try:
        # Validate action type
        if action not in ["DEPOSIT", "WITHDRAWAL"]:
            return schemas.PaymentResponse(
                message="Error",
                status=400,
                response={
                    "code": 1001,
                    "error": "Invalid action. Use 'DEPOSIT' or 'WITHDRAWAL'"
                }
            )
        
        # Validate currency
        if currency != "INR":
            return schemas.PaymentResponse(
                message="Error",
                status=400,
                response={
                    "code": 1002,
                    "error": "Only INR currency is supported"
                }
            )
        
        # Create payment request data
        try:
            payment_data = schemas.PaymentCreate(
                reference=reference,
                payment_type=schemas.PaymentType.DEPOSIT if action == "DEPOSIT" else schemas.PaymentType.WITHDRAWAL,
                payment_method=schemas.PaymentMethod.UPI if not bank else schemas.PaymentMethod.BANK_TRANSFER,
                amount=amount,
                currency=currency,
                account_name=account_name,
                account_number=account_number,
                bank=bank,
                bank_ifsc=bank_ifsc,
                callback_url=callback_url or merchant.callback_url,
                user_data=user_data
            )
        except ValidationError as e:
            return schemas.PaymentResponse(
                message="Error",
                status=400,
                response={
                    "code": 1003,
                    "error": str(e.errors()[0].get("msg")),
                    "details": e.errors()
                }
            )
        
        # Process payment
        processor = PaymentProcessor(db)
        try:
            if action == "DEPOSIT":
                payment, response_data = processor.process_deposit_request(merchant, payment_data)
            else:
                payment, response_data = processor.process_withdrawal_request(merchant, payment_data)
                
            # Format success response
            return schemas.PaymentResponse(
                message="Success",
                status=201,
                response=response_data
            )
        except ValueError as e:
            return schemas.PaymentResponse(
                message="Error",
                status=400,
                response={
                    "code": 1004,
                    "error": str(e)
                }
            )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return schemas.PaymentResponse(
            message="Error",
            status=500,
            response={
                "code": 1005,
                "error": "Internal server error"
            }
        )


@router.post("/check-request", response_model=schemas.CheckRequestResponse)
def check_payment_request(
    *,
    db: Session = Depends(deps.get_db),
    merchant: models.Merchant = Depends(deps.get_merchant_by_api_key),
    trxnHashKey: str = Body(...),
) -> Any:
    """
    Check status of a payment request
    """
    processor = PaymentProcessor(db)
    payment = processor.get_payment_by_hash(trxnHashKey)
    
    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )
    
    # Check if payment belongs to requesting merchant
    if payment.merchant_id != merchant.id:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized to access this transaction"
        )
    
    # Format response according to documentation
    return {
        "message": "Success",
        "status": 200,
        "response": {
            "transactionId": payment.id,
            "reference": payment.reference,
            "type": payment.payment_type.value,
            "status": payment.status.value,
            "remarks": payment.remarks or "",
            "requestedDate": payment.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    }


@router.post("/verify-payment")
def verify_payment_with_utr(
    *,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    payment_verify: schemas.PaymentVerify,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Verify a payment using UTR number
    """
    verifier = UTRVerifier(db)
    try:
        payment = verifier.verify_utr(
            payment_verify.utr_number,
            payment_verify.payment_id,
            str(current_user.id)
        )
        
        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found or already processed"
            )
        
        # Add background task to send callback
        background_tasks.add_task(
            send_callback_notification,
            db,
            payment
        )
        
        return {
            "message": "Payment verified successfully",
            "payment_id": payment.id,
            "status": payment.status.value
        }
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error verifying payment: {str(e)}"
        )


def send_callback_notification(db: Session, payment: models.Payment) -> None:
    """
    Send callback notification to merchant
    """
    # Get merchant
    merchant = db.query(models.Merchant).filter(
        models.Merchant.id == payment.merchant_id
    ).first()
    
    if not merchant or not merchant.callback_url:
        logger.warning(f"No callback URL for payment {payment.id}")
        return
    
    # Prepare callback data
    callback_data = {
        "reference_id": payment.reference,
        "status": 2 if payment.status == models.PaymentStatus.CONFIRMED else 3,
        "remarks": payment.remarks or "Payment processed",
        "amount": str(payment.amount)
    }
    
    try:
        # Send callback
        response = requests.post(
            merchant.callback_url,
            json=callback_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Update payment record
        payment.callback_sent = True
        payment.response_data = {
            "callback_status": response.status_code,
            "callback_response": response.text if response.status_code == 200 else None
        }
        
        db.add(payment)
        db.commit()
        
        logger.info(f"Callback sent for payment {payment.id}, status: {response.status_code}")
    except Exception as e:
        logger.error(f"Callback error for payment {payment.id}: {str(e)}")
        payment.response_data = {
            "callback_error": str(e)
        }
        db.add(payment)
        db.commit()