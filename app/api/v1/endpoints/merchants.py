# app/api/v1/endpoints/merchants.py
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.utils.dependencies import get_db, get_current_active_superuser, get_current_user
from app.utils.security import create_api_key

router = APIRouter()


@router.get("/", response_model=List[schemas.Merchant])
def read_merchants(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve merchants.
    """
    merchants = db.query(models.Merchant).offset(skip).limit(limit).all()
    return merchants


@router.post("/", response_model=schemas.Merchant)
def create_merchant(
    *,
    db: Session = Depends(get_db),
    merchant_in: schemas.MerchantCreate,
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Create new merchant.
    """
    # Check if we need to create a new user or use an existing one
    user = None
    if merchant_in.user_id:
        user = db.query(models.User).filter(models.User.id == merchant_in.user_id).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="The user with this ID does not exist in the system",
            )
    elif merchant_in.email:
        # Check if user with this email exists
        user = db.query(models.User).filter(models.User.email == merchant_in.email).first()
        if user:
            # Use existing user
            pass
        elif merchant_in.password:
            # Create new user
            user = models.User(
                email=merchant_in.email,
                hashed_password=get_password_hash(merchant_in.password),
                full_name=merchant_in.business_name,
                is_superuser=False,
                is_active=True,
                api_key=create_api_key()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            raise HTTPException(
                status_code=400,
                detail="Password is required when creating a new user",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either user_id or email must be provided",
        )
    
    # Create merchant
    merchant = models.Merchant(
        user_id=user.id,
        business_name=merchant_in.business_name,
        business_type=merchant_in.business_type,
        contact_phone=merchant_in.contact_phone,
        address=merchant_in.address,
        webhook_url=merchant_in.webhook_url,
        callback_url=merchant_in.callback_url,
        is_active=merchant_in.is_active,
        whitelist_ips=merchant_in.whitelist_ips,
        bank_details=merchant_in.bank_details.dict() if merchant_in.bank_details else None,
        upi_details=merchant_in.upi_details.dict() if merchant_in.upi_details else None,
        min_deposit=merchant_in.min_deposit,
        max_deposit=merchant_in.max_deposit,
        min_withdrawal=merchant_in.min_withdrawal,
        max_withdrawal=merchant_in.max_withdrawal,
        api_key=user.api_key,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@router.put("/{merchant_id}", response_model=schemas.Merchant)
def update_merchant(
    *,
    db: Session = Depends(get_db),
    merchant_id: str = Path(...),
    merchant_in: schemas.MerchantUpdate,
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Update a merchant.
    """
    merchant = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=404,
            detail="The merchant with this ID does not exist in the system",
        )
    
    update_data = merchant_in.dict(exclude_unset=True)
    
    # Handle special case for bank and UPI details
    if "bank_details" in update_data and update_data["bank_details"]:
        update_data["bank_details"] = update_data["bank_details"].dict()
    
    if "upi_details" in update_data and update_data["upi_details"]:
        update_data["upi_details"] = update_data["upi_details"].dict()
    
    for field, value in update_data.items():
        if value is not None:
            setattr(merchant, field, value)
    
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@router.get("/{merchant_id}", response_model=schemas.Merchant)
def get_merchant(
    *,
    db: Session = Depends(get_db),
    merchant_id: str = Path(...),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get merchant details.
    """
    merchant = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=404,
            detail="The merchant with this ID does not exist in the system",
        )
    return merchant


@router.post("/{merchant_id}/regenerate-api-key", response_model=schemas.Merchant)
def regenerate_api_key(
    *,
    db: Session = Depends(get_db),
    merchant_id: str = Path(...),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Regenerate API key for a merchant.
    """
    merchant = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=404,
            detail="The merchant with this ID does not exist in the system",
        )
    
    # Generate new API key
    new_api_key = create_api_key()
    
    # Update merchant API key
    merchant.api_key = new_api_key
    
    # Update user API key as well
    user = db.query(models.User).filter(models.User.id == merchant.user_id).first()
    if user:
        user.api_key = new_api_key
        db.add(user)
    
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


