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
from passlib.context import CryptContext
from sqlalchemy_utils import database_exists, create_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database configuration
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "root")
DB_HOST = os.getenv("POSTGRES_SERVER", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "payment_system")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# Create database URL
SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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

def hash_password(password: str) -> str:
    """Hash a password using passlib's bcrypt implementation"""
    return pwd_context.hash(password)

def create_tables():
    """Create all tables in the database"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def create_superuser():
    """Create initial superuser if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if superuser exists
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if not user:
            logger.info("Creating initial superuser...")
            
            # Create superuser with bcrypt hashed password
            password = "admin123"  # More secure default password
            hashed_password = hash_password(password)
            
            # Generate API key
            api_key = str(uuid.uuid4())
            
            # Create user record
            user = User(
                email="admin@example.com",
                hashed_password=hashed_password,
                full_name="Initial Admin",
                is_superuser=True,
                is_active=True,
                api_key=api_key
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create admin record
            admin = Admin(
                user_id=user.id,
                phone="1234567890",  # Default phone number
                can_manage_merchants=True,
                can_verify_transactions=True,
                can_export_reports=True
            )
            db.add(admin)
            db.commit()
            
            logger.info("Initial superuser and admin records created successfully")
            logger.info(f"Admin email: admin@example.com")
            logger.info(f"Admin password: {password}")
            logger.info(f"Admin API key: {api_key}")
        else:
            # Check if admin record exists
            admin = db.query(Admin).filter(Admin.user_id == user.id).first()
            if not admin:
                # Create admin record if it doesn't exist
                admin = Admin(
                    user_id=user.id,
                    phone="1234567890",  # Default phone number
                    can_manage_merchants=True,
                    can_verify_transactions=True,
                    can_export_reports=True
                )
                db.add(admin)
                db.commit()
                logger.info("Admin record created for existing superuser")
            
            # Ensure user has API key
            if not user.api_key:
                user.api_key = str(uuid.uuid4())
                db.commit()
                logger.info(f"Generated new API key for admin: {user.api_key}")
            
            logger.info("Superuser and admin records exist")
            logger.info(f"Admin email: {user.email}")
            logger.info(f"Admin API key: {user.api_key}")
    except Exception as e:
        logger.error(f"Error creating superuser: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def setup_database():
    """Initialize the database"""
    try:
        logger.info(f"Connecting to database: {SQLALCHEMY_DATABASE_URI}")
        
        # Create database if it doesn't exist
        if not database_exists(engine.url):
            create_database(engine.url)
            logger.info(f"Created database: {DB_NAME}")
        
        # Drop all tables and recreate
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped all existing tables")
        
        # Create tables
        create_tables()
        
        # Create superuser
        create_superuser()
        
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        raise

if __name__ == "__main__":
    setup_database()