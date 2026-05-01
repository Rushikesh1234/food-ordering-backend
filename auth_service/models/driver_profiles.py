from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from auth_service.db.session import Base

class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    license_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    vehicle_details = Column(String, nullable=True)

    user = relationship("User", back_populates="driver_profile")