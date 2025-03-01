# app/api/v1/endpoints/reports.py
from typing import Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app import models, schemas
from app.utils.dependencies import get_db, get_current_active_superuser, get_current_user, get_merchant_by_api_key
from app.services.csv_exporter import CSVExporter

router = APIRouter()


@router.get("/payments")
def get_merchant_payments(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
) -> Any:
    """
    Get merchant payments with filtering and pagination
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Build query
    query = db.query(models.Payment).filter(models.Payment.merchant_id == merchant.id)
    
    if start_date:
        query = query.filter(models.Payment.created_at >= start_date)
    
    if end_date:
        query = query.filter(models.Payment.created_at <= end_date)
    
    if status:
        query = query.filter(models.Payment.status == status)
    
    # Get total count
    total_count = query.count()
    
    # Get paginated results
    payments = query.order_by(models.Payment.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Convert to schema
    payment_list = []
    for payment in payments:
        payment_list.append(schemas.Payment.from_orm(payment))
    
    return {
        "items": payment_list,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "pages": (total_count + page_size - 1) // page_size
    }


@router.get("/download-payments")
def download_merchant_payments(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
) -> Any:
    """
    Download merchant payments as CSV
    """
    exporter = CSVExporter(db)
    try:
        csv_content = exporter.generate_payments_csv_string(str(merchant.id), start_date, end_date)
        
        # Create response
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=payments_{merchant.business_name}_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting payments: {str(e)}"
        )


@router.get("/admin/payments")
def admin_get_all_payments(
    *,
    db: Session = Depends(get_db),
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    payment_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Admin endpoint to get all payments with filtering and pagination
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Build query
    query = db.query(models.Payment)
    
    if merchant_id:
        query = query.filter(models.Payment.merchant_id == merchant_id)
    
    if start_date:
        query = query.filter(models.Payment.created_at >= start_date)
    
    if end_date:
        query = query.filter(models.Payment.created_at <= end_date)
    
    if status:
        query = query.filter(models.Payment.status == status)
    
    if payment_type:
        query = query.filter(models.Payment.payment_type == payment_type)
    
    # Get total count
    total_count = query.count()
    
    # Get paginated results
    payments = query.order_by(models.Payment.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Convert to schema
    payment_list = []
    for payment in payments:
        payment_list.append(schemas.Payment.from_orm(payment))
    
    return {
        "items": payment_list,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "pages": (total_count + page_size - 1) // page_size
    }


@router.get("/admin/dashboard-stats")
def admin_dashboard_stats(
    *,
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get admin dashboard statistics
    """
    # Calculate start date
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total merchants
    total_merchants = db.query(models.Merchant).count()
    
    # Active merchants
    active_merchants = db.query(models.Merchant).filter(models.Merchant.is_active == True).count()
    
    # Total transactions
    total_transactions = db.query(models.Payment).filter(
        models.Payment.created_at >= start_date
    ).count()
    
    # Successful transactions
    successful_transactions = db.query(models.Payment).filter(
        models.Payment.created_at >= start_date,
        models.Payment.status == "CONFIRMED"
    ).count()
    
    # Total deposit amount
    deposit_amount_result = db.query(
        db.func.sum(models.Payment.amount)
    ).filter(
        models.Payment.created_at >= start_date,
        models.Payment.payment_type == "DEPOSIT",
        models.Payment.status == "CONFIRMED"
    ).scalar()
    
    total_deposit_amount = deposit_amount_result or 0
    
    # Total withdrawal amount
    withdrawal_amount_result = db.query(
        db.func.sum(models.Payment.amount)
    ).filter(
        models.Payment.created_at >= start_date,
        models.Payment.payment_type == "WITHDRAWAL",
        models.Payment.status == "CONFIRMED"
    ).scalar()
    
    total_withdrawal_amount = withdrawal_amount_result or 0
    
    # Pending verification count
    pending_verification = db.query(models.Payment).filter(
        models.Payment.status == "PENDING"
    ).count()
    
    return {
        "total_merchants": total_merchants,
        "active_merchants": active_merchants,
        "total_transactions": total_transactions,
        "successful_transactions": successful_transactions,
        "success_rate": (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0,
        "total_deposit_amount": total_deposit_amount,
        "total_withdrawal_amount": total_withdrawal_amount,
        "pending_verification": pending_verification,
        "days": days
    }