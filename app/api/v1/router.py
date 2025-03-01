# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.endpoints import auth, admin, merchants, payments, reports,analytics,whitelist

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(merchants.router, prefix="/merchants", tags=["merchants"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
# Analytics
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# IP Whitelist
api_router.include_router(whitelist.router, prefix="/whitelist", tags=["whitelist"])

