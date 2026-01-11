from sqlalchemy import String, Column, Integer, DateTime, UniqueConstraint, ForeignKey
from app.db.session import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('name', 'address', name='uix_restaurant_name_address'),
    )

    menu_item = relationship("MenuItem", back_populates="restaurant")
    order = relationship("Order", back_populates="restaurant")
    owner = relationship("User", back_populates="restaurant")
