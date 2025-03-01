from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app import models, schemas
from app.utils.dependencies import get_db, get_merchant_by_api_key, get_current_user
from app.services.payment_link_service import PaymentLinkService
from app.schemas.payment_link import PaymentLinkCreate, PaymentLink, PaymentLinkUpdate, CustomerPaymentInfo

router = APIRouter()


@router.post("/", response_model=PaymentLink)
def create_payment_link(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    payment_link_in: PaymentLinkCreate,
) -> Any:
    """
    Create a new payment link
    """
    service = PaymentLinkService(db)
    payment_link = service.create_payment_link(
        merchant_id=str(merchant.id),
        payload=payment_link_in
    )
    
    # Return with complete URL
    result = PaymentLink.from_orm(payment_link)
    return result


@router.get("/", response_model=List[PaymentLink])
def list_payment_links(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
) -> Any:
    """
    List payment links for a merchant
    """
    query = db.query(models.PaymentLink).filter(models.PaymentLink.merchant_id == merchant.id)
    
    if active_only:
        query = query.filter(models.PaymentLink.is_active == True)
    
    payment_links = query.order_by(models.PaymentLink.created_at.desc()).offset(skip).limit(limit).all()
    
    # Return with complete URLs
    result = [PaymentLink.from_orm(link) for link in payment_links]
    return result


@router.get("/{payment_link_id}", response_model=PaymentLink)
def get_payment_link(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    payment_link_id: UUID,
) -> Any:
    """
    Get a specific payment link
    """
    payment_link = db.query(models.PaymentLink).filter(
        models.PaymentLink.id == payment_link_id,
        models.PaymentLink.merchant_id == merchant.id
    ).first()
    
    if not payment_link:
        raise HTTPException(status_code=404, detail="Payment link not found")
    
    return PaymentLink.from_orm(payment_link)


@router.put("/{payment_link_id}", response_model=PaymentLink)
def update_payment_link(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    payment_link_id: UUID,
    payment_link_in: PaymentLinkUpdate,
) -> Any:
    """
    Update a payment link
    """
    payment_link = db.query(models.PaymentLink).filter(
        models.PaymentLink.id == payment_link_id,
        models.PaymentLink.merchant_id == merchant.id
    ).first()
    
    if not payment_link:
        raise HTTPException(status_code=404, detail="Payment link not found")
    
    # Update fields
    update_data = payment_link_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment_link, field, value)
    
    db.add(payment_link)
    db.commit()
    db.refresh(payment_link)
    
    return PaymentLink.from_orm(payment_link)


@router.delete("/{payment_link_id}", response_model=PaymentLink)
def deactivate_payment_link(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    payment_link_id: UUID,
) -> Any:
    """
    Deactivate a payment link (soft delete)
    """
    payment_link = db.query(models.PaymentLink).filter(
        models.PaymentLink.id == payment_link_id,
        models.PaymentLink.merchant_id == merchant.id
    ).first()
    
    if not payment_link:
        raise HTTPException(status_code=404, detail="Payment link not found")
    
    # Deactivate link
    payment_link.is_active = False
    db.add(payment_link)
    db.commit()
    db.refresh(payment_link)
    
    return PaymentLink.from_orm(payment_link)


# Public facing endpoints for customers

@router.get("/public/{unique_code}")
def get_public_payment_link(
    *,
    db: Session = Depends(get_db),
    unique_code: str,
) -> Any:
    """
    Get payment link details for public access
    
    This endpoint is used by the payment page to get the payment link details
    """
    service = PaymentLinkService(db)
    payment_link = service.get_payment_link(unique_code)
    
    if not payment_link:
        raise HTTPException(status_code=404, detail="Payment link not found")
    
    # Validate payment link
    is_valid, error_message = service.validate_payment_link(payment_link)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Get merchant details
    merchant = db.query(models.Merchant).filter(models.Merchant.id == payment_link.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    return {
        "title": payment_link.title,
        "description": payment_link.description,
        "merchant": merchant.business_name,
        "amount": payment_link.amount,
        "currency": payment_link.currency,
        "allowed_methods": payment_link.allowed_methods or ["UPI", "BANK_TRANSFER"],
        "custom_amount": payment_link.amount is None,
        "merchant_id": str(payment_link.merchant_id),
        "payment_link_id": str(payment_link.id)
    }


@router.post("/public/{unique_code}/pay")
def process_public_payment(
    *,
    db: Session = Depends(get_db),
    unique_code: str,
    customer_info: CustomerPaymentInfo,
) -> Any:
    """
    Process a payment using a payment link
    
    This endpoint is used by the payment page to process a payment
    """
    service = PaymentLinkService(db)
    payment_link = service.get_payment_link(unique_code)
    
    if not payment_link:
        raise HTTPException(status_code=404, detail="Payment link not found")
    
    # Validate payment link
    is_valid, error_message = service.validate_payment_link(payment_link)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    try:
        # Process payment
        payment, response_data = service.process_payment(payment_link, customer_info)
        
        # If UTR number provided, submit it
        if customer_info.utr_number:
            service.submit_utr_for_payment(str(payment.id), customer_info.utr_number)
        
        return {
            "message": "Payment created successfully",
            "payment_id": str(payment.id),
            "status": payment.status,
            "response": response_data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing payment: {str(e)}")


@router.post("/public/submit-utr/{payment_id}")
def submit_utr(
    *,
    db: Session = Depends(get_db),
    payment_id: UUID,
    utr_number: str,
) -> Any:
    """
    Submit UTR number for a payment
    
    This endpoint is used by the payment page to submit a UTR number for verification
    """
    service = PaymentLinkService(db)
    
    try:
        payment = service.submit_utr_for_payment(str(payment_id), utr_number)
        
        return {
            "message": "UTR number submitted successfully",
            "payment_id": str(payment.id),
            "status": payment.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting UTR: {str(e)}")