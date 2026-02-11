from sqlalchemy import ForeignKey, String, Column, Integer, DateTime, Numeric
import uuid
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.session import Base
from sqlalchemy.orm import relationship

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default='CREATED')

    idempotency_key = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    driver = relationship("User", back_populates="delivers", foreign_keys=[driver_id])

    restaurant = relationship("Restaurant", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")

 
class Outbox(Base):
    __tablename__ = "outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregatetype = Column(String)
    aggregateid = Column(String)
    type = Column(String)
    payload = Column(JSONB)
