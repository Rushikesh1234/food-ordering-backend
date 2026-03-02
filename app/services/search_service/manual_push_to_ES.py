# For Migrating DB Tables to ES for Indexing for Old Data
# To run the script - python -m app.services.search_service.manual_push_to_ES

import os
import logging
from sqlalchemy import text
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
from app.db.session import get_db_context

load_dotenv()

ES_HOST = os.getenv("ELASTICSEARCH_HOST")
ES_USER = str(os.getenv("ES_USER", "elastic"))
ES_PASS = str(os.getenv("ES_PASSWORD"))

# Initialize ES Client
es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False,
    ssl_show_warn=False,
    request_timeout=30,
    retry_on_timeout=True
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def migrate_restaurants():
    with get_db_context() as db:
        logger.info("Fetching Restaurants...")
        query = text("SELECT id, name, address, phone_number, owner_id FROM restaurants")
        result = db.execute(query.execution_options(stream_results=True))
        
        def gen():
            for row in result.mappings():
                yield {
                    "_index": "restaurants",
                    "_id": str(row['id']),
                    "_source": {
                        "restaurant_id": row['id'],
                        "restaurant_name": row['name'],
                        "restaurant_address": row['address'],
                        "restaurant_phone_number": row['phone_number'],
                        "owner_id": row['owner_id']
                    }
                }
        
        success, _ = helpers.bulk(es, gen())
        logger.info(f"Successfully migrated {success} restaurants.")

def migrate_menu_items():
    with get_db_context() as db:
        logger.info("Fetching Menu Items...")
        # Note: I included restaurant_name in the query since your consumer expects it
        query = text("""
            SELECT m.id, m.name, m.description, m.price, m.restaurant_id, r.name as restaurant_name 
            FROM menu_items m
            JOIN restaurants r ON m.restaurant_id = r.id
        """)
        result = db.execute(query.execution_options(stream_results=True))
        
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
                        "menuitem_price": float(row['price'])
                    }
                }
        
        success, _ = helpers.bulk(es, gen())
        logger.info(f"Successfully migrated {success} menu items.")

if __name__ == "__main__":
    migrate_restaurants()
    migrate_menu_items()