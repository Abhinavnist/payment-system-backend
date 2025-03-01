"""
API dependencies module for FastAPI dependency injection
This file redirects to the actual dependencies in utils/dependencies.py
"""

# Re-export dependencies from utils
from app.utils.dependencies import (
    get_db,
    get_current_user,
    get_current_active_superuser,
    get_merchant_by_api_key,
)