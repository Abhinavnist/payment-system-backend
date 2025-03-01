from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models
from app.utils.dependencies import get_db, get_current_active_superuser, get_merchant_by_api_key
from app.services.analytics_service import AnalyticsService

router = APIRouter()


# Admin Analytics Endpoints

@router.get("/admin/summary")
def admin_payment_summary(
    *,
    db: Session = Depends(get_db),
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get summary statistics for all payments
    
    Admin-only endpoint with option to filter by merchant
    """
    analytics = AnalyticsService(db)
    return analytics.get_payment_summary(merchant_id, start_date, end_date)


@router.get("/admin/trends")
def admin_payment_trends(
    *,
    db: Session = Depends(get_db),
    merchant_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get daily payment trends
    
    Admin-only endpoint with option to filter by merchant
    """
    analytics = AnalyticsService(db)
    return analytics.get_daily_trends(merchant_id, days)


@router.get("/admin/payment-methods")
def admin_payment_method_distribution(
    *,
    db: Session = Depends(get_db),
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get distribution of payments by payment method
    
    Admin-only endpoint with option to filter by merchant
    """
    analytics = AnalyticsService(db)
    return analytics.get_payment_method_distribution(merchant_id, start_date, end_date)


@router.get("/admin/merchant-performance")
def admin_merchant_performance(
    *,
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get top merchants by payment volume
    
    Admin-only endpoint
    """
    analytics = AnalyticsService(db)
    return analytics.get_merchant_performance(days, limit)


@router.get("/admin/payment-link-performance")
def admin_payment_link_performance(
    *,
    db: Session = Depends(get_db),
    merchant_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get performance metrics for payment links
    
    Admin-only endpoint with option to filter by merchant
    """
    analytics = AnalyticsService(db)
    return analytics.get_payment_link_performance(merchant_id, days, limit)


@router.get("/admin/verification-metrics")
def admin_verification_metrics(
    *,
    db: Session = Depends(get_db),
    merchant_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: models.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get metrics related to payment verification
    
    Admin-only endpoint with option to filter by merchant
    """
    analytics = AnalyticsService(db)
    return analytics.get_verification_metrics(merchant_id, days)


# Merchant Analytics Endpoints

@router.get("/merchant/summary")
def merchant_payment_summary(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
) -> Any:
    """
    Get summary statistics for merchant payments
    
    Merchant-only endpoint
    """
    analytics = AnalyticsService(db)
    return analytics.get_payment_summary(str(merchant.id), start_date, end_date)


@router.get("/merchant/trends")
def merchant_payment_trends(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    days: int = Query(30, ge=1, le=90),
) -> Any:
    """
    Get daily payment trends for merchant
    
    Merchant-only endpoint
    """
    analytics = AnalyticsService(db)
    return analytics.get_daily_trends(str(merchant.id), days)


@router.get("/merchant/payment-methods")
def merchant_payment_method_distribution(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
) -> Any:
    """
    Get distribution of payments by payment method for merchant
    
    Merchant-only endpoint
    """
    analytics = AnalyticsService(db)
    return analytics.get_payment_method_distribution(str(merchant.id), start_date, end_date)


@router.get("/merchant/payment-link-performance")
def merchant_payment_link_performance(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
) -> Any:
    """
    Get performance metrics for merchant's payment links
    
    Merchant-only endpoint
    """
    analytics = AnalyticsService(db)
    return analytics.get_payment_link_performance(str(merchant.id), days, limit)


@router.get("/merchant/verification-metrics")
def merchant_verification_metrics(
    *,
    db: Session = Depends(get_db),
    merchant: models.Merchant = Depends(get_merchant_by_api_key),
    days: int = Query(30, ge=1, le=90),
) -> Any:
    """
    Get metrics related to payment verification for merchant
    
    Merchant-only endpoint
    """
    analytics = AnalyticsService(db)
    return analytics.get_verification_metrics(str(merchant.id), days)