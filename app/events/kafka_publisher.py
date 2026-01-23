import json
from typing import cast
from confluent_kafka import Producer

from app.events.publisher import EventPublisher
from app.core.kafka_config import KAFKA_BOOTSTRAP_SERVERS, OREDER_EVENTS_TOPIC

class KafkaEventPublisher(EventPublisher):
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            "linger.ms": 10,
            'broker.address.family': 'v4'
        })

    def delivery_report(self, err, msg):
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def publish(self, event) -> None:
        try:
            event_data = event.model_dump()
            order_id = str(event_data.get("order_id"))
            json_payload = json.dumps(event_data, default=str)
            self.producer.produce(
                topic=OREDER_EVENTS_TOPIC,
                key=order_id.encode('utf-8'),
                value=json_payload.encode('utf-8'),
                callback=self.delivery_report
            )
            self.producer.flush()
        except Exception as e:
            print(f"Kafka publish error: {e}")