import threading
from collections import defaultdict
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

EventType = str | type[T]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[EventType[Any], list[Callable[[Any], None]]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type: EventType[T], handler: Callable[[T], None]) -> None:
        with self._lock:
            self._subscribers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        event_type = type(event) if not isinstance(event, str) else event
        with self._lock:
            handlers = list(self._subscribers.get(event_type, []))
        for handler in handlers:
            handler(event)
