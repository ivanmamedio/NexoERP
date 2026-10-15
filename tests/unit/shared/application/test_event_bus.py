from dataclasses import dataclass

from erp.shared.application.events import EventBus


@dataclass
class SampleEvent:
    value: int
    __test__ = False  # Evita que o pytest tente coletar esta classe como teste


def test_event_bus_subscribe_and_publish() -> None:
    bus = EventBus()
    received: list[int] = []

    def handler(event: SampleEvent) -> None:
        received.append(event.value)

    bus.subscribe(SampleEvent, handler)
    bus.publish(SampleEvent(42))

    assert received == [42]


def test_event_bus_multiple_handlers() -> None:
    bus = EventBus()
    results: list[int] = []

    bus.subscribe(SampleEvent, lambda e: results.append(e.value * 2))
    bus.subscribe(SampleEvent, lambda e: results.append(e.value * 3))

    bus.publish(SampleEvent(10))
    assert sorted(results) == [20, 30]


def test_event_bus_isolation() -> None:
    bus = EventBus()
    received_test: list[int] = []
    received_other: list[int] = []

    @dataclass
    class OtherEvent:
        __test__ = False

    bus.subscribe(SampleEvent, lambda e: received_test.append(e.value))
    bus.subscribe(OtherEvent, lambda e: received_other.append(1))

    bus.publish(SampleEvent(1))

    assert len(received_test) == 1
    assert len(received_other) == 0
