from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app import models, schemas
from app.utils.dependencies import get_db, get_current_active_superuser
from app.schemas.ip_whitelist import IPWhitelistUpdate

router = APIRouter()


@router.get("/merchant/{merchant_id}/whitelist", response_model=List[str])
def get_merchant_whitelist(
    *,
    db: Session = Depends(get_db),
    merchant_id: str,
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get merchant IP whitelist
    """
    merchant = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    return merchant.whitelist_ips or []


@router.post("/merchant/{merchant_id}/whitelist", response_model=List[str])
def update_merchant_whitelist(
    *,
    db: Session = Depends(get_db),
    merchant_id: str,
    whitelist_data: IPWhitelistUpdate,
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Update merchant IP whitelist
    """
    merchant = db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    # Update whitelist
    if whitelist_data.operation == "add":
        # Initialize if not exists
        if not merchant.whitelist_ips:
            merchant.whitelist_ips = []
        
        # Add new IPs if not already in list
        for ip in whitelist_data.ip_addresses:
            if ip not in merchant.whitelist_ips:
                merchant.whitelist_ips.append(ip)
    
    elif whitelist_data.operation == "remove":
        if merchant.whitelist_ips:
            # Remove IPs
            merchant.whitelist_ips = [ip for ip in merchant.whitelist_ips if ip not in whitelist_data.ip_addresses]
    
    elif whitelist_data.operation == "replace":
        # Replace entire whitelist
        merchant.whitelist_ips = whitelist_data.ip_addresses
    
    # Save changes
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    
    return merchant.whitelist_ips or []