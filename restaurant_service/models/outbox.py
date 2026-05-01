from sqlalchemy import String, Column, DateTime, Boolean
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB

from restaurant_service.db.session import Base

class Outbox(Base):
    __tablename__ = "outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregatetype = Column(String)
    aggregateid = Column(String)
    type = Column(String)
    payload = Column(JSONB)
    processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())