import enum
from sqlalchemy import UniqueConstraint, Enum, String, Column, Integer, DateTime, ForeignKey
import uuid, enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from order_service.db.session import Base

class OrderStatus(enum.Enum):
    CREATED = "CREATED"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    ACCEPTED = "ACCEPTED"
    PREPARING = "PREPARING"
    READY = "READY"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False, index=True)

    restaurant_id = Column(Integer, ForeignKey("local_restaurants.id"), nullable=False, index=True)

    driver_id = Column(Integer, nullable=True, index=True)

    total_amount = Column(Integer, nullable=False, default=0)
    
    stripe_payment_intent_id = Column(String, nullable=True, index=True)

    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False, index=True)
    
    idempotency_key = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    order_items = relationship("OrderItem", back_populates="order")
    restaurant = relationship("LocalRestaurant", back_populates="orders")

    __table_args__ = (
        UniqueConstraint('user_id', 'idempotency_key', name='uix_user_id_idempotency_key'),
    )

    def __repr__(self):
        return f"<Order(id={self.id}, OrderStatus='{self.status.value}')>"

