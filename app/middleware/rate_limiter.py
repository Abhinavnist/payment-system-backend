import time
from typing import Dict, Tuple, Optional
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from fastapi.responses import JSONResponse

class RateLimiter(BaseHTTPMiddleware):
    """
    Rate limiter middleware that limits requests based on client IP
    Different limits can be set for different API endpoints
    """
    def __init__(
        self, 
        app: FastAPI, 
        rate_limits: Optional[Dict[str, Tuple[int, int]]] = None
    ):
        """
        Initialize rate limiter
        
        Args:
            app: FastAPI application
            rate_limits: Dictionary of path patterns and their limits
                        Format: {path_prefix: (requests, seconds)}
                        Example: {"/api/v1/payments/": (100, 60)} -> 100 requests per 60 seconds
        """
        super().__init__(app)
        self.rate_limits = rate_limits or {
            # Default limits
            "/api/v1/payments/": (100, 60),  # 100 requests per minute
            "/api/v1/auth/": (20, 60),       # 20 requests per minute for auth endpoints
            "/api/v1/admin/": (300, 60),     # 300 requests per minute for admin
            "/api/v1/": (1000, 60),          # 1000 requests per minute overall
        }
        
        # Store request history: {ip: {path_prefix: [(timestamp, path), ...]}}
        self.request_history = defaultdict(lambda: defaultdict(list))

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Allow docs and OpenAPI endpoints without rate limiting
        if path.endswith(("/docs", "/openapi.json", "/redoc")):
            return await call_next(request)
            
        # Check rate limits for matching path prefixes
        current_time = time.time()
        
        for path_prefix, (max_requests, period) in self.rate_limits.items():
            if path.startswith(path_prefix):
                # Clean up old requests
                self.request_history[client_ip][path_prefix] = [
                    req for req in self.request_history[client_ip][path_prefix]
                    if current_time - req[0] < period
                ]
                
                # Add current request
                self.request_history[client_ip][path_prefix].append((current_time, path))
                
                # Check if limit exceeded
                if len(self.request_history[client_ip][path_prefix]) > max_requests:
                    # Set the retry-after header to the time remaining in the current window
                    oldest_timestamp = self.request_history[client_ip][path_prefix][0][0]
                    retry_after = int(period - (current_time - oldest_timestamp))
                    
                    # Return rate limit error
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": f"Rate limit exceeded. Try again in {retry_after} seconds."
                        },
                        headers={"Retry-After": str(retry_after)}
                    )
        
        # Proceed with the request
        return await call_next(request)


# Add to main.py
# app.add_middleware(RateLimiter)