import json
import redis
from confluent_kafka import Consumer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "order.events"
GROUP_ID = "customer-notification-group"

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
    key = f"notif_service:proc:{event_id}"
    is_new = redis_client.set(key, "true", nx=True, ex=EVENT_HISTORY_TTL)
    return is_new is None

def create_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest"
    })

def process_event(event: dict):
    event_type = event.get("event_type")

    if event_type == "OrderCreated":
        order_id = event['order_id']
        total_amount = event['total_amount']
        print(
            f"[NOTIFICATION] To Customer: Order {order_id} placed successfully!"
            f"Total: ${total_amount}"
        )
        print(
            f"[NOTIFICATION] To Restaurant: New Order {order_id} received!"
            f"Total: ${total_amount}"
        )
    
    elif event_type == "OrderStatusUpdated":
        new_status = event['new_status']
        order_id = event['order_id']

        if new_status == "ASSIGNED":
            print(f"[NOTIFICATION] To Driver: New Job! Please pick up Order {order_id}.")
            print(f"[NOTIFICATION] To Customer: Good news! A Driver has been assigned to you Order {order_id}.")
        elif new_status == "PICKED_UP":
            print(f"[NOTIFICATION] To Customer: Your food is on the way! Order {order_id}.")
        elif new_status == "DELIVERED":
            print(f"[NOTIFICATION] To Customer: Enjoy your meal! Order {order_id} delivered.")
        elif new_status == "CANCELLED":
            actor = event['actor_role']
            if actor == "restaurant":
                msg = "The restaurant is unable to fulfill your order. You've been refunded."
            elif actor == "driver":
                msg = "The driver had an issue and cancelled the delivery. We are finding a new one."
            else:
                msg = "Your order has been cancelled successfully."

            print(f"[NOTIFICATION] To Customer: {msg}")

def start_consumer():
    consumer = create_consumer()
    consumer.subscribe([TOPIC])
    print("Consumer Notificaiton Service Started...")

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