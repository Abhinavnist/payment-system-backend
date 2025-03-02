import uvicorn
import logging
from fastapi import FastAPI, Request, Depends
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.middleware.ip_whitelist import IPWhitelistMiddleware
from app.middleware.rate_limiter import RateLimiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add rate limiting middleware first
app.add_middleware(RateLimiter)

# Add IP whitelist middleware
app.add_middleware(IPWhitelistMiddleware)

# Set all CORS enabled origins last
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)



@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        # Create initial data in DB
        init_db(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Welcome to the Payment System API", "docs": "/docs"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)