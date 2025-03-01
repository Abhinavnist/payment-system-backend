#!/usr/bin/env python
"""
Simplified script to create database tables directly
"""
import logging
import os
import sys
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define database URL directly
DB_USER = "postgres"
DB_PASSWORD = "root"  # Using the password from your error message
DB_HOST = "localhost"
DB_NAME = "payment_system"
SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Define models directly in this script
class User(Base):
    __tablename__ = "user"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    api_key = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Admin(Base):
    __tablename__ = "admin"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    phone = Column(String, nullable=True)
    can_manage_merchants = Column(Boolean, default=True)
    can_verify_transactions = Column(Boolean, default=True)
    can_export_reports = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Merchant(Base):
    __tablename__ = "merchant"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    business_name = Column(String, nullable=False)
    business_type = Column(String, nullable=True)
    contact_phone = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    api_key = Column(String, unique=True, index=True, nullable=False)
    webhook_url = Column(String, nullable=True)
    callback_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    whitelist_ips = Column(JSONB, nullable=True)
    bank_details = Column(JSONB, nullable=True)
    upi_details = Column(JSONB, nullable=True)
    min_deposit = Column(Integer, default=500)
    max_deposit = Column(Integer, default=300000)
    min_withdrawal = Column(Integer, default=1000)
    max_withdrawal = Column(Integer, default=1000000)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class PaymentType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"

class PaymentMethod(str, enum.Enum):
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"

class Payment(Base):
    __tablename__ = "payment"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchant.id"), nullable=False)
    reference = Column(String, nullable=False, index=True)
    trxn_hash_key = Column(String, nullable=False, unique=True, index=True)
    payment_type = Column(Enum(PaymentType), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String, default="INR")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    upi_id = Column(String, nullable=True)
    qr_code_data = Column(Text, nullable=True)
    bank_name = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    utr_number = Column(String, nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    verification_method = Column(String, nullable=True)
    user_data = Column(JSONB, nullable=True)
    request_data = Column(JSONB, nullable=True)
    response_data = Column(JSONB, nullable=True)
    callback_sent = Column(Boolean, default=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

def create_tables():
    """Create all tables in the database"""
    inspector = inspect(engine)
    
    if not inspector.has_table("user"):
        logger.info("Creating database tables...")
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully")
    else:
        logger.info("Tables already exist")

def create_superuser():
    """Create initial superuser if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if superuser exists
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if not user:
            logger.info("Creating initial superuser...")
            # Generate password hash
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash("admin")
            
            # Create superuser
            user = User(
                email="admin@example.com",
                hashed_password=hashed_password,
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
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info(f"Connecting to database: {SQLALCHEMY_DATABASE_URI}")
    create_tables()
    create_superuser()
    logger.info("Database setup completed")