# app/models/admin.py
from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Admin(Base):
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    user = relationship("User", backref="admin_profile")
    
    phone = Column(String, nullable=True)
    can_manage_merchants = Column(Boolean, default=True)
    can_verify_transactions = Column(Boolean, default=True)
    can_export_reports = Column(Boolean, default=True)
