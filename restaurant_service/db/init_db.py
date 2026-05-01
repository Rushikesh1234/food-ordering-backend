from restaurant_service.db.session import Base, engine

from restaurant_service.models import outbox
from restaurant_service.models import menu_item, restaurant

def init_db():
    print("🚀 Initializing Restaurant Microservice Database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Restaurant tables created successfully.")

if __name__ == "__main__":
    init_db()