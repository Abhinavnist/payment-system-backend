from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User

# Create database engine
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_user_permissions():
    """Update admin@example.com to be a superuser"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if user:
            print("\nUpdating user permissions...")
            user.is_superuser = True
            db.commit()
            print("User updated successfully")
            print(f"Email: {user.email}")
            print(f"Is Active: {user.is_active}")
            print(f"Is Superuser: {user.is_superuser}")
            print(f"API Key: {user.api_key}")
        else:
            print("\nUser not found")
    finally:
        db.close()

if __name__ == "__main__":
    update_user_permissions() 