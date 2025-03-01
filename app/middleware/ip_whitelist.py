from typing import List, Callable, Optional
from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.merchant import Merchant

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check if the request IP is in the allowed list for merchant API endpoints
    """
    async def dispatch(self, request: Request, call_next):
        # Skip IP check for non-merchant endpoints and authentication endpoints
        path = request.url.path
        if not path.startswith("/api/v1/payments") and not path.startswith("/api/v1/reports"):
            return await call_next(request)
            
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        # Check if API key is provided
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return await call_next(request)
            
        # Get merchant by API key using a new database session
        db = SessionLocal()
        try:
            merchant = db.query(Merchant).filter(Merchant.api_key == api_key).first()
            
            if merchant and merchant.whitelist_ips:
                # Check if client IP is in whitelist
                if client_ip not in merchant.whitelist_ips:
                    raise HTTPException(
                        status_code=403, 
                        detail={"code": 1001, "message": "IP Address is not whitelisted"}
                    )
        finally:
            db.close()
                
        return await call_next(request)


# Add Middleware in main.py
# app.add_middleware(IPWhitelistMiddleware)


def check_ip_whitelist(request: Request, db: Session = Depends(SessionLocal)):
    """
    Dependency to check if request IP is whitelisted for the merchant
    Can be used for specific endpoints
    """
    client_ip = request.client.host if request.client else None
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(status_code=401, detail="API key missing")
        
    merchant = db.query(Merchant).filter(Merchant.api_key == api_key).first()
    
    if not merchant:
        raise HTTPException(status_code=401, detail="Invalid API key")
        
    if merchant.whitelist_ips and client_ip not in merchant.whitelist_ips:
        raise HTTPException(
            status_code=403, 
            detail={"code": 1001, "message": "IP Address is not whitelisted"}
        )
    
    return merchant