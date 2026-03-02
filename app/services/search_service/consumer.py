import json
from confluent_kafka import Consumer
import redis
from elasticsearch import Elasticsearch

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPICS = ["events.Restaurant", "events.MenuItem"]
GROUP_ID = "elasticsearch-sync-group"

def creat_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest"
    })

REDIS_HOST = "localhost"
REDIS_PORT = 6379
EVENT_HISTORY_TTL = 86400

def create_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        max_connections=50,
        socket_timeout=5
    )

def is_duplicate_event(redis_client, event_id: int) -> bool:
    key = f"elasticsearch_service:proc:{event_id}"
    is_new = redis_client.set(key, "true", nx=True, ex=EVENT_HISTORY_TTL)
    return is_new is None

import os
ES_HOST = str(os.getenv("ELASTICSEARCH_HOST"))
ES_USER = str(os.getenv("ES_USER", "elastic"))
ES_PASS = str(os.getenv("ES_PASSWORD"))

def create_elasticsearch_client():
    return Elasticsearch([ES_HOST], basic_auth=(ES_USER, ES_PASS), verify_certs=False)

def process_event(elasticsearch_client, event: dict):
    event_type = event.get("event_type")

    if event_type == "RestaurantCreated":
        
        restaurant_id = event.get("restaurant_id")
        if not restaurant_id:
            print("[ELASTICSEARCH RestaurantCreated SYNC]: Missing restaurant_id in event, skipping...")
            return

        document = {
            "restaurant_id" : restaurant_id,
            "restaurant_name" : event.get("restaurant_name"),
            "restaurant_address" : event.get("restaurant_address"),
            "restaurant_phone_number" : event.get("restaurant_phone_number"),
            "owner_id" : event.get("owner_id")
        }
        elasticsearch_client.index(
            index = "restaurants",
            id = document["restaurant_id"],
            document = document
        )
        print(f"[ELASTICSEARCH RestaurantCreated SYNC]: New Restaurant Created - ID: {event["restaurant_id"]}, Restaurant_Name: {event["restaurant_name"]}")
    
    elif event_type == "MenuItemCreated":

        menuitem_id = event.get("menuitem_id")
        if not menuitem_id:
            print("[ELASTICSEARCH MenuItemCreated SYNC]: Missing menuitem_id in event, skipping...")
            return

        document = {
            "menuitem_id" : menuitem_id,
            "restaurant_id" : event["restaurant_id"],  
            "restaurant_name" : event.get("restaurant_name"),  
            "menuitem_name" : event.get("menuitem_name"),
            "menuitem_description" : event.get("menuitem_description"),  
            "menuitem_price" : event.get("menuitem_price")
        }

        elasticsearch_client.index(
            index = "menuitems",
            id = document["menuitem_id"],
            document = document
        )

        print(f"[ELASTICSEARCH MenuItemCreated SYNC]: New MenuItem Created - ID: {event["menuitem_id"]}, Menuitem_Name: {event["menuitem_name"]} for Restaurant_ID: {event.get("restaurant_name")} at Price: {event["menuitem_price"]}")
    
    print(f"Synced {event_type} to Elasticsearch")

def start_consumer():
    consumer = creat_consumer()
    consumer.subscribe(TOPICS)
    print("[ELASTICSEARCH Sync] Elastcisearch Kafka Sync Service started...")

    redis_client = create_redis_client()
    print("[ELASTICSEARCH Sync] Redis client connected...")

    elasticsearch_client = create_elasticsearch_client()
    print("[ELASTICSEARCH Sync] Elasticsearch client connected...")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            message = msg.value()

            if message is not None:
                try:
                    event = json.loads(message.decode("utf-8"))
                    event_payload = event.get("payload", {})

                    event_id = event_payload.get("event_id")
                    
                    if not event_id:
                        print("[ELASTICSEARCH Sync] Received evetn without event_id, skipping...")
                        continue
                    
                    if is_duplicate_event(redis_client, event_id):
                        print(f"[ELASTICSEARCH Sync] Duplicate event {event_id} detected, skipping...")
                        continue   

                    process_event(elasticsearch_client, event_payload)
                except json.JSONDecodeError as e:
                    print("[ELASTICSEARCH Sync] Failed to parse JSON: {e}")
            else:    
                print("[ELASTICSEARCH Sync] Received a tombstone or enpty message.")
    
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()


