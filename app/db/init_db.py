# app/db/init_db.py
import logging
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.core.config import settings
from app import models, schemas
from app.utils.security import get_password_hash

logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Check if we need to create a superuser
    user = db.query(models.User).filter(models.User.email == "admin@example.com").first()
    if not user:
        user_in = schemas.UserCreate(
            email="admin@example.com",
            password="admin",
            is_superuser=True,
            full_name="Initial Admin",
        )
        user = models.User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_superuser=user_in.is_superuser,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Initial superuser created")

