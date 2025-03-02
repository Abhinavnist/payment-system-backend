from typing import List, Callable, Optional
from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.db.session import SessionLocal
from app.models.merchant import Merchant

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check if the request IP is in the allowed list for merchant API endpoints
    """
    async def dispatch(self, request: Request, call_next):
        # Skip IP check for non-merchant endpoints
        path = request.url.path
        
        # List of paths to skip IP check
        skip_paths = [
            "/api/v1/auth",
            "/api/v1/admin",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        
        # Skip IP check for excluded paths
        for skip_path in skip_paths:
            if path.startswith(skip_path):
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
            
            # Only check whitelist if merchant exists and has whitelist configured
            if merchant and merchant.whitelist_ips and len(merchant.whitelist_ips) > 0:
                if client_ip not in merchant.whitelist_ips:
                    return JSONResponse(
                        status_code=403,
                        content={"code": 1001, "message": f"IP Address {client_ip} is not whitelisted"}
                    )
        except Exception as e:
            # Log the error but don't block the request
            print(f"Error in IP whitelist check: {str(e)}")
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
        return None  # Allow requests without API key
        
    merchant = db.query(Merchant).filter(Merchant.api_key == api_key).first()
    
    if not merchant:
        return None  # Allow if merchant not found
        
    if merchant.whitelist_ips and len(merchant.whitelist_ips) > 0 and client_ip not in merchant.whitelist_ips:
        raise HTTPException(
            status_code=403, 
            detail={"code": 1001, "message": f"IP Address {client_ip} is not whitelisted"}
        )
    
    return merchant