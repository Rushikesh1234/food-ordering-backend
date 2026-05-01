import json
import redis
from confluent_kafka import Consumer

from analytics_service.config.redis_config import redis_client

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "events.Order"
GROUP_ID = "analytics-group"

EVENT_HISTORY_TTL = 7200
def is_duplicate_event(event_id:str) -> bool:
    key = f"analytics_service:proc:{event_id}"
    is_new = redis_client.set(key, "true", nx=True, ex=EVENT_HISTORY_TTL)
    return is_new is None

order_count = 0
total_revenue = 0.0

def create_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest"
    })

def process_event(event : dict):
    global order_count, total_revenue

    if event.get("event_type") == "OrderCreated":
        order_count += 1
        total_revenue += event["total_amount"]

        revenue_in_dollars = total_revenue / 100
        print(
            f"[ANALYTICS] Orders: {order_count}, "
            f"[ANALYTICS] Revenue: ${revenue_in_dollars:,.2f}"
        )

def start_consumer():
    consumer = create_consumer()
    consumer.subscribe([TOPIC])
    print("[ANALYTICS] Analytics Service started...")

    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            if msg.error():
                print(f"[ANALYTICS] Consumer error: {msg.error()}")
                continue
                
            message = msg.value()

            if message is not None:
                try:
                    event = json.loads(message.decode("utf-8"))
                    event_payload = event.get("payload", {})

                    event_id = event_payload.get("event_id")
                    
                    if not event_id:
                        print("[ANALYTICS] Received event without event_id, skipping...")
                        continue
                        
                    if is_duplicate_event(event_id):
                        print(f"[ANALYTICS] Duplicate event {event_id} detected, skipping...")
                        continue    

                    process_event(event_payload)
                except json.JSONDecodeError as e:
                    print(f"[ANALYTICS] Failed to parse JSON: {e}")
            else:
                print("[ANALYTICS] Received a tombstone or empty message.")
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()