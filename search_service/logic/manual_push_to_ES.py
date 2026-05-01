import logging
from sqlalchemy import text
from elasticsearch import Elasticsearch, helpers

from search_service.db.session import SessionLocal

from search_service.config.elasticsearch_config import ES_CONFIG

# Initialize ES Client
es = Elasticsearch(**ES_CONFIG)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def migrate_restaurants():
    """Matches your format_restaurant_doc logic."""
    db = SessionLocal()
    try:
        logger.info("Migrating Restaurants...")
        # Query the raw data as it exists in PG
        query = text("""
            SELECT id, name, address, owner_id, contact, cuisine_type 
            FROM restaurants
        """)
        result = db.execute(query)
        
        def gen():
            for row in result.mappings():
                
                raw_cuisine = row.get('cuisine_type', [])
                categories = raw_cuisine
                if isinstance(categories, str):
                    categories = raw_cuisine.strip("{}").split(",")

                addr = row['address'] or {}
                full_address = f"{addr.get('unit', '')} {addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state_code', '')} {addr.get('zip_code', '')}".strip()
                
                contact = row['contact'] or {}
                contact_details = f"{contact.get("phone", "")} {contact.get("email", "")} {contact.get("website", "")}".strip()

                yield {
                    "_index": "restaurants",
                    "_id": str(row['id']),
                    "_source": {
                        "restaurant_id": row['id'],
                        "restaurant_name": row['name'],
                        "category": categories,
                        "restaurant_address": full_address,
                        "restaurant_contact": contact_details,
                        "owner_id": row['owner_id'],
                        "location": {
                            "lat": addr.get("geo", {}).get("lat"),
                            "lon": addr.get("geo", {}).get("lon")
                        }
                    }
                }
        
        success, _ = helpers.bulk(es, gen())
        logger.info(f"Migrated {success} restaurants.")
    finally:
        db.close()

def migrate_menu_items():
    """Matches your format_menuitem_doc logic."""
    db = SessionLocal()
    try:
        logger.info("Migrating Menu Items...")
        query = text("""
            SELECT m.id, m.name, m.description, m.price, m.restaurant_id, r.name as restaurant_name 
            FROM menu_items m
            JOIN restaurants r ON m.restaurant_id = r.id
        """)
        result = db.execute(query)
        
        def gen():
            for row in result.mappings():

                yield {
                    "_index": "menuitems",
                    "_id": str(row['id']),
                    "_source": {
                        "menuitem_id": row['id'],
                        "restaurant_id": row['restaurant_id'],
                        "restaurant_name": row['restaurant_name'],
                        "menuitem_name": row['name'],
                        "menuitem_description": row['description'],
                        "menuitem_price": int(row['price'])
                    }
                }
        
        success, _ = helpers.bulk(es, gen())
        logger.info(f"Migrated {success} menu items.")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_restaurants()
    migrate_menu_items()