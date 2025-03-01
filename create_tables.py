#!/usr/bin/env python
"""
Script to create all database tables directly using SQLAlchemy
Use this if you're having issues with Alembic migrations
"""
import logging
import os
import sys

# Add the current directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base
from app.db.session import engine
from app.core.config import settings
from app import models
from app.utils.security import get_password_hash

from sqlalchemy.orm import Session
from sqlalchemy import inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db() -> None:
    # Create inspector to check if tables exist
    inspector = inspect(engine)
    
    # Check if tables exist
    if not inspector.has_table("user"):
        logger.info("Creating database tables...")
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully")
    else:
        logger.info("Tables already exist")
    
    # Create a session
    from app.db.session import SessionLocal
    db = SessionLocal()
    
    try:
        # Check if we need to create a superuser
        user = db.query(models.User).filter(models.User.email == "admin@example.com").first()
        if not user:
            logger.info("Creating initial superuser...")
            user = models.User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin"),
                full_name="Initial Admin",
                is_superuser=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Initial superuser created successfully")
        else:
            logger.info("Superuser already exists")
    except Exception as e:
        logger.error(f"Error creating superuser: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization completed")