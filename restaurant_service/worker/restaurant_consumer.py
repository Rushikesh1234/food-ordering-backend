import json
import uuid
from typing import cast
from confluent_kafka import Consumer
from sqlalchemy.orm import Session

from restaurant_service.config.redis_config import redis_client, IDEMPOTENCY_TTL

from restaurant_service.db.session import SessionLocal

from restaurant_service.models.kitchen_order import KitchenOrder, KitchenOrderStatus

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPICS = ["events.Order"]
GROUP_ID = "order-service-sync-group"

def creat_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True
    })

def is_duplicate_event(event_id: int) -> bool:
    key = f"rest_svc:proc:{event_id}"
    is_new = redis_client.set(key, "true", nx=True, ex=IDEMPOTENCY_TTL)
    return is_new is None

def process_event(db:Session, event_payload: dict):

    event_type = event_payload.get("event_type")
    
    if event_type == "OrderPaid":
        order_id = event_payload['order_id']

        order_exists = db.query(KitchenOrder).filter(KitchenOrder.order_id == order_id).first()
        if order_exists:
            print(f"[Restaurant Order SYNC] Order {order_id} already exists, skipping...")
            return

        new_ticket = KitchenOrder(
            order_id = order_id,
            restaurant_id = event_payload.get("restaurant_id"),
            items = event_payload.get("items"),
            status = KitchenOrderStatus.RECEIVED
        )

        db.add(new_ticket)

    db.commit()
    print(f"[Restaurant Order SYNC] Synced {event_type} to Order Service")

def start_consumer():

    consumer = creat_consumer()
    consumer.subscribe(TOPICS)
    print("[Restaurant Order SYNC] Kafka Sync Service started...")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print(f"[Restaurant Order SYNC] Consumer error: {msg.error()}")
                continue

            message = msg.value()

            if message is not None:
                try:
                    event = json.loads(message.decode("utf-8"))
                    event_payload = event.get("payload", {})

                    event_id = event_payload.get("event_id")
                    
                    if not event_id:
                        print("[Restaurant Order SYNC] Received evetn without event_id, skipping...")
                        continue
                    
                    if is_duplicate_event(event_id):
                        print(f"[Restaurant Order SYNC] Duplicate event {event_id} detected, skipping...")
                        continue   

                    with SessionLocal() as db:
                        try:
                            process_event(
                                db=db,
                                event_payload=event_payload
                            )
                        except Exception as e:
                            db.rollback()
                            print(f"[Restaurant Order SYNC] Error processing event: {e}")

                except json.JSONDecodeError as e:
                    print(f"[Restaurant Order SYNC] Failed to parse JSON: {e}")
            else:    
                print("[Restaurant Order SYNC] Received a tombstone or enpty message.")
    
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()
