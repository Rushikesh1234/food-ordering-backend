from sqlalchemy import String, Column, Integer, Boolean, DateTime, UniqueConstraint, ForeignKey, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from restaurant_service.db.session import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    cuisine_type = Column(ARRAY(String), nullable=True)

    address = Column(JSONB, nullable=False)
    contact = Column(JSONB, nullable=False)
    settings = Column(JSONB, nullable=False)

    owner_id = Column(Integer, nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('name', 'slug', 'address', name='uix_restaurant_name_address'),
    )

    menu_items = relationship("MenuItem", back_populates="restaurant")
