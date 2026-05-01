from sqlalchemy import String, Column, Integer, DateTime, Float, Boolean

from driver_service.db.session import Base

class LocalDriverAssignment(Base):
    __tablename__ = "local_drivers_assignment"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    is_available = Column(Boolean, default=True, index=True)

    last_lat = Column(Float, nullable=True)
    last_lng = Column(Float, nullable=True)

    last_location_update = Column(DateTime, nullable=True)