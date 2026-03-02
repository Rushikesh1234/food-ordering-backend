import json
import redis
from confluent_kafka import Consumer
from typing import cast

from app.db.session import get_db_context

from app.services.order_service.update_order_status_service import update_order

from app.models.user import User
from app.models.order import Order

from app.schemas.user import UserRole

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "events.Order"
GROUP_ID = "drivers-assignment-group"

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
    key = f"driver_service:proc:{event_id}"
    is_new = redis_client.set(key, "true", nx=True, ex=EVENT_HISTORY_TTL)
    return is_new is None

def create_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest"
    })

def process_event(event : dict):
    if event.get("event_type") == "OrderStatusUpdated" and event.get("new_status") == "READY":
        order_id = event.get("order_id")
        print(f"[DRIVER ASSIGNMENT]DEBUG: Order {order_id} is READY. Searching for a driver...")

        with get_db_context() as db:
            try:
                order = db.query(Order).filter(Order.id == order_id).first()
                if not order:
                    print(f"[DRIVER ASSIGNMENT] ERROR: Order {order_id} does not exist.")
                    return
                
                if str(order.status) == "ASSIGNED":
                    print(f"[DRIVER ASSIGNMENT] DEBUG: Order {order_id} is already assigned. Skipping.")
                    return
                
                driver = db.query(User).filter(User.role == UserRole.DRIVER).first()
                if driver:
                    system_user = User(id=0, role="system", email="system@foodapp.com")
                    try:
                        update_order(
                            db,
                            system_user,
                            cast(int, order_id),
                            "ASSIGNED",
                            cast(int, driver.id),
                            commit=False
                        )
                        db.commit()
                        print(f"[DRIVER ASSIGNMENT] SUCCESS: Order {order_id} assigned to Driver {driver.id}")
                    except Exception as e:
                        db.rollback()
                        print(f"[DRIVER ASSIGNMENT] ERROR: Failed to assign driver for order {order_id}: {e}")
                else:
                    print(f"[DRIVER ASSIGNMENT]WARNING: No drivers available for Order {order_id}")
            except Exception as e:
                print(f"[DRIVER ASSIGNMENT] ERROR: Failed to assign driver for order {order_id}: {e}")

def start_consumer():
    consumer = create_consumer()
    consumer.subscribe([TOPIC])
    print("Driver Assignments Service started...")

    redis_client = create_redis_client()
    print("Redis client connected...")

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
                        print("Received event without event_id, skipping...")
                        continue
                        
                    if is_duplicate_event(redis_client, event_id):
                        print(f"Duplicate event {event_id} detected, skipping...")
                        continue    

                    process_event(event_payload)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
            else:
                print("Received a tombstone or empty message.")
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()