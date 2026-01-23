import json
from confluent_kafka import Consumer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "order.events"
GROUP_ID = "analytics-group"

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
            f"Revenue: ${round(total_revenue, 2)}"
        )

def start_consumer():
    consumer = create_consumer()
    consumer.subscribe([TOPIC])

    print("Analytics Service started...")

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