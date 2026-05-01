from driver_service.db.session import Base, engine
from driver_service.models import outbox
from driver_service.models import local_sync

def init_db():
    print("🚀 Initializing Driver Service Microservice Database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Driver Service tables created successfully.")

if __name__ == "__main__":
    init_db()