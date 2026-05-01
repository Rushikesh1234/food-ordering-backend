from sqlalchemy import UniqueConstraint, Enum, String, Column, Integer, DateTime, Boolean
import uuid, enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from order_service.db.session import Base

class LocalMenuItem(Base):
    __tablename__ = "local_menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    restaurant_id = Column(Integer, index=True)
    price = Column(Integer, nullable=False)
    is_available = Column(Boolean, default=True)

    order_items = relationship("OrderItem", back_populates="menu_item")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class LocalRestaurant(Base):
    __tablename__ = "local_restaurants"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    owner_id = Column(Integer)
    is_active = Column(Boolean, default=True)

    orders = relationship("Order", back_populates="restaurant")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class LocalDriver(Base):
    __tablename__ = "local_drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
