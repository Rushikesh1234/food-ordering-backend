from sqlalchemy import Enum, Column, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from restaurant_service.db.session import Base

class KitchenOrderStatus(enum.Enum):
    RECEIVED = "RECEIVED"
    PREPARING = "PREPARING"
    CANCELLED = "CANCELLED"
    READY = "READY"

class KitchenOrder(Base):
    __tablename__ = "kitchen_orders"

    id = Column(Integer, primary_key=True)

    order_id = Column(Integer, unique=True, index=True)
    restaurant_id = Column(Integer, index=True)

    items = Column(JSONB) 
    
    # Internal kitchen status: RECEIVED, PREPARING, READY, CANCELLED
    status: Mapped[KitchenOrderStatus] = mapped_column(Enum(KitchenOrderStatus), default=KitchenOrderStatus.RECEIVED, nullable=False, index=True) 

    created_at = Column(DateTime, server_default=func.now())