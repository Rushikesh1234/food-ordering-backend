import json
from confluent_kafka import Consumer

from search_service.config.redis_config import redis_client, IDEMPOTENCY_TTL

from search_service.config.elasticsearch_config import get_sync_elasticsearch_client

from search_service.logic.index_logic import format_restaurant_doc, format_menuitem_doc

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPICS = ["events.Restaurant", "events.MenuItem"]
GROUP_ID = "elasticsearch-sync-group"

def creat_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest"
    })

def is_duplicate_event(event_id: int) -> bool:
    key = f"elasticsearch_service:proc:{event_id}"
    is_new = redis_client.set(key, "true", nx=True, ex=IDEMPOTENCY_TTL)
    return is_new is None

def process_event(elasticsearch_client, event_payload: dict):
    event_type = event_payload.get("event_type")

    if event_type == "RestaurantCreated":
        document = format_restaurant_doc(event_payload)

        if document: 
            elasticsearch_client.index(
                index = "restaurants",
                id = document["restaurant_id"],
                document = document
            )
            print(f"[ELASTICSEARCH SYNC]: New Restaurant Created - ID: {event_payload["restaurant_id"]}, Restaurant_Name: {event_payload["restaurant_name"]}")
        
    elif event_type == "MenuItemCreated":
        document = format_menuitem_doc(event_payload)

        if document:
            elasticsearch_client.index(
                index = "menuitems",
                id = document["menuitem_id"],
                document = document
            )
            print(f"[ELASTICSEARCH SYNC]: New MenuItem Created - ID: {event_payload["menuitem_id"]}, Menuitem_Name: {event_payload["menuitem_name"]} for Restaurant_ID: {event_payload.get("restaurant_name")} at Price: {event_payload["menuitem_price"]}")
        
    print(f"[ELASTICSEARCH Sync] Synced {event_type} to Elasticsearch")

def start_consumer():
    consumer = creat_consumer()
    consumer.subscribe(TOPICS)
    print("[ELASTICSEARCH Sync] Kafka Sync Service started...")

    elasticsearch_client = get_sync_elasticsearch_client()
    print("[ELASTICSEARCH Sync] Synchronized Elasticsearch client connected...")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print(f"[ELASTICSEARCH Sync] Consumer error: {msg.error()}")
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
                    
                    if is_duplicate_event(event_id):
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


