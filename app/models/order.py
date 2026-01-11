from sqlalchemy import ForeignKey, String, Column, Integer, DateTime, Numeric
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default='CREATED')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="order")
    restaurant = relationship("Restaurant", back_populates="order")
    order_item = relationship("OrderItem", back_populates="order")