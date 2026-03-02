import json
import redis
from confluent_kafka import Consumer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "events.Order"
GROUP_ID = "analytics-group"

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

def is_duplicate_event(redis_client, event_id:str) -> bool:
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

        print(
            f"[ANALYTICS] Orders: {order_count}, "
            f"[ANALYTICS] Revenue: ${round(total_revenue, 2)}"
        )

def start_consumer():
    consumer = create_consumer()
    consumer.subscribe([TOPIC])
    print("[ANALYTICS] Analytics Service started...")

    redis_client = create_redis_client()
    print("[ANALYTICS]Redis client connected...")

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
                        
                    if is_duplicate_event(redis_client, event_id):
                        print(f"[ANALYTICS] Duplicate event {event_id} detected, skipping...")
                        continue    

                    process_event(event_payload)
                except json.JSONDecodeError as e:
                    print(f"[ANALYTICS]Failed to parse JSON: {e}")
            else:
                print("[ANALYTICS] Received a tombstone or empty message.")
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()