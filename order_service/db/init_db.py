from order_service.db.session import Base, engine
from order_service.models import outbox
from order_service.models import local_sync, order, order_item

def init_db():
    print("🚀 Initializing Order Menu Microservice Database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Order and OrderItem tables created successfully.")

if __name__ == "__main__":
    init_db()