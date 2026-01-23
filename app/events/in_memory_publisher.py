from app.events.publisher import EventPublisher

class InMemoryPublisher(EventPublisher):
    def publish(self, event) -> None:
        print(f"Event published: {event.json()}")