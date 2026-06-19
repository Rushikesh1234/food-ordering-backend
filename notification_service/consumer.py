import json
import redis
from confluent_kafka import Consumer

from notification_service.config.redis_config import redis_client, IDEMPOTENCY_TTL

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPICS = ["events.Order", "events.KitchenOrder"]
GROUP_ID = "customer-notification-group"

def is_duplicate_event(event_id:str) -> bool:
    key = f"notif_service:proc:{event_id}"
    is_new = redis_client.set(key, "true", nx=True, ex=IDEMPOTENCY_TTL)
    return is_new is None

def create_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest"
    })

def process_event(event_payload: dict):
    event_type = event_payload.get("event_type")

    if event_type == "OrderCreated":
        order_id = event_payload['order_id']
        total_amount = event_payload['total_amount']

        order_amount_in_dollars = total_amount / 100
        print(
            f"[NOTIFICATION] To Customer: Order {order_id} placed successfully!"
            f"Total: ${order_amount_in_dollars:,.2f}"
        )
        print(
            f"[NOTIFICATION] To Restaurant: New Order {order_id} received!"
            f"Total: ${order_amount_in_dollars:,.2f}"
        )
    
    elif event_type == "OrderStatusUpdated":
        new_status = event_payload['new_status']
        order_id = event_payload['order_id']

        if new_status == "ASSIGNED":
            print(f"[NOTIFICATION] To Driver: New Job! Please pick up Order {order_id}.")
            print(f"[NOTIFICATION] To Customer: Good news! A Driver has been assigned to you Order {order_id}.")
        elif new_status == "PICKED_UP":
            print(f"[NOTIFICATION] To Customer: Your food is on the way! Order {order_id}.")
        elif new_status == "DELIVERED":
            print(f"[NOTIFICATION] To Customer: Enjoy your meal! Order {order_id} delivered.")
        elif new_status == "CANCELLED":
            actor = event_payload['actor_role']
            if actor == "restaurant":
                msg = "The restaurant is unable to fulfill your order. You've been refunded."
            elif actor == "driver":
                msg = "The driver had an issue and cancelled the delivery. We are finding a new one."
            else:
                msg = "Your order has been cancelled successfully."

            print(f"[NOTIFICATION] To Customer: {msg}")
    
    elif event_type == "OrderPaid":
        order_id = event_payload['order_id']
        print(f"[NOTIFICATION] To Restaurant: Order {order_id} has been paid! Please start preparing it.")

def start_consumer():
    consumer = create_consumer()
    consumer.subscribe(TOPICS)
    print("[NOTIFICATION] Consumer Notificaiton Service Started...")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(f"[NOTIFICATION] Consumer error: {msg.error()}")
                continue
            
            message = msg.value()

            if message is not None:
                try:
                    event = json.loads(message.decode("utf-8"))
                    event_payload = event.get("payload", {})

                    event_id = event_payload.get("event_id")
                    
                    if not event_id:
                        print("[NOTIFICATION] Received event without event_id, skipping...")
                        continue
                        
                    if is_duplicate_event(event_id):
                        print(f"[NOTIFICATION] Duplicate event {event_id} detected, skipping...")
                        continue    

                    process_event(event_payload)
                except json.JSONDecodeError as e:
                    print(f"[NOTIFICATION] Failed to parse JSON: {e}")
            else:
                print("[NOTIFICATION] Received a tombstone or empty message.")
            
    except KeyboardInterrupt:
        pass
    
    finally:
        consumer.close()