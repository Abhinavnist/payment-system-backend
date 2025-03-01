import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, validator

class Settings:
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SERVER_NAME: str = "payment-system"
    SERVER_HOST: str = "http://localhost:8000"
    # BACKEND_CORS_ORIGINS is a list of origins
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str = "Payment System API"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "root"  # Using the password from your error
    POSTGRES_DB: str = "payment_system"
    
    # Directly construct the database URI as a string
    SQLALCHEMY_DATABASE_URI: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"

    # Payment system specific settings
    MIN_DEPOSIT_AMOUNT: int = 500
    MAX_DEPOSIT_AMOUNT: int = 300000
    MIN_WITHDRAWAL_AMOUNT: int = 1000
    MAX_WITHDRAWAL_AMOUNT: int = 1000000
    CURRENCY: str = "INR"
    
    # UPI settings
    UPI_TIMEOUT_SECONDS: int = 300  # Time for UPI payment completion
    
    # Security settings
    API_KEY_LENGTH: int = 64
    HASH_ALGORITHM: str = "SHA-256"
    
    # CSV export settings
    CSV_EXPORT_PATH: str = "exports"


settings = Settings()