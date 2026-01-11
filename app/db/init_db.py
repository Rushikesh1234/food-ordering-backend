from app.db.session import Base, engine
from app.models import restaurant, user, menu_item, order_item, order

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created.")

