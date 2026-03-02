from sqlalchemy import String, Column
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.session import Base

class Outbox(Base):
    __tablename__ = "outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregatetype = Column(String)
    aggregateid = Column(String)
    type = Column(String)
    payload = Column(JSONB)