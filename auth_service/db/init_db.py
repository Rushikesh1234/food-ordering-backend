from auth_service.db.session import Base, engine
from auth_service.models import driver_profiles
from auth_service.models import outbox, user

def init_db():
    print("🚀 Initializing User Database...")
    Base.metadata.create_all(bind=engine)
    print("✅ User tables created successfully.")

if __name__ == "__main__":
    init_db()