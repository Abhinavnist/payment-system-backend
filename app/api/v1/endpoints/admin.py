# app/api/v1/endpoints/admin.py
from typing import Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path, File, UploadFile, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.utils.dependencies import get_db, get_current_active_superuser
from app.utils.security import get_password_hash, create_api_key
from app.services.utr_verifier import UTRVerifier
from app.services.csv_exporter import CSVExporter
from app.services.payment_processor import PaymentProcessor
from app.services.bank_statement_processor import BankStatementProcessor
import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/users", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@router.post("/users", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    user = models.User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_superuser=user_in.is_superuser,
        api_key=create_api_key() if user_in.is_superuser else None
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this ID does not exist in the system",
        )
    
    update_data = user_in.dict(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/pending-payments", response_model=List[schemas.Payment])
def get_pending_payments(
    *,
    db: Session = Depends(get_db),
    merchant_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get list of pending payments for verification
    """
    verifier = UTRVerifier(db)
    payments = verifier.get_pending_payments(merchant_id, days)
    return payments


@router.post("/verify-payment/{payment_id}", response_model=schemas.Payment)
def admin_verify_payment(
    *,
    db: Session = Depends(get_db),
    payment_id: str = Path(...),
    utr_number: str = Body(...),
    remarks: Optional[str] = Body(None),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Admin verification of payment with UTR number
    """
    verifier = UTRVerifier(db)
    payment = verifier.verify_utr(utr_number, payment_id, str(current_user.id))
    
    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found or already processed"
        )
    
    if remarks:
        payment.remarks = remarks
        db.add(payment)
        db.commit()
        db.refresh(payment)
    
    return payment


@router.post("/decline-payment/{payment_id}", response_model=schemas.Payment)
def admin_decline_payment(
    *,
    db: Session = Depends(get_db),
    payment_id: str = Path(...),
    remarks: str = Body(...),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Decline a payment
    """
    processor = PaymentProcessor(db)
    payment = processor.decline_payment(payment_id, remarks, str(current_user.id))
    return payment


@router.get("/export-payments")
def export_payments(
    *,
    db: Session = Depends(get_db),
    merchant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Export payments data to CSV
    """
    exporter = CSVExporter(db)
    try:
        filepath = exporter.export_payments(merchant_id, start_date, end_date)
        return FileResponse(
            filepath,
            media_type="text/csv",
            filename=f"payments_export_{datetime.now().strftime('%Y%m%d')}.csv"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting payments: {str(e)}"
        )
    

@router.post("/upload-bank-statement")
async def upload_bank_statement(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Upload bank statement for automated UTR verification
    
    This endpoint processes a bank statement file and automatically matches
    UTR numbers with pending payments.
    """
    try:
        # Read file content
        content = await file.read()
        
        # Process statement
        processor = BankStatementProcessor(db)
        result = processor.process_statement(
            file_content=content,
            file_type=file.content_type,
            verified_by=str(current_user.id)
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400, 
                detail=result["error"]
            )
        
        return {
            "message": "Bank statement processed successfully",
            "filename": file.filename,
            "total_transactions": result["total_transactions"],
            "matches_found": result["matches"],
            "matched_payments": result["matched_payments"],
            "unmatched_transactions": len(result["unmatched_transactions"])
        }
    except Exception as e:
        logger.error(f"Error processing bank statement: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing bank statement: {str(e)}"
        )