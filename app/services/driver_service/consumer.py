import json
from confluent_kafka import Consumer
from typing import cast

from app.db.session import get_db_context

from app.services.order_validation.order_status_service import update_order_status

from app.models.user import User
from app.models.order import Order

from app.schemas.user import UserRole

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "order.events"
GROUP_ID = "drivers-assignment-group"

def create_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest"
    })

def process_event(event : dict):
    if event.get("event_type") == "OrderStatusUpdated" and event.get("new_status") == "READY":
        order_id = event.get("order_id")
        print(f"DEBUG: Order {order_id} is READY. Searching for a driver...")

        with get_db_context() as db:
            try:
                order = db.query(Order).filter(Order.id == order_id).first()
                if order:
                    if str(order.status) == "ASSIGNED":
                        print(f"DEBUG: Order {order_id} is already assigned. Skipping.")
                        return
                    else:
                        driver = db.query(User).filter(User.role == UserRole.DRIVER).first()
                        if driver:
                            system_user = User(id=0, role="system", email="system@foodapp.com")
                            update_order_status(
                                db,
                                system_user,
                                cast(int, order_id),
                                "ASSIGNED",
                                cast(int, driver.id)
                            )
                            print(f"SUCCESS: Order {order_id} assigned to Driver {driver.id}")
                        else:
                            print(f"WARNING: No drivers available for Order {order_id}")
                else:
                    print(f"ERROR: Order {order_id} does not exists.")
            except Exception as e:
                print(f"ERROR: Failed to assign driver for order {order_id}: {e}")

def start_consumer():
    consumer = create_consumer()
    consumer.subscribe([TOPIC])

    print("Driver Assignments Service started...")

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
                    process_event(event)
                except Exception as e:
                    print(f"Failed to parse JSON: {e}")
            else:
                print("Received a tombstone or empty message.")
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()