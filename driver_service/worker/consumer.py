import json
import uuid
from confluent_kafka import Consumer
from sqlalchemy.orm import Session
from typing import cast
from datetime import datetime

from driver_service.config.redis_config import redis_client

from driver_service.db.session import SessionLocal

from driver_service.schemas.driver_assign_events import DriverAssignedEvent

from driver_service.models.outbox import Outbox
from driver_service.models.local_sync import LocalDriverAssignment

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = ["events.Order", "events.User"]
GROUP_ID = "drivers-assignment-group"

EVENT_HISTORY_TTL = 7200
def is_duplicate_event(event_id:str) -> bool:
    key = f"driver_service:proc:{event_id}"
    is_new = redis_client.set(key, "true", nx=True, ex=EVENT_HISTORY_TTL)
    return is_new is None

def create_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest"
    })

def process_event(db:Session, event_payload : dict):

    event_type = event_payload.get("event_type")

    if (event_type == "UserCreated" or event_type == "UserUpdated") and event_payload.get("role") == "driver" :
        driver_id = event_payload["user_id"]
        driver = db.query(LocalDriverAssignment).filter(LocalDriverAssignment.id == driver_id).first()

        if not driver:
            driver = LocalDriverAssignment(
                id = driver_id
            )
            db.add(driver)

        driver.is_active = event_payload["is_active"]
        driver.name = event_payload["name"]

        print(f"[DRIVER ASSIGNMENT] Synced Driver Detail - ID: {driver.id}, Is_Active: {driver.is_active}, Name: {driver.name}")

    elif event_type == "OrderStatusUpdated" and event_payload.get("new_status") == "READY":
        order_id = event_payload.get("order_id")
        print(f"[DRIVER ASSIGNMENT] DEBUG: Order {order_id} is READY. Searching for a driver...")
                
        driver = db.query(LocalDriverAssignment).filter(
            LocalDriverAssignment.is_active == True,
            LocalDriverAssignment.is_available == True
        ).with_for_update(skip_locked=True).first()

        if driver:
            # system_user = User(id=0, role="system", email="system@foodapp.com")
            try:
                driver.is_available = cast(bool, False)  # type: ignore
                
                event_data = DriverAssignedEvent(
                    order_id = cast(int, order_id),
                    driver_id = cast(int, driver.id)
                )

                event_entry = Outbox(
                    id = uuid.uuid4(),
                    aggregatetype = "DriverAssignment",
                    aggregateid = str(order_id),
                    type = event_data.event_type,
                    payload = event_data.model_dump(mode='json')
                )
                db.add(event_entry)

                print(f"[DRIVER ASSIGNMENT] SUCCESS: Order {order_id} assigned to Driver {driver.id}")
            
            except Exception as e:
                db.rollback()
                print(f"[DRIVER ASSIGNMENT] ERROR: Failed to assign driver for order {order_id}: {e}")
        else:
            print(f"[DRIVER ASSIGNMENT] WARNING: No drivers available for Order {order_id}")

def start_consumer():
    consumer = create_consumer()
    consumer.subscribe(TOPIC)
    print("[DRIVER ASSIGNMENT] Driver Assignments Service started...")

    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            if msg.error():
                print(f"[DRIVER ASSIGNMENT] Consumer error: {msg.error()}")
                continue
                
            message = msg.value()

            if message is not None:
                try:
                    event = json.loads(message.decode("utf-8"))
                    event_payload = event.get("payload", {})

                    event_id = event_payload.get("event_id")
                    
                    if not event_id:
                        print("[DRIVER ASSIGNMENT] Received event without event_id, skipping...")
                        continue
                        
                    if is_duplicate_event(event_id):
                        print(f"[DRIVER ASSIGNMENT] Duplicate event {event_id} detected, skipping...")
                        continue    
                    
                    with SessionLocal() as db:
                        try:
                            process_event(
                                db=db,
                                event_payload=event_payload
                            )
                            db.commit()
                        except Exception as e:
                            db.rollback()
                            print(f"[DRIVER ASSIGNMENT] Error processing event: {e}")

                except json.JSONDecodeError as e:
                    print(f"[DRIVER ASSIGNMENT] Failed to parse JSON: {e}")
            else:
                print("[DRIVER ASSIGNMENT] Received a tombstone or empty message.")
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()