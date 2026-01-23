from abc import ABC, abstractmethod

class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event_name: str) -> None:
        """Publish an event with the given name."""
        pass